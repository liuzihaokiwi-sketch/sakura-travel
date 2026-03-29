"""
Ops API – Catalog CRUD（内容库管理）
提供酒店 / 餐厅 / 景点的列表查询、详情、创建、更新、删除接口。
供管理后台"内容库"页面使用。
"""
from __future__ import annotations

from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase, Poi, Hotel, Restaurant
from app.db.models.derived import EntityScore as EntityScoreModel
from app.db.session import get_db

router = APIRouter()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Pydantic 请求/响应模型
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EntityCreate(BaseModel):
    entity_type: str = Field(..., description="poi / hotel / restaurant")
    name_zh: str
    name_en: Optional[str] = None
    name_ja: Optional[str] = None
    city_code: str
    area_name: Optional[str] = None
    address_ja: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    data_tier: str = "B"
    is_active: bool = True
    google_place_id: Optional[str] = None
    # POI 专属
    poi_category: Optional[str] = None
    typical_duration_min: Optional[int] = None
    admission_fee_jpy: Optional[int] = None
    admission_free: bool = False
    google_rating: Optional[float] = None
    requires_advance_booking: bool = False
    # Hotel 专属
    hotel_type: Optional[str] = None
    star_rating: Optional[float] = None
    price_tier: Optional[str] = None
    typical_price_min_jpy: Optional[int] = None
    # Restaurant 专属
    cuisine_type: Optional[str] = None
    michelin_star: Optional[int] = None
    tabelog_score: Optional[float] = None
    price_range_min_jpy: Optional[int] = None
    price_range_max_jpy: Optional[int] = None
    requires_reservation: bool = False


class EntityUpdate(BaseModel):
    name_zh: Optional[str] = None
    name_en: Optional[str] = None
    name_ja: Optional[str] = None
    area_name: Optional[str] = None
    address_ja: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    data_tier: Optional[str] = None
    is_active: Optional[bool] = None
    google_place_id: Optional[str] = None
    # POI 专属
    poi_category: Optional[str] = None
    typical_duration_min: Optional[int] = None
    admission_fee_jpy: Optional[int] = None
    admission_free: Optional[bool] = None
    google_rating: Optional[float] = None
    requires_advance_booking: Optional[bool] = None
    # Hotel 专属
    hotel_type: Optional[str] = None
    star_rating: Optional[float] = None
    price_tier: Optional[str] = None
    typical_price_min_jpy: Optional[int] = None
    booking_score: Optional[float] = None
    # Restaurant 专属
    cuisine_type: Optional[str] = None
    michelin_star: Optional[int] = None
    tabelog_score: Optional[float] = None
    price_range_min_jpy: Optional[int] = None
    price_range_max_jpy: Optional[int] = None
    requires_reservation: Optional[bool] = None


class ScoreUpdate(BaseModel):
    editorial_boost: int = Field(..., ge=-8, le=8, description="编辑加权 -8 ~ +8")
    score_profile: str = Field("general", description="评分档案")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 辅助函数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _get_entity_or_404(db: AsyncSession, entity_id: str) -> EntityBase:
    try:
        uid = uuid.UUID(entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid entity_id")
    entity = await db.get(EntityBase, uid)
    if not entity:
        raise HTTPException(status_code=404, detail="entity not found")
    return entity


def _serialize_entity(entity: EntityBase, poi=None, hotel=None, restaurant=None, scores=None) -> dict:
    base = {
        "entity_id": str(entity.entity_id),
        "entity_type": entity.entity_type,
        "name_zh": entity.name_zh,
        "name_en": entity.name_en,
        "name_ja": entity.name_ja,
        "city_code": entity.city_code,
        "area_name": entity.area_name,
        "address_ja": entity.address_ja,
        "lat": float(entity.lat) if entity.lat else None,
        "lng": float(entity.lng) if entity.lng else None,
        "data_tier": entity.data_tier,
        "is_active": entity.is_active,
        "google_place_id": entity.google_place_id,
        "created_at": entity.created_at.isoformat() if entity.created_at else None,
        "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
        "scores": scores or [],
        "trust_status": getattr(entity, "trust_status", "unverified"),
        "verified_by": getattr(entity, "verified_by", None),
        "verified_at": entity.verified_at.isoformat() if getattr(entity, "verified_at", None) else None,
        "trust_note": getattr(entity, "trust_note", None),
        "data_source": (
            "google" if entity.google_place_id
            else "tabelog" if getattr(entity, "tabelog_id", None)
            else "ai"
        ),
    }
    if poi:
        base["poi_category"] = poi.poi_category
        base["typical_duration_min"] = poi.typical_duration_min
        base["admission_fee_jpy"] = poi.admission_fee_jpy
        base["admission_free"] = poi.admission_free
        base["google_rating"] = float(poi.google_rating) if poi.google_rating else None
        base["google_review_count"] = poi.google_review_count
        base["requires_advance_booking"] = poi.requires_advance_booking
        base["best_season"] = poi.best_season
        base["crowd_level_typical"] = poi.crowd_level_typical
    if hotel:
        base["hotel_type"] = hotel.hotel_type
        base["star_rating"] = float(hotel.star_rating) if hotel.star_rating else None
        base["chain_name"] = hotel.chain_name
        base["price_tier"] = hotel.price_tier
        base["typical_price_min_jpy"] = hotel.typical_price_min_jpy
        base["google_rating"] = float(hotel.google_rating) if hotel.google_rating else None
        base["booking_score"] = float(hotel.booking_score) if hotel.booking_score else None
        base["amenities"] = hotel.amenities or []
        base["is_family_friendly"] = hotel.is_family_friendly
        base["check_in_time"] = hotel.check_in_time
        base["check_out_time"] = hotel.check_out_time
    if restaurant:
        base["cuisine_type"] = restaurant.cuisine_type
        base["michelin_star"] = restaurant.michelin_star
        base["tabelog_score"] = float(restaurant.tabelog_score) if restaurant.tabelog_score else None
        base["google_rating"] = float(restaurant.tabelog_score) if restaurant.tabelog_score else None
        base["price_range_min_jpy"] = restaurant.price_range_min_jpy
        base["price_range_max_jpy"] = restaurant.price_range_max_jpy
        base["requires_reservation"] = restaurant.requires_reservation
        base["reservation_difficulty"] = restaurant.reservation_difficulty
        base["has_english_menu"] = restaurant.has_english_menu
    return base


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LIST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/catalog/entities")
async def list_entities(
    entity_type: Optional[str] = Query(None, description="poi / hotel / restaurant"),
    city_code: Optional[str] = Query(None),
    data_tier: Optional[str] = Query(None, description="S / A / B"),
    is_active: Optional[bool] = Query(None),
    trust_status: Optional[str] = Query(None, description="verified / unverified / ai_generated / suspicious / rejected"),
    q: Optional[str] = Query(None, description="搜索名称关键词"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """列出实体（酒店/餐厅/景点），支持过滤和分页"""
    stmt = select(EntityBase)
    if entity_type:
        stmt = stmt.where(EntityBase.entity_type == entity_type)
    if city_code:
        stmt = stmt.where(EntityBase.city_code == city_code)
    if data_tier:
        stmt = stmt.where(EntityBase.data_tier == data_tier)
    if is_active is not None:
        stmt = stmt.where(EntityBase.is_active == is_active)
    if trust_status:
        stmt = stmt.where(EntityBase.trust_status == trust_status)
    if q:
        stmt = stmt.where(
            EntityBase.name_zh.ilike(f"%{q}%") |
            EntityBase.name_en.ilike(f"%{q}%")
        )

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = stmt.order_by(EntityBase.updated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    entities = result.scalars().all()

    # 批量查各子表 + 评分
    entity_ids = [e.entity_id for e in entities]
    poi_map: dict = {}
    hotel_map: dict = {}
    rest_map: dict = {}
    score_map: dict = {}

    if entity_ids:
        # POI
        poi_res = await db.execute(select(Poi).where(Poi.entity_id.in_(entity_ids)))
        for p in poi_res.scalars().all():
            poi_map[p.entity_id] = p
        # Hotel
        hotel_res = await db.execute(select(Hotel).where(Hotel.entity_id.in_(entity_ids)))
        for h in hotel_res.scalars().all():
            hotel_map[h.entity_id] = h
        # Restaurant
        rest_res = await db.execute(select(Restaurant).where(Restaurant.entity_id.in_(entity_ids)))
        for r in rest_res.scalars().all():
            rest_map[r.entity_id] = r
        # Scores
        score_res = await db.execute(
            select(EntityScoreModel).where(EntityScoreModel.entity_id.in_(entity_ids))
        )
        for s in score_res.scalars().all():
            eid = s.entity_id
            if eid not in score_map:
                score_map[eid] = []
            score_map[eid].append({
                "score_id": s.score_id,
                "score_profile": s.score_profile,
                "base_score": float(s.base_score),
                "editorial_boost": s.editorial_boost,
                "final_score": float(s.final_score),
                "computed_at": s.computed_at.isoformat() if s.computed_at else None,
            })

    items = [
        _serialize_entity(
            e,
            poi=poi_map.get(e.entity_id),
            hotel=hotel_map.get(e.entity_id),
            restaurant=rest_map.get(e.entity_id),
            scores=score_map.get(e.entity_id, []),
        )
        for e in entities
    ]

    return {"total": total, "offset": offset, "limit": limit, "items": items}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GET ONE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/catalog/entities/{entity_id}")
async def get_entity(entity_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    entity = await _get_entity_or_404(db, entity_id)
    uid = entity.entity_id
    poi = (await db.execute(select(Poi).where(Poi.entity_id == uid))).scalar_one_or_none()
    hotel = (await db.execute(select(Hotel).where(Hotel.entity_id == uid))).scalar_one_or_none()
    restaurant = (await db.execute(select(Restaurant).where(Restaurant.entity_id == uid))).scalar_one_or_none()
    score_res = await db.execute(select(EntityScoreModel).where(EntityScoreModel.entity_id == uid))
    scores = [
        {
            "score_id": s.score_id,
            "score_profile": s.score_profile,
            "base_score": float(s.base_score),
            "editorial_boost": s.editorial_boost,
            "final_score": float(s.final_score),
            "computed_at": s.computed_at.isoformat() if s.computed_at else None,
        }
        for s in score_res.scalars().all()
    ]
    return _serialize_entity(entity, poi=poi, hotel=hotel, restaurant=restaurant, scores=scores)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CREATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/catalog/entities", status_code=201)
async def create_entity(body: EntityCreate, db: AsyncSession = Depends(get_db)) -> dict:
    """新建实体（同时建 entity_base + 子表）"""
    entity = EntityBase(
        entity_type=body.entity_type,
        name_zh=body.name_zh,
        name_en=body.name_en,
        name_ja=body.name_ja,
        city_code=body.city_code,
        area_name=body.area_name,
        address_ja=body.address_ja,
        lat=body.lat,
        lng=body.lng,
        data_tier=body.data_tier,
        is_active=body.is_active,
        google_place_id=body.google_place_id,
    )
    db.add(entity)
    await db.flush()  # 取得 entity_id

    if body.entity_type == "poi":
        poi = Poi(
            entity_id=entity.entity_id,
            poi_category=body.poi_category,
            typical_duration_min=body.typical_duration_min,
            admission_fee_jpy=body.admission_fee_jpy,
            admission_free=body.admission_free,
            google_rating=body.google_rating,
            requires_advance_booking=body.requires_advance_booking,
        )
        db.add(poi)
    elif body.entity_type == "hotel":
        hotel = Hotel(
            entity_id=entity.entity_id,
            hotel_type=body.hotel_type,
            star_rating=body.star_rating,
            price_tier=body.price_tier,
            typical_price_min_jpy=body.typical_price_min_jpy,
        )
        db.add(hotel)
    elif body.entity_type == "restaurant":
        restaurant = Restaurant(
            entity_id=entity.entity_id,
            cuisine_type=body.cuisine_type,
            michelin_star=body.michelin_star,
            tabelog_score=body.tabelog_score,
            price_range_min_jpy=body.price_range_min_jpy,
            price_range_max_jpy=body.price_range_max_jpy,
            requires_reservation=body.requires_reservation,
        )
        db.add(restaurant)

    await db.commit()
    await db.refresh(entity)
    return {"entity_id": str(entity.entity_id), "created": True}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BATCH TRUST UPDATE（必须在 {entity_id} 动态路由之前注册）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TrustUpdate(BaseModel):
    entity_ids: list[str]
    trust_status: str  # verified / suspicious / rejected / unverified / ai_generated
    trust_note: Optional[str] = None


@router.patch("/catalog/entities/batch-trust")
async def batch_update_trust(body: TrustUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    """批量更新 trust_status"""
    from sqlalchemy import update
    uids = [uuid.UUID(eid) for eid in body.entity_ids]
    await db.execute(
        update(EntityBase)
        .where(EntityBase.entity_id.in_(uids))
        .values(
            trust_status=body.trust_status,
            trust_note=body.trust_note,
            verified_by="admin",
            verified_at=func.now(),
        )
    )
    await db.commit()
    return {"updated": len(uids), "trust_status": body.trust_status}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPDATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.patch("/catalog/entities/{entity_id}")
async def update_entity(entity_id: str, body: EntityUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    """更新实体基础信息 + 子表字段"""
    entity = await _get_entity_or_404(db, entity_id)
    uid = entity.entity_id

    # 更新 entity_base
    for field in ("name_zh", "name_en", "name_ja", "area_name", "address_ja",
                  "lat", "lng", "data_tier", "is_active", "google_place_id"):
        val = getattr(body, field, None)
        if val is not None:
            setattr(entity, field, val)

    # 更新子表
    if entity.entity_type == "poi":
        poi = (await db.execute(select(Poi).where(Poi.entity_id == uid))).scalar_one_or_none()
        if poi:
            for field in ("poi_category", "typical_duration_min", "admission_fee_jpy",
                          "admission_free", "google_rating", "requires_advance_booking"):
                val = getattr(body, field, None)
                if val is not None:
                    setattr(poi, field, val)
    elif entity.entity_type == "hotel":
        hotel = (await db.execute(select(Hotel).where(Hotel.entity_id == uid))).scalar_one_or_none()
        if hotel:
            for field in ("hotel_type", "star_rating", "price_tier",
                          "typical_price_min_jpy", "booking_score"):
                val = getattr(body, field, None)
                if val is not None:
                    setattr(hotel, field, val)
    elif entity.entity_type == "restaurant":
        rest = (await db.execute(select(Restaurant).where(Restaurant.entity_id == uid))).scalar_one_or_none()
        if rest:
            for field in ("cuisine_type", "michelin_star", "tabelog_score",
                          "price_range_min_jpy", "price_range_max_jpy", "requires_reservation"):
                val = getattr(body, field, None)
                if val is not None:
                    setattr(rest, field, val)

    await db.commit()
    return {"entity_id": entity_id, "updated": True}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DELETE（软删除：is_active = False）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.delete("/catalog/entities/{entity_id}")
async def delete_entity(
    entity_id: str,
    hard: bool = Query(False, description="true 为物理删除，默认软删除"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """删除实体（默认软删除 is_active=False，hard=true 时物理删除）"""
    entity = await _get_entity_or_404(db, entity_id)
    if hard:
        await db.delete(entity)
    else:
        entity.is_active = False
    await db.commit()
    return {"entity_id": entity_id, "deleted": True, "hard": hard}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCORE：更新 editorial_boost
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.patch("/catalog/entities/{entity_id}/score")
async def update_score(entity_id: str, body: ScoreUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    """
    更新（或创建）某个 score_profile 下的 editorial_boost，重算 final_score。
    """
    entity = await _get_entity_or_404(db, entity_id)
    uid = entity.entity_id

    score = (
        await db.execute(
            select(EntityScoreModel)
            .where(EntityScoreModel.entity_id == uid)
            .where(EntityScoreModel.score_profile == body.score_profile)
        )
    ).scalar_one_or_none()

    if score:
        score.editorial_boost = body.editorial_boost
        raw = float(score.base_score) + body.editorial_boost
        score.final_score = max(0.0, min(100.0, raw))
    else:
        # 如果还没有评分记录，创建一条
        score = EntityScoreModel(
            entity_id=uid,
            score_profile=body.score_profile,
            base_score=50.0,
            editorial_boost=body.editorial_boost,
            final_score=max(0.0, min(100.0, 50.0 + body.editorial_boost)),
        )
        db.add(score)

    await db.commit()
    return {
        "entity_id": entity_id,
        "score_profile": body.score_profile,
        "editorial_boost": body.editorial_boost,
        "final_score": float(score.final_score),
    }
