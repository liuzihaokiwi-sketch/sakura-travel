"""
corridors.py — T14: 走廊标准化

corridors 是空间上的"线"或"片区"，用于：
- activity_cluster.primary_corridor 关联
- entity_base.corridor_tags 关联
- itinerary_fit_scorer 的 corridor_alignment 评分
- secondary_filler 的 same_corridor 优先逻辑

每个走廊属于一个或多个 city_code，有标准化 ID + 别名。

corridor_alias_map:
  将非标准 area_name（如"祗园""gion""ぎおん"）映射到标准 corridor_id。
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Corridor(Base):
    """
    走廊定义表 — 标准化的区域 / 线路片区。

    走廊是比 city 更细粒度的空间单元，比 entity 更粗粒度。
    如 higashiyama（东山线）、arashiyama（岚山片区）、shinjuku（新宿站周边）。
    """

    __tablename__ = "corridors"

    corridor_id: Mapped[str] = mapped_column(
        String(80), primary_key=True,
        comment="标准化 ID，如 kyo_higashiyama / osa_namba / tyo_shinjuku"
    )
    name_zh: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(100))
    name_ja: Mapped[Optional[str]] = mapped_column(String(100))

    # 所属城市（一个走廊通常只属于一个城市）
    city_code: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="kyoto / osaka / tokyo / ..."
    )

    # 地理中心点（用于粗略距离计算）
    center_lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    center_lng: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))

    # 走廊类型
    corridor_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="area",
        comment="area / line / station_hub — 片区/步行线/枢纽站圈"
    )

    # 关联的交通枢纽
    main_stations: Mapped[Optional[list]] = mapped_column(
        JSONB, default=list,
        comment='["清水五条","祇園四条"] — 主要车站/地铁站'
    )

    # 邻近走廊（用于 corridor_alignment 扩展评分）
    adjacent_corridor_ids: Mapped[Optional[list]] = mapped_column(
        JSONB, default=list,
        comment='["kyo_gion","kyo_kiyomizu"] — 步行可达的邻近走廊'
    )

    # 走廊活跃度
    typical_visit_hours: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1),
        comment="典型游览该走廊所需小时数（如 3.5）"
    )

    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_corridors_city", "city_code"),
        Index("ix_corridors_type", "corridor_type"),
    )


class CorridorAliasMap(Base):
    """
    走廊别名映射表 — 将非标准 area_name 映射到标准 corridor_id。

    如：
      "祇園"       → kyo_gion
      "gion"       → kyo_gion
      "ぎおん"     → kyo_gion
      "四条河原町"  → kyo_kawaramachi
      "Shijo"      → kyo_kawaramachi

    用于：
    1. entity_base.area_name → corridor_id 的自动标准化
    2. entity_base.corridor_tags 的自动填充
    3. 用户输入区域名的模糊匹配
    """

    __tablename__ = "corridor_alias_map"

    alias_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    corridor_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("corridors.corridor_id", ondelete="CASCADE"),
        nullable=False,
    )
    alias_text: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="非标准名称（原始 area_name、日文、罗马音等）"
    )
    alias_lang: Mapped[Optional[str]] = mapped_column(
        String(10), comment="zh / ja / en / romaji"
    )
    normalized_text: Mapped[Optional[str]] = mapped_column(
        Text, comment="小写+去空格标准化文本，用于快速匹配"
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否为该走廊在该语言下的首选名称"
    )

    __table_args__ = (
        UniqueConstraint("corridor_id", "alias_text", name="uq_corridor_alias"),
        Index("ix_corridor_alias_normalized_trgm", "normalized_text",
              postgresql_using="gin",
              postgresql_ops={"normalized_text": "gin_trgm_ops"}),
        Index("ix_corridor_alias_corridor", "corridor_id"),
    )
