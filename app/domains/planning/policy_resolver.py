from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.db.models.city_circles import CityCircle
from app.domains.planning.config_resolver import ResolvedConfig


@dataclass
class CityCircleProfilePolicy:
    circle_family: str = "generic"
    region_family: str = "generic"
    destination_mode: str = "multi_city_circle"
    selection_bias: float = 0.0
    explain_tags: list[str] = field(default_factory=list)


@dataclass
class MobilityPolicy:
    primary_mode: str = "public_transit"
    intra_city_mode: str = "walk_transit"
    cross_city_tolerance: str = "medium"
    max_transfer_minutes_per_day: int = 90
    airport_access_style: str = "balanced"
    last_night_airport_buffer_minutes: int = 90


@dataclass
class ClimateAndSeasonPolicy:
    climate_family: str = "temperate"
    seasonality_mode: str = "balanced"
    high_risk_months: list[int] = field(default_factory=list)
    pace_cap_adjustment: int = 0
    season_fit_bias: float = 0.0
    explain_risks: list[str] = field(default_factory=list)


@dataclass
class RoutingStylePolicy:
    routing_mode: str = "hub_and_spoke"
    prefer_single_base: bool = False
    max_cross_city_days: int = 3
    max_majors_per_day: int = 1
    daytrip_bias: str = "balanced"
    backtrack_penalty_bias: float = 0.0


@dataclass
class HotelBasePolicy:
    base_pattern_bias: str = "balanced"
    prefer_last_night_near_hub: bool = False
    last_night_hub_max_minutes: int = 90
    long_segment_base_preference: str = "balanced"
    route_node_bias_weight: float = 0.0


@dataclass
class DayFramePolicy:
    arrival_capacity_ratio: float = 1.0
    normal_capacity_ratio: float = 1.0
    departure_capacity_ratio: float = 1.0
    transit_budget_multiplier: float = 1.0
    transit_buffer_minutes: int = 0
    low_density_mode: bool = False
    driving_day_slack_minutes: int = 0


@dataclass
class BookingAndReservationPolicy:
    high_pressure_constraint: str = "soft"
    unbooked_major_action: str = "degrade_only"
    hold_back_edge_days: bool = True
    trace_level: str = "minimal"


@dataclass
class ResolvedPolicySet:
    circle_id: str
    city_circle_profile: CityCircleProfilePolicy = field(default_factory=CityCircleProfilePolicy)
    mobility_policy: MobilityPolicy = field(default_factory=MobilityPolicy)
    climate_and_season_policy: ClimateAndSeasonPolicy = field(default_factory=ClimateAndSeasonPolicy)
    routing_style_policy: RoutingStylePolicy = field(default_factory=RoutingStylePolicy)
    hotel_base_policy: HotelBasePolicy = field(default_factory=HotelBasePolicy)
    day_frame_policy: DayFramePolicy = field(default_factory=DayFramePolicy)
    booking_and_reservation_policy: BookingAndReservationPolicy = field(default_factory=BookingAndReservationPolicy)
    config_snapshot: dict[str, Any] = field(default_factory=dict)
    sources: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "circle_id": self.circle_id,
            "city_circle_profile": asdict(self.city_circle_profile),
            "mobility_policy": asdict(self.mobility_policy),
            "climate_and_season_policy": asdict(self.climate_and_season_policy),
            "routing_style_policy": asdict(self.routing_style_policy),
            "hotel_base_policy": asdict(self.hotel_base_policy),
            "day_frame_policy": asdict(self.day_frame_policy),
            "booking_and_reservation_policy": asdict(self.booking_and_reservation_policy),
            "config_snapshot": self.config_snapshot,
            "sources": self.sources,
        }

    def source_summary(self) -> list[str]:
        lines: list[str] = []
        for source in self.sources:
            module = source.get("module") or "policy"
            origin = source.get("origin") or "unknown"
            detail = source.get("detail") or ""
            if detail:
                lines.append(f"{module}: {origin} ({detail})")
            else:
                lines.append(f"{module}: {origin}")
        return lines


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


_DEFAULT_BUNDLE: dict[str, Any] = {
    "city_circle_profile": {
        "circle_family": "generic",
        "region_family": "generic",
        "destination_mode": "multi_city_circle",
        "selection_bias": 0.0,
        "explain_tags": ["generic"],
    },
    "mobility_policy": {
        "primary_mode": "public_transit",
        "intra_city_mode": "walk_transit",
        "cross_city_tolerance": "medium",
        "max_transfer_minutes_per_day": 90,
        "airport_access_style": "balanced",
        "last_night_airport_buffer_minutes": 90,
    },
    "climate_and_season_policy": {
        "climate_family": "temperate",
        "seasonality_mode": "balanced",
        "high_risk_months": [],
        "pace_cap_adjustment": 0,
        "season_fit_bias": 0.0,
        "explain_risks": [],
    },
    "routing_style_policy": {
        "routing_mode": "hub_and_spoke",
        "prefer_single_base": False,
        "max_cross_city_days": 3,
        "max_majors_per_day": 1,
        "daytrip_bias": "balanced",
        "backtrack_penalty_bias": 0.0,
    },
    "hotel_base_policy": {
        "base_pattern_bias": "balanced",
        "prefer_last_night_near_hub": False,
        "last_night_hub_max_minutes": 90,
        "long_segment_base_preference": "balanced",
        "route_node_bias_weight": 0.0,
    },
    "day_frame_policy": {
        "arrival_capacity_ratio": 1.0,
        "normal_capacity_ratio": 1.0,
        "departure_capacity_ratio": 1.0,
        "transit_budget_multiplier": 1.0,
        "transit_buffer_minutes": 0,
        "low_density_mode": False,
        "driving_day_slack_minutes": 0,
    },
    "booking_and_reservation_policy": {
        "high_pressure_constraint": "soft",
        "unbooked_major_action": "degrade_only",
        "hold_back_edge_days": True,
        "trace_level": "minimal",
    },
}


_POLICY_OVERRIDES: dict[str, dict[str, Any]] = {
    "kansai_classic_circle": {
        "city_circle_profile": {
            "circle_family": "kansai",
            "region_family": "japan",
            "selection_bias": 0.06,
            "explain_tags": ["multi_base_friendly", "culture_food"],
        },
        "mobility_policy": {
            "primary_mode": "public_transit",
            "cross_city_tolerance": "medium_high",
            "max_transfer_minutes_per_day": 100,
        },
        "routing_style_policy": {
            "routing_mode": "multi_base_urban",
            "prefer_single_base": False,
            "max_cross_city_days": 4,
            "daytrip_bias": "high",
        },
        "hotel_base_policy": {
            "base_pattern_bias": "double_base",
            "prefer_last_night_near_hub": False,
            "long_segment_base_preference": "balanced",
            "route_node_bias_weight": 0.08,
        },
        "day_frame_policy": {
            "arrival_capacity_ratio": 0.8,
            "normal_capacity_ratio": 1.0,
            "departure_capacity_ratio": 0.75,
            "transit_budget_multiplier": 1.0,
            "transit_buffer_minutes": 10,
            "low_density_mode": False,
            "driving_day_slack_minutes": 0,
        },
        "booking_and_reservation_policy": {
            "high_pressure_constraint": "soft",
            "unbooked_major_action": "degrade_only",
            "hold_back_edge_days": True,
            "trace_level": "minimal",
        },
    },
    "tokyo_metropolitan_circle": {
        "city_circle_profile": {
            "circle_family": "kanto",
            "region_family": "japan",
            "selection_bias": 0.05,
            "explain_tags": ["urban_transit_dense"],
        },
        "mobility_policy": {
            "primary_mode": "public_transit",
            "intra_city_mode": "walk_transit",
            "cross_city_tolerance": "medium",
            "max_transfer_minutes_per_day": 110,
        },
        "routing_style_policy": {
            "routing_mode": "single_core_with_daytrips",
            "prefer_single_base": True,
            "max_cross_city_days": 2,
            "daytrip_bias": "medium",
            "backtrack_penalty_bias": 0.08,
        },
        "hotel_base_policy": {
            "base_pattern_bias": "single_base",
            "prefer_last_night_near_hub": False,
            "long_segment_base_preference": "urban_core",
            "route_node_bias_weight": 0.02,
        },
        "day_frame_policy": {
            "arrival_capacity_ratio": 0.85,
            "normal_capacity_ratio": 1.05,
            "departure_capacity_ratio": 0.8,
            "transit_budget_multiplier": 0.95,
            "transit_buffer_minutes": 0,
            "low_density_mode": False,
            "driving_day_slack_minutes": 0,
        },
    },
    "kanto_city_circle": {
        "city_circle_profile": {
            "circle_family": "kanto",
            "region_family": "japan",
            "selection_bias": 0.05,
            "explain_tags": ["urban_transit_dense"],
        },
        "mobility_policy": {
            "primary_mode": "public_transit",
            "intra_city_mode": "walk_transit",
            "cross_city_tolerance": "medium",
            "max_transfer_minutes_per_day": 110,
        },
        "routing_style_policy": {
            "routing_mode": "single_core_with_daytrips",
            "prefer_single_base": True,
            "max_cross_city_days": 2,
            "daytrip_bias": "medium",
            "backtrack_penalty_bias": 0.08,
        },
        "hotel_base_policy": {
            "base_pattern_bias": "single_base",
            "prefer_last_night_near_hub": False,
            "long_segment_base_preference": "urban_core",
            "route_node_bias_weight": 0.02,
        },
        "day_frame_policy": {
            "arrival_capacity_ratio": 0.85,
            "normal_capacity_ratio": 1.05,
            "departure_capacity_ratio": 0.8,
            "transit_budget_multiplier": 0.95,
            "transit_buffer_minutes": 0,
            "low_density_mode": False,
            "driving_day_slack_minutes": 0,
        },
    },
    "hokkaido_nature_circle": {
        "city_circle_profile": {
            "circle_family": "hokkaido",
            "region_family": "japan",
            "selection_bias": 0.03,
            "explain_tags": ["season_sensitive", "low_density"],
        },
        "mobility_policy": {
            "primary_mode": "self_drive_or_limited_transit",
            "intra_city_mode": "mixed",
            "cross_city_tolerance": "low",
            "max_transfer_minutes_per_day": 140,
            "airport_access_style": "airport_buffer_first",
            "last_night_airport_buffer_minutes": 120,
        },
        "climate_and_season_policy": {
            "climate_family": "snow",
            "seasonality_mode": "winter_sensitive",
            "high_risk_months": [12, 1, 2],
            "pace_cap_adjustment": -1,
            "season_fit_bias": 0.08,
            "explain_risks": ["snow", "road_closure", "short_daylight"],
        },
        "routing_style_policy": {
            "routing_mode": "low_density_blocks",
            "prefer_single_base": False,
            "max_cross_city_days": 2,
            "max_majors_per_day": 1,
            "daytrip_bias": "low",
            "backtrack_penalty_bias": 0.12,
        },
        "hotel_base_policy": {
            "base_pattern_bias": "multi_base",
            "prefer_last_night_near_hub": True,
            "last_night_hub_max_minutes": 120,
            "long_segment_base_preference": "route_node",
            "route_node_bias_weight": 0.2,
        },
        "day_frame_policy": {
            "arrival_capacity_ratio": 0.7,
            "normal_capacity_ratio": 0.88,
            "departure_capacity_ratio": 0.6,
            "transit_budget_multiplier": 1.3,
            "transit_buffer_minutes": 30,
            "low_density_mode": True,
            "driving_day_slack_minutes": 30,
        },
        "booking_and_reservation_policy": {
            "high_pressure_constraint": "soft",
            "unbooked_major_action": "degrade_only",
            "hold_back_edge_days": True,
            "trace_level": "minimal",
        },
    },
    "hokkaido_city_circle": {
        "city_circle_profile": {
            "circle_family": "hokkaido",
            "region_family": "japan",
            "selection_bias": 0.03,
            "explain_tags": ["season_sensitive", "low_density"],
        },
        "mobility_policy": {
            "primary_mode": "self_drive_or_limited_transit",
            "intra_city_mode": "mixed",
            "cross_city_tolerance": "low",
            "max_transfer_minutes_per_day": 140,
            "airport_access_style": "airport_buffer_first",
            "last_night_airport_buffer_minutes": 120,
        },
        "climate_and_season_policy": {
            "climate_family": "snow",
            "seasonality_mode": "winter_sensitive",
            "high_risk_months": [12, 1, 2],
            "pace_cap_adjustment": -1,
            "season_fit_bias": 0.08,
            "explain_risks": ["snow", "road_closure", "short_daylight"],
        },
        "routing_style_policy": {
            "routing_mode": "low_density_blocks",
            "prefer_single_base": False,
            "max_cross_city_days": 2,
            "max_majors_per_day": 1,
            "daytrip_bias": "low",
            "backtrack_penalty_bias": 0.12,
        },
        "hotel_base_policy": {
            "base_pattern_bias": "multi_base",
            "prefer_last_night_near_hub": True,
            "last_night_hub_max_minutes": 120,
            "long_segment_base_preference": "route_node",
            "route_node_bias_weight": 0.2,
        },
        "day_frame_policy": {
            "arrival_capacity_ratio": 0.7,
            "normal_capacity_ratio": 0.88,
            "departure_capacity_ratio": 0.6,
            "transit_budget_multiplier": 1.3,
            "transit_buffer_minutes": 30,
            "low_density_mode": True,
            "driving_day_slack_minutes": 30,
        },
        "booking_and_reservation_policy": {
            "high_pressure_constraint": "soft",
            "unbooked_major_action": "degrade_only",
            "hold_back_edge_days": True,
            "trace_level": "minimal",
        },
    },
    "south_china_five_city_circle": {
        "city_circle_profile": {
            "circle_family": "south_china",
            "region_family": "china",
            "selection_bias": 0.04,
            "explain_tags": ["metro_mix", "city_cluster"],
        },
        "mobility_policy": {
            "primary_mode": "metro_taxi_mix",
            "intra_city_mode": "metro_taxi_mix",
            "cross_city_tolerance": "medium_high",
            "max_transfer_minutes_per_day": 100,
            "airport_access_style": "multi_gateway",
        },
        "climate_and_season_policy": {
            "climate_family": "humid_subtropical",
            "seasonality_mode": "rainy_season_sensitive",
            "high_risk_months": [5, 6, 7, 8, 9],
            "pace_cap_adjustment": 0,
            "season_fit_bias": 0.02,
            "explain_risks": ["rain", "typhoon"],
        },
        "routing_style_policy": {
            "routing_mode": "metro_cluster_chain",
            "prefer_single_base": False,
            "max_cross_city_days": 4,
            "daytrip_bias": "medium_high",
        },
        "hotel_base_policy": {
            "base_pattern_bias": "double_base",
            "prefer_last_night_near_hub": True,
            "last_night_hub_max_minutes": 100,
            "long_segment_base_preference": "balanced",
            "route_node_bias_weight": 0.08,
        },
        "day_frame_policy": {
            "arrival_capacity_ratio": 0.82,
            "normal_capacity_ratio": 1.0,
            "departure_capacity_ratio": 0.78,
            "transit_budget_multiplier": 1.05,
            "transit_buffer_minutes": 15,
            "low_density_mode": False,
            "driving_day_slack_minutes": 0,
        },
    },
    "guangdong_city_circle": {
        "city_circle_profile": {
            "circle_family": "guangdong",
            "region_family": "china",
            "selection_bias": 0.04,
            "explain_tags": ["metro_mix", "city_cluster"],
        },
        "mobility_policy": {
            "primary_mode": "metro_taxi_mix",
            "intra_city_mode": "metro_taxi_mix",
            "cross_city_tolerance": "medium_high",
            "max_transfer_minutes_per_day": 100,
            "airport_access_style": "multi_gateway",
        },
        "climate_and_season_policy": {
            "climate_family": "humid_subtropical",
            "seasonality_mode": "rainy_season_sensitive",
            "high_risk_months": [5, 6, 7, 8, 9],
            "pace_cap_adjustment": 0,
            "season_fit_bias": 0.02,
            "explain_risks": ["rain", "typhoon"],
        },
        "routing_style_policy": {
            "routing_mode": "metro_cluster_chain",
            "prefer_single_base": False,
            "max_cross_city_days": 4,
            "daytrip_bias": "medium_high",
        },
        "hotel_base_policy": {
            "base_pattern_bias": "double_base",
            "prefer_last_night_near_hub": True,
            "last_night_hub_max_minutes": 100,
            "long_segment_base_preference": "balanced",
            "route_node_bias_weight": 0.08,
        },
        "day_frame_policy": {
            "arrival_capacity_ratio": 0.82,
            "normal_capacity_ratio": 1.0,
            "departure_capacity_ratio": 0.78,
            "transit_budget_multiplier": 1.05,
            "transit_buffer_minutes": 15,
            "low_density_mode": False,
            "driving_day_slack_minutes": 0,
        },
    },
    "northern_xinjiang_city_circle": {
        "city_circle_profile": {
            "circle_family": "northern_xinjiang",
            "region_family": "china",
            "selection_bias": 0.02,
            "explain_tags": ["road_trip", "long_segment"],
        },
        "mobility_policy": {
            "primary_mode": "self_drive_or_charter",
            "intra_city_mode": "drive",
            "cross_city_tolerance": "low",
            "max_transfer_minutes_per_day": 180,
            "airport_access_style": "arrival_buffer_first",
            "last_night_airport_buffer_minutes": 150,
        },
        "climate_and_season_policy": {
            "climate_family": "continental",
            "seasonality_mode": "extreme_temperature_sensitive",
            "high_risk_months": [11, 12, 1, 2, 3],
            "pace_cap_adjustment": -1,
            "season_fit_bias": 0.01,
            "explain_risks": ["road_distance", "weather_window"],
        },
        "routing_style_policy": {
            "routing_mode": "linear_road_trip",
            "prefer_single_base": False,
            "max_cross_city_days": 2,
            "max_majors_per_day": 1,
            "daytrip_bias": "low",
            "backtrack_penalty_bias": 0.18,
        },
        "hotel_base_policy": {
            "base_pattern_bias": "multi_base",
            "prefer_last_night_near_hub": True,
            "last_night_hub_max_minutes": 150,
            "long_segment_base_preference": "route_node",
            "route_node_bias_weight": 0.25,
        },
        "day_frame_policy": {
            "arrival_capacity_ratio": 0.65,
            "normal_capacity_ratio": 0.82,
            "departure_capacity_ratio": 0.55,
            "transit_budget_multiplier": 1.45,
            "transit_buffer_minutes": 45,
            "low_density_mode": True,
            "driving_day_slack_minutes": 45,
        },
        "booking_and_reservation_policy": {
            "high_pressure_constraint": "hard",
            "unbooked_major_action": "degrade_only",
            "hold_back_edge_days": True,
            "trace_level": "minimal",
        },
    },
}


def resolve_policy_set(
    circle_id: str,
    *,
    circle: CityCircle | None = None,
    resolved_config: ResolvedConfig | None = None,
) -> ResolvedPolicySet:
    merged = _deep_merge(_DEFAULT_BUNDLE, _POLICY_OVERRIDES.get(circle_id, {}))
    sources: list[dict[str, Any]] = [
        {"module": "bundle", "origin": "default", "detail": "base layer"},
    ]

    if circle_id in _POLICY_OVERRIDES:
        sources.append({"module": "bundle", "origin": "circle_override", "detail": circle_id})

    if circle is not None:
        if circle.season_strength:
            merged["climate_and_season_policy"]["season_fit_bias"] += 0.02
            sources.append({"module": "climate_and_season_policy", "origin": "city_circle", "detail": "season_strength"})
        if len(circle.base_city_codes or []) <= 1:
            merged["routing_style_policy"]["prefer_single_base"] = True
            sources.append({"module": "routing_style_policy", "origin": "city_circle", "detail": "single_base_hint"})

    config_snapshot: dict[str, Any] = {}
    if resolved_config is not None:
        transfer_cap = resolved_config.threshold(
            "max_transfer_minutes_per_day",
            merged["mobility_policy"]["max_transfer_minutes_per_day"],
        )
        cross_city_cap = resolved_config.threshold(
            "max_cross_city_days",
            merged["routing_style_policy"]["max_cross_city_days"],
        )
        merged["mobility_policy"]["max_transfer_minutes_per_day"] = int(transfer_cap)
        merged["routing_style_policy"]["max_cross_city_days"] = int(cross_city_cap)
        config_snapshot = {
            "max_transfer_minutes_per_day": int(transfer_cap),
            "max_cross_city_days": int(cross_city_cap),
            "sources": resolved_config.sources,
        }
        sources.append({"module": "config", "origin": "config_resolver", "detail": "threshold merge"})

    return ResolvedPolicySet(
        circle_id=circle_id,
        city_circle_profile=CityCircleProfilePolicy(**merged["city_circle_profile"]),
        mobility_policy=MobilityPolicy(**merged["mobility_policy"]),
        climate_and_season_policy=ClimateAndSeasonPolicy(**merged["climate_and_season_policy"]),
        routing_style_policy=RoutingStylePolicy(**merged["routing_style_policy"]),
        hotel_base_policy=HotelBasePolicy(**merged["hotel_base_policy"]),
        day_frame_policy=DayFramePolicy(**merged["day_frame_policy"]),
        booking_and_reservation_policy=BookingAndReservationPolicy(**merged["booking_and_reservation_policy"]),
        config_snapshot=config_snapshot,
        sources=sources,
    )
