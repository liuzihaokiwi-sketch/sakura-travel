from __future__ import annotations

import uuid as _uuid
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape, Undefined
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.derived import ItineraryPlan
from app.domains.rendering.shared_export_contract import build_shared_page_export_contract


class _DotDict(dict):
    """dict subclass that allows attribute access, shadowing dict methods safely.

    Jinja2 resolves `obj.attr` via getattr first, then getitem.
    For plain dict, `.items` returns the method, not the data key.
    _DotDict overrides __getattr__ so `.items` returns data['items'] when present.
    """
    def __getattr__(self, name: str) -> Any:
        try:
            val = self[name]
            return _wrap(val)
        except KeyError:
            raise AttributeError(name)

    def get(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        val = super().get(key, default)
        return _wrap(val)

    def __missing__(self, key: str) -> Any:
        return None


def _wrap(obj: Any) -> Any:
    """Recursively wrap dicts as _DotDict and list items."""
    if isinstance(obj, _DotDict):
        return obj
    if isinstance(obj, dict):
        return _DotDict({k: _wrap(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [_wrap(x) for x in obj]
    return obj

_TEMPLATES_DIR = Path(__file__).parent / "templates"

# page_type → 模板文件名（不含 .html）
_TEMPLATE_MAP: dict[str, str] = {
    "cover":                    "cover",
    "toc":                      "toc",
    "preference_fulfillment":   "preference_fulfillment",
    "major_activity_overview":  "major_activity_overview",
    "route_overview":           "route_overview",
    "hotel_strategy":           "hotel_strategy",
    "booking_window":           "booking_window",
    "departure_prep":           "departure_prep",
    "live_notice":              "live_notice",
    "chapter_opener":           "chapter_opener",
    "day_execution":            "day_execution",
    "major_activity_detail":    "major_activity_detail",
    "hotel_detail":             "hotel_detail",
    "restaurant_detail":        "restaurant_detail",
    "photo_theme_detail":       "photo_theme_detail",
}


class _SafeUndefined(Undefined):
    """未定义变量返回空字符串而不是抛错，防止模板因缺字段崩溃。"""
    def __str__(self) -> str:
        return ""
    def __iter__(self):
        return iter([])
    def __bool__(self) -> bool:
        return False


def _make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        undefined=_SafeUndefined,
    )
    return env


def _render_page_vm(env: Environment, vm: dict[str, Any]) -> str:
    """将单个 PageViewModel（dict）渲染为 HTML 片段。"""
    page_type = vm.get("page_type", "skeleton")
    template_name = _TEMPLATE_MAP.get(page_type, "skeleton") + ".html"
    try:
        tmpl = env.get_template(template_name)
    except Exception:
        tmpl = env.get_template("skeleton.html")
    safe_vm = _wrap(vm)
    return tmpl.render(vm=safe_vm)


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

    meta = plan.plan_metadata or {}
    template_meta = meta.get("template_meta") if isinstance(meta.get("template_meta"), dict) else {}

    # 优先使用 page_models（已由 page_planner 构建的 view model 缓存）
    page_models: dict[str, Any] = meta.get("page_models") or {}
    page_plan: list[dict] = meta.get("page_plan") or []

    if not page_models:
        # 降级到旧版 shared_export_contract 路径
        shared_page_export = build_shared_page_export_contract(meta)
        if not shared_page_export:
            raise ValueError("plan_metadata.page_models is missing and shared_export_contract failed")
        pages_ordered = shared_page_export.get("pages") or []
        # 旧路径只有粗糙数据，用 skeleton 渲染
        env = _make_env()
        page_html_parts = []
        for page in pages_ordered:
            vm = {
                "page_type": page.get("page_type", "skeleton"),
                "page_size": page.get("page_size", "full"),
                "heading": {
                    "title": page.get("title", ""),
                    "subtitle": page.get("subtitle", ""),
                    "page_number": None,
                },
                "hero": {
                    "image_url": page.get("hero_url"),
                    "image_alt": page.get("title", ""),
                } if page.get("hero_url") else None,
                "sections": [],
                "day_index": page.get("day_index"),
                "sticker_zone": page.get("sticker_zone"),
                "freewrite_zone": page.get("freewrite_zone"),
            }
            page_html_parts.append(_render_page_vm(env, vm))
        pages_html = "\n".join(page_html_parts)
    else:
        env = _make_env()
        # 按 page_plan 顺序渲染 view models
        if page_plan:
            ordered_ids = [p["page_id"] for p in sorted(page_plan, key=lambda p: p.get("page_order", 0))]
        else:
            ordered_ids = list(page_models.keys())

        page_html_parts = []
        for pid in ordered_ids:
            vm = page_models.get(pid)
            if not vm:
                continue
            page_html_parts.append(_render_page_vm(env, vm))
        pages_html = "\n".join(page_html_parts)

    base_tmpl = env.get_template("base.html")
    return base_tmpl.render(
        meta={
            "title": template_meta.get("title_zh") or "旅行手账",
        },
        body_content=pages_html,  # 通过 {% block body %} 注入
    )
