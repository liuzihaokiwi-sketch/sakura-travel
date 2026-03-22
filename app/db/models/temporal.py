"""
temporal.py — T2: 实体时态画像表

entity_temporal_profiles 存储随时间/季节/时段变化的实体特征。
将 best_time_window / weather_sensitivity / queue_risk_level 从 entity_base 中剥离，
避免静态表污染，支持多条时态记录（同一实体不同季节不同时段可有不同记录）。
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class EntityTemporalProfile(Base):
    """
    实体时态画像。

    同一实体可有多条记录，每条对应不同的 (season_code, daypart) 组合。
    UNIQUE (entity_id, season_code, daypart)。

    典型用法：
      - 清水寺春季早晨：queue_risk_level=extreme, best_time_window=06:00-08:00
      - 清水寺冬季下午：queue_risk_level=low, weather_sensitivity=high
    """

    __tablename__ = "entity_temporal_profiles"

    profile_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )

    # 时间维度
    season_code: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="spring / summer / autumn / winter / all_year"
    )
    month_range: Mapped[Optional[str]] = mapped_column(
        String(20), comment="精确月份范围，如 '03-04' / '07-08'，覆盖 season_code"
    )
    daypart: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="morning / afternoon / evening / night / all_day"
    )

    # 最佳到达时间窗口
    best_time_window: Mapped[Optional[str]] = mapped_column(
        String(50), comment="建议到达时间，如 '06:00-09:00' / '16:30-18:00'"
    )

    # 风险信号（时态敏感，不放在静态层）
    queue_risk_level: Mapped[Optional[str]] = mapped_column(
        String(10), comment="low / medium / high / extreme"
    )
    weather_sensitivity: Mapped[Optional[str]] = mapped_column(
        String(10), comment="none / low / medium / high"
    )
    crowd_level: Mapped[Optional[str]] = mapped_column(
        String(10), comment="low / medium / high / extreme"
    )

    # 补充说明
    availability_notes: Mapped[Optional[str]] = mapped_column(
        Text, comment="特殊营业/关闭说明，如'国庆日关闭''花见期间仅开放外苑'"
    )

    # 数据来源
    source_type: Mapped[Optional[str]] = mapped_column(
        String(20), comment="official / platform / ai_estimated / manual"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("entity_id", "season_code", "daypart",
                         name="uq_temporal_entity_season_daypart"),
        Index("ix_temporal_entity_id", "entity_id"),
        Index("ix_temporal_season_daypart", "season_code", "daypart"),
    )
