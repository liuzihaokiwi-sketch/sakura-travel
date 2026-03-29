"""
tests/integration/test_knowledge_pack.py -- E3 knowledge pack integration tests

Tests:
  1. Knowledge pack loading for kansai (circle_knowledge module)
  2. Circle content loading (circle_content module)
  3. Fallback behavior for unknown circles
  4. Knowledge pack integration with PlanningOutput prep_notes

Run:
  pytest tests/integration/test_knowledge_pack.py -v
"""
from __future__ import annotations

from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Lazy imports
# ---------------------------------------------------------------------------


def _import_circle_knowledge():
    from app.domains.planning.circle_knowledge import get_circle_knowledge
    return get_circle_knowledge


def _import_circle_content():
    from app.domains.planning.circle_content import (
        get_circle_content,
        get_circle_family_from_circle_id,
        CircleContent,
    )
    return get_circle_content, get_circle_family_from_circle_id, CircleContent


def _import_kansai_knowledge():
    from app.domains.planning.circle_knowledge.kansai import get_kansai_knowledge
    return get_kansai_knowledge


# ===========================================================================
# Knowledge pack loading (circle_knowledge)
# ===========================================================================

class TestKansaiKnowledgePack:
    """Test kansai knowledge pack structure and content completeness."""

    def test_kansai_knowledge_returns_dict(self):
        get_circle_knowledge = _import_circle_knowledge()
        knowledge = get_circle_knowledge("kansai")
        assert isinstance(knowledge, dict)
        assert knowledge is not None

    def test_kansai_knowledge_has_circle_id(self):
        get_circle_knowledge = _import_circle_knowledge()
        knowledge = get_circle_knowledge("kansai")
        assert knowledge["circle_id"] == "kansai_classic"

    def test_kansai_knowledge_has_version(self):
        get_circle_knowledge = _import_circle_knowledge()
        knowledge = get_circle_knowledge("kansai")
        assert "version" in knowledge
        assert knowledge["version"].startswith("v")

    def test_kansai_knowledge_has_required_sections(self):
        get_circle_knowledge = _import_circle_knowledge()
        knowledge = get_circle_knowledge("kansai")
        sections = knowledge["sections"]
        required_sections = [
            "airport_transport",
            "ic_card",
            "communication",
            "luggage",
            "payment",
            "useful_apps",
            "emergency",
            "seasonal_tips",
        ]
        for section_key in required_sections:
            assert section_key in sections, f"Missing required section: {section_key}"

    def test_each_section_has_title_and_items(self):
        get_circle_knowledge = _import_circle_knowledge()
        knowledge = get_circle_knowledge("kansai")
        sections = knowledge["sections"]
        for section_key, section in sections.items():
            assert "title" in section, f"Section {section_key} missing 'title'"
            assert "items" in section, f"Section {section_key} missing 'items'"
            assert len(section["items"]) >= 1, f"Section {section_key} has no items"

    def test_each_section_has_tips(self):
        get_circle_knowledge = _import_circle_knowledge()
        knowledge = get_circle_knowledge("kansai")
        sections = knowledge["sections"]
        for section_key, section in sections.items():
            # tips should exist as a key (may be empty for some sections)
            assert "tips" in section, f"Section {section_key} missing 'tips' key"

    def test_airport_transport_covers_kix(self):
        """Airport transport section should mention KIX (Kansai International)."""
        get_circle_knowledge = _import_circle_knowledge()
        knowledge = get_circle_knowledge("kansai")
        items = knowledge["sections"]["airport_transport"]["items"]
        text = " ".join(items)
        assert "KIX" in text or "关西" in text, "airport_transport should mention KIX"

    def test_emergency_has_phone_numbers(self):
        get_circle_knowledge = _import_circle_knowledge()
        knowledge = get_circle_knowledge("kansai")
        items = knowledge["sections"]["emergency"]["items"]
        text = " ".join(items)
        assert "119" in text or "110" in text, "emergency section should contain emergency phone numbers"

    def test_kansai_classic_alias_works(self):
        """Both 'kansai' and 'kansai_classic' should return the same data."""
        get_circle_knowledge = _import_circle_knowledge()
        k1 = get_circle_knowledge("kansai")
        k2 = get_circle_knowledge("kansai_classic")
        assert k1 is not None
        assert k2 is not None
        assert k1["circle_id"] == k2["circle_id"]

    def test_direct_kansai_function_matches_registry(self):
        get_circle_knowledge = _import_circle_knowledge()
        get_kansai_knowledge = _import_kansai_knowledge()
        via_registry = get_circle_knowledge("kansai")
        via_direct = get_kansai_knowledge()
        assert via_registry == via_direct


# ===========================================================================
# Circle content loading (circle_content)
# ===========================================================================

class TestCircleContentLoading:
    """Test circle_content module for various circle families."""

    def test_kansai_content_loads(self):
        get_circle_content, _, _ = _import_circle_content()
        content = get_circle_content("kansai")
        assert content is not None
        assert content.persona_name, "persona_name should not be empty"
        assert content.dest_name, "dest_name should not be empty"
        assert content.persona_bio, "persona_bio should not be empty"

    def test_kansai_content_has_static_prep(self):
        get_circle_content, _, _ = _import_circle_content()
        content = get_circle_content("kansai")
        assert content.static_prep, "static_prep should not be empty"
        assert "title" in content.static_prep
        assert "sections" in content.static_prep
        assert len(content.static_prep["sections"]) >= 3

    def test_kansai_dest_aliases(self):
        get_circle_content, _, _ = _import_circle_content()
        content = get_circle_content("kansai")
        assert "kyoto" in content.dest_aliases
        assert "osaka" in content.dest_aliases
        assert content.resolve_dest_name("kyoto") == "京都"
        assert content.resolve_dest_name("osaka") == "大阪"

    def test_kanto_content_loads(self):
        get_circle_content, _, _ = _import_circle_content()
        content = get_circle_content("kanto")
        assert content is not None
        assert content.persona_name

    def test_hokkaido_content_loads(self):
        get_circle_content, _, _ = _import_circle_content()
        content = get_circle_content("hokkaido")
        assert content is not None
        assert content.dest_name

    def test_guangdong_content_loads(self):
        get_circle_content, _, _ = _import_circle_content()
        content = get_circle_content("guangdong")
        assert content is not None

    def test_northern_xinjiang_content_loads(self):
        get_circle_content, _, _ = _import_circle_content()
        content = get_circle_content("northern_xinjiang")
        assert content is not None

    def test_south_china_content_loads(self):
        get_circle_content, _, _ = _import_circle_content()
        content = get_circle_content("south_china")
        assert content is not None

    def test_visual_trigger_tags_are_set(self):
        get_circle_content, _, _ = _import_circle_content()
        content = get_circle_content("kansai")
        assert isinstance(content.visual_trigger_tags, set)
        # Kansai should have some visual tags
        assert len(content.visual_trigger_tags) >= 3


# ===========================================================================
# Circle family resolution
# ===========================================================================

class TestCircleFamilyResolution:
    """Test get_circle_family_from_circle_id for various circle ID patterns."""

    def test_kansai_patterns(self):
        _, get_family, _ = _import_circle_content()
        assert get_family("kansai_classic_circle") == "kansai"
        assert get_family("kansai_v1") == "kansai"
        assert get_family("KANSAI") == "kansai"

    def test_kanto_patterns(self):
        _, get_family, _ = _import_circle_content()
        assert get_family("kanto_city_circle") == "kanto"
        assert get_family("tokyo_v1") == "kanto"

    def test_hokkaido_patterns(self):
        _, get_family, _ = _import_circle_content()
        assert get_family("hokkaido_city_circle") == "hokkaido"
        assert get_family("hokkaido_v2") == "hokkaido"

    def test_south_china_patterns(self):
        _, get_family, _ = _import_circle_content()
        assert get_family("south_china_five_city_circle") == "south_china"
        assert get_family("guangzhou_metro") == "south_china"
        assert get_family("shenzhen_circle") == "south_china"

    def test_guangdong_patterns(self):
        _, get_family, _ = _import_circle_content()
        assert get_family("guangdong_city_circle") == "guangdong"

    def test_xinjiang_patterns(self):
        _, get_family, _ = _import_circle_content()
        assert get_family("northern_xinjiang_city_circle") == "northern_xinjiang"
        assert get_family("xinjiang_v1") == "northern_xinjiang"

    def test_unknown_falls_back_to_kansai(self):
        _, get_family, _ = _import_circle_content()
        assert get_family("unknown_circle_999") == "kansai"
        assert get_family("") == "kansai"


# ===========================================================================
# Fallback behavior for unknown circles
# ===========================================================================

class TestUnknownCircleFallback:
    """Test that unknown circle IDs produce graceful fallback behavior."""

    def test_unknown_knowledge_returns_none(self):
        get_circle_knowledge = _import_circle_knowledge()
        result = get_circle_knowledge("totally_unknown_circle_xyz")
        assert result is None, "Unknown circle should return None from knowledge registry"

    def test_unknown_content_falls_back_to_kansai(self):
        get_circle_content, _, _ = _import_circle_content()
        # Unknown family falls back to kansai in the implementation
        content = get_circle_content("totally_unknown_family")
        assert content is not None
        assert content.dest_name == "关西", "Unknown family should fall back to kansai content"

    def test_none_circle_id_safe(self):
        _, get_family, _ = _import_circle_content()
        family = get_family("")
        assert family == "kansai"


# ===========================================================================
# Knowledge pack integration with PlanningOutput
# ===========================================================================

class TestKnowledgePackIntegration:
    """Test that knowledge packs flow into PlanningOutput prep_notes correctly."""

    def test_kansai_knowledge_sections_count(self):
        """Building knowledge sections from kansai pack should yield 8 sections."""
        get_circle_knowledge = _import_circle_knowledge()
        knowledge = get_circle_knowledge("kansai")
        sections = knowledge["sections"]
        expected_keys = [
            "airport_transport", "ic_card", "communication",
            "luggage", "payment", "useful_apps", "emergency", "seasonal_tips",
        ]
        present = [k for k in expected_keys if k in sections]
        assert len(present) == 8, f"Expected 8 knowledge sections, got {len(present)}"

    def test_knowledge_sections_to_flat_list(self):
        """Simulate the planning_output.py logic of converting sections to flat list."""
        get_circle_knowledge = _import_circle_knowledge()
        knowledge = get_circle_knowledge("kansai")
        sections = knowledge["sections"]

        _ALL_SECTION_KEYS = (
            "airport_transport", "ic_card", "communication",
            "luggage", "payment", "useful_apps", "emergency", "seasonal_tips",
        )
        combined_items: list[str] = []
        knowledge_sections: list[dict] = []
        for section_key in _ALL_SECTION_KEYS:
            sec = sections.get(section_key, {})
            if not sec:
                continue
            title = sec.get("title", section_key)
            items = sec.get("items", [])
            tips = sec.get("tips", [])
            combined_items.append(f"[{title}]")
            combined_items.extend(items)
            if tips:
                combined_items.extend(tips)
            knowledge_sections.append({
                "key": section_key,
                "title": title,
                "items": items,
                "tips": tips,
            })

        assert len(combined_items) >= 20, f"Expected at least 20 combined items, got {len(combined_items)}"
        assert len(knowledge_sections) == 8

    def test_prep_notes_from_test_helper_has_items(self):
        """Test helper's PlanningOutput should have non-empty prep_notes."""
        from tests.helpers.build_test_planning_output import build_test_planning_output
        po = build_test_planning_output(total_days=3, destination="kansai")
        assert po.prep_notes["items"], "prep_notes items should not be empty"

    def test_departure_prep_vm_reflects_knowledge(self):
        """Departure prep view model should include knowledge sections when available."""
        from tests.helpers.build_test_planning_output import build_test_planning_output
        from app.domains.rendering.chapter_planner import plan_chapters
        from app.domains.rendering.page_planner import plan_pages
        from app.domains.rendering.page_view_model import build_view_models

        po = build_test_planning_output(total_days=3, destination="kansai")

        # Inject knowledge-pack-style prep_notes to simulate real pipeline
        get_circle_knowledge = _import_circle_knowledge()
        knowledge = get_circle_knowledge("kansai")
        if knowledge:
            _ALL_SECTION_KEYS = (
                "airport_transport", "ic_card", "communication",
                "luggage", "payment", "useful_apps", "emergency", "seasonal_tips",
            )
            sections_data = knowledge.get("sections", {})
            combined_items: list[str] = []
            knowledge_sections: list[dict] = []
            for sk in _ALL_SECTION_KEYS:
                sec = sections_data.get(sk, {})
                if not sec:
                    continue
                title = sec.get("title", sk)
                items = sec.get("items", [])
                tips = sec.get("tips", [])
                combined_items.append(f"[{title}]")
                combined_items.extend(items)
                if tips:
                    combined_items.extend(tips)
                knowledge_sections.append({"key": sk, "title": title, "items": items, "tips": tips})

            po.prep_notes = {
                "title": "关西出行准备",
                "items": combined_items,
                "knowledge": knowledge,
                "knowledge_sections": knowledge_sections,
            }

        chapters = plan_chapters(po)
        pages = plan_pages(chapters, po)
        vms = build_view_models(pages, po)

        # Find departure_prep VM
        dp_page = next((p for p in pages if p.page_type == "departure_prep"), None)
        assert dp_page is not None, "departure_prep page should exist"

        vm = vms[dp_page.page_id]
        # When knowledge_sections is present, VM should have multiple text_block sections
        text_blocks = [s for s in vm.sections if s.section_type == "text_block"]
        assert len(text_blocks) >= 4, (
            f"Departure prep with knowledge pack should have many text_block sections, got {len(text_blocks)}"
        )

        # internal_state should indicate knowledge pack is present
        assert vm.internal_state.get("has_knowledge_pack") is True
