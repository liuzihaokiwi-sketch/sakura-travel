from __future__ import annotations

from typing import Optional
"""
Layer A – Catalog (静态事实层)
8 tables: entity_base, pois, hotels, restaurants,
          entity_tags, entity_media, entity_editor_notes, hotel_area_guide
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
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


# ── entity_base ───────────────────────────────────────────────────────────────
class EntityBase(Base):
    """中心表：所有 POI / 酒店 / 餐厅共享的基础信息（CTI 模式）"""

    __tablename__ = "entity_base"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="poi | hotel | restaurant"
    )

    # 名称（多语言冗余，避免每次 JOIN translations）
    name_zh: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ja: Mapped[Optional[str]] = mapped_column(String(200))
    name_en: Mapped[Optional[str]] = mapped_column(String(200))

    # 地理位置
    city_code: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="tokyo / osaka / kyoto / ..."
    )
    prefecture: Mapped[Optional[str]] = mapped_column(String(50))
    area_name: Mapped[Optional[str]] = mapped_column(String(100), comment="具体区域，如涩谷/新宿")
    address_ja: Mapped[Optional[str]] = mapped_column(String(500))
    address_en: Mapped[Optional[str]] = mapped_column(String(500))
    lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    lng: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))

    # 向量嵌入（用于语义搜索）
    embedding: Mapped[Optional[list]] = mapped_column(Vector(1536))

    # 数据层级
    data_tier: Mapped[str] = mapped_column(
        String(1), nullable=False, default="B", comment="S / A / B"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # 外部 ID 映射
    google_place_id: Mapped[Optional[str]] = mapped_column(String(200), unique=True)
    tabelog_id: Mapped[Optional[str]] = mapped_column(String(200))

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    poi: Mapped[Optional["Poi"]] = relationship("Poi", back_populates="entity", uselist=False)
    hotel: Mapped[Optional["Hotel"]] = relationship(
        "Hotel", back_populates="entity", uselist=False
    )
    restaurant: Mapped[Optional["Restaurant"]] = relationship(
        "Restaurant", back_populates="entity", uselist=False
    )
    tags: Mapped[list["EntityTag"]] = relationship("EntityTag", back_populates="entity")
    media: Mapped[list["EntityMedia"]] = relationship("EntityMedia", back_populates="entity")
    editor_notes: Mapped[list["EntityEditorNote"]] = relationship(
        "EntityEditorNote", back_populates="entity"
    )

    __table_args__ = (
        Index("ix_entity_base_city_type", "city_code", "entity_type"),
        Index("ix_entity_base_data_tier", "data_tier"),
        Index("ix_entity_base_google_place_id", "google_place_id"),
    )


# ── pois ──────────────────────────────────────────────────────────────────────
class Poi(Base):
    """景点扩展表（CTI：entity_base.entity_type = 'poi'）"""

    __tablename__ = "pois"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # 分类
    poi_category: Mapped[Optional[str]] = mapped_column(
        String(50), comment="shrine / temple / park / museum / theme_park / ..."
    )
    sub_category: Mapped[Optional[str]] = mapped_column(String(50))

    # 时间 & 票价（事实，不走 LLM）
    typical_duration_min: Mapped[Optional[int]] = mapped_column(
        SmallInteger, comment="典型游览时长（分钟）"
    )
    opening_hours_json: Mapped[Optional[dict]] = mapped_column(JSONB, comment="标准化 opening hours")
    admission_fee_jpy: Mapped[Optional[int]] = mapped_column(Integer, comment="成人票价（日元）")
    admission_free: Mapped[bool] = mapped_column(Boolean, default=False)

    # 特色标签
    best_season: Mapped[Optional[str]] = mapped_column(String(20), comment="spring/summer/autumn/winter/all")
    crowd_level_typical: Mapped[Optional[str]] = mapped_column(
        String(10), comment="low / medium / high"
    )
    requires_advance_booking: Mapped[bool] = mapped_column(Boolean, default=False)

    # 评分
    google_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    google_review_count: Mapped[Optional[int]] = mapped_column(Integer)

    entity: Mapped["EntityBase"] = relationship("EntityBase", back_populates="poi")


# ── hotels ────────────────────────────────────────────────────────────────────
class Hotel(Base):
    """酒店扩展表（CTI：entity_base.entity_type = 'hotel'）"""

    __tablename__ = "hotels"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # 分类
    hotel_type: Mapped[Optional[str]] = mapped_column(
        String(30), comment="business / ryokan / capsule / resort / boutique"
    )
    star_rating: Mapped[Optional[float]] = mapped_column(Numeric(2, 1))
    chain_name: Mapped[Optional[str]] = mapped_column(String(100))

    # 规模
    room_count: Mapped[Optional[int]] = mapped_column(SmallInteger)
    check_in_time: Mapped[Optional[str]] = mapped_column(String(5), comment="HH:MM，如 15:00")
    check_out_time: Mapped[Optional[str]] = mapped_column(String(5))

    # 设施标签
    amenities: Mapped[Optional[list]] = mapped_column(JSONB, comment="['onsen', 'breakfast', ...]")
    is_family_friendly: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pet_friendly: Mapped[bool] = mapped_column(Boolean, default=False)

    # 价格基准（仅参考，实时价格走 Snapshots）
    price_tier: Mapped[Optional[str]] = mapped_column(
        String(10), comment="budget / mid / premium / luxury"
    )
    typical_price_min_jpy: Mapped[Optional[int]] = mapped_column(
        Integer, comment="每晚最低参考价"
    )

    # 外部 ID
    booking_hotel_id: Mapped[Optional[str]] = mapped_column(String(200))
    agoda_hotel_id: Mapped[Optional[str]] = mapped_column(String(200))

    # 评分
    google_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    booking_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))

    entity: Mapped["EntityBase"] = relationship("EntityBase", back_populates="hotel")
    area_guide: Mapped[Optional["HotelAreaGuide"]] = relationship(
        "HotelAreaGuide", back_populates="hotel", uselist=False
    )


# ── restaurants ───────────────────────────────────────────────────────────────
class Restaurant(Base):
    """餐厅扩展表（CTI：entity_base.entity_type = 'restaurant'）"""

    __tablename__ = "restaurants"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # 分类
    cuisine_type: Mapped[Optional[str]] = mapped_column(
        String(50), comment="sushi / ramen / kaiseki / izakaya / ..."
    )
    sub_cuisine: Mapped[Optional[str]] = mapped_column(String(50))
    michelin_star: Mapped[Optional[int]] = mapped_column(SmallInteger, comment="0 / 1 / 2 / 3")
    tabelog_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))

    # 运营
    opening_hours_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    seating_count: Mapped[Optional[int]] = mapped_column(SmallInteger)
    requires_reservation: Mapped[bool] = mapped_column(Boolean, default=False)
    reservation_difficulty: Mapped[Optional[str]] = mapped_column(
        String(10), comment="easy / medium / hard / impossible"
    )

    # 价格
    price_range_min_jpy: Mapped[Optional[int]] = mapped_column(Integer, comment="人均最低（日元）")
    price_range_max_jpy: Mapped[Optional[int]] = mapped_column(Integer)
    budget_lunch_jpy: Mapped[Optional[int]] = mapped_column(Integer)
    budget_dinner_jpy: Mapped[Optional[int]] = mapped_column(Integer)

    # 特性
    has_english_menu: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vegetarian_friendly: Mapped[bool] = mapped_column(Boolean, default=False)
    is_halal: Mapped[bool] = mapped_column(Boolean, default=False)

    entity: Mapped["EntityBase"] = relationship("EntityBase", back_populates="restaurant")


# ── entity_tags ───────────────────────────────────────────────────────────────
class EntityTag(Base):
    """实体标签表（多对多，扁平化存储）"""

    __tablename__ = "entity_tags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    tag_namespace: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="feature / audience / theme / avoid"
    )
    tag_value: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[Optional[str]] = mapped_column(
        String(20), comment="editor / algorithm / google"
    )

    entity: Mapped["EntityBase"] = relationship("EntityBase", back_populates="tags")

    __table_args__ = (
        Index("ix_entity_tags_entity_id", "entity_id"),
        Index("ix_entity_tags_namespace_value", "tag_namespace", "tag_value"),
    )


# ── entity_media ──────────────────────────────────────────────────────────────
class EntityMedia(Base):
    """实体媒体资源（图片/视频）"""

    __tablename__ = "entity_media"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    media_type: Mapped[str] = mapped_column(String(10), nullable=False, comment="image / video")
    url: Mapped[str] = mapped_column(Text, nullable=False)
    caption_zh: Mapped[Optional[str]] = mapped_column(String(500))
    caption_ja: Mapped[Optional[str]] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[Optional[str]] = mapped_column(String(50), comment="google / editorial / user")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    entity: Mapped["EntityBase"] = relationship("EntityBase", back_populates="media")

    __table_args__ = (Index("ix_entity_media_entity_id", "entity_id"),)


# ── entity_editor_notes ───────────────────────────────────────────────────────
class EntityEditorNote(Base):
    """编辑人工标注（Editorial Boost 依赖此表）"""

    __tablename__ = "entity_editor_notes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    note_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="editorial_boost / avoid_warning / seasonal_note / insider_tip",
    )
    boost_value: Mapped[Optional[int]] = mapped_column(
        SmallInteger, comment="-8 to +8，仅 editorial_boost 类型使用"
    )
    content_zh: Mapped[Optional[str]] = mapped_column(Text)
    content_en: Mapped[Optional[str]] = mapped_column(Text)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    entity: Mapped["EntityBase"] = relationship("EntityBase", back_populates="editor_notes")

    __table_args__ = (Index("ix_editor_notes_entity_id", "entity_id"),)


# ── hotel_area_guide ──────────────────────────────────────────────────────────
class HotelAreaGuide(Base):
    """酒店周边区域导览（编辑撰写，用于行程渲染）"""

    __tablename__ = "hotel_area_guide"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hotels.entity_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    area_summary_zh: Mapped[Optional[str]] = mapped_column(Text, comment="区域 3-5 行介绍")
    nearby_poi_ids: Mapped[Optional[list]] = mapped_column(
        JSONB, comment="[uuid, ...] 步行可达景点"
    )
    transport_tips_zh: Mapped[Optional[str]] = mapped_column(Text, comment="交通提示")
    walking_distance_station_min: Mapped[Optional[int]] = mapped_column(
        SmallInteger, comment="到最近地铁站步行分钟数"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="area_guide")
