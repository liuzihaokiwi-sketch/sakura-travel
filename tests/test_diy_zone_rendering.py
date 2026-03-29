"""
Tests for D6: DIY zone rendering (sticker_zone + freewrite_zone).

Covers:
  1. _render_diy_zones() HTML output for all zone variants
  2. _render_sticker_zone_html / _render_freewrite_zone_html helpers
  3. _render_page() places top-float stickers before content, bottom zones after
  4. DiyZoneContent dataclass in page_view_model
  5. _inject_diy_zones() adds diy_zone section to PageViewModel
  6. PagePlan DIY fields flow through shared_export_contract
  7. page_type_registry includes diy slots in optional_slots
"""
from __future__ import annotations

import pytest

from app.domains.rendering.magazine.html_renderer import (
    _render_diy_zones,
    _render_freewrite_zone_html,
    _render_page,
    _render_sticker_zone_html,
)
from app.domains.rendering.page_planner import PagePlan, _DIY_ZONE_RULES
from app.domains.rendering.page_type_registry import PAGE_TYPE_REGISTRY
from app.domains.rendering.page_view_model import (
    DiyZoneContent,
    PageViewModel,
    HeadingVM,
    FooterVM,
    SectionVM,
    _inject_diy_zones,
)


# ── Sticker zone HTML ────────────────────────────────────────────────────────


class TestRenderStickerZoneHtml:
    def test_top_right(self):
        html = _render_sticker_zone_html("top_right")
        assert 'class="diy-sticker-zone top-right"' in html
        assert "贴纸区" in html
        assert "Sticker Zone" in html
        assert "&#9734;" in html  # star icon

    def test_bottom_left(self):
        html = _render_sticker_zone_html("bottom_left")
        assert "bottom-left" in html

    def test_corner(self):
        html = _render_sticker_zone_html("corner")
        assert "corner" in html

    def test_none_returns_empty(self):
        assert _render_sticker_zone_html(None) == ""
        assert _render_sticker_zone_html("none") == ""
        assert _render_sticker_zone_html("") == ""

    def test_unknown_value_defaults_to_top_right(self):
        html = _render_sticker_zone_html("unknown_pos")
        assert "top-right" in html


# ── Freewrite zone HTML ──────────────────────────────────────────────────────


class TestRenderFrewriteZoneHtml:
    def test_bottom_strip(self):
        html = _render_freewrite_zone_html("bottom_strip")
        assert 'class="diy-freewrite-zone bottom-strip"' in html
        assert "手写区" in html
        assert "Notes" in html
        assert "&#9998;" in html  # pencil icon

    def test_side_margin(self):
        html = _render_freewrite_zone_html("side_margin")
        assert "side-margin" in html

    def test_full_half(self):
        html = _render_freewrite_zone_html("full_half")
        assert "full-half" in html

    def test_none_returns_empty(self):
        assert _render_freewrite_zone_html(None) == ""
        assert _render_freewrite_zone_html("none") == ""

    def test_unknown_value_defaults_to_bottom_strip(self):
        html = _render_freewrite_zone_html("unknown_pos")
        assert "bottom-strip" in html


# ── Combined _render_diy_zones ────────────────────────────────────────────────


class TestRenderDiyZones:
    def test_both_zones_present(self):
        page = {"sticker_zone": "bottom_left", "freewrite_zone": "bottom_strip"}
        html = _render_diy_zones(page)
        assert "diy-sticker-zone" in html
        assert "diy-freewrite-zone" in html
        assert "diy-zones-wrapper" in html

    def test_sticker_only(self):
        page = {"sticker_zone": "top_right", "freewrite_zone": None}
        html = _render_diy_zones(page)
        assert "diy-sticker-zone" in html
        assert "diy-freewrite-zone" not in html

    def test_freewrite_only(self):
        page = {"sticker_zone": None, "freewrite_zone": "full_half"}
        html = _render_diy_zones(page)
        assert "diy-freewrite-zone" in html
        assert "diy-sticker-zone" not in html

    def test_neither_zone(self):
        page = {"sticker_zone": None, "freewrite_zone": None}
        assert _render_diy_zones(page) == ""

    def test_top_sticker_rendered_inline(self):
        """Top stickers (top_right, corner) should be rendered as inline float, not in wrapper."""
        page = {"sticker_zone": "top_right", "freewrite_zone": "bottom_strip"}
        html = _render_diy_zones(page)
        # Sticker should appear before the wrapper
        sticker_pos = html.index("diy-sticker-zone")
        wrapper_pos = html.index("diy-zones-wrapper")
        assert sticker_pos < wrapper_pos

    def test_bottom_sticker_in_wrapper(self):
        """Bottom stickers (bottom_left) should be inside the wrapper."""
        page = {"sticker_zone": "bottom_left", "freewrite_zone": "bottom_strip"}
        html = _render_diy_zones(page)
        wrapper_start = html.index("diy-zones-wrapper")
        sticker_pos = html.index("diy-sticker-zone")
        assert sticker_pos > wrapper_start


# ── _render_page integration ─────────────────────────────────────────────────


class TestRenderPageDiy:
    def _make_page(self, sticker=None, freewrite=None):
        return {
            "title": "Day 1",
            "subtitle": "Tokyo",
            "summary": "sightseeing",
            "hero_url": "",
            "hero_fallback": "",
            "hero_source": "",
            "asset_slots": [],
            "sticker_zone": sticker,
            "freewrite_zone": freewrite,
        }

    def test_has_diy_class_when_zones_present(self):
        html = _render_page(self._make_page(sticker="top_right"))
        assert "has-diy" in html

    def test_no_has_diy_class_when_no_zones(self):
        html = _render_page(self._make_page())
        assert "has-diy" not in html

    def test_top_sticker_before_h2(self):
        """Top-right sticker should appear before the heading for float wrapping."""
        html = _render_page(self._make_page(sticker="top_right"))
        sticker_pos = html.index("diy-sticker-zone")
        h2_pos = html.index("<h2>")
        assert sticker_pos < h2_pos

    def test_bottom_freewrite_after_content(self):
        """Bottom freewrite should appear after the main content."""
        html = _render_page(self._make_page(freewrite="bottom_strip"))
        fw_pos = html.index("diy-freewrite-zone")
        h2_pos = html.index("<h2>")
        assert fw_pos > h2_pos


# ── DiyZoneContent dataclass ─────────────────────────────────────────────────


class TestDiyZoneContent:
    def test_defaults(self):
        c = DiyZoneContent()
        assert c.sticker_zone is None
        assert c.freewrite_zone is None

    def test_with_values(self):
        c = DiyZoneContent(sticker_zone="top_right", freewrite_zone="bottom_strip")
        assert c.sticker_zone == "top_right"
        assert c.freewrite_zone == "bottom_strip"


# ── _inject_diy_zones ────────────────────────────────────────────────────────


class TestInjectDiyZones:
    def _make_page_plan(self, sticker=None, freewrite=None):
        return PagePlan(
            page_id="test_page",
            page_order=1,
            chapter_id="ch1",
            page_type="day_execution",
            page_size="full",
            topic_family="daily",
            sticker_zone=sticker,
            freewrite_zone=freewrite,
        )

    def _make_vm(self):
        return PageViewModel(
            page_id="test_page",
            page_type="day_execution",
            page_size="full",
            heading=HeadingVM(title="Test"),
            footer=FooterVM(page_number=1),
        )

    def test_injects_when_sticker_present(self):
        vm = self._make_vm()
        page = self._make_page_plan(sticker="top_right")
        _inject_diy_zones(vm, page)
        diy_sections = [s for s in vm.sections if s.section_type == "diy_zone"]
        assert len(diy_sections) == 1
        assert isinstance(diy_sections[0].content, DiyZoneContent)
        assert diy_sections[0].content.sticker_zone == "top_right"

    def test_injects_when_freewrite_present(self):
        vm = self._make_vm()
        page = self._make_page_plan(freewrite="bottom_strip")
        _inject_diy_zones(vm, page)
        diy_sections = [s for s in vm.sections if s.section_type == "diy_zone"]
        assert len(diy_sections) == 1
        assert diy_sections[0].content.freewrite_zone == "bottom_strip"

    def test_no_inject_when_both_none(self):
        vm = self._make_vm()
        page = self._make_page_plan()
        _inject_diy_zones(vm, page)
        assert not any(s.section_type == "diy_zone" for s in vm.sections)

    def test_both_zones_in_single_section(self):
        vm = self._make_vm()
        page = self._make_page_plan(sticker="bottom_left", freewrite="bottom_strip")
        _inject_diy_zones(vm, page)
        diy_sections = [s for s in vm.sections if s.section_type == "diy_zone"]
        assert len(diy_sections) == 1
        content = diy_sections[0].content
        assert content.sticker_zone == "bottom_left"
        assert content.freewrite_zone == "bottom_strip"


# ── PagePlan DIY zone rules ──────────────────────────────────────────────────


class TestDiyZoneRules:
    def test_day_execution_has_diy(self):
        sticker, freewrite = _DIY_ZONE_RULES["day_execution"]
        assert sticker == "bottom_left"
        assert freewrite == "bottom_strip"

    def test_chapter_opener_has_diy(self):
        sticker, freewrite = _DIY_ZONE_RULES["chapter_opener"]
        assert sticker == "top_right"
        assert freewrite == "bottom_strip"

    def test_cover_has_sticker_only(self):
        sticker, freewrite = _DIY_ZONE_RULES["cover"]
        assert sticker == "corner"
        assert freewrite is None

    def test_toc_has_no_diy(self):
        sticker, freewrite = _DIY_ZONE_RULES["toc"]
        assert sticker is None
        assert freewrite is None


# ── page_type_registry optional_slots ─────────────────────────────────────────


class TestRegistryDiySlots:
    def test_day_execution_has_diy_slots(self):
        defn = PAGE_TYPE_REGISTRY["day_execution"]
        assert "sticker_zone" in defn.optional_slots
        assert "freewrite_zone" in defn.optional_slots

    def test_chapter_opener_has_diy_slots(self):
        defn = PAGE_TYPE_REGISTRY["chapter_opener"]
        assert "sticker_zone" in defn.optional_slots
        assert "freewrite_zone" in defn.optional_slots

    def test_cover_has_sticker_slot(self):
        defn = PAGE_TYPE_REGISTRY["cover"]
        assert "sticker_zone" in defn.optional_slots

    def test_hotel_detail_has_freewrite_slot(self):
        defn = PAGE_TYPE_REGISTRY["hotel_detail"]
        assert "freewrite_zone" in defn.optional_slots

    def test_restaurant_detail_has_both_diy_slots(self):
        defn = PAGE_TYPE_REGISTRY["restaurant_detail"]
        assert "sticker_zone" in defn.optional_slots
        assert "freewrite_zone" in defn.optional_slots


# ── CSS content checks ────────────────────────────────────────────────────────


class TestDiyCssContent:
    """Verify that the CSS string contains WeasyPrint-compatible rules."""

    def test_no_flexbox(self):
        from app.domains.rendering.magazine.html_renderer import _DIY_CSS
        # WeasyPrint has limited flexbox support; our CSS should not rely on it
        assert "display: flex" not in _DIY_CSS

    def test_has_page_rules(self):
        from app.domains.rendering.magazine.html_renderer import _DIY_CSS
        assert "@page" in _DIY_CSS
        assert "size: A4" in _DIY_CSS

    def test_has_page_break(self):
        from app.domains.rendering.magazine.html_renderer import _DIY_CSS
        assert "page-break-before: always" in _DIY_CSS

    def test_has_float_positioning(self):
        from app.domains.rendering.magazine.html_renderer import _DIY_CSS
        assert "float: right" in _DIY_CSS
        assert "float: left" in _DIY_CSS

    def test_has_notebook_lines(self):
        from app.domains.rendering.magazine.html_renderer import _DIY_CSS
        assert "repeating-linear-gradient" in _DIY_CSS

    def test_has_clearfix(self):
        from app.domains.rendering.magazine.html_renderer import _DIY_CSS
        assert "clear: both" in _DIY_CSS
