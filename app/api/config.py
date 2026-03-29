"""
GET /config/product-tiers
返回当前活跃的产品定价配置，供前端价格页动态渲染。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.soft_rules import ProductConfig

router = APIRouter(prefix="/config", tags=["config"])

# ── 硬编码兜底（若 DB 无数据时使用）────────────────────────────────────────
_DEFAULT_TIERS = {
    "tiers": [
        {
            "id": "free",
            "name": "一日体验版",
            "tagline": "先看看适不适合你",
            "price": 0,
            "price_display": "免费",
            "price_note": "",
            "original_price": None,
            "featured": False,
            "badge": None,
            "cta": "先免费看一天 →",
            "href": "/quiz",
            "modifications": 0,
            "includes": [
                "1 天完整行程安排",
                "2-3 个景点的推荐理由",
                "当天交通指引",
                "行程品质预览",
            ],
            "excludes": [
                "其余天数行程",
                "餐厅和酒店推荐",
                "避坑指南和出行准备",
            ],
            "who": "想先看看效果再决定的人",
        },
        {
            "id": "standard",
            "name": "完整攻略",
            "tagline": "完整行程 · 每一天都安排好",
            "price": 198,
            "price_display": "¥198起",
            "price_note": "含3天 · 每多1天+¥20 · 拆册+¥29/册",
            "original_price": None,
            "featured": True,
            "badge": "🔥 90%用户选择",
            "cta": "先免费看一天 →",
            "href": "/quiz",
            "modifications": 2,
            "includes": [
                "全程每日行程（30-40页完整攻略）",
                "每天为什么这样安排的解释",
                "餐厅精选 + 预约指引 + 替代方案",
                "酒店区域建议 + 选择理由",
                "交通最优方案 + 省钱技巧",
                "避坑指南 + 出行前准备清单",
                "拍照攻略 + 最佳时段",
                "Plan B 备选方案",
                "预订优先级提醒",
                "全程预算参考",
                "2 次行程精调",
            ],
            "excludes": [
                "1对1深度沟通",
                "出行期间答疑",
            ],
            "who": "第一次去日本、想省心不踩坑的人",
        },
        {
            "id": "premium",
            "name": "尊享定制版",
            "tagline": "有人帮你全程把关",
            "price": 888,
            "price_display": "¥888",
            "price_note": "",
            "original_price": None,
            "featured": False,
            "badge": None,
            "cta": "了解尊享定制 →",
            "href": "/quiz",
            "modifications": 5,
            "includes": [
                "完整攻略全部内容",
                "1对1需求深度沟通",
                "5 次行程精调",
                "出行期间实时答疑",
                "蜜月/纪念日特别安排",
                "隐藏小众目的地推荐",
                "高端餐厅酒店精选",
            ],
            "excludes": [],
            "who": "蜜月、纪念日、或想要全程有人跟进的人",
        },
    ],
    "compare_rows": [
        {"label": "知道每天去哪、路线怎么走", "free": "1天", "standard": "✅ 精确到小时", "premium": "✅ 精确到小时"},
        {"label": "不用自己查交通换乘", "free": "—", "standard": "✅ 手把手写清楚", "premium": "✅ 手把手写清楚"},
        {"label": "每顿饭不用现场纠结", "free": "—", "standard": "✅ 推荐+备选", "premium": "✅ 推荐+备选+高端精选"},
        {"label": "门票/预约不怕漏掉", "free": "—", "standard": "✅ 提醒清单", "premium": "✅ 提醒清单"},
        {"label": "下雨/排队有备选方案", "free": "—", "standard": "✅ 每天都有Plan B", "premium": "✅ 每天都有Plan B"},
        {"label": "不用花两周做功课", "free": "部分", "standard": "✅ 拿到就能出发", "premium": "✅ 拿到就能出发"},
        {"label": "有人帮我把关行程合理性", "free": "—", "standard": "—", "premium": "✅ 1对1沟通"},
        {"label": "旅途中遇到问题能问人", "free": "—", "standard": "—", "premium": "✅ 实时答疑"},
        {"label": "攻略页数", "free": "3-5页", "standard": "30-40页", "premium": "40-50页"},
        {"label": "行程精调次数", "free": "0次", "standard": "2次", "premium": "5次"},
    ],
}


@router.get("/product-tiers")
async def get_product_tiers(db: AsyncSession = Depends(get_db)) -> dict:
    """
    返回产品定价配置。
    优先从 product_config 表读取 key='product_tiers'，
    不存在则返回硬编码默认值。
    """
    try:
        result = await db.execute(
            select(ProductConfig).where(
                ProductConfig.config_key == "product_tiers",
                ProductConfig.is_active == True,  # noqa: E712
            )
        )
        cfg = result.scalar_one_or_none()
        if cfg and cfg.config_value:
            return cfg.config_value
    except Exception:
        pass

    return _DEFAULT_TIERS
