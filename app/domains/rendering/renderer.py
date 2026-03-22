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

    # 解析 notes_zh 获取实体名和文案
    import json as _json
    for rd in rendered_days:
        for it in rd.get("timeline", []):
            notes = {}
            if it.get("notes_zh"):
                try:
                    notes = _json.loads(it["notes_zh"])
                except (ValueError, TypeError):
                    notes = {"copy_zh": it["notes_zh"]}
            if not it.get("entity_name"):
                it["entity_name"] = notes.get("copy_zh", "")
            it["copy_zh"] = notes.get("copy_zh", "")
            it["tips_zh_parsed"] = notes.get("tips_zh", "")

    rc = plan.report_content or {}

    # T6: 检测 schema_version，v2 走 v2 渲染上下文
    if rc.get("schema_version") == "v2":
        return _build_render_context_v2(rc, rendered_days, plan, meta)

    return {
        "plan_id": str(plan.plan_id),
        "total_days": meta.get("total_days", len(days)),
        "cities": meta.get("cities", []),
        "budget_level": meta.get("budget_level", "mid"),
        "budget_level_zh": _budget_zh(meta.get("budget_level", "mid")),
        "estimated_total_cost_jpy": meta.get("estimated_total_cost_jpy"),
        "days": rendered_days,
        "status": plan.status,
        "report_content": plan.report_content,
    }


def _build_render_context_v2(
    rc: dict,
    rendered_days: list,
    plan: "ItineraryPlan",
    meta: dict,
) -> dict:
    """
    T6：为 schema_version=v2 的 report_content 构建渲染上下文。
    在 v1 字段基础上额外提供 design_brief、每日 8 字段等 v2 内容。
    """
    layer1 = rc.get("layer1_overview", {})
    design_brief = rc.get("design_brief", {})
    layer2 = rc.get("layer2_daily", [])

    # 把 layer2 中的 v2 字段合并到 rendered_days（按 day_number 对齐）
    layer2_map = {d.get("day_number"): d for d in layer2}
    for rd in rendered_days:
        dn = rd.get("day_number")
        layer2_day = layer2_map.get(dn, {})
        rd["primary_area"] = layer2_day.get("primary_area", "")
        rd["secondary_area"] = layer2_day.get("secondary_area", "")
        rd["day_goal"] = layer2_day.get("day_goal", "")
        rd["must_keep"] = layer2_day.get("must_keep", "")
        rd["first_cut"] = layer2_day.get("first_cut", "")
        rd["start_anchor"] = layer2_day.get("start_anchor", "")
        rd["end_anchor"] = layer2_day.get("end_anchor", "")
        rd["route_integrity_score"] = layer2_day.get("route_integrity_score", 1.0)
        rd["report"] = layer2_day.get("report", {})
        rd["conditional_pages"] = layer2_day.get("conditional_pages", [])

    return {
        "plan_id": str(plan.plan_id),
        "schema_version": "v2",
        "total_days": meta.get("total_days", len(rendered_days)),
        "cities": meta.get("cities", []),
        "budget_level": meta.get("budget_level", "mid"),
        "budget_level_zh": _budget_zh(meta.get("budget_level", "mid")),
        "estimated_total_cost_jpy": meta.get("estimated_total_cost_jpy"),
        "days": rendered_days,
        "status": plan.status,
        "report_content": rc,
        # v2 专属字段
        "design_brief": design_brief,
        "design_philosophy": layer1.get("design_philosophy", {}),
        "overview": layer1.get("overview", {}),
        "booking_reminders": layer1.get("booking_reminders", []),
        "seasonal_tips": layer1.get("seasonal_tips", ""),
        "prep_checklist": layer1.get("prep_checklist", {}),
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

    T6：如果 report_content.schema_version == "v2"，且调用方没有指定模板，
    自动切换到 itinerary_v2.html。

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

    # T6：v2 report 自动选 v2 模板（调用方显式指定模板时不覆盖）
    resolved_template = template_name
    if (
        template_name == "itinerary_default.html"
        and context.get("schema_version") == "v2"
    ):
        resolved_template = "itinerary_v2.html"

    env = _get_jinja_env()
    tmpl = env.get_template(resolved_template)
    return tmpl.render(**context)


async def render_pdf(html_content: str) -> bytes:
    """
    把 HTML 字符串转成 PDF bytes。
    优先使用 xhtml2pdf（纯 Python，无系统依赖），
    fallback 到 weasyprint。
    """
    import io

    # 方案一：xhtml2pdf（纯 Python，Windows 友好）
    # xhtml2pdf 不支持 CSS var()，需要替换成实际值
    try:
        from xhtml2pdf import pisa
        import re

        # 提取 :root 中的 CSS 变量定义
        css_vars = {}
        root_match = re.search(r':root\s*\{([^}]+)\}', html_content)
        if root_match:
            for m in re.finditer(r'--([\w-]+)\s*:\s*([^;]+);', root_match.group(1)):
                css_vars[f'var(--{m.group(1)})'] = m.group(2).strip()

        # 替换所有 var(--xxx) 引用
        pdf_html = html_content
        for var_ref, val in css_vars.items():
            pdf_html = pdf_html.replace(var_ref, val)

        # 移除 xhtml2pdf 不支持的 CSS 特性
        pdf_html = re.sub(r'backdrop-filter:[^;]+;', '', pdf_html)
        pdf_html = re.sub(r'-webkit-print-color-adjust:[^;]+;', '', pdf_html)
        pdf_html = re.sub(r'print-color-adjust:[^;]+;', '', pdf_html)

        result = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(pdf_html), dest=result)
        if pisa_status.err:
            raise RuntimeError(f"xhtml2pdf error count: {pisa_status.err}")
        return result.getvalue()
    except ImportError:
        pass

    # 方案二：weasyprint（需要系统 GTK 库）
    try:
        from weasyprint import HTML
        return HTML(string=html_content).write_pdf()
    except (ImportError, OSError):
        pass

    raise ImportError("PDF 生成需要安装 xhtml2pdf 或 weasyprint: pip install xhtml2pdf")
