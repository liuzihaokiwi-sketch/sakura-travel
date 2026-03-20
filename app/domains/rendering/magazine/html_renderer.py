"""
杂志级 HTML 渲染器

render_html(plan_id, session) -> str
  将 ItineraryPlan 组装成完整 HTML 字符串（Jinja2 渲染）

图片 fallback 逻辑（Task 4.12）：
  entity_media 有图 → 使用图片 URL
  entity_media 无图 → data/city_defaults/{city_code}.jpg
  图片字段缺失    → None（前端 CSS 占位）
"""
from __future__ import annotations

import json
import logging
import urllib.parse
import uuid as _uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase, EntityMedia, EntityTag
from app.db.models.derived import ItineraryDay, ItineraryItem, ItineraryPlan

logger = logging.getLogger(__name__)

# ── 路径 ──────────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent.parent.parent.parent  # /project root
_TEMPLATES_DIR = _ROOT / "templates"
_CITY_DEFAULTS_DIR = _ROOT / "data" / "city_defaults"

# ── 城市默认图片（Unsplash 可商用，作为 fallback）──────────────────────────────
# 优先使用本地 /static/city_defaults/ 目录下的图片
# 如果不存在则使用 Unsplash 外链
_CITY_DEFAULT_IMAGES_LOCAL: Dict[str, str] = {
    "tokyo":     "/static/city_defaults/tokyo.jpg",
    "osaka":     "/static/city_defaults/osaka.jpg",
    "kyoto":     "/static/city_defaults/kyoto.jpg",
    "sapporo":   "/static/city_defaults/sapporo.jpg",
    "fukuoka":   "/static/city_defaults/fukuoka.jpg",
    "naha":      "/static/city_defaults/naha.jpg",
    "hiroshima": "/static/city_defaults/hiroshima.jpg",
    "nagoya":    "/static/city_defaults/nagoya.jpg",
    "hakone":    "/static/city_defaults/hakone.jpg",
    "nikko":     "/static/city_defaults/nikko.jpg",
}

_CITY_DEFAULT_IMAGES_REMOTE: Dict[str, str] = {
    "tokyo":     "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800&q=80",
    "osaka":     "https://images.unsplash.com/photo-1590559899731-a382839e5549?w=800&q=80",
    "kyoto":     "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&q=80",
    "sapporo":   "https://images.unsplash.com/photo-1571167366136-b57e07761625?w=800&q=80",
    "fukuoka":   "https://images.unsplash.com/photo-1542051841857-5f90071e7989?w=800&q=80",
    "naha":      "https://images.unsplash.com/photo-1590077428593-a55bb07c4665?w=800&q=80",
    "hiroshima": "https://images.unsplash.com/photo-1576675466969-38eeae4b41f6?w=800&q=80",
    "nagoya":    "https://images.unsplash.com/photo-1536098561742-ca998e48cbcc?w=800&q=80",
    "hakone":    "https://images.unsplash.com/photo-1528360983277-13d401cdc186?w=800&q=80",
    "nikko":     "https://images.unsplash.com/photo-1570459027562-4a916cc6113f?w=800&q=80",
}

# 通用日本 fallback（当 city_code 未知时使用）
_JAPAN_FALLBACK_IMAGE = "https://images.unsplash.com/photo-1528164344705-47542687000d?w=800&q=80"


def _get_city_default_image(city_code: str) -> Optional[str]:
    """按优先级获取城市默认图：本地文件 → 远程 Unsplash → 通用日本图"""
    # 1. 检查本地文件是否存在
    local_path = _CITY_DEFAULTS_DIR / f"{city_code}.jpg"
    if local_path.exists():
        return _CITY_DEFAULT_IMAGES_LOCAL.get(city_code)
    # 2. 使用远程 Unsplash URL
    if city_code in _CITY_DEFAULT_IMAGES_REMOTE:
        return _CITY_DEFAULT_IMAGES_REMOTE[city_code]
    # 3. 通用 fallback
    return _JAPAN_FALLBACK_IMAGE

# 兼容旧引用
_CITY_DEFAULT_IMAGES = _CITY_DEFAULT_IMAGES_LOCAL

_CITY_NAME_ZH = {
    "tokyo": "东京", "osaka": "大阪", "kyoto": "京都",
    "sapporo": "札幌", "fukuoka": "福冈", "naha": "那霸（冲绳）",
    "hiroshima": "广岛", "nagoya": "名古屋", "hakone": "箱根",
    "nikko": "日光",
}


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )


# ── 图片获取 + fallback（Task 4.12）─────────────────────────────────────────

async def _get_entity_image(
    session: AsyncSession,
    entity_id: _uuid.UUID,
    city_code: str,
) -> Optional[str]:
    """
    获取实体图片 URL，按优先级：
    1. entity_media 表中 media_type='photo' 的第一张
    2. 城市默认图片（data/city_defaults/{city_code}.jpg）
    3. None（CSS 占位）
    """
    try:
        result = await session.execute(
            select(EntityMedia).where(
                EntityMedia.entity_id == entity_id,
                EntityMedia.media_type == "photo",
            ).limit(1)
        )
        media = result.scalar_one_or_none()
        if media and media.url:
            return media.url
    except Exception as e:
        logger.warning("查询 entity_media 失败 entity=%s: %s", entity_id, e)

    # fallback: 城市默认图（本地 → Unsplash → 通用日本图）
    return _get_city_default_image(city_code)


# ── 标签提取 ─────────────────────────────────────────────────────────────────

async def _get_entity_tags(
    session: AsyncSession,
    entity_id: _uuid.UUID,
) -> List[str]:
    """获取实体的展示标签（affinity namespace，格式: 'theme:score' → 取 theme）。"""
    try:
        result = await session.execute(
            select(EntityTag).where(
                EntityTag.entity_id == entity_id,
                EntityTag.tag_namespace == "affinity",
            )
        )
        tags = result.scalars().all()
        tag_strs = []
        for t in tags:
            parts = t.tag_value.split(":", 1) if t.tag_value else []
            if parts:
                tag_strs.append(parts[0])
        return tag_strs[:6]
    except Exception:
        return []


# ── 文案提取（从 notes_zh JSON）─────────────────────────────────────────────

def _parse_copy(notes_zh: Optional[str]) -> tuple[str, str]:
    """从 notes_zh 解析 AI 文案（JSON 格式）。"""
    if not notes_zh:
        return "", ""
    try:
        data = json.loads(notes_zh)
        return data.get("copy_zh", ""), data.get("tips_zh", "")
    except (json.JSONDecodeError, TypeError):
        return notes_zh, ""  # 旧格式直接作为 copy_zh


# ── 渲染上下文组装 ───────────────────────────────────────────────────────────

async def _build_magazine_context(
    session: AsyncSession,
    plan: ItineraryPlan,
) -> Dict[str, Any]:
    """将 ORM 对象转换为 Jinja2 渲染上下文。"""

    meta = plan.plan_metadata or {}
    template_meta = meta.get("template_meta", {})
    scene = meta.get("scene", "general")
    city_codes: List[str] = meta.get("city_codes", [])
    cities_zh = [_CITY_NAME_ZH.get(c, c) for c in city_codes]

    # 封面图：取第一个城市的默认图
    cover_image_url = _CITY_DEFAULT_IMAGES.get(city_codes[0]) if city_codes else None

    # 查询所有 days
    days_result = await session.execute(
        select(ItineraryDay)
        .where(ItineraryDay.plan_id == plan.plan_id)
        .order_by(ItineraryDay.day_number)
    )
    days = days_result.scalars().all()

    rendered_days = []
    for day in days:
        # 查询 items
        items_result = await session.execute(
            select(ItineraryItem)
            .where(ItineraryItem.day_id == day.day_id)
            .order_by(ItineraryItem.sort_order)
        )
        items = items_result.scalars().all()

        timeline = []
        _prev_entity_id = None  # 用于计算与上一个景点的交通时间
        for item in items:
            item_data: Dict[str, Any] = {
                "item_type": item.item_type,
                "entity_type": item.item_type,
                "start_time": item.start_time,
                "end_time": item.end_time,
                "duration_min": item.duration_min,
                "is_optional": item.is_optional,
                "notes_zh": item.notes_zh,
                "image_url": None,
                "entity_name": None,
                "entity_name_ja": None,
                "copy_zh": "",
                "tips_zh": "",
                "tags": [],
                "rating": None,
                "opening_hours_zh": None,
                "admission_fee_jpy": None,
                "maps_url": None,
                "travel_time_zh": None,
                "hotel_area_zh": None,
            }

            if item.entity_id:
                entity = await session.get(EntityBase, item.entity_id)
                if entity:
                    item_data["entity_name"] = entity.name_zh
                    item_data["entity_name_ja"] = entity.name_ja
                    item_data["entity_type"] = entity.entity_type
                    item_data["item_type"] = entity.entity_type

                    # 图片（with fallback）
                    item_data["image_url"] = await _get_entity_image(
                        session, entity.entity_id, day.city_code
                    )

                    # 标签
                    item_data["tags"] = await _get_entity_tags(session, entity.entity_id)

                    # Google Maps URL
                    name_for_maps = entity.name_ja or entity.name_zh or ""
                    item_data["maps_url"] = (
                        f"https://maps.google.com/?q={urllib.parse.quote(name_for_maps + ' Japan')}"
                        if name_for_maps else None
                    )

                    # 从子表获取额外信息（显式异步查询，避免懒加载）
                    if entity.entity_type == "poi":
                        from app.db.models.catalog import Poi
                        poi_r = await session.get(Poi, entity.entity_id)
                        if poi_r:
                            item_data["rating"] = poi_r.google_rating
                            item_data["admission_fee_jpy"] = (
                                0 if poi_r.admission_free else poi_r.admission_fee_jpy
                            )
                            item_data["duration_min"] = item_data["duration_min"] or poi_r.typical_duration_min
                            if poi_r.opening_hours_json:
                                oh = poi_r.opening_hours_json
                                if isinstance(oh, str):
                                    try:
                                        oh = json.loads(oh)
                                    except Exception:
                                        oh = {}
                                periods = oh.get("periods", []) if isinstance(oh, dict) else []
                                if periods and isinstance(periods, list):
                                    item_data["opening_hours_zh"] = _format_hours(periods)

                    elif entity.entity_type == "restaurant":
                        from app.db.models.catalog import Restaurant
                        rest_r = await session.get(Restaurant, entity.entity_id)
                        if rest_r:
                            # Restaurant 用 tabelog_score，无 google_rating
                            item_data["rating"] = getattr(rest_r, "tabelog_score", None) or getattr(rest_r, "google_rating", None)

                    elif entity.entity_type == "hotel":
                        from app.db.models.catalog import Hotel
                        hotel_r = await session.get(Hotel, entity.entity_id)
                        if hotel_r:
                            item_data["rating"] = hotel_r.google_rating
                            item_data["hotel_area_zh"] = hotel_r.area_name if hasattr(hotel_r, "area_name") else None

            # ── 注入交通时间（Task 6.6）──────────────────────────────────────
            # 计算与上一个有实体的景点之间的交通时间
            current_entity_id = item.entity_id if item.entity_id else None
            if _prev_entity_id and current_entity_id:
                try:
                    from app.domains.planning.route_matrix import get_travel_time as _get_tt
                    tt = await _get_tt(session, _prev_entity_id, current_entity_id, mode="transit")
                    dur = tt.get("duration_min", 0)
                    if dur >= 60:
                        h, m = divmod(dur, 60)
                        item_data["travel_time_zh"] = f"交通约 {h} 小时 {m} 分钟" if m else f"交通约 {h} 小时"
                    else:
                        item_data["travel_time_zh"] = f"交通约 {dur} 分钟"
                except Exception as _e:
                    logger.debug(f"交通时间计算失败: {_e}")

            if current_entity_id:
                _prev_entity_id = current_entity_id

            # 解析 AI 文案
            copy_zh, tips_zh = _parse_copy(item.notes_zh)
            item_data["copy_zh"] = copy_zh
            item_data["tips_zh"] = tips_zh

            # hotel_area 特殊处理
            if item.item_type == "hotel_area":
                item_data["hotel_area_zh"] = (
                    item.notes_zh or template_meta.get("hotel_area_zh", "推荐区域")
                )
                item_data["copy_zh"] = ""
                item_data["tips_zh"] = ""

            timeline.append(item_data)

        rendered_days.append({
            "day_number": day.day_number,
            "city_code": day.city_code,
            "city_name_zh": _CITY_NAME_ZH.get(day.city_code, day.city_code),
            "day_theme": day.day_theme,
            "day_summary_zh": day.day_summary_zh,
            "timeline": timeline,
            "transport_notes_zh": None,
        })

    return {
        "plan_id": str(plan.plan_id),
        "scene": scene,
        "title_zh": template_meta.get("title_zh", f"日本 {meta.get('total_days', len(days))} 日游"),
        "tagline_zh": template_meta.get("tagline_zh", "深度探索，尽享日本之美"),
        "total_days": meta.get("total_days", len(days)),
        "city_codes": city_codes,
        "cities_zh": cities_zh,
        "cover_image_url": cover_image_url,
        "days": rendered_days,
        "travel_info": None,  # 可由上层传入覆盖
    }


def _format_hours(periods: list) -> str:
    """从 opening_hours_json.periods 格式化为可读字符串。"""
    try:
        if not periods:
            return ""
        # 取第一条（通常为工作日）
        p = periods[0]
        open_ = p.get("open", {})
        close_ = p.get("close", {})
        oh = open_.get("time", "")
        ch = close_.get("time", "")
        if oh and ch:
            oh_fmt = f"{oh[:2]}:{oh[2:]}"
            ch_fmt = f"{ch[:2]}:{ch[2:]}"
            return f"{oh_fmt} - {ch_fmt}"
    except Exception:
        pass
    return ""


# ── 静态内容页渲染（AI-C 模板，C1-C6）────────────────────────────────────────

def render_pre_trip_guide(
    city_codes: List[str] | None = None,
    scene: str = "general",
    guide_data: dict | None = None,
) -> str:
    """渲染出行前准备攻略页 (C1.1)。"""
    env = _get_jinja_env()
    tmpl = env.get_template("magazine/pre_trip_guide.html.j2")
    return tmpl.render(
        city_codes=city_codes or [],
        scene=scene,
        guide_data=guide_data or {},
    )


def render_safety_guide(
    city_codes: List[str] | None = None,
    scene: str = "general",
) -> str:
    """渲染安全须知页 (C2.1)。"""
    env = _get_jinja_env()
    tmpl = env.get_template("magazine/safety_guide.html.j2")
    return tmpl.render(
        city_codes=city_codes or [],
        scene=scene,
    )


def render_avoid_traps(
    tier: str = "basic",
    city_codes: List[str] | None = None,
    scene: str = "general",
) -> str:
    """渲染避坑指南页 (C4.1)。tier: 'basic' | 'deep' | 'premium'。"""
    env = _get_jinja_env()
    tmpl = env.get_template("magazine/avoid_traps.html.j2")
    return tmpl.render(
        tier=tier,
        city_codes=city_codes or [],
        scene=scene,
    )


def render_photo_guide(
    city_codes: List[str] | None = None,
    scene: str = "general",
) -> str:
    """渲染拍照攻略页 (C3.1)。"""
    env = _get_jinja_env()
    tmpl = env.get_template("magazine/photo_guide.html.j2")
    return tmpl.render(
        city_codes=city_codes or [],
        scene=scene,
    )


def render_instagrammable_guide(
    scene: str = "general",
) -> str:
    """渲染出片攻略页（穿搭/修图/短视频）(C3.1)。"""
    env = _get_jinja_env()
    tmpl = env.get_template("magazine/instagrammable_guide.html.j2")
    return tmpl.render(scene=scene)


def render_restaurant_report(
    restaurants: List[Dict[str, Any]] | None = None,
    city_codes: List[str] | None = None,
    total_days: int = 7,
) -> str:
    """渲染餐厅推荐报告页 (C5.1)。

    支持的字段别名（自动归一化）：
      genre / cuisine_type → cuisine
      budget_dinner_jpy / budget_lunch_jpy → budget_jpy
      tabelog_score → score_tabelog
      google_rating → google_rating
    """
    def _normalize(r: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(r)
        # cuisine 字段归一化
        if "cuisine" not in out:
            out["cuisine"] = out.get("genre") or out.get("cuisine_type") or ""
        # budget_jpy 字段归一化
        if "budget_jpy" not in out:
            out["budget_jpy"] = (
                out.get("budget_dinner_jpy")
                or out.get("budget_lunch_jpy")
                or out.get("budget_jpy")
            )
        # budget_cny 自动换算（1 JPY ≈ 0.05 CNY）
        if "budget_cny" not in out and out.get("budget_jpy"):
            try:
                out["budget_cny"] = int(out["budget_jpy"] * 0.05)
            except (TypeError, ValueError):
                pass
        # score 字段归一化
        if "score_tabelog" not in out:
            out["score_tabelog"] = out.get("tabelog_score") or out.get("score")
        return out

    env = _get_jinja_env()
    tmpl = env.get_template("magazine/restaurant_report.html.j2")
    return tmpl.render(
        restaurants=[_normalize(r) for r in (restaurants or [])],
        city_codes=city_codes or [],
        total_days=total_days,
    )


def _normalize_hotel(h: Dict[str, Any]) -> Dict[str, Any]:
    """酒店字段归一化（DB → 模板字段名统一）。"""
    out = dict(h)
    # name 字段
    if "name_zh" not in out:
        out["name_zh"] = out.get("name") or out.get("name_ja") or ""
    # price 字段
    if "price_min_jpy" not in out:
        out["price_min_jpy"] = out.get("typical_price_min_jpy") or out.get("price_min")
    if "price_min_cny" not in out and out.get("price_min_jpy"):
        try:
            out["price_min_cny"] = int(out["price_min_jpy"] * 0.05)
        except (TypeError, ValueError):
            pass
    # one_liner / desc
    if "one_liner" not in out:
        out["one_liner"] = out.get("why") or out.get("description") or ""
    return out


def render_hotel_list_simple(
    hotels: List[Dict[str, Any]] | None = None,
    city_codes: List[str] | None = None,
) -> str:
    """渲染酒店推荐列表（简单版，¥68）(C5.2)。"""
    env = _get_jinja_env()
    tmpl = env.get_template("magazine/hotel_list_simple.html.j2")
    return tmpl.render(
        hotels=[_normalize_hotel(h) for h in (hotels or [])],
        city_codes=city_codes or [],
    )


def render_hotel_report(
    hotels: List[Dict[str, Any]] | None = None,
    city_codes: List[str] | None = None,
) -> str:
    """渲染酒店深度推荐报告（详细版，¥128+）(C5.2)。"""
    env = _get_jinja_env()
    tmpl = env.get_template("magazine/hotel_report.html.j2")
    return tmpl.render(
        hotels=[_normalize_hotel(h) for h in (hotels or [])],
        city_codes=city_codes or [],
    )


def render_compare_report(
    flight_comparison: Dict[str, Any] | None = None,
    hotel_comparison: List[Dict[str, Any]] | None = None,
    total_original_cny: int = 0,
    total_optimized_cny: int = 0,
    total_savings_cny: int = 0,
    savings_percent: int = 0,
) -> str:
    """渲染比价报告（¥888+）(C5.3)。"""
    env = _get_jinja_env()
    tmpl = env.get_template("magazine/compare_report.html.j2")
    return tmpl.render(
        flight_comparison=flight_comparison,
        hotel_comparison=hotel_comparison or [],
        total_original_cny=total_original_cny,
        total_optimized_cny=total_optimized_cny,
        total_savings_cny=total_savings_cny,
        savings_percent=savings_percent,
    )


def render_savings_summary(
    savings_items: List[Dict[str, Any]] | None = None,
    total_original_cny: int = 0,
    total_optimized_cny: int = 0,
    total_savings_cny: int = 0,
    savings_percent: int = 0,
    generated_at: str | None = None,
) -> str:
    """渲染省钱汇总页（¥888+ 末页）(C5.3)。

    savings_items 支持字段别名：
      saving / savings_cny → savings_cny
      original / original_cny
      optimized / optimized_cny
    """
    def _normalize_saving(s: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(s)
        if "savings_cny" not in out:
            out["savings_cny"] = out.get("saving") or out.get("saved") or 0
        if "original_cny" not in out:
            out["original_cny"] = out.get("original") or 0
        if "optimized_cny" not in out:
            sv = out.get("savings_cny", 0)
            orig = out.get("original_cny", 0)
            out["optimized_cny"] = out.get("optimized") or (orig - sv if orig else 0)
        return out

    env = _get_jinja_env()
    tmpl = env.get_template("magazine/savings_summary.html.j2")
    return tmpl.render(
        savings_items=[_normalize_saving(s) for s in (savings_items or [])],
        total_original_cny=total_original_cny,
        total_optimized_cny=total_optimized_cny,
        total_savings_cny=total_savings_cny,
        savings_percent=savings_percent,
        generated_at=generated_at,
    )


# ── 对外接口 ─────────────────────────────────────────────────────────────────

async def render_html(
    plan_id: _uuid.UUID | str,
    session: AsyncSession,
) -> str:
    """
    将 ItineraryPlan 渲染为杂志风格 HTML 字符串。

    Args:
        plan_id: ItineraryPlan UUID
        session: AsyncSession

    Returns:
        HTML 字符串

    Raises:
        ValueError: plan_id 不存在
    """
    if isinstance(plan_id, str):
        plan_id = _uuid.UUID(plan_id)

    result = await session.execute(
        select(ItineraryPlan).where(ItineraryPlan.plan_id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise ValueError(f"ItineraryPlan not found: {plan_id}")

    context = await _build_magazine_context(session, plan)
    env = _get_jinja_env()

    # 渲染完整 HTML（基于 base.html.j2）
    # 由于 base 使用 block content，我们渲染 main 模板
    main_tmpl_src = """
{% extends 'magazine/base.html.j2' %}
{% block content %}
<div class="magazine-container">
  {% include 'magazine/cover.html.j2' %}
  {% for day in days %}
    {% include 'magazine/day_card.html.j2' %}
  {% endfor %}
  {% include 'magazine/tips_page.html.j2' %}
</div>
{% endblock %}
"""
    tmpl = env.from_string(main_tmpl_src)
    return tmpl.render(**context)
