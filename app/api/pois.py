from __future__ import annotations

"""
POI / 实体搜索 API

GET  /pois               搜索景点（支持 city / category / keyword 过滤）
GET  /pois/{entity_id}   获取单个景点详情
GET  /cities             返回已支持的城市列表
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase, Hotel, Poi, Restaurant
from app.db.session import get_db

router = APIRouter(prefix="/pois", tags=["pois"])
cities_router = APIRouter(prefix="/cities", tags=["cities"])


# ── 响应模型 ──────────────────────────────────────────────────────────────────

class PoiOut(BaseModel):
    entity_id: str
    entity_type: str
    name_zh: str
    name_ja: Optional[str] = None
    city_code: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    poi_category: Optional[str] = None
    typical_duration_min: Optional[int] = None
    admission_fee_jpy: Optional[int] = None
    google_rating: Optional[float] = None
    google_review_count: Optional[int] = None
    best_season: Optional[str] = None
    cuisine_type: Optional[str] = None
    budget_lunch_jpy: Optional[int] = None
    budget_dinner_jpy: Optional[int] = None
    tabelog_score: Optional[float] = None
    price_tier: Optional[str] = None
    star_rating: Optional[float] = None
    typical_price_min_jpy: Optional[int] = None
    maps_url: Optional[str] = None


class PoiListResponse(BaseModel):
    total: int
    items: List[PoiOut]


# ── 辅助 ──────────────────────────────────────────────────────────────────────

_CITY_ZH = {
    "tokyo": "东京", "osaka": "大阪", "kyoto": "京都",
    "nara": "奈良", "hakone": "箱根", "hiroshima": "广岛",
    "sapporo": "札幌", "fukuoka": "福冈", "naha": "那霸（冲绳）",
    "nagoya": "名古屋", "nikko": "日光", "kamakura": "镰仓",
}


def _maps_url(name: str) -> str:
    import urllib.parse
    return f"https://maps.google.com/?q={urllib.parse.quote(name + ' Japan')}"


def _build_poi_out(entity: EntityBase) -> PoiOut:
    data: dict[str, Any] = {
        "entity_id": str(entity.entity_id),
        "entity_type": entity.entity_type,
        "name_zh": entity.name_zh or "",
        "name_ja": entity.name_ja,
        "city_code": entity.city_code,
        "lat": float(entity.lat) if entity.lat else None,
        "lng": float(entity.lng) if entity.lng else None,
        "maps_url": _maps_url(entity.name_zh or entity.name_ja or ""),
    }

    if entity.entity_type == "poi" and entity.poi:
        p = entity.poi
        data.update({
            "poi_category": p.poi_category,
            "typical_duration_min": p.typical_duration_min,
            "admission_fee_jpy": p.admission_fee_jpy,
            "google_rating": float(p.google_rating) if p.google_rating else None,
            "google_review_count": p.google_review_count,
            "best_season": p.best_season,
        })
    elif entity.entity_type == "restaurant" and entity.restaurant:
        r = entity.restaurant
        data.update({
            "cuisine_type": r.cuisine_type,
            "budget_lunch_jpy": r.budget_lunch_jpy,
            "budget_dinner_jpy": r.budget_dinner_jpy,
            "tabelog_score": float(r.tabelog_score) if r.tabelog_score else None,
        })
    elif entity.entity_type == "hotel" and entity.hotel:
        h = entity.hotel
        data.update({
            "price_tier": h.price_tier,
            "star_rating": float(h.star_rating) if h.star_rating else None,
            "typical_price_min_jpy": h.typical_price_min_jpy,
            "google_rating": float(h.google_rating) if h.google_rating else None,
        })

    return PoiOut(**data)


# ── GET /pois ─────────────────────────────────────────────────────────────────

@router.get("", response_model=PoiListResponse)
async def search_pois(
    city: Optional[str] = Query(None, description="城市代码：kyoto / tokyo / osaka ..."),
    entity_type: Optional[str] = Query(None, description="类型：poi / restaurant / hotel"),
    category: Optional[str] = Query(None, description="POI分类：shrine/temple/park/museum/castle/landmark/shopping/onsen/theme_park"),
    keyword: Optional[str] = Query(None, description="名称模糊搜索（中/日文）"),
    season: Optional[str] = Query(None, description="季节：spring/summer/autumn/winter"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="最低评分"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> PoiListResponse:
    """
    搜索景点/餐厅/酒店。可按城市、类型、分类、关键词、季节、评分过滤。
    """
    # 基础 stmt
    if entity_type == "restaurant":
        stmt = (
            select(EntityBase)
            .join(Restaurant, Restaurant.entity_id == EntityBase.entity_id)
            .where(EntityBase.is_active.is_(True), EntityBase.entity_type == "restaurant")
            .order_by(Restaurant.tabelog_score.desc().nulls_last())
        )
    elif entity_type == "hotel":
        stmt = (
            select(EntityBase)
            .join(Hotel, Hotel.entity_id == EntityBase.entity_id)
            .where(EntityBase.is_active.is_(True), EntityBase.entity_type == "hotel")
            .order_by(Hotel.google_rating.desc().nulls_last())
        )
    else:
        stmt = (
            select(EntityBase)
            .outerjoin(Poi, Poi.entity_id == EntityBase.entity_id)
            .where(EntityBase.is_active.is_(True))
        )
        if entity_type:
            stmt = stmt.where(EntityBase.entity_type == entity_type)
        if category:
            stmt = stmt.where(Poi.poi_category == category)
        if season:
            stmt = stmt.where(or_(Poi.best_season == season, Poi.best_season.is_(None)))
        if min_rating is not None:
            stmt = stmt.where(Poi.google_rating >= min_rating)
        stmt = stmt.order_by(Poi.google_rating.desc().nulls_last())

    # 通用过滤
    if city:
        stmt = stmt.where(EntityBase.city_code == city)
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(or_(EntityBase.name_zh.ilike(kw), EntityBase.name_ja.ilike(kw)))

    # 总数（简化版，不带复杂 join）
    count_stmt = select(EntityBase.entity_id).where(EntityBase.is_active.is_(True))
    if city:
        count_stmt = count_stmt.where(EntityBase.city_code == city)
    if entity_type:
        count_stmt = count_stmt.where(EntityBase.entity_type == entity_type)
    count_result = await db.execute(count_stmt)
    total = len(count_result.all())

    # 分页查询
    result = await db.execute(stmt.offset(offset).limit(limit))
    entities = result.scalars().unique().all()

    items = []
    for entity in entities:
        await db.refresh(entity, ["poi", "restaurant", "hotel"])
        items.append(_build_poi_out(entity))

    return PoiListResponse(total=total, items=items)


# ── GET /pois/{entity_id} ─────────────────────────────────────────────────────

@router.get("/{entity_id}", response_model=PoiOut)
async def get_poi_detail(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
) -> PoiOut:
    """获取单个实体详情"""
    import uuid as _uuid
    try:
        eid = _uuid.UUID(entity_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid entity_id")

    result = await db.execute(select(EntityBase).where(EntityBase.entity_id == eid))
    entity = result.scalar_one_or_none()
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")

    await db.refresh(entity, ["poi", "restaurant", "hotel"])
    return _build_poi_out(entity)


# ── GET /cities ───────────────────────────────────────────────────────────────

@cities_router.get("")
async def list_cities(db: AsyncSession = Depends(get_db)) -> dict:
    """返回 DB 中有数据的城市列表"""
    result = await db.execute(
        select(EntityBase.city_code).where(EntityBase.is_active.is_(True)).distinct()
    )
    codes = sorted({row[0] for row in result.all()})
    return {
        "cities": [
            {"city_code": code, "city_name_zh": _CITY_ZH.get(code, code)}
            for code in codes
        ]
    }
