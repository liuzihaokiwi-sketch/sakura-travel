"""
planning_v2 module for trip itinerary planning.

Provides data models and workflow orchestration for the v2 planning system,
which handles user constraints, feasibility checking, and day-by-day
itinerary generation.
"""

from .models import (
    CandidatePool,
    CircleProfile,
    DailyConstraints,
    EntityType,
    FeasibilityResult,
    GenerationStep,
    Grade,
    RegionSummary,
    TimeWindow,
    UserConstraints,
)
from .orchestrator import run_planning_v2
from .step01_constraints import resolve_user_constraints
from .step02_region_summary import build_region_summary
from .step03_city_planner import plan_city_combination
from .step04_poi_pool import build_poi_pool
from .step05_5_validator import validate_and_substitute
from .step05_activity_planner import plan_daily_activities
from .step06_hotel_pool import build_hotel_pool
from .step07_hotel_planner import select_hotels
from .step08_daily_constraints import build_daily_constraints_list
from .step09_sequence_planner import plan_daily_sequences
from .step10_feasibility import check_feasibility
from .step11_conflict_resolver import resolve_conflicts
from .step12_timeline_builder import build_timeline
from .step13_5_meal_planner import select_meals
from .step15_plan_b import build_plan_b
from .step16_handbook import generate_handbook_content

__all__ = [
    "CircleProfile",
    "TimeWindow",
    "UserConstraints",
    "RegionSummary",
    "CandidatePool",
    "DailyConstraints",
    "FeasibilityResult",
    "GenerationStep",
    "EntityType",
    "Grade",
    "resolve_user_constraints",
    "build_region_summary",
    "plan_city_combination",
    "build_poi_pool",
    "plan_daily_activities",
    "validate_and_substitute",
    "build_hotel_pool",
    "select_hotels",
    "build_daily_constraints_list",
    "plan_daily_sequences",
    "check_feasibility",
    "resolve_conflicts",
    "build_timeline",
    "select_meals",
    "build_plan_b",
    "generate_handbook_content",
    "run_planning_v2",
]
