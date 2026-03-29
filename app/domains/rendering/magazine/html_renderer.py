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
/* ── 印刷页面基础布局（WeasyPrint @page） ─────────────────────────── */
@page {
    size: A4;
    margin: 20mm 18mm 22mm 18mm;
}
@page :first {
    margin: 0;
}

body {
    font-family: "Noto Sans CJK SC", "Noto Sans SC", "PingFang SC", "Hiragino Sans GB", sans-serif;
    font-size: 10pt;
    line-height: 1.5;
    color: #2c2c2c;
}

/* 每一页分节 */
.shared-page {
    page-break-before: always;
    page-break-inside: avoid;
    position: relative;
    box-sizing: border-box;
}
.shared-page:first-child {
    page-break-before: auto;
}

/* ── 手账本 DIY 区域样式 ─────────────────────────────────────────────── */

/* ---------- 贴纸区：1/4 页虚线框，浅暖色底 ---------- */
.diy-sticker-zone {
    width: 90px;
    height: 90px;
    border: 1.5px dashed #c8a97a;
    border-radius: 6px;
    background: #fff8eb;
    text-align: center;
    padding-top: 18px;
    box-sizing: border-box;
}
.diy-sticker-zone .diy-icon {
    display: block;
    font-size: 16px;
    color: #c8a97a;
    opacity: 0.4;
    margin-bottom: 2px;
}
.diy-sticker-zone .diy-label {
    font-size: 7pt;
    color: #c8a97a;
    letter-spacing: 0.3px;
    opacity: 0.7;
    line-height: 1.3;
}

/* 位置变体：通过 float 实现（WeasyPrint 不支持 flexbox 可靠定位） */
.diy-sticker-zone.top-right {
    float: right;
    margin: 0 0 8px 10px;
}
.diy-sticker-zone.bottom-left {
    float: left;
    margin: 8px 10px 0 0;
    clear: left;
}
.diy-sticker-zone.corner {
    float: left;
    margin: 0 10px 8px 0;
}

/* ---------- 手写区：横线纸效果（notebook-style lined area） ---------- */
.diy-freewrite-zone {
    border: 1px dashed #c8a97a;
    border-radius: 4px;
    background-color: #fffcf5;
    background-image: repeating-linear-gradient(
        to bottom,
        transparent,
        transparent 21px,
        #e0d5c0 21px,
        #e0d5c0 22px
    );
    box-sizing: border-box;
    position: relative;
    clear: both;
}
.diy-freewrite-zone .diy-label {
    display: block;
    padding: 4px 0 0 8px;
    font-size: 7pt;
    color: #c8a97a;
    opacity: 0.6;
    letter-spacing: 0.3px;
}

/* 底部条形手写区：全宽，约 80px 高 */
.diy-freewrite-zone.bottom-strip {
    width: 100%;
    height: 80px;
    margin-top: 10px;
}

/* 侧边手写区：窄条，用 float 布局替代 absolute */
.diy-freewrite-zone.side-margin {
    float: right;
    width: 56px;
    min-height: 140px;
    margin-left: 8px;
}

/* 半页手写区：全宽，约 170px 高 */
.diy-freewrite-zone.full-half {
    width: 100%;
    height: 170px;
    margin-top: 14px;
}

/* 带 DIY 区域的页面 clearfix */
.shared-page.has-diy {
    position: relative;
}
.shared-page.has-diy::after {
    content: "";
    display: block;
    clear: both;
}

/* ── DIY 区域容器 ─────────────────────────────────────────────────── */
.diy-zones-wrapper {
    margin-top: 12px;
    page-break-inside: avoid;
    clear: both;
}
.diy-zones-wrapper.inline-top {
    margin-top: 0;
    margin-bottom: 8px;
}
</style>
"""


def _render_sticker_zone_html(sticker: str) -> str:
    """Render a single sticker zone div. Returns empty string if sticker is None/none."""
    if not sticker or sticker == "none":
        return ""
    css_class = {
        "top_right": "top-right",
        "bottom_left": "bottom-left",
        "corner": "corner",
    }.get(sticker, "top-right")
    return (
        f'<div class="diy-sticker-zone {css_class}">'
        '<span class="diy-icon">&#9734;</span>'
        '<span class="diy-label">贴纸区<br>Sticker Zone</span>'
        '</div>'
    )


def _render_freewrite_zone_html(freewrite: str) -> str:
    """Render a single freewrite zone div. Returns empty string if freewrite is None/none."""
    if not freewrite or freewrite == "none":
        return ""
    css_class = {
        "bottom_strip": "bottom-strip",
        "side_margin": "side-margin",
        "full_half": "full-half",
    }.get(freewrite, "bottom-strip")
    return (
        f'<div class="diy-freewrite-zone {css_class}">'
        '<span class="diy-label">&#9998; 手写区 / Notes</span>'
        '</div>'
    )


def _render_diy_zones(page: dict[str, Any]) -> str:
    """
    根据 page 的 sticker_zone / freewrite_zone 字段生成 DIY 区域 HTML。
    字段值来自 PagePlan.sticker_zone 和 PagePlan.freewrite_zone（通过 shared_export_contract 传递）。

    贴纸区：虚线框 + 星形图标 + 双语标签 "贴纸区 / Sticker Zone"
    手写区：横线纸效果（notebook paper style）+ 双语标签 "手写区 / Notes"

    生成的 HTML 分为两部分：
    - inline_top: 顶部 float 的贴纸区（top_right / corner），在正文前渲染
    - bottom: 底部贴纸区 + 手写区，在正文后渲染
    """
    sticker = page.get("sticker_zone")
    freewrite = page.get("freewrite_zone")

    sticker_html = _render_sticker_zone_html(sticker)
    freewrite_html = _render_freewrite_zone_html(freewrite)

    if not sticker_html and not freewrite_html:
        return ""

    parts: list[str] = []

    # 贴纸区在顶部 float（top_right / corner）时，放在正文前面以实现文字环绕
    is_top_sticker = sticker in ("top_right", "corner")

    if is_top_sticker and sticker_html:
        # 顶部贴纸直接 inline（float）
        parts.append(sticker_html)

    # 底部区域包裹在 wrapper 中
    bottom_parts: list[str] = []
    if not is_top_sticker and sticker_html:
        bottom_parts.append(sticker_html)
    if freewrite_html:
        bottom_parts.append(freewrite_html)

    if bottom_parts:
        parts.append(
            '<div class="diy-zones-wrapper">'
            + "".join(bottom_parts)
            + '</div>'
        )

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

    # Split DIY HTML: top stickers (float) go before content, bottom zones go after
    sticker = page.get("sticker_zone")
    is_top_sticker = sticker in ("top_right", "corner")

    # Build top-float sticker (rendered before main content for text wrapping)
    top_diy = ""
    bottom_diy = ""
    if diy_html:
        if is_top_sticker:
            top_diy = _render_sticker_zone_html(sticker)
            # Bottom wrapper contains only freewrite (sticker already rendered at top)
            fw_html = _render_freewrite_zone_html(page.get("freewrite_zone"))
            bottom_diy = f'<div class="diy-zones-wrapper">{fw_html}</div>' if fw_html else ""
        else:
            bottom_diy = diy_html

    return (
        f'<section class="shared-page{has_diy}">'
        f'{top_diy}'
        f'<h2>{title}</h2>'
        f'<p>{subtitle}</p>'
        f'<div>{summary}</div>'
        f'<div>hero_url={hero_url}</div>'
        f'<div>hero_fallback={hero_fallback}</div>'
        f'<div>hero_source={hero_source}</div>'
        f'<ul>{slots_html}</ul>'
        f'{bottom_diy}'
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
        "<div class='export-marker'>共享页面导出</div>"
        f"<h1>{_escape(title)}</h1>"
        f"<p>{_escape(tagline)}</p>"
        f"<div>asset_manifest_version={_escape(asset_manifest_version)}</div>"
        f"{pages_html}"
        "</body></html>"
    )
