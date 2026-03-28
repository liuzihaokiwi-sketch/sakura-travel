from __future__ import annotations

from datetime import datetime
from typing import Any


# ── 归一化辅助（供外部 import，消除各调用方的本地副本） ─────────────────────────

_PARTY_TYPE_MAP: dict[str, str] = {
    "family_with_kids": "family_child",
    "family_no_kids": "family_no_child",
    "family": "family_child",
    "friends": "group",
    "besties": "group",
    "parents": "senior",
    "business": "group",
}

_PACE_MAP: dict[str, str] = {
    "balanced": "moderate",
    "intensive": "packed",
    "light": "relaxed",
    "dense": "packed",
}


def normalize_party_type(raw: str | None) -> str:
    """将前端/表单的 party_type 值归一到内部枚举。"""
    party = (raw or "couple").strip().lower()
    return _PARTY_TYPE_MAP.get(party, party or "couple")


def normalize_pace(raw: str | None) -> str:
    """将前端/表单的 pace 值归一到内部枚举。"""
    pace = (raw or "moderate").strip().lower()
    return _PACE_MAP.get(pace, pace or "moderate")


# ── source 标记辅助 ────────────────────────────────────────────────────────────

def _annotated(value: Any, source: str) -> dict:
    """将字段值包装为 {value, source} 格式。"""
    return {"value": value, "source": source}


def unpack_canonical_values(canonical: dict[str, Any]) -> dict[str, Any]:
    """
    从 build_layer2_canonical_input 的带 source 标记格式中提取平铺值。

    输入: {"field": {"value": ..., "source": "explicit"|"inferred"}, ...}
    输出: {"field": ..., ...}  （contract_version 等非注解字段原样保留）
    """
    result: dict[str, Any] = {}
    for k, v in canonical.items():
        if isinstance(v, dict) and "value" in v and "source" in v:
            result[k] = v["value"]
        else:
            result[k] = v
    return result


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
    return []


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
    """
    将表单原始 dict 归一化为 Layer 2 合约格式。

    每个业务字段使用 {value, source} 二元组标记来源：
      - "explicit": 用户明确填写
      - "inferred": 系统从其他字段推断或使用默认值
    使用 unpack_canonical_values() 可提取平铺的值字典。
    """
    # ── 到达时间 ──────────────────────────────────────────────────────────────
    has_explicit_arrival = bool(raw.get("arrival_date") and raw.get("arrival_time"))
    arrival_dt = _parse_local_datetime(
        raw.get("arrival_date") or raw.get("travel_start_date"),
        raw.get("arrival_time"),
    )

    # ── 离开时间 ──────────────────────────────────────────────────────────────
    has_explicit_departure = bool(raw.get("departure_date") and raw.get("departure_time"))
    departure_dt = _parse_local_datetime(
        raw.get("departure_date") or raw.get("travel_end_date"),
        raw.get("departure_time"),
    )

    # ── 城市圈 ────────────────────────────────────────────────────────────────
    circle = _requested_city_circle(raw)
    circle_source = "explicit" if circle else "inferred"

    # ── 同行信息 ──────────────────────────────────────────────────────────────
    companion_source = "explicit" if raw.get("party_size") is not None else "inferred"

    # ── 预算 ──────────────────────────────────────────────────────────────────
    budget_source = "explicit" if raw.get("budget_level") else "inferred"

    booked_items = _build_booked_items(raw)
    do_not_go_places = _clean_list(raw.get("do_not_go_places"))
    must_visit_places = _clean_list(raw.get("must_visit_places"))
    visited_places = _clean_list(raw.get("visited_places"))

    return {
        "contract_version": "layer2_v1",
        "requested_city_circle": _annotated(circle, circle_source),
        "arrival_local_datetime": _annotated(
            arrival_dt.isoformat(timespec="minutes") if arrival_dt else None,
            "explicit" if has_explicit_arrival else "inferred",
        ),
        "departure_local_datetime": _annotated(
            departure_dt.isoformat(timespec="minutes") if departure_dt else None,
            "explicit" if has_explicit_departure else "inferred",
        ),
        "must_visit_places": _annotated(must_visit_places, "explicit"),
        "visited_places": _annotated(visited_places, "explicit"),
        "do_not_go_places": _annotated(do_not_go_places, "explicit"),
        "booked_items": _annotated(booked_items, "explicit"),
        "companion_breakdown": _annotated(_build_companion_breakdown(raw), companion_source),
        "budget_range": _annotated(_build_budget_range(raw), budget_source),
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
