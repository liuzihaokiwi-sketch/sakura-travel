"""
planning_v2 module for trip itinerary planning.

Provides data models and workflow orchestration for the v2 planning system,
which handles user constraints, feasibility checking, and day-by-day
itinerary generation.
"""

from .models import (
    TimeWindow,
    UserConstraints,
    RegionSummary,
    CandidatePool,
    DailyConstraints,
    FeasibilityResult,
    GenerationStep,
    EntityType,
    Grade,
)
from .step04_poi_pool import build_poi_pool
from .step06_hotel_pool import build_hotel_pool

__all__ = [
    "TimeWindow",
    "UserConstraints",
    "RegionSummary",
    "CandidatePool",
    "DailyConstraints",
    "FeasibilityResult",
    "GenerationStep",
    "EntityType",
    "Grade",
    "build_poi_pool",
    "build_hotel_pool",
]
