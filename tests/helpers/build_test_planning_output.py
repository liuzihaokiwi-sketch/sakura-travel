"""Test helper: build a PlanningOutput from inline test data."""
from __future__ import annotations

from app.domains.rendering.planning_output import PlanningOutput
from app.domains.planning.report_schema import (
    BookingAlertItem,
    ConditionalSection,
    DayRisk,
    DaySection,
    DaySlot,
    DesignBrief,
    EmotionalGoal,
    ExecutionNotes,
    OverviewSection,
    PreferenceFulfillmentItem,
    ProfileSummary,
    ReportMeta,
    RiskWatchItem,
    RouteSummaryCard,
    SelectedCircleInfo,
)


def build_test_planning_output(
    total_days: int = 1,
    destination: str = "kansai",
    trip_id: str = "plan-1",
) -> PlanningOutput:
    """Build a minimal PlanningOutput for testing page pipeline."""
    days = []
    emotional_goals = []
    conditionals = []
    booking_alerts = []
    risk_watch = []
    route_summary = []

    for d in range(1, total_days + 1):
        day_type = "arrival" if d == 1 else ("departure" if d == total_days and total_days > 1 else "normal")
        intensity = "balanced"

        slots = [
            DaySlot(
                slot_index=0,
                kind="poi",
                entity_id=f"ent_{d}_001",
                title=f"Attraction Day {d}",
                area="higashiyama",
                start_time_hint="09:00",
                duration_mins=90,
                booking_required=(d == 1),
            ),
        ]

        risks = []
        if d == 1:
            risks.append(DayRisk(risk_type="booking", description="Reservation recommended", mitigation="Book online"))

        trigger_tags = []
        if day_type == "arrival":
            trigger_tags.append("arrival")

        days.append(DaySection(
            day_index=d,
            title=f"Day {d} Theme",
            primary_area="higashiyama",
            day_goal="Explore the area",
            intensity=intensity,
            start_anchor="Station",
            end_anchor="Hotel",
            must_keep=f"Attraction Day {d}",
            first_cut="Optional walk",
            route_integrity_score=0.88,
            risks=risks,
            slots=slots,
            reasoning=["Arrival day keeps low transfer cost"],
            execution_notes=ExecutionNotes(weather_plan="Switch to museum", energy_plan="Skip night walk"),
            trigger_tags=trigger_tags,
        ))

        emotional_goals.append(EmotionalGoal(
            day_index=d,
            mood_keyword="explore",
            mood_sentence="Easy exploration day.",
        ))

        route_summary.append(RouteSummaryCard(
            day_index=d, title=f"Day {d} Theme",
            primary_area="higashiyama", intensity=intensity,
        ))

        conditionals.append(ConditionalSection(
            section_type="extra",
            trigger_reason=f"Day {d} poi",
            related_day_indexes=[d],
            payload={
                "entity_id": f"ent_{d}_001",
                "name": f"Attraction Day {d}",
                "entity_type": "poi",
                "day_index": d,
                "data_tier": "S",
                "area": "higashiyama",
            },
        ))

    if any(s.booking_required for day in days for s in day.slots):
        booking_alerts.append(BookingAlertItem(
            label="Reservation required",
            booking_level="should_book",
            deadline_hint="7 days before",
            impact_if_missed="queue risk",
        ))
        risk_watch.append(RiskWatchItem(
            risk_type="booking",
            description="Reservation recommended",
            day_index=1,
        ))

    return PlanningOutput(
        meta=ReportMeta(
            trip_id=trip_id,
            destination=destination,
            total_days=total_days,
        ),
        profile_summary=ProfileSummary(
            party_type="couple",
            pace_preference="balanced",
            budget_bias="mid",
        ),
        design_brief=DesignBrief(
            route_strategy=[f"City circle: {destination}"],
            hotel_base=None,
        ),
        overview=OverviewSection(route_summary=route_summary),
        days=days,
        booking_alerts=booking_alerts,
        prep_notes={"title": "Departure checklist", "items": ["Passport", "eSIM"]},
        conditional_sections=conditionals,
        emotional_goals=emotional_goals,
        risk_watch_items=risk_watch,
        selection_evidence=[
            {
                "entity_id": f"ent_{d}_001",
                "name": f"Attraction Day {d}",
                "hero_image_url": None,
                "why_selected": "Top rated",
            }
            for d in range(1, total_days + 1)
        ],
        circles=[SelectedCircleInfo(circle_id="kansai_classic_circle", name_zh="关西经典")],
        day_circle_map={d: "kansai_classic_circle" for d in range(1, total_days + 1)},
    )
