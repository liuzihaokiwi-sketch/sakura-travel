"""
tests/integration/test_full_pipeline.py -- E3 end-to-end integration tests

Verifies the full pipeline chain:
  form input -> normalization -> planning output -> chapter planning ->
  page planning -> view model construction -> copy enrichment ->
  quality gate -> budget estimation -> Plan B -> rate limiter -> rotation penalty

All DB and external AI calls are mocked.

Run:
  pytest tests/integration/test_full_pipeline.py -v --timeout=120
"""
from __future__ import annotations

import asyncio
import math
import time
import uuid
from dataclasses import asdict
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Lazy imports to avoid CI failures when DB drivers are missing
# ---------------------------------------------------------------------------


def _import_planning_output():
    from app.domains.rendering.planning_output import PlanningOutput
    return PlanningOutput


def _import_chapter_planner():
    from app.domains.rendering.chapter_planner import plan_chapters, ChapterPlan
    return plan_chapters, ChapterPlan


def _import_page_planner():
    from app.domains.rendering.page_planner import plan_pages, plan_pages_and_persist, PagePlan
    return plan_pages, plan_pages_and_persist, PagePlan


def _import_view_model_builder():
    from app.domains.rendering.page_view_model import build_view_models, PageViewModel
    return build_view_models, PageViewModel


def _import_copy_enrichment():
    from app.domains.rendering.copy_enrichment import enrich_page_copy
    return enrich_page_copy


def _import_quality_gate():
    from app.core.quality_gate import run_quality_gate_sync, run_quality_gate, QualityGateResult
    return run_quality_gate_sync, run_quality_gate, QualityGateResult


def _import_budget_estimator():
    from app.domains.planning.budget_estimator import (
        DayBudgetEstimate,
        TripBudgetEstimate,
        estimate_trip_budget,
        TRANSPORT_BUDGET_BY_TIER,
        HOTEL_BUDGET_BY_TIER,
        FOOD_FLOOR_BY_TIER,
        MISC_BUFFER_RATE,
        JPY_TO_CNY,
    )
    return (
        DayBudgetEstimate, TripBudgetEstimate, estimate_trip_budget,
        TRANSPORT_BUDGET_BY_TIER, HOTEL_BUDGET_BY_TIER, FOOD_FLOOR_BY_TIER,
        MISC_BUFFER_RATE, JPY_TO_CNY,
    )


def _import_plan_b_builder():
    from app.domains.planning.plan_b_builder import (
        build_plan_b_for_day,
        _OUTDOOR_CATEGORIES,
        _INDOOR_CATEGORIES,
        _is_weather_sensitive,
        _needs_booking,
    )
    return build_plan_b_for_day, _OUTDOOR_CATEGORIES, _INDOOR_CATEGORIES, _is_weather_sensitive, _needs_booking


def _import_rate_limiter():
    from app.core.rate_limiter import (
        InMemoryBackend,
        _classify_path,
        GENERATION_WINDOW,
        GENERATION_MAX,
    )
    return InMemoryBackend, _classify_path, GENERATION_WINDOW, GENERATION_MAX


def _import_rotation():
    from app.domains.ranking.rotation import (
        compute_rotation_penalty,
        apply_rotation_penalty,
        _ROTATION_ALPHA,
        _MAX_PENALTY,
    )
    return compute_rotation_penalty, apply_rotation_penalty, _ROTATION_ALPHA, _MAX_PENALTY


# ---------------------------------------------------------------------------
# Shared test helper
# ---------------------------------------------------------------------------

def _build_test_planning_output(total_days: int = 3, destination: str = "kansai"):
    """Build a PlanningOutput via the existing test helper."""
    from tests.helpers.build_test_planning_output import build_test_planning_output
    return build_test_planning_output(total_days=total_days, destination=destination)


# ===========================================================================
# (a) Planning output construction test
# ===========================================================================

class TestPlanningOutputConstruction:
    """Given mock ItineraryPlan + days + items, verify PlanningOutput fields."""

    def test_prep_notes_populated(self):
        po = _build_test_planning_output(total_days=3)
        assert po.prep_notes, "prep_notes must not be empty"
        assert "title" in po.prep_notes
        assert "items" in po.prep_notes
        assert len(po.prep_notes["items"]) >= 1

    def test_days_correct_count(self):
        for n in (1, 3, 5, 7):
            po = _build_test_planning_output(total_days=n)
            assert len(po.days) == n, f"Expected {n} days, got {len(po.days)}"

    def test_booking_alerts_populated_when_booking_required(self):
        po = _build_test_planning_output(total_days=3)
        # Day 1 has booking_required=True in the test helper
        assert len(po.booking_alerts) >= 1, "booking_alerts should be populated for booking-required slots"
        assert po.booking_alerts[0].booking_level in ("must_book", "should_book", "good_to_book")

    def test_emotional_goals_exist_per_day(self):
        po = _build_test_planning_output(total_days=4)
        assert len(po.emotional_goals) == 4
        for eg in po.emotional_goals:
            assert eg.mood_keyword, "mood_keyword must not be empty"
            assert eg.mood_sentence, "mood_sentence must not be empty"

    def test_meta_fields_complete(self):
        po = _build_test_planning_output(total_days=3, destination="kansai")
        assert po.meta.trip_id
        assert po.meta.destination == "kansai"
        assert po.meta.total_days == 3

    def test_profile_summary_fields(self):
        po = _build_test_planning_output(total_days=2)
        assert po.profile_summary.party_type == "couple"
        assert po.profile_summary.pace_preference in ("light", "balanced", "dense")

    def test_conditional_sections_generated(self):
        po = _build_test_planning_output(total_days=3)
        assert len(po.conditional_sections) >= 1, "conditional_sections should exist for POI slots"
        for cs in po.conditional_sections:
            assert cs.section_type in ("extra", "restaurant", "hotel", "transport", "photo", "budget")
            assert "entity_id" in cs.payload

    def test_selection_evidence_generated(self):
        po = _build_test_planning_output(total_days=2)
        assert len(po.selection_evidence) >= 1
        for ev in po.selection_evidence:
            assert "entity_id" in ev
            assert "name" in ev

    def test_circles_and_day_circle_map(self):
        po = _build_test_planning_output(total_days=3)
        assert len(po.circles) >= 1
        assert po.circles[0].circle_id
        for d in po.days:
            assert d.day_index in po.day_circle_map


# ===========================================================================
# (b) Page planning test
# ===========================================================================

class TestPagePlanning:
    """Given a PlanningOutput, verify chapter + page plan correctness."""

    def test_chapter_structure(self):
        plan_chapters, _ = _import_chapter_planner()
        po = _build_test_planning_output(total_days=5)
        chapters = plan_chapters(po)
        chapter_types = [c.chapter_type for c in chapters]
        assert chapter_types[0] == "frontmatter"
        assert chapter_types[-1] == "appendix"

    def test_all_expected_page_types_present(self):
        plan_chapters, _ = _import_chapter_planner()
        plan_pages, _, _ = _import_page_planner()
        po = _build_test_planning_output(total_days=3)
        chapters = plan_chapters(po)
        pages = plan_pages(chapters, po)

        page_types = {p.page_type for p in pages}
        required_types = {"cover", "toc", "day_execution", "departure_prep"}
        for rt in required_types:
            assert rt in page_types, f"Missing required page type: {rt}"

    def test_booking_window_present_when_booking_required(self):
        plan_chapters, _ = _import_chapter_planner()
        plan_pages, _, _ = _import_page_planner()
        po = _build_test_planning_output(total_days=3)
        # Day 1 has booking_required=True
        chapters = plan_chapters(po)
        pages = plan_pages(chapters, po)
        page_types = {p.page_type for p in pages}
        assert "booking_window" in page_types, "booking_window page should be present when slots have booking_required"

    def test_day_execution_pages_match_days(self):
        plan_chapters, _ = _import_chapter_planner()
        plan_pages, _, _ = _import_page_planner()
        po = _build_test_planning_output(total_days=5)
        chapters = plan_chapters(po)
        pages = plan_pages(chapters, po)

        day_exec_pages = [p for p in pages if p.page_type == "day_execution"]
        assert len(day_exec_pages) == 5, f"Expected 5 day_execution pages, got {len(day_exec_pages)}"
        day_indices = sorted(p.day_index for p in day_exec_pages)
        assert day_indices == [1, 2, 3, 4, 5]

    def test_diy_zones_assigned_to_correct_page_types(self):
        plan_chapters, _ = _import_chapter_planner()
        plan_pages, _, _ = _import_page_planner()
        po = _build_test_planning_output(total_days=3)
        chapters = plan_chapters(po)
        pages = plan_pages(chapters, po)

        for page in pages:
            if page.page_type == "day_execution":
                assert page.sticker_zone == "bottom_left", f"day_execution should have bottom_left sticker zone"
                assert page.freewrite_zone == "bottom_strip"
            elif page.page_type == "cover":
                assert page.sticker_zone == "corner", f"cover should have corner sticker zone"
            elif page.page_type == "toc":
                assert page.sticker_zone is None
                assert page.freewrite_zone is None

    def test_page_order_continuous(self):
        plan_chapters, _ = _import_chapter_planner()
        plan_pages, _, _ = _import_page_planner()
        po = _build_test_planning_output(total_days=3)
        chapters = plan_chapters(po)
        pages = plan_pages(chapters, po)

        orders = [p.page_order for p in pages]
        assert orders == list(range(1, len(pages) + 1)), "Page orders must be continuously numbered from 1"

    def test_page_budget_not_exceeded(self):
        plan_chapters, _ = _import_chapter_planner()
        plan_pages, _, _ = _import_page_planner()
        # 14-day trip should stay within 70-page budget
        po = _build_test_planning_output(total_days=14)
        chapters = plan_chapters(po)
        pages = plan_pages(chapters, po)
        assert len(pages) <= 70, f"14-day plan should not exceed 70 pages, got {len(pages)}"

    def test_multi_circle_chapters(self):
        """6+ day, multi-circle trip should produce circle chapters."""
        from app.domains.planning.report_schema import SelectedCircleInfo
        plan_chapters, _ = _import_chapter_planner()
        po = _build_test_planning_output(total_days=7)
        # Inject a second circle
        po.circles.append(SelectedCircleInfo(circle_id="kanto_city_circle", name_zh="关东"))
        po.day_circle_map[5] = "kanto_city_circle"
        po.day_circle_map[6] = "kanto_city_circle"
        po.day_circle_map[7] = "kanto_city_circle"
        chapters = plan_chapters(po)
        circle_chapters = [c for c in chapters if c.chapter_type == "circle"]
        assert len(circle_chapters) >= 2, "Multi-circle 7-day trip should produce >=2 circle chapters"


# ===========================================================================
# (c) View model construction test
# ===========================================================================

class TestViewModelConstruction:
    """Given page plans + planning output, verify view model correctness."""

    def _build_pages_and_vms(self, total_days: int = 3):
        plan_chapters, _ = _import_chapter_planner()
        plan_pages, _, _ = _import_page_planner()
        build_view_models, _ = _import_view_model_builder()
        po = _build_test_planning_output(total_days=total_days)
        chapters = plan_chapters(po)
        pages = plan_pages(chapters, po)
        vms = build_view_models(pages, po)
        return pages, vms, po

    def test_every_page_has_view_model(self):
        pages, vms, _ = self._build_pages_and_vms()
        for page in pages:
            assert page.page_id in vms, f"Missing VM for page {page.page_id}"

    def test_day_execution_has_timeline(self):
        pages, vms, _ = self._build_pages_and_vms()
        day_exec = [p for p in pages if p.page_type == "day_execution"]
        for page in day_exec:
            vm = vms[page.page_id]
            section_types = [s.section_type for s in vm.sections]
            assert "timeline" in section_types, f"day_execution VM {page.page_id} missing timeline section"

    def test_day_execution_has_diy_zone(self):
        pages, vms, _ = self._build_pages_and_vms()
        day_exec = [p for p in pages if p.page_type == "day_execution"]
        for page in day_exec:
            vm = vms[page.page_id]
            section_types = [s.section_type for s in vm.sections]
            assert "diy_zone" in section_types, f"day_execution VM {page.page_id} missing diy_zone section"

    def test_cover_has_stat_strip(self):
        pages, vms, _ = self._build_pages_and_vms()
        cover = next(p for p in pages if p.page_type == "cover")
        vm = vms[cover.page_id]
        section_types = [s.section_type for s in vm.sections]
        assert "stat_strip" in section_types

    def test_toc_has_entries(self):
        pages, vms, _ = self._build_pages_and_vms()
        toc = next(p for p in pages if p.page_type == "toc")
        vm = vms[toc.page_id]
        section_types = [s.section_type for s in vm.sections]
        assert "toc_list" in section_types
        toc_section = next(s for s in vm.sections if s.section_type == "toc_list")
        assert hasattr(toc_section.content, "entries") or "entries" in (toc_section.content or {})

    def test_plan_b_present_in_day_execution(self):
        """day_execution VM should have plan_b section if Plan B data exists."""
        from app.domains.planning.report_schema import PlanBOption
        plan_chapters, _ = _import_chapter_planner()
        plan_pages, _, _ = _import_page_planner()
        build_view_models, _ = _import_view_model_builder()
        po = _build_test_planning_output(total_days=3)
        # Inject plan_b into day 1
        po.days[0].plan_b = [PlanBOption(trigger="rain", alternative="Visit museum instead", entity_ids=["e1", "e2"])]
        chapters = plan_chapters(po)
        pages = plan_pages(chapters, po)
        vms = build_view_models(pages, po)
        day1_page = next(p for p in pages if p.page_type == "day_execution" and p.day_index == 1)
        vm = vms[day1_page.page_id]
        section_types = [s.section_type for s in vm.sections]
        assert "plan_b" in section_types, "Plan B section should be present when day has plan_b data"

    def test_booking_window_has_booking_timeline(self):
        pages, vms, _ = self._build_pages_and_vms()
        bw_pages = [p for p in pages if p.page_type == "booking_window"]
        if bw_pages:
            vm = vms[bw_pages[0].page_id]
            section_types = [s.section_type for s in vm.sections]
            assert "booking_timeline" in section_types
            assert "stat_strip" in section_types

    def test_departure_prep_has_text_blocks(self):
        pages, vms, _ = self._build_pages_and_vms()
        dp = next(p for p in pages if p.page_type == "departure_prep")
        vm = vms[dp.page_id]
        section_types = [s.section_type for s in vm.sections]
        assert "text_block" in section_types

    def test_editable_content_on_day_execution(self):
        pages, vms, _ = self._build_pages_and_vms()
        day_exec = [p for p in pages if p.page_type == "day_execution"]
        for page in day_exec:
            vm = vms[page.page_id]
            assert vm.editable_content, f"editable_content should be populated for {page.page_id}"
            assert "mood_sentence" in vm.editable_content
            assert "day_intro_draft" in vm.editable_content

    def test_stable_inputs_on_day_execution(self):
        pages, vms, _ = self._build_pages_and_vms()
        day_exec = [p for p in pages if p.page_type == "day_execution"]
        for page in day_exec:
            vm = vms[page.page_id]
            assert "day_index" in vm.stable_inputs
            assert "slot_count" in vm.stable_inputs


# ===========================================================================
# (d) Copy enrichment test (mock AI client)
# ===========================================================================

class TestCopyEnrichment:
    """Given view models + planning output, verify AI copy enrichment populates fields."""

    @pytest.mark.asyncio
    async def test_mood_sentence_and_tagline_populated(self):
        enrich_page_copy = _import_copy_enrichment()
        plan_chapters, _ = _import_chapter_planner()
        plan_pages_fn, _, _ = _import_page_planner()
        build_view_models, _ = _import_view_model_builder()
        po = _build_test_planning_output(total_days=3)
        chapters = plan_chapters(po)
        pages = plan_pages_fn(chapters, po)
        vms = build_view_models(pages, po)

        # Mock the AI client so _ai_generate_day_copy and _ai_generate_cover_copy return values
        with patch(
            "app.domains.rendering.copy_enrichment._ai_generate_day_copy",
            new_callable=AsyncMock,
            return_value={"mood_sentence": "AI mood test", "day_intro": "AI intro test"},
        ), patch(
            "app.domains.rendering.copy_enrichment._ai_generate_cover_copy",
            new_callable=AsyncMock,
            return_value={"tagline": "AI tagline test"},
        ):
            enriched = await enrich_page_copy(vms, po)

        # Check day_execution pages have mood_sentence
        for page_id, vm in enriched.items():
            if vm.page_type == "day_execution":
                ec = vm.editable_content
                assert ec.get("mood_sentence"), f"mood_sentence should be populated for {page_id}"

        # Check cover page has tagline
        cover_vms = [vm for vm in enriched.values() if vm.page_type == "cover"]
        if cover_vms:
            ec = cover_vms[0].editable_content
            assert ec.get("trip_tagline"), "trip_tagline should be populated on cover"

    @pytest.mark.asyncio
    async def test_enrichment_uses_rule_fallback_on_ai_failure(self):
        enrich_page_copy = _import_copy_enrichment()
        plan_chapters, _ = _import_chapter_planner()
        plan_pages_fn, _, _ = _import_page_planner()
        build_view_models, _ = _import_view_model_builder()
        po = _build_test_planning_output(total_days=2)
        chapters = plan_chapters(po)
        pages = plan_pages_fn(chapters, po)
        vms = build_view_models(pages, po)

        # Mock AI to fail
        with patch(
            "app.domains.rendering.copy_enrichment._ai_generate_day_copy",
            new_callable=AsyncMock,
            side_effect=Exception("AI unavailable"),
        ), patch(
            "app.domains.rendering.copy_enrichment._ai_generate_cover_copy",
            new_callable=AsyncMock,
            side_effect=Exception("AI unavailable"),
        ):
            enriched = await enrich_page_copy(vms, po)

        # Should still have rule-based fallbacks
        for page_id, vm in enriched.items():
            if vm.page_type == "day_execution":
                ec = vm.editable_content
                # Rule-based mood comes from emotional_goals
                assert "mood_sentence" in ec, "mood_sentence should have rule fallback"

        cover_vms = [vm for vm in enriched.values() if vm.page_type == "cover"]
        if cover_vms:
            ec = cover_vms[0].editable_content
            assert "trip_tagline" in ec, "trip_tagline should have rule fallback"


# ===========================================================================
# (e) Quality gate test
# ===========================================================================

class TestQualityGate:
    """Given a plan JSON, verify quality gate returns score and rules."""

    def _minimal_plan(self, days: int = 5) -> dict:
        return {
            "plan_id": str(uuid.uuid4()),
            "days": [
                {
                    "day_index": i + 1,
                    "day_number": i + 1,
                    "title": f"Day {i + 1}",
                    "primary_area": "kyoto",
                    "items": [
                        {
                            "entity_id": str(uuid.uuid4()),
                            "entity_type": "poi",
                            "item_type": "poi",
                            "entity_name": f"Spot {j + 1}",
                            "title": f"Spot {j + 1}",
                            "start_time": f"{9 + j * 2:02d}:00",
                            "duration_min": 90,
                            "booking_required": False,
                            "recommendation_reason": "High quality attraction with great reviews and unique features.",
                            "copy_zh": f"Spot {j + 1} is a great attraction",
                            "risk_warnings": ["Peak hours may be crowded"],
                        }
                        for j in range(4)
                    ] + [
                        {
                            "entity_id": str(uuid.uuid4()),
                            "entity_type": "restaurant",
                            "item_type": "restaurant",
                            "entity_name": f"Restaurant {i + 1}",
                            "title": f"Restaurant {i + 1}",
                            "start_time": "18:00",
                            "duration_min": 60,
                            "recommendation_reason": "Local favourite with authentic cuisine and great atmosphere.",
                            "copy_zh": f"Restaurant {i + 1} serves authentic local cuisine",
                            "risk_warnings": ["No reservations accepted"],
                        }
                    ],
                    "transport_note": "JR + walk",
                    "walk_score": 8.0,
                }
                for i in range(days)
            ],
        }

    def test_quality_gate_returns_score(self):
        run_quality_gate_sync, _, _ = _import_quality_gate()
        plan = self._minimal_plan(days=3)
        result = run_quality_gate_sync(plan)
        assert 0.0 <= result.score <= 1.0, f"Score out of range: {result.score}"
        assert isinstance(result.passed, bool)

    def test_valid_plan_no_hard_failures(self):
        run_quality_gate_sync, _, _ = _import_quality_gate()
        plan = self._minimal_plan(days=5)
        result = run_quality_gate_sync(plan)
        hard_errors = [r for r in result.results if not r.passed and r.severity == "error"]
        # We allow some DB-dependent rules to fail (QTY-06, 07, 10), but structural rules should pass
        structural_errors = [
            e for e in hard_errors
            if e.rule_id not in ("QTY-06", "QTY-07", "QTY-10")
        ]
        assert len(structural_errors) == 0, f"Unexpected structural hard failures: {[e.rule_id for e in structural_errors]}"

    def test_empty_plan_fails(self):
        run_quality_gate_sync, _, _ = _import_quality_gate()
        result = run_quality_gate_sync({"days": []})
        assert result.passed is False or result.score < 0.5, "Empty plan should not pass quality gate"

    @pytest.mark.asyncio
    async def test_async_quality_gate(self):
        _, run_quality_gate, _ = _import_quality_gate()
        plan = self._minimal_plan(days=3)
        result = await run_quality_gate(plan, db=None)
        assert 0.0 <= result.score <= 1.0


# ===========================================================================
# (f) Budget estimation test
# ===========================================================================

class TestBudgetEstimation:
    """Given day budgets, verify aggregation math and reasonable ranges."""

    def test_component_sum_equals_total(self):
        (
            DayBudgetEstimate, _, estimate_trip_budget,
            TRANSPORT_BUDGET_BY_TIER, HOTEL_BUDGET_BY_TIER, FOOD_FLOOR_BY_TIER,
            MISC_BUFFER_RATE, JPY_TO_CNY,
        ) = _import_budget_estimator()

        day_budgets = [
            DayBudgetEstimate(
                day_index=1,
                admission_jpy=1500,
                food_jpy=4000,
                transport_jpy=1200,
                hotel_jpy=10000,
            ),
            DayBudgetEstimate(
                day_index=2,
                admission_jpy=2000,
                food_jpy=3500,
                transport_jpy=1200,
                hotel_jpy=10000,
            ),
            DayBudgetEstimate(
                day_index=3,
                admission_jpy=800,
                food_jpy=5000,
                transport_jpy=1200,
                hotel_jpy=0,  # last day, no hotel
            ),
        ]

        trip = estimate_trip_budget(day_budgets)

        assert trip.total_days == 3
        assert trip.total_admission_jpy == 1500 + 2000 + 800
        assert trip.total_food_jpy == 4000 + 3500 + 5000
        assert trip.total_transport_jpy == 1200 * 3

        # total_jpy includes misc buffer
        expected_total = sum(d.total_jpy for d in day_budgets)
        assert trip.total_jpy == expected_total

        # Check that misc_jpy = 10% of subtotal for each day
        for db in day_budgets:
            subtotal = db.admission_jpy + db.food_jpy + db.transport_jpy + db.hotel_jpy
            # Calling total_jpy triggers misc calculation
            _ = db.total_jpy
            assert db.misc_jpy == int(subtotal * MISC_BUFFER_RATE)

    def test_cny_conversion(self):
        (
            DayBudgetEstimate, _, estimate_trip_budget,
            *_, JPY_TO_CNY,
        ) = _import_budget_estimator()

        db = DayBudgetEstimate(day_index=1, admission_jpy=1000, food_jpy=3000, transport_jpy=1000, hotel_jpy=8000)
        total_jpy = db.total_jpy
        expected_cny = round(total_jpy * JPY_TO_CNY, 0)
        assert db.total_cny == expected_cny

    def test_reasonable_daily_ranges(self):
        """A mid-tier daily budget should be in a reasonable range."""
        (
            DayBudgetEstimate, _, estimate_trip_budget,
            TRANSPORT_BUDGET_BY_TIER, HOTEL_BUDGET_BY_TIER, FOOD_FLOOR_BY_TIER,
            *_,
        ) = _import_budget_estimator()

        db = DayBudgetEstimate(
            day_index=1,
            admission_jpy=1000,
            food_jpy=FOOD_FLOOR_BY_TIER["mid"],
            transport_jpy=TRANSPORT_BUDGET_BY_TIER["mid"],
            hotel_jpy=HOTEL_BUDGET_BY_TIER["mid"],
        )
        total = db.total_jpy
        # Mid-tier daily total should be between 10k and 30k JPY
        assert 10000 <= total <= 30000, f"Daily total {total} JPY out of reasonable range"

    def test_avg_daily_computed(self):
        (
            DayBudgetEstimate, _, estimate_trip_budget,
            *_,
        ) = _import_budget_estimator()

        day_budgets = [
            DayBudgetEstimate(day_index=i, admission_jpy=500, food_jpy=3000, transport_jpy=1000, hotel_jpy=8000)
            for i in range(1, 4)
        ]
        trip = estimate_trip_budget(day_budgets)
        assert trip.avg_daily_jpy == trip.total_jpy // 3


# ===========================================================================
# (g) Plan B generation test (mock DB)
# ===========================================================================

class TestPlanBGeneration:
    """Verify Plan B logic: weather replacements + booking failure alternatives."""

    @pytest.mark.asyncio
    async def test_weather_replacement_generates_indoor_alternative(self):
        build_plan_b_for_day, _OUTDOOR_CATEGORIES, *_ = _import_plan_b_builder()

        from app.domains.planning.report_schema import DaySlot

        # Create an outdoor POI slot
        outdoor_slot = DaySlot(
            slot_index=0,
            kind="poi",
            entity_id="outdoor_temple_001",
            title="Famous Temple",
            area="higashiyama",
            start_time_hint="09:00",
            duration_mins=90,
        )

        # Mock session + entity lookups
        session = AsyncMock()

        # EntityBase mock (outdoor temple)
        entity_base = MagicMock()
        entity_base.entity_id = "outdoor_temple_001"
        entity_base.entity_type = "poi"
        entity_base.city_code = "kyoto"
        entity_base.area_name = "higashiyama"
        entity_base.risk_flags = ["weather_sensitive"]
        entity_base.booking_method = None

        # Poi mock
        poi_mock = MagicMock()
        poi_mock.poi_category = "temple"
        poi_mock.typical_duration_min = 90
        poi_mock.requires_advance_booking = False

        # Indoor alternative result
        indoor_result = MagicMock()
        indoor_row = {"entity_id": "indoor_museum_001", "name_zh": "Museum X", "area_name": "higashiyama"}
        indoor_result.mappings.return_value.first.return_value = indoor_row

        def session_get_side_effect(model, entity_id):
            if model.__name__ == "EntityBase":
                return entity_base if entity_id == "outdoor_temple_001" else None
            if model.__name__ == "Poi":
                return poi_mock if entity_id == "outdoor_temple_001" else None
            return None

        session.get = AsyncMock(side_effect=session_get_side_effect)
        session.execute = AsyncMock(return_value=indoor_result)

        plan_b = await build_plan_b_for_day(session, [outdoor_slot], "kyoto", "mid")
        weather_options = [pb for pb in plan_b if "rain" in pb["trigger"].lower() or "下雨" in pb["trigger"]]
        assert len(weather_options) >= 1, "Should generate weather replacement for outdoor POI"
        assert "Museum X" in weather_options[0]["alternative"] or "indoor_museum_001" in str(weather_options[0]["entity_ids"])

    @pytest.mark.asyncio
    async def test_booking_failure_generates_walkin_alternative(self):
        build_plan_b_for_day, *_ = _import_plan_b_builder()
        from app.domains.planning.report_schema import DaySlot

        booking_slot = DaySlot(
            slot_index=0,
            kind="poi",
            entity_id="booking_required_001",
            title="Popular Restaurant",
            area="gion",
            start_time_hint="12:00",
            duration_mins=60,
        )

        session = AsyncMock()

        entity_base = MagicMock()
        entity_base.entity_id = "booking_required_001"
        entity_base.entity_type = "restaurant"
        entity_base.city_code = "kyoto"
        entity_base.area_name = "gion"
        entity_base.risk_flags = ["requires_reservation"]
        entity_base.booking_method = "online_advance"

        poi_mock = None  # restaurant type, no poi

        walkin_result = MagicMock()
        walkin_row = {"entity_id": "walkin_rest_001", "name_zh": "Walk-in Spot", "area_name": "gion"}
        walkin_result.mappings.return_value.first.return_value = walkin_row

        def session_get_side_effect(model, entity_id):
            if model.__name__ == "EntityBase":
                return entity_base if entity_id == "booking_required_001" else None
            if model.__name__ == "Poi":
                return None
            return None

        session.get = AsyncMock(side_effect=session_get_side_effect)
        session.execute = AsyncMock(return_value=walkin_result)

        plan_b = await build_plan_b_for_day(session, [booking_slot], "kyoto", "mid")
        booking_options = [pb for pb in plan_b if "预约" in pb["trigger"] or "booking" in pb["trigger"].lower()]
        assert len(booking_options) >= 1, "Should generate booking failure alternative"

    def test_weather_sensitivity_detection(self):
        _, _, _, _is_weather_sensitive, _ = _import_plan_b_builder()
        ent = MagicMock()
        ent.risk_flags = ["weather_sensitive"]
        assert _is_weather_sensitive(ent, None) is True

        ent2 = MagicMock()
        ent2.risk_flags = []
        assert _is_weather_sensitive(ent2, None) is False

    def test_needs_booking_detection(self):
        _, _, _, _, _needs_booking = _import_plan_b_builder()
        ent = MagicMock()
        ent.booking_method = "online_advance"
        ent.risk_flags = []
        poi = MagicMock()
        poi.requires_advance_booking = False
        assert _needs_booking(ent, poi) is True

        ent2 = MagicMock()
        ent2.booking_method = "walk_in"
        ent2.risk_flags = []
        poi2 = MagicMock()
        poi2.requires_advance_booking = False
        assert _needs_booking(ent2, poi2) is False


# ===========================================================================
# (h) Rate limiter test
# ===========================================================================

class TestRateLimiter:
    """Test the in-memory sliding window rate limiter."""

    @pytest.mark.asyncio
    async def test_allows_within_limit(self):
        InMemoryBackend, _, _, _ = _import_rate_limiter()
        backend = InMemoryBackend(cleanup_interval=3600)

        for i in range(5):
            allowed, remaining, limit, reset = await backend.hit("test_key", 60, 5)
            assert allowed is True, f"Request {i + 1} should be allowed"
            assert remaining == 5 - (i + 1)

        await backend.close()

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self):
        InMemoryBackend, _, _, _ = _import_rate_limiter()
        backend = InMemoryBackend(cleanup_interval=3600)

        # Fill up the limit
        for _ in range(5):
            await backend.hit("test_key", 60, 5)

        # 6th request should be blocked
        allowed, remaining, limit, reset = await backend.hit("test_key", 60, 5)
        assert allowed is False, "Request beyond limit should be blocked"
        assert remaining == 0
        assert limit == 5

        await backend.close()

    @pytest.mark.asyncio
    async def test_different_keys_independent(self):
        InMemoryBackend, _, _, _ = _import_rate_limiter()
        backend = InMemoryBackend(cleanup_interval=3600)

        # Fill up key1
        for _ in range(3):
            await backend.hit("key1", 60, 3)

        # key1 should be blocked
        allowed1, _, _, _ = await backend.hit("key1", 60, 3)
        assert allowed1 is False

        # key2 should still be allowed
        allowed2, _, _, _ = await backend.hit("key2", 60, 3)
        assert allowed2 is True

        await backend.close()

    @pytest.mark.asyncio
    async def test_headers_returned(self):
        InMemoryBackend, _, _, _ = _import_rate_limiter()
        backend = InMemoryBackend(cleanup_interval=3600)

        allowed, remaining, limit, reset_after = await backend.hit("hdr_key", 60, 10)
        assert limit == 10
        assert remaining == 9
        assert isinstance(reset_after, int)
        assert reset_after >= 0

        await backend.close()

    @pytest.mark.asyncio
    async def test_429_returned_on_blocked(self):
        """Simulates what middleware does: returns 429 when blocked."""
        InMemoryBackend, _, _, _ = _import_rate_limiter()
        backend = InMemoryBackend(cleanup_interval=3600)

        # Exhaust limit
        for _ in range(2):
            await backend.hit("key_429", 60, 2)

        allowed, remaining, limit, reset_after = await backend.hit("key_429", 60, 2)
        assert allowed is False
        # Middleware would return 429 with these headers
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_after),
        }
        assert headers["X-RateLimit-Remaining"] == "0"
        assert int(headers["X-RateLimit-Reset"]) > 0

        await backend.close()

    def test_path_classification(self):
        _, classify_path, _, _ = _import_rate_limiter()

        group, window, max_req = classify_path("/trips/123/generate")
        assert group == "generate"
        assert max_req == 5

        group, window, max_req = classify_path("/submissions")
        assert group == "form"
        assert max_req == 30

        group, window, max_req = classify_path("/api/v1/plans")
        assert group == "general"
        assert max_req == 60


# ===========================================================================
# (i) Rotation penalty test
# ===========================================================================

class TestRotationPenalty:
    """Verify score penalties applied correctly per tier."""

    def test_zero_count_no_penalty(self):
        compute_rotation_penalty, _, _, _ = _import_rotation()
        assert compute_rotation_penalty(0) == 0.0

    def test_low_count_small_penalty(self):
        compute_rotation_penalty, _, _ROTATION_ALPHA, _ = _import_rotation()
        p = compute_rotation_penalty(1)
        expected = _ROTATION_ALPHA * math.log2(2)
        assert abs(p - round(expected, 3)) < 0.001

    def test_high_count_capped_at_max(self):
        compute_rotation_penalty, _, _, _MAX_PENALTY = _import_rotation()
        p = compute_rotation_penalty(1000)
        assert p == _MAX_PENALTY, f"Penalty should be capped at {_MAX_PENALTY}, got {p}"

    def test_penalty_increases_monotonically(self):
        compute_rotation_penalty, _, _, _ = _import_rotation()
        prev = 0.0
        for count in [1, 2, 5, 10, 20, 50]:
            p = compute_rotation_penalty(count)
            assert p >= prev, f"Penalty should increase monotonically: count={count}, p={p}, prev={prev}"
            prev = p

    def test_apply_rotation_penalty_tiers(self):
        _, apply_rotation_penalty, _, _ = _import_rotation()

        base = 100.0

        # 0-5: no penalty
        assert apply_rotation_penalty(base, 0) == base
        assert apply_rotation_penalty(base, 5) == base

        # 6-10: -5%
        assert apply_rotation_penalty(base, 6) == round(base * 0.95, 2)
        assert apply_rotation_penalty(base, 10) == round(base * 0.95, 2)

        # 11-20: -10%
        assert apply_rotation_penalty(base, 11) == round(base * 0.90, 2)
        assert apply_rotation_penalty(base, 20) == round(base * 0.90, 2)

        # 21+: -15%
        assert apply_rotation_penalty(base, 21) == round(base * 0.85, 2)
        assert apply_rotation_penalty(base, 100) == round(base * 0.85, 2)

    def test_negative_count_safe(self):
        compute_rotation_penalty, _, _, _ = _import_rotation()
        assert compute_rotation_penalty(-1) == 0.0
        assert compute_rotation_penalty(-100) == 0.0

    def test_known_penalty_values(self):
        """Verify documented penalty examples from the module docstring."""
        compute_rotation_penalty, _, _ROTATION_ALPHA, _MAX_PENALTY = _import_rotation()

        # count=5 -> ~0.38 (alpha=0.30, log2(6)~2.585)
        p5 = compute_rotation_penalty(5)
        expected_5 = min(_MAX_PENALTY, round(_ROTATION_ALPHA * math.log2(6), 3))
        assert p5 == expected_5

        # count=20 -> ~0.69
        p20 = compute_rotation_penalty(20)
        expected_20 = min(_MAX_PENALTY, round(_ROTATION_ALPHA * math.log2(21), 3))
        assert p20 == expected_20


# ===========================================================================
# (i) Knowledge pack tests
# ===========================================================================

class TestKnowledgePack:
    """Verify Kansai knowledge pack structure and content."""

    def test_kansai_knowledge_has_required_sections(self):
        from app.domains.planning.circle_knowledge.kansai import get_kansai_knowledge
        k = get_kansai_knowledge()
        assert k["circle_id"] == "kansai_classic"
        sections = k["sections"]
        required = {"airport_transport", "ic_card", "communication", "luggage", "payment", "emergency"}
        for key in required:
            assert key in sections, f"Missing section: {key}"
            sec = sections[key]
            assert sec.get("title"), f"Section {key} missing title"
            assert sec.get("items"), f"Section {key} has no items"

    def test_get_circle_knowledge_returns_kansai(self):
        from app.domains.planning.circle_knowledge import get_circle_knowledge
        k = get_circle_knowledge("kansai_classic")
        assert k is not None
        assert k["circle_id"] == "kansai_classic"

    def test_get_circle_knowledge_alias(self):
        from app.domains.planning.circle_knowledge import get_circle_knowledge
        assert get_circle_knowledge("kansai") is not None

    def test_get_circle_knowledge_unknown_returns_none(self):
        from app.domains.planning.circle_knowledge import get_circle_knowledge
        assert get_circle_knowledge("unknown_circle_xyz") is None

    def test_kansai_ic_card_section_has_tips(self):
        from app.domains.planning.circle_knowledge.kansai import get_kansai_knowledge
        k = get_kansai_knowledge()
        ic = k["sections"]["ic_card"]
        assert len(ic.get("tips", [])) >= 1, "ic_card section should have at least 1 tip"

    def test_kansai_emergency_section_has_numbers(self):
        from app.domains.planning.circle_knowledge.kansai import get_kansai_knowledge
        k = get_kansai_knowledge()
        em = k["sections"]["emergency"]
        items_text = " ".join(em.get("items", []))
        # 急救 119 和报警 110 应该在紧急联系里
        assert "119" in items_text
        assert "110" in items_text


# ===========================================================================
# (j) DIY HTML rendering tests
# ===========================================================================

class TestDiyHtmlRendering:
    """Verify DIY zone CSS and HTML rendering in html_renderer."""

    def test_diy_css_injected_in_html_output(self):
        from app.domains.rendering.magazine.html_renderer import _DIY_CSS
        assert "diy-sticker-zone" in _DIY_CSS
        assert "diy-freewrite-zone" in _DIY_CSS
        assert "dashed" in _DIY_CSS

    def test_render_diy_zones_sticker_only(self):
        from app.domains.rendering.magazine.html_renderer import _render_diy_zones
        page = {"sticker_zone": "top_right", "freewrite_zone": None}
        html = _render_diy_zones(page)
        assert "diy-sticker-zone" in html
        assert "top-right" in html
        assert "diy-freewrite-zone" not in html

    def test_render_diy_zones_freewrite_only(self):
        from app.domains.rendering.magazine.html_renderer import _render_diy_zones
        page = {"sticker_zone": None, "freewrite_zone": "bottom_strip"}
        html = _render_diy_zones(page)
        assert "diy-freewrite-zone" in html
        assert "bottom-strip" in html
        assert "diy-sticker-zone" not in html

    def test_render_diy_zones_both(self):
        from app.domains.rendering.magazine.html_renderer import _render_diy_zones
        page = {"sticker_zone": "corner", "freewrite_zone": "full_half"}
        html = _render_diy_zones(page)
        assert "diy-sticker-zone" in html
        assert "diy-freewrite-zone" in html
        assert "corner" in html
        assert "full-half" in html

    def test_render_diy_zones_none_values(self):
        from app.domains.rendering.magazine.html_renderer import _render_diy_zones
        assert _render_diy_zones({}) == ""
        assert _render_diy_zones({"sticker_zone": None, "freewrite_zone": None}) == ""
        assert _render_diy_zones({"sticker_zone": "none", "freewrite_zone": "none"}) == ""

    def test_render_page_has_diy_class_when_zones_present(self):
        from app.domains.rendering.magazine.html_renderer import _render_page
        page = {
            "title": "Day 1", "subtitle": "", "summary": "",
            "hero_url": "", "hero_fallback": "placeholder", "hero_source": "none",
            "asset_slots": [],
            "sticker_zone": "top_right",
            "freewrite_zone": "bottom_strip",
        }
        html = _render_page(page)
        assert "has-diy" in html
        assert "diy-sticker-zone" in html
        assert "diy-freewrite-zone" in html

    def test_render_page_no_diy_class_without_zones(self):
        from app.domains.rendering.magazine.html_renderer import _render_page
        page = {
            "title": "Day 1", "subtitle": "", "summary": "",
            "hero_url": "", "hero_fallback": "placeholder", "hero_source": "none",
            "asset_slots": [],
            "sticker_zone": None,
            "freewrite_zone": None,
        }
        html = _render_page(page)
        assert "has-diy" not in html


# ===========================================================================
# (k) BookingAlert deadline_hint format tests
# ===========================================================================

class TestBookingAlertFormat:
    """Verify BookingAlertItem is correctly constructed from entity schema fields."""

    def test_booking_alert_item_fields(self):
        from app.domains.planning.report_schema import BookingAlertItem
        alert = BookingAlertItem(
            entity_id="test-uuid",
            label="伏见稻荷大社",
            booking_level="must_book",
            deadline_hint="建议出发前 14 天预约",
            impact_if_missed="可能无法入场或排队时间超长",
            fallback_label="https://example.com",
        )
        assert alert.booking_level == "must_book"
        assert "14" in alert.deadline_hint
        assert alert.fallback_label is not None

    def test_booking_level_valid_values(self):
        from app.domains.planning.report_schema import BookingAlertItem
        for level in ("must_book", "should_book", "good_to_book", "walkin_ok"):
            a = BookingAlertItem(label="test", booking_level=level)
            assert a.booking_level == level

    def test_booking_alert_default_level(self):
        from app.domains.planning.report_schema import BookingAlertItem
        a = BookingAlertItem(label="test")
        assert a.booking_level == "good_to_book"

    def test_planning_output_booking_alerts_from_helper(self):
        """BookingAlertItem from the test helper should have correct fields."""
        po = _build_test_planning_output(total_days=1)
        # Test helper creates booking_required=True for day 1
        assert len(po.booking_alerts) >= 1
        alert = po.booking_alerts[0]
        assert alert.label
        assert alert.booking_level in ("must_book", "should_book", "good_to_book", "walkin_ok")
        assert isinstance(alert.deadline_hint, str)


# ===========================================================================
# (l) Quality gate empty-days regression
# ===========================================================================

class TestQualityGateEmptyPlan:
    """Verify the empty-days fix prevents false positives."""

    def test_empty_days_fails(self):
        run_quality_gate_sync, _, _ = _import_quality_gate()
        result = run_quality_gate_sync({"days": []})
        assert result.passed is False, "Empty days should fail quality gate"
        assert result.score < 1.0

    def test_none_days_fails(self):
        run_quality_gate_sync, _, _ = _import_quality_gate()
        result = run_quality_gate_sync({})
        assert result.passed is False

    def test_single_day_with_spots_passes_qty01(self):
        from app.core.quality_gate import check_qty_01
        plan = {
            "days": [{
                "day_number": 1,
                "items": [
                    {"item_type": "poi"} for _ in range(4)
                ],
            }]
        }
        result = check_qty_01(plan)
        assert result.passed is True
