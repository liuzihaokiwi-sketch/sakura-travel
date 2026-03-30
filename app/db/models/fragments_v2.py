"""D1: DayFragment model for pre-made itinerary fragments"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DayFragment(Base):
    """Pre-made day fragments (half-day or full-day themed activities)

    Fragments are reusable building blocks for itineraries, with conditional
    alternatives for closed days, rain, etc. Each item in the items JSONB
    array can include:
    - entity_id, entity_name, type, start, duration, note
    - closed_days: list of weekday numbers (0=Mon) when activity is unavailable
    - alternatives: list of {entity_id, reason, note} for substitution
    - rain_alternative: single {entity_id, reason, note} for rainy days
    """

    __tablename__ = "day_fragments"

    fragment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_code: Mapped[str] = mapped_column(String(50), nullable=False)
    corridor: Mapped[Optional[str]] = mapped_column(String(100))
    fragment_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'half_day' | 'full_day'
    theme: Mapped[Optional[str]] = mapped_column(String(100))

    items: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    total_duration: Mapped[Optional[int]] = mapped_column(SmallInteger)  # minutes
    estimated_cost: Mapped[Optional[int]] = mapped_column(Integer)  # JPY per person

    best_season: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(20)))
    weather_ok: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(20)), server_default="'{any}'")
    suitable_for: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(20)), server_default="'{any}'")
    pace: Mapped[str] = mapped_column(String(20), server_default="'moderate'")
    energy_level: Mapped[str] = mapped_column(String(20), server_default="'medium'")

    start_station: Mapped[Optional[str]] = mapped_column(String(100))
    end_station: Mapped[Optional[str]] = mapped_column(String(100))
    transit_from_prev: Mapped[Optional[str]] = mapped_column(String(200))

    title_zh: Mapped[Optional[str]] = mapped_column(String(200))
    summary_zh: Mapped[Optional[str]] = mapped_column(Text)
    practical_notes: Mapped[Optional[str]] = mapped_column(Text)

    quality_score: Mapped[Optional[float]] = mapped_column(Numeric(4, 2))
    is_verified: Mapped[bool] = mapped_column(Boolean, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
