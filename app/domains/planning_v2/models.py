"""
Data models for planning_v2 module.

Defines core dataclasses for trip planning workflow, including time windows,
user constraints, region summaries, candidate pools, daily constraints,
feasibility checks, and generation steps.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime


@dataclass
class TimeWindow:
    """Represents a time window with start, end, and duration.

    Attributes:
        start: Start time in HH:MM format
        end: End time in HH:MM format
        duration_mins: Duration in minutes
    """
    start: str
    end: str
    duration_mins: int


@dataclass
class UserConstraints:
    """User constraints for trip planning.

    Encapsulates trip window, user profile, and various constraints
    including must-visit items, do-not-go locations, and visited items.

    Attributes:
        trip_window: Dict with keys {start_date, end_date, total_days}
        user_profile: Dict with keys {party_type, budget_tier, must_have_tags, nice_to_have_tags}
        constraints: Dict with keys {must_visit, do_not_go, visited, booked_items}
    """
    trip_window: dict
    user_profile: dict
    constraints: dict


@dataclass
class RegionSummary:
    """Summary statistics for a geographic region/circle.

    Provides overview of available entities and their distribution
    across types and quality grades.

    Attributes:
        circle_name: Name of the city circle (e.g., "Kanto", "Kansai")
        cities: List of city names in this region
        entity_count: Total number of entities
        entities_by_type: Dict mapping entity type to count {poi, restaurant, hotel, ...}
        grade_distribution: Dict mapping grade letter to count {S, A, B, C, ...}
    """
    circle_name: str
    cities: list
    entity_count: int
    entities_by_type: dict
    grade_distribution: dict


@dataclass
class CandidatePool:
    """Represents a single candidate entity for itinerary planning.

    Contains all metadata needed for feasibility checking and scheduling
    including location, tags, time requirements, costs, and review signals.

    Attributes:
        entity_id: Unique identifier for the entity
        name_zh: Chinese name of the entity
        entity_type: Type of entity (poi, restaurant, hotel, event, etc.)
        grade: Quality grade (S/A/B/C)
        latitude: Geographic latitude
        longitude: Geographic longitude
        tags: List of semantic tags (e.g., "outdoor", "cultural", "seasonal")
        visit_minutes: Recommended visit duration in minutes
        cost_jpy: Estimated cost in Japanese Yen
        open_hours: Dict with keys {open_days, open_hours, closed_notes}
        review_signals: Dict with review metadata and sentiment signals
    """
    entity_id: str
    name_zh: str
    entity_type: str
    grade: str
    latitude: float
    longitude: float
    tags: list
    visit_minutes: int
    cost_jpy: int
    open_hours: dict
    review_signals: dict


@dataclass
class DailyConstraints:
    """Constraints and context for a single day in the itinerary.

    Captures day-specific information including weather, operating hours,
    closed entities, transportation limitations, and anchorpoints.

    Attributes:
        date: Date in YYYY-MM-DD format
        day_of_week: Day name (Mon, Tue, Wed, Thu, Fri, Sat, Sun)
        sunrise: Sunrise time in HH:MM format
        sunset: Sunset time in HH:MM format
        closed_entities: List of entity_ids that are closed on this day
        low_freq_transits: List of dicts describing low-frequency transit options
        anchors: List of dicts for fixed timepoint items (flights, booked reservations)
        hotel_breakfast_included: Whether hotel breakfast is included
        hotel_dinner_included: Whether hotel dinner is included
    """
    date: str
    day_of_week: str
    sunrise: str
    sunset: str
    closed_entities: list = field(default_factory=list)
    low_freq_transits: list = field(default_factory=list)
    anchors: list = field(default_factory=list)
    hotel_breakfast_included: bool = False
    hotel_dinner_included: bool = False


@dataclass
class FeasibilityResult:
    """Result of feasibility checking for a proposed itinerary segment.

    Contains pass/fail status along with violations and recommendations.

    Attributes:
        status: Overall status (pass, fail, warning)
        violations: List of dicts describing constraint violations
        suggestions: List of suggestions to resolve violations
    """
    status: str
    violations: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)


@dataclass
class GenerationStep:
    """Tracks a single step in the itinerary generation pipeline.

    Records execution metadata including input hash, output, errors,
    and token usage for monitoring and debugging.

    Attributes:
        step_id: Step identifier (01, 02, 03, etc.)
        status: Execution status (running, success, failed)
        input_hash: Hash of input data for caching/deduplication
        output: Step output data
        error: Error message if status is failed
        thinking_tokens: Number of tokens used for extended thinking
    """
    step_id: str
    status: str
    input_hash: str
    output: dict
    error: Optional[str] = None
    thinking_tokens: int = 0


# Type aliases for common patterns
EntityType = str  # poi, restaurant, hotel, event, etc.
Grade = str       # S, A, B, C, etc.
