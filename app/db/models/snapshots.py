from __future__ import annotations

from typing import Optional
"""
Layer B – Live Snapshots (动态事实层)
6 tables: source_snapshots, hotel_offer_snapshots, hotel_offer_lines,
          flight_offer_snapshots, poi_opening_snapshots, weather_snapshots
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ── source_snapshots ──────────────────────────────────────────────────────────
class SourceSnapshot(Base):
    """外部 API 原始响应存档（溯源 + 调试 + 重放）"""

    __tablename__ = "source_snapshots"

    snapshot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="google_places / booking / tabelog / ..."
    )
    object_type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="hotel / poi / restaurant / flight"
    )
    object_id: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="外部系统 ID 或 entity_id"
    )
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, comment="原始 API 响应")
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    http_status: Mapped[Optional[int]] = mapped_column(SmallInteger)
    request_url: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("ix_source_snapshots_source_object", "source_name", "object_type", "object_id"),
        Index("ix_source_snapshots_expires_at", "expires_at"),
    )


# ── hotel_offer_snapshots ─────────────────────────────────────────────────────
class HotelOfferSnapshot(Base):
    """酒店报价快照（由 booking.com / agoda API 采集）"""

    __tablename__ = "hotel_offer_snapshots"

    offer_snapshot_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="SET NULL"),
        nullable=True,
        comment="关联到 entity_base（可为空，采集时可能尚未入库）",
    )
    source_name: Mapped[str] = mapped_column(String(50), nullable=False)
    check_in_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="YYYY-MM-DD")
    check_out_date: Mapped[str] = mapped_column(String(10), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    currency: Mapped[str] = mapped_column(String(3), default="JPY")
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB)

    lines: Mapped[list["HotelOfferLine"]] = relationship(
        "HotelOfferLine", back_populates="snapshot"
    )

    __table_args__ = (
        Index("ix_hotel_offers_entity_dates", "entity_id", "check_in_date", "check_out_date"),
        Index("ix_hotel_offers_expires", "expires_at"),
    )


# ── hotel_offer_lines ─────────────────────────────────────────────────────────
class HotelOfferLine(Base):
    """酒店报价明细（每种房型/价格档次一行）"""

    __tablename__ = "hotel_offer_lines"

    line_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    offer_snapshot_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("hotel_offer_snapshots.offer_snapshot_id", ondelete="CASCADE"),
        nullable=False,
    )
    room_type: Mapped[Optional[str]] = mapped_column(String(100))
    bed_type: Mapped[Optional[str]] = mapped_column(String(50))
    price_per_night: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    total_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    breakfast_included: Mapped[bool] = mapped_column(Boolean, default=False)
    cancellable: Mapped[bool] = mapped_column(Boolean, default=True)
    rooms_available: Mapped[Optional[int]] = mapped_column(SmallInteger)
    booking_url: Mapped[Optional[str]] = mapped_column(Text)

    snapshot: Mapped["HotelOfferSnapshot"] = relationship(
        "HotelOfferSnapshot", back_populates="lines"
    )

    __table_args__ = (Index("ix_hotel_offer_lines_snapshot", "offer_snapshot_id"),)


# ── flight_offer_snapshots ────────────────────────────────────────────────────
class FlightOfferSnapshot(Base):
    """航班报价快照"""

    __tablename__ = "flight_offer_snapshots"

    flight_snapshot_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    origin_iata: Mapped[str] = mapped_column(String(3), nullable=False)
    dest_iata: Mapped[str] = mapped_column(String(3), nullable=False, default="TYO")
    departure_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="YYYY-MM-DD")
    return_date: Mapped[Optional[str]] = mapped_column(String(10))
    source_name: Mapped[str] = mapped_column(String(50), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    currency: Mapped[str] = mapped_column(String(3), default="CNY")
    min_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB)

    __table_args__ = (
        Index(
            "ix_flight_snapshots_route_date",
            "origin_iata",
            "dest_iata",
            "departure_date",
        ),
    )


# ── poi_opening_snapshots ─────────────────────────────────────────────────────
class PoiOpeningSnapshot(Base):
    """景点实时开放状态快照（Google Places / 官网）"""

    __tablename__ = "poi_opening_snapshots"

    opening_snapshot_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_name: Mapped[str] = mapped_column(String(50), nullable=False)
    check_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="YYYY-MM-DD")
    is_open: Mapped[Optional[bool]] = mapped_column(Boolean)
    opening_hours_json: Mapped[Optional[dict]] = mapped_column(JSONB, comment="当天营业时间详情")
    special_note: Mapped[Optional[str]] = mapped_column(
        Text, comment="临时闭馆/节假日特殊说明"
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_poi_opening_entity_date", "entity_id", "check_date"),
    )


# ── weather_snapshots ─────────────────────────────────────────────────────────
class WeatherSnapshot(Base):
    """天气快照（按城市/日期）"""

    __tablename__ = "weather_snapshots"

    weather_snapshot_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    city_code: Mapped[str] = mapped_column(String(50), nullable=False)
    forecast_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="YYYY-MM-DD")
    source_name: Mapped[str] = mapped_column(String(50), nullable=False)
    temp_high_c: Mapped[Optional[float]] = mapped_column(Numeric(4, 1))
    temp_low_c: Mapped[Optional[float]] = mapped_column(Numeric(4, 1))
    condition: Mapped[Optional[str]] = mapped_column(
        String(30), comment="sunny / cloudy / rainy / snowy"
    )
    precipitation_mm: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_weather_city_date", "city_code", "forecast_date"),
    )
