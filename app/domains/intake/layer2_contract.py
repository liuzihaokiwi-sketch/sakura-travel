from __future__ import annotations

from datetime import datetime
from typing import Any


def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return value.strip()


def _clean_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    for value in values:
        text = _clean_str(value)
        if text:
            cleaned.append(text)
    return cleaned


def _parse_local_datetime(date_value: Any, time_value: Any) -> datetime | None:
    date_text = _clean_str(date_value)
    time_text = _clean_str(time_value)
    if not date_text:
        return None
    if not time_text:
        time_text = "00:00"
    try:
        return datetime.fromisoformat(f"{date_text}T{time_text}")
    except ValueError:
        return None


def _requested_city_circle(raw: dict[str, Any]) -> str | None:
    requested = _clean_str(raw.get("requested_city_circle"))
    if requested:
        return requested
    return None


def _build_booked_items(raw: dict[str, Any]) -> list[dict[str, Any]]:
    explicit = raw.get("booked_items")
    if isinstance(explicit, list):
        return [item for item in explicit if isinstance(item, dict)]

    booked_items: list[dict[str, Any]] = []
    for hotel in raw.get("booked_hotels") or []:
        if not isinstance(hotel, dict):
            continue
        booked_items.append(
            {
                "type": "hotel",
                "city_code": _clean_str(hotel.get("city_code") or hotel.get("city")),
                "name": _clean_str(hotel.get("name")),
                "area": _clean_str(hotel.get("area")),
                "checkin": _clean_str(hotel.get("checkin") or hotel.get("check_in")),
                "checkout": _clean_str(hotel.get("checkout") or hotel.get("check_out")),
                "locked": True,
            }
        )

    for event in raw.get("fixed_events") or []:
        if not isinstance(event, dict):
            continue
        booked_items.append(
            {
                "type": "fixed_item",
                "name": _clean_str(event.get("name")),
                "location": _clean_str(event.get("location") or event.get("place")),
                "date": _clean_str(event.get("date")),
                "time_hint": _clean_str(event.get("time")),
                "locked": True,
            }
        )

    return booked_items


def _build_companion_breakdown(raw: dict[str, Any]) -> dict[str, Any]:
    party_size = raw.get("party_size")
    try:
        normalized_party_size = int(party_size) if party_size is not None else None
    except (TypeError, ValueError):
        normalized_party_size = None

    party_ages = []
    for value in raw.get("party_ages") or []:
        try:
            party_ages.append(int(value))
        except (TypeError, ValueError):
            continue

    children_ages = []
    for value in raw.get("children_ages") or []:
        try:
            children_ages.append(int(value))
        except (TypeError, ValueError):
            continue

    adults_count = normalized_party_size
    if adults_count is not None:
        adults_count = max(0, adults_count - len(children_ages))

    return {
        "party_type": _clean_str(raw.get("party_type")) or "couple",
        "party_size": normalized_party_size,
        "adults_count": adults_count,
        "children_count": len(children_ages),
        "children_ages": children_ages,
        "has_elderly": bool(raw.get("has_elderly")),
        "has_children": bool(raw.get("has_children")),
        "party_ages": party_ages,
    }


def _build_budget_range(raw: dict[str, Any]) -> dict[str, Any]:
    currency = _clean_str(raw.get("budget_currency")).upper() or "CNY"
    total = raw.get("budget_total_cny")
    if total is None:
        total = raw.get("budget_total_jpy")
        if total is not None:
            currency = "JPY"

    try:
        normalized_total = int(total) if total is not None else None
    except (TypeError, ValueError):
        normalized_total = None

    return {
        "budget_level": _clean_str(raw.get("budget_level")) or "mid",
        "budget_focus": _clean_str(raw.get("budget_focus")) or None,
        "currency": currency,
        "total": normalized_total,
    }


def build_layer2_canonical_input(raw: dict[str, Any]) -> dict[str, Any]:
    arrival_dt = _parse_local_datetime(
        raw.get("arrival_date") or raw.get("travel_start_date"),
        raw.get("arrival_time"),
    )
    departure_dt = _parse_local_datetime(
        raw.get("departure_date") or raw.get("travel_end_date"),
        raw.get("departure_time"),
    )
    booked_items = _build_booked_items(raw)
    do_not_go_places = _clean_list(raw.get("do_not_go_places") or raw.get("dont_want_places"))
    must_visit_places = _clean_list(raw.get("must_visit_places") or raw.get("must_go_places"))
    visited_places = _clean_list(raw.get("visited_places"))

    return {
        "contract_version": "layer2_v1",
        "requested_city_circle": _requested_city_circle(raw),
        "arrival_local_datetime": arrival_dt.isoformat(timespec="minutes") if arrival_dt else None,
        "departure_local_datetime": departure_dt.isoformat(timespec="minutes") if departure_dt else None,
        "must_visit_places": must_visit_places,
        "visited_places": visited_places,
        "do_not_go_places": do_not_go_places,
        "booked_items": booked_items,
        "companion_breakdown": _build_companion_breakdown(raw),
        "budget_range": _build_budget_range(raw),
    }


def parse_layer2_datetime(value: Any) -> datetime | None:
    text = _clean_str(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def build_layer2_profile_contract(profile: Any) -> dict[str, Any]:
    arrival_dt = getattr(profile, "arrival_local_datetime", None)
    departure_dt = getattr(profile, "departure_local_datetime", None)
    return {
        "contract_version": getattr(profile, "contract_version", None) or "layer2_v1",
        "requested_city_circle": getattr(profile, "requested_city_circle", None),
        "arrival_local_datetime": arrival_dt.isoformat(timespec="minutes") if arrival_dt else None,
        "departure_local_datetime": departure_dt.isoformat(timespec="minutes") if departure_dt else None,
        "visited_places": list(getattr(profile, "visited_places", None) or []),
        "must_visit_places": list(getattr(profile, "must_visit_places", None) or []),
        "do_not_go_places": list(getattr(profile, "do_not_go_places", None) or []),
        "booked_items": list(getattr(profile, "booked_items", None) or []),
        "companion_breakdown": dict(getattr(profile, "companion_breakdown", None) or {}),
        "budget_range": dict(getattr(profile, "budget_range", None) or {}),
    }
