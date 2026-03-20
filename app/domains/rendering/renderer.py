from __future__ import annotations

"""
renderer: 行程 HTML/PDF 渲染
- render_html: 用 Jinja2 把 ItineraryPlan 渲染成 HTML 字符串
- render_pdf:  把 HTML 转成 PDF bytes（依赖 weasyprint，可选）
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase
from app.db.models.derived import ItineraryDay, ItineraryItem, ItineraryPlan

# 模板目录
_TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )


# ── 数据组装 ──────────────────────────────────────────────────────────────────

async def _build_render_context(
    session: AsyncSession,
    plan: ItineraryPlan,
) -> Dict[str, Any]:
    """把 ORM 对象转成模板可用的纯 dict 结构"""

    # 查询所有 days（已按 day_number 排序）
    days_result = await session.execute(
        select(ItineraryDay)
        .where(ItineraryDay.plan_id == plan.plan_id)
        .order_by(ItineraryDay.day_number)
    )
    days = days_result.scalars().all()

    # 收集所有 entity_id，批量查名称
    entity_ids = set()
    day_items_map: Dict[int, List[ItineraryItem]] = {}

    for day in days:
        items_result = await session.execute(
            select(ItineraryItem)
            .where(ItineraryItem.day_id == day.day_id)
            .order_by(ItineraryItem.sort_order)
        )
        items = items_result.scalars().all()
        day_items_map[day.day_id] = items
        for item in items:
            if item.entity_id:
                entity_ids.add(item.entity_id)

    # 批量查 entity 名称
    entity_names: Dict[str, str] = {}
    if entity_ids:
        ent_result = await session.execute(
            select(EntityBase).where(EntityBase.entity_id.in_(entity_ids))
        )
        for ent in ent_result.scalars().all():
            entity_names[str(ent.entity_id)] = ent.name_zh

    # 组装渲染数据
    meta = plan.plan_metadata or {}
    rendered_days = []
    for day in days:
        items_data = []
        for item in day_items_map.get(day.day_id, []):
            entity_name = entity_names.get(str(item.entity_id)) if item.entity_id else None
            items_data.append({
                "item_type": item.item_type,
                "entity_name": entity_name,
                "start_time": item.start_time,
                "end_time": item.end_time,
                "duration_min": item.duration_min,
                "notes_zh": item.notes_zh,
                "estimated_cost_jpy": item.estimated_cost_jpy,
                "is_optional": item.is_optional,
                "maps_url": _maps_url(entity_name) if entity_name else None,
            })
        rendered_days.append({
            "day_number": day.day_number,
            "date": day.date,
            "city_code": day.city_code,
            "city_name_zh": _city_name_zh(day.city_code),
            "day_theme": day.day_theme,
            "estimated_cost_jpy": day.estimated_cost_jpy,
            "timeline": items_data,
        })

    return {
        "plan_id": str(plan.plan_id),
        "total_days": meta.get("total_days", len(days)),
        "cities": meta.get("cities", []),
        "budget_level": meta.get("budget_level", "mid"),
        "budget_level_zh": _budget_zh(meta.get("budget_level", "mid")),
        "estimated_total_cost_jpy": meta.get("estimated_total_cost_jpy"),
        "days": rendered_days,
        "status": plan.status,
    }


def _maps_url(name: str) -> str:
    import urllib.parse
    return f"https://maps.google.com/?q={urllib.parse.quote(name + ' Japan')}"


def _city_name_zh(city_code: str) -> str:
    return {
        "tokyo": "东京", "osaka": "大阪", "kyoto": "京都",
        "sapporo": "札幌", "fukuoka": "福冈", "naha": "那霸（冲绳）",
        "hiroshima": "广岛", "nagoya": "名古屋", "hakone": "箱根",
        "nikko": "日光",
    }.get(city_code, city_code)


def _budget_zh(level: str) -> str:
    return {"budget": "经济", "mid": "中档", "premium": "高档", "luxury": "奢华"}.get(level, level)


# ── 对外接口 ──────────────────────────────────────────────────────────────────

async def render_html(
    session: AsyncSession,
    plan_id: str,
    template_name: str = "itinerary_default.html",
) -> str:
    """
    把 ItineraryPlan 渲染成 HTML 字符串。

    Args:
        session:       AsyncSession
        plan_id:       ItineraryPlan.plan_id（UUID 字符串）
        template_name: Jinja2 模板文件名

    Returns:
        HTML 字符串

    Raises:
        ValueError: plan_id 不存在
    """
    import uuid as _uuid
    result = await session.execute(
        select(ItineraryPlan).where(ItineraryPlan.plan_id == _uuid.UUID(plan_id))
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise ValueError(f"ItineraryPlan not found: {plan_id}")

    context = await _build_render_context(session, plan)
    env = _get_jinja_env()
    tmpl = env.get_template(template_name)
    return tmpl.render(**context)


async def render_pdf(html_content: str) -> bytes:
    """
    把 HTML 字符串转成 PDF bytes。
    依赖 weasyprint（需要系统安装 cairo/pango）。
    如果 weasyprint 未安装，raise ImportError 并提示。
    """
    try:
        from weasyprint import HTML
    except ImportError:
        raise ImportError(
            "weasyprint 未安装，请运行: pip install weasyprint\n"
            "macOS 还需要: brew install cairo pango gdk-pixbuf libffi"
        )
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
