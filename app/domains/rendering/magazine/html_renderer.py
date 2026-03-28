from __future__ import annotations

import html
import uuid as _uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.derived import ItineraryPlan
from app.domains.rendering.shared_export_contract import build_shared_page_export_contract


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


# ── DIY 区域 CSS ──────────────────────────────────────────────────────────────

_DIY_CSS = """
<style>
/* ── 手账本 DIY 区域样式 ─────────────────────────────────────────────── */

/* 贴纸区：虚线框，右上/左下角 */
.diy-sticker-zone {
    position: absolute;
    width: 80px;
    height: 80px;
    border: 1.5px dashed #c8a97a;
    border-radius: 4px;
    background: rgba(255, 248, 235, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    color: #c8a97a;
    letter-spacing: 0.5px;
}
.diy-sticker-zone.top-right {
    top: 12px; right: 12px;
}
.diy-sticker-zone.bottom-left {
    bottom: 12px; left: 12px;
}
.diy-sticker-zone.corner {
    top: 12px; left: 12px;
}
.diy-sticker-zone::after {
    content: "贴纸区";
}

/* 手写留白区 */
.diy-freewrite-zone {
    border: 1px dashed #c8a97a;
    border-radius: 3px;
    background: repeating-linear-gradient(
        transparent,
        transparent 23px,
        #e8dcc8 23px,
        #e8dcc8 24px
    );
    background-color: rgba(255, 252, 245, 0.8);
    color: #c8a97a;
    font-size: 9px;
    padding: 6px 10px;
    display: flex;
    align-items: flex-start;
    box-sizing: border-box;
}
.diy-freewrite-zone::before {
    content: "✏ 我的记录";
    opacity: 0.6;
}
.diy-freewrite-zone.bottom-strip {
    width: 100%;
    height: 72px;
    margin-top: 8px;
}
.diy-freewrite-zone.side-margin {
    width: 60px;
    min-height: 120px;
    position: absolute;
    right: 4px;
    top: 50%;
    transform: translateY(-50%);
    writing-mode: vertical-rl;
}
.diy-freewrite-zone.full-half {
    width: 100%;
    height: 160px;
    margin-top: 12px;
}

/* 带 DIY 区域的页面使用 relative 定位 */
.shared-page.has-diy {
    position: relative;
    overflow: visible;
}
</style>
"""


def _render_diy_zones(page: dict[str, Any]) -> str:
    """
    根据 page 的 sticker_zone / freewrite_zone 字段生成 DIY 区域 HTML。
    字段值来自 PagePlan.sticker_zone 和 PagePlan.freewrite_zone（通过 shared_export_contract 传递）。
    """
    parts = []

    sticker = page.get("sticker_zone")
    if sticker and sticker != "none":
        css_class = {
            "top_right": "top-right",
            "bottom_left": "bottom-left",
            "corner": "corner",
        }.get(sticker, "top-right")
        parts.append(f'<div class="diy-sticker-zone {css_class}"></div>')

    freewrite = page.get("freewrite_zone")
    if freewrite and freewrite != "none":
        css_class = {
            "bottom_strip": "bottom-strip",
            "side_margin": "side-margin",
            "full_half": "full-half",
        }.get(freewrite, "bottom-strip")
        parts.append(f'<div class="diy-freewrite-zone {css_class}"></div>')

    return "".join(parts)


def _render_page(page: dict[str, Any]) -> str:
    title = _escape(page.get("title"))
    subtitle = _escape(page.get("subtitle"))
    summary = _escape(page.get("summary"))
    hero_url = _escape(page.get("hero_url"))
    hero_fallback = _escape(page.get("hero_fallback"))
    hero_source = _escape(page.get("hero_source"))
    slot_lines = []
    for slot in page.get("asset_slots") or []:
        slot_lines.append(
            "<li>"
            f"{_escape(slot.get('slot_name'))} "
            f"asset_id={_escape(slot.get('asset_id'))} "
            f"url={_escape(slot.get('asset_url'))}"
            "</li>"
        )
    slots_html = "".join(slot_lines)

    diy_html = _render_diy_zones(page)
    has_diy = " has-diy" if diy_html else ""

    return (
        f'<section class="shared-page{has_diy}">'
        f'<h2>{title}</h2>'
        f'<p>{subtitle}</p>'
        f'<div>{summary}</div>'
        f'<div>hero_url={hero_url}</div>'
        f'<div>hero_fallback={hero_fallback}</div>'
        f'<div>hero_source={hero_source}</div>'
        f'<ul>{slots_html}</ul>'
        f'{diy_html}'
        '</section>'
    )


async def render_html(
    plan_id: _uuid.UUID | str,
    session: AsyncSession,
) -> str:
    if isinstance(plan_id, str):
        plan_id = _uuid.UUID(plan_id)

    result = await session.execute(
        select(ItineraryPlan).where(ItineraryPlan.plan_id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise ValueError(f"ItineraryPlan not found: {plan_id}")

    shared_page_export = build_shared_page_export_contract(plan.plan_metadata)
    if not shared_page_export:
        raise ValueError("plan_metadata.page_models is missing for shared export contract")

    meta = plan.plan_metadata or {}
    template_meta = meta.get("template_meta") if isinstance(meta.get("template_meta"), dict) else {}
    title = template_meta.get("title_zh") or "共享页面导出"
    tagline = template_meta.get("tagline_zh") or ""
    asset_manifest_version = shared_page_export.get("asset_manifest_version") or ""

    pages_html = "".join(_render_page(page) for page in shared_page_export.get("pages") or [])
    return (
        "<html><head>"
        "<meta charset='utf-8'>"
        f"{_DIY_CSS}"
        "</head><body>"
        f"<h1>{_escape(title)}</h1>"
        f"<p>{_escape(tagline)}</p>"
        f"<div>asset_manifest_version={_escape(asset_manifest_version)}</div>"
        f"{pages_html}"
        "</body></html>"
    )
