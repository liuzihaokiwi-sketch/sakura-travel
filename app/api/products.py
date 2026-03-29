"""
Products API  (D2.2 — 从 DB 读取 SKU)
======================================
GET  /products                    — 返回所有 is_active=True 的 SKU
GET  /products/{sku_id}           — 返回单个 SKU 详情
GET  /products/{sku_id}/price     — 计算实际价格（含额外天数加价）
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.business import ProductSku

router = APIRouter(prefix="/products", tags=["products"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SkuItem(BaseModel):
    sku_id: str
    name: str
    description: str
    price_cny: float
    currency: str = "CNY"
    sku_type: str
    max_days: Optional[int] = None
    features: Dict[str, Any] = {}
    # 兼容旧字段
    includes: List[str] = []
    template_codes: List[str] = []
    supported_scenes: List[str] = ["couple", "family", "solo", "senior"]


class ProductListResponse(BaseModel):
    products: List[SkuItem]
    total: int


class PriceResponse(BaseModel):
    sku_id: str
    base_price_cny: float
    base_days: int
    requested_days: int
    extra_days: int
    extra_day_price: float
    volumes: int = 1
    split_book_price: float = 0.0
    total_price_cny: float
    currency: str = "CNY"
    formula: str = ""


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _sku_to_item(sku: ProductSku) -> SkuItem:
    """将 DB ProductSku 转换为 API SkuItem"""
    features = sku.features or {}
    workflow = features.get("workflow_config", {})
    sections = features.get("sections", [])

    # 构造 includes 列表（从 sections 映射为中文描述）
    section_desc = {
        "daily_timeline":          "AI 智能行程时间轴",
        "route_map":               "每日路线地图",
        "spot_info":               "景点详细信息",
        "area_hotel_tip":          "住宿区域建议",
        "basic_transport":         "基础交通指南",
        "transport":               "交通方案",
        "transport_detailed":      "详细交通方案",
        "transport_optimal":       "最优交通组合",
        "transport_pass_guide":    "交通卡攻略",
        "hotel_list_simple":       "推荐酒店列表",
        "hotel_report":            "酒店分析报告",
        "hotel_report_detailed":   "酒店深度分析报告",
        "restaurant_report":       "餐厅推荐报告",
        "restaurant_report_detailed": "餐厅深度推荐报告",
        "pre_trip_guide":          "出行前准备攻略",
        "safety_guide":            "安全须知",
        "avoid_traps":             "避坑指南（基础版）",
        "avoid_traps_deep":        "避坑指南（深度版）",
        "photo_spots":             "摄影机位攻略",
        "instagrammable_guide":    "出片+穿搭攻略",
        "hotel_compare_report":    "酒店比价报告",
        "savings_summary":         "省钱总结报告",
        "version_comparison":      "多版本行程对比",
        "honeymoon_highlights":    "蜜月特色体验推荐",
        "luxury_dining":           "高端餐厅精选",
    }
    includes = [section_desc.get(s, s) for s in sections if s in section_desc]

    # 从 workflow_config 读取天数信息
    base_days = workflow.get("base_days") or workflow.get("fixed_days") or (sku.max_days or 7)

    return SkuItem(
        sku_id=sku.sku_id,
        name=sku.sku_name,
        description=_build_description(sku.sku_name, sku.price_cny, features),
        price_cny=float(sku.price_cny),
        sku_type=sku.sku_type,
        max_days=sku.max_days,
        features=features,
        includes=includes,
        template_codes=[
            "tokyo_classic_3d",
            "tokyo_classic_5d",
            "tokyo_sakura_7d",
            "kansai_classic_4d",
            "kansai_classic_6d",
            "tokyo_kansai_8d",
        ],
        supported_scenes=["couple", "family", "solo", "senior"],
    )


def _build_description(name: str, price: float, features: dict) -> str:
    wf = features.get("workflow_config", {})
    mode = wf.get("mode", "template")
    base_days = wf.get("base_days") or wf.get("fixed_days") or 7
    extra = wf.get("extra_day_price")

    desc = f"¥{price} · {name}。"
    if mode == "template":
        desc += f"固定 {base_days} 天模板行程，含杂志级 PDF + H5 预览。"
    elif mode in ("auto_generate", "personalized", "deep_personalized"):
        desc += f"基础 {base_days} 天个性化行程"
        if extra:
            desc += f"，每多 1 天加 ¥{extra}"
        desc += "。"
    elif mode == "premium":
        desc += f"高端全案 {base_days} 天起，含机票+酒店比价优化。"
    elif mode == "full_custom":
        desc += f"蜜月全案定制 {base_days} 天起，专人顾问+全程比价。"
    return desc


# ── 价格常量（与 seed_product_skus.py 保持一致）─────────────────────────────
_BASE_PRICE_CNY = 198
_BASE_DAYS_INCLUDED = 3
_EXTRA_DAY_PRICE = 20
_SPLIT_BOOK_PRICE = 29

# ── 静态 fallback（DB 为空时返回）────────────────────────────────────────────
_FALLBACK_PRODUCTS: List[SkuItem] = [
    SkuItem(
        sku_id="standard_198",
        name="日本旅行·完整攻略",
        description="¥198起 · 含3天行程，每多1天+¥20，拆册+¥29/册。",
        price_cny=198.0,
        sku_type="standard",
        max_days=21,
        features={
            "pricing": {
                "base_price_cny": _BASE_PRICE_CNY,
                "base_days_included": _BASE_DAYS_INCLUDED,
                "extra_day_price": _EXTRA_DAY_PRICE,
                "split_book_price": _SPLIT_BOOK_PRICE,
                "formula": "¥198 + ¥20×(天数-3) + ¥29×(册数-1)",
            },
            "workflow_config": {
                "mode": "personalized",
                "allow_custom_days": True,
                "base_days": _BASE_DAYS_INCLUDED,
                "extra_day_price": _EXTRA_DAY_PRICE,
                "split_book_price": _SPLIT_BOOK_PRICE,
            },
        },
        includes=["AI 智能行程时间轴", "路线地图", "景点详细信息", "住宿区域建议",
                  "交通卡攻略", "餐厅推荐报告", "出行前准备攻略", "避坑指南（基础版）",
                  "拍照攻略", "Plan B 备选方案", "预订优先级提醒", "全程预算参考"],
        template_codes=["kansai_classic_5d", "kansai_classic_6d",
                        "tokyo_classic_3d", "tokyo_classic_5d"],
        supported_scenes=["couple", "family", "solo", "senior"],
    ),
]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=ProductListResponse, summary="获取 SKU 列表")
async def list_products(
    db: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    """返回所有上线 SKU（is_active=True），按价格升序排列。"""
    result = await db.execute(
        select(ProductSku)
        .where(ProductSku.is_active == True)  # noqa: E712
        .order_by(ProductSku.price_cny.asc())
    )
    skus = result.scalars().all()

    if not skus:
        # DB 没有数据时返回静态 fallback
        return ProductListResponse(products=_FALLBACK_PRODUCTS, total=len(_FALLBACK_PRODUCTS))

    items = [_sku_to_item(s) for s in skus]
    return ProductListResponse(products=items, total=len(items))


@router.get("/{sku_id}", response_model=SkuItem, summary="获取单个 SKU 详情")
async def get_product(
    sku_id: str,
    db: AsyncSession = Depends(get_db),
) -> SkuItem:
    """获取指定 SKU 详情（含 features / workflow_config / component_config）"""
    sku = (await db.execute(
        select(ProductSku).where(
            ProductSku.sku_id == sku_id,
            ProductSku.is_active == True,  # noqa: E712
        )
    )).scalar_one_or_none()

    if sku is None:
        # 兼容旧 sku_id: basic_v1 → basic_20
        if sku_id == "basic_v1":
            sku = (await db.execute(
                select(ProductSku).where(ProductSku.sku_id == "basic_20")
            )).scalar_one_or_none()

    if sku is None:
        raise HTTPException(status_code=404, detail=f"SKU '{sku_id}' not found")

    return _sku_to_item(sku)


@router.get("/{sku_id}/price", response_model=PriceResponse, summary="计算实际价格（含加天费+拆册费）")
async def calculate_price(
    sku_id: str,
    days: int = Query(..., ge=1, le=90, description="实际出行天数"),
    volumes: int = Query(1, ge=1, le=10, description="手账本册数（拆册）"),
    db: AsyncSession = Depends(get_db),
) -> PriceResponse:
    """
    计算指定 SKU + 天数 + 册数的实际价格。

    新定价公式（2026.03）:
      total = base_price + max(0, days - base_days) * extra_day_price
                         + max(0, volumes - 1) * split_book_price

    示例: standard_198 选 7 天 1 册 → ¥198 + 4×¥20 = ¥278
    示例: standard_198 选 7 天 2 册 → ¥198 + 4×¥20 + 1×¥29 = ¥307
    """
    sku = (await db.execute(
        select(ProductSku).where(
            ProductSku.sku_id == sku_id,
            ProductSku.is_active == True,  # noqa: E712
        )
    )).scalar_one_or_none()

    if sku is None:
        raise HTTPException(status_code=404, detail=f"SKU '{sku_id}' not found")

    features = sku.features or {}
    workflow = features.get("workflow_config", {})
    base_days: int = workflow.get("base_days") or workflow.get("fixed_days") or (sku.max_days or 7)
    extra_day_price: float = float(workflow.get("extra_day_price", _EXTRA_DAY_PRICE))
    split_book_price: float = float(workflow.get("split_book_price", _SPLIT_BOOK_PRICE))
    base_price = float(sku.price_cny)

    extra_days = max(0, days - base_days)
    extra_volumes = max(0, volumes - 1)
    total_price = base_price + extra_days * extra_day_price + extra_volumes * split_book_price

    return PriceResponse(
        sku_id=sku_id,
        base_price_cny=base_price,
        base_days=base_days,
        requested_days=days,
        extra_days=extra_days,
        extra_day_price=extra_day_price,
        volumes=volumes,
        split_book_price=split_book_price if extra_volumes > 0 else 0.0,
        total_price_cny=round(total_price, 2),
        formula=f"¥{base_price:.0f} + ¥{extra_day_price:.0f}×{extra_days} + ¥{split_book_price:.0f}×{extra_volumes}",
    )