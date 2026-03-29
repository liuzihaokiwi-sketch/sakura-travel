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
    UniqueConstraint,
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

    # T4: 新增静态地理+路线字段
    nearest_station: Mapped[Optional[str]] = mapped_column(
        String(100), comment="最近地铁/车站名称"
    )
    corridor_tags: Mapped[Optional[list]] = mapped_column(
        JSONB, default=list,
        comment="所属走廊标签列表，如 ['higashiyama', 'gion']"
    )
    typical_duration_baseline: Mapped[Optional[int]] = mapped_column(
        SmallInteger, comment="基准游览时长（分钟），非时态值，时态值在 entity_temporal_profiles"
    )
    # price_band — REMOVED (migration 20260329_140000), 用 budget_tier 替代
    # operating_stability_level — REMOVED (migration 20260329_140000)

    # A3: 新增内容质量与预约字段
    quality_tier: Mapped[Optional[str]] = mapped_column(
        String(1), comment="S/A/B/C — 内容深度等级，影响规划权重和自动发布门槛"
    )
    budget_tier: Mapped[Optional[str]] = mapped_column(
        String(10), comment="free/budget/mid/premium/luxury — 统一预算分层"
    )
    risk_flags: Mapped[Optional[list]] = mapped_column(
        JSONB, default=list,
        comment="风险标签列表，如 ['requires_reservation','seasonal_closure','long_queue']"
    )
    booking_method: Mapped[Optional[str]] = mapped_column(
        String(20), comment="walk_in/online_advance/phone/impossible — 主要预约方式"
    )
    # best_time_of_day — REMOVED (migration 20260329_140000), 用 entity_temporal_profiles 替代
    # visit_duration_min — REMOVED (migration 20260329_140000), 用 pois.typical_duration_min 替代

    # A6: 推荐计数与轮转
    recommendation_count_30d: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="过去30天被推荐进行程的次数，用于轮转降权"
    )
    last_recommended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="最后一次被推荐的时间"
    )

    # 数据可信度
    trust_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unverified",
        comment="verified / unverified / ai_generated / suspicious / rejected"
    )
    verified_by: Mapped[Optional[str]] = mapped_column(String(100))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trust_note: Mapped[Optional[str]] = mapped_column(Text)

    # 定时刷新
    last_refreshed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="上次 AI 刷新实体数据的时间，用于定时更新调度"
    )

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
        Index("ix_entity_base_trust_status", "trust_status"),
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

    # A3: 预约与排队
    advance_booking_days: Mapped[Optional[int]] = mapped_column(
        SmallInteger, comment="建议提前预约天数（-1=无需，0=当天，7=提前一周）"
    )
    booking_url: Mapped[Optional[str]] = mapped_column(Text, comment="官方预约/购票链接")
    queue_wait_typical_min: Mapped[Optional[int]] = mapped_column(
        SmallInteger, comment="典型排队等候时间（分钟）"
    )

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

    # A3: 预约
    advance_booking_days: Mapped[Optional[int]] = mapped_column(
        SmallInteger, comment="建议提前预约天数"
    )
    booking_url: Mapped[Optional[str]] = mapped_column(
        Text, comment="官方预约链接（Tablecheck / Omakase 等）"
    )

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
    """
    实体媒体资源（图片/视频）。

    扩展字段参考：fix/图片采集与描述评价数据方案_v1.md §5.1
    """

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

    # ── 图片采集方案扩展字段 ──────────────────────────────────────────────
    source_kind: Mapped[Optional[str]] = mapped_column(
        String(30),
        comment="official_site / official_social / google_places / licensed_partner / manual_upload / other_candidate"
    )
    source_page_url: Mapped[Optional[str]] = mapped_column(
        Text, comment="图片来源页面 URL（溯源用）"
    )
    attribution_text: Mapped[Optional[str]] = mapped_column(
        String(500), comment="归属文本（Google Places 要求展示）"
    )
    copyright_note: Mapped[Optional[str]] = mapped_column(String(200))
    license_status: Mapped[Optional[str]] = mapped_column(
        String(20), default="review_needed",
        comment="allowed / restricted / review_needed"
    )
    image_role: Mapped[Optional[str]] = mapped_column(
        String(30),
        comment="hero / exterior / lobby / room / bath / breakfast / signature_dish / "
                "interior / menu / main_scene / entrance / transit_hint / experience"
    )
    quality_score: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2), comment="0-10 图片质量评分（清晰度+构图+代表性）"
    )
    representativeness_score: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2), comment="0-10 图片对实体的代表性评分"
    )
    season_tag: Mapped[Optional[str]] = mapped_column(
        String(20), comment="spring / summer / autumn / winter / all_season"
    )
    daypart_tag: Mapped[Optional[str]] = mapped_column(
        String(20), comment="day / sunset / night / all_day"
    )
    is_selected: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="精选标记（从候选池进入最终展示）"
    )
    needs_review: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否需要人工审核"
    )
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    width: Mapped[Optional[int]] = mapped_column(SmallInteger)
    height: Mapped[Optional[int]] = mapped_column(SmallInteger)
    file_size_kb: Mapped[Optional[int]] = mapped_column(SmallInteger)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    entity: Mapped["EntityBase"] = relationship("EntityBase", back_populates="media")

    __table_args__ = (
        Index("ix_entity_media_entity_id", "entity_id"),
        Index("ix_entity_media_role", "image_role"),
        Index("ix_entity_media_selected", "entity_id", "is_selected"),
        Index("ix_entity_media_review", "needs_review", "license_status"),
    )


# ── entity_descriptions ──────────────────────────────────────────────────────
class EntityDescription(Base):
    """
    实体描述文本（多来源、多类型）。

    参考：fix/图片采集与描述评价数据方案_v1.md §5.2
    不同于 entity_editor_notes（人工编辑标注），这里存的是
    各种来源的描述候选+最终展示文本。
    """

    __tablename__ = "entity_descriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_kind: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="official / google / ai_generated / manual / platform"
    )
    description_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="official_summary / generated_short / generated_reason / "
                "expectation_hint / operator_override / why_selected / "
                "what_to_expect / who_it_is_for / skip_if / ordering_hint"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="zh", comment="zh / ja / en")
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_entity_desc_entity", "entity_id"),
        Index("ix_entity_desc_type", "description_type"),
        Index("ix_entity_desc_active", "entity_id", "description_type", "is_active"),
    )


# ── entity_review_signals ────────────────────────────────────────────────────
class EntityReviewSignal(Base):
    """
    实体评价信号聚合表。

    参考：fix/图片采集与描述评价数据方案_v1.md §5.2
    不存原文评论，只存聚合分数和标签。
    """

    __tablename__ = "entity_review_signals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    rating_source: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="google / tabelog / booking / tripadvisor / jalan"
    )
    aggregate_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    review_count: Mapped[Optional[int]] = mapped_column(BigInteger)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    positive_tags: Mapped[Optional[list]] = mapped_column(
        JSONB, default=list, comment='["景观好","早餐强","交通便利"]'
    )
    negative_tags: Mapped[Optional[list]] = mapped_column(
        JSONB, default=list, comment='["排队久","房间小","隔音差"]'
    )
    summary_tags: Mapped[Optional[list]] = mapped_column(
        JSONB, default=list, comment='["适合情侣","适合纪念日"]'
    )
    queue_risk_level: Mapped[Optional[str]] = mapped_column(
        String(10), comment="none / low / medium / high"
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("entity_id", "rating_source", name="uq_review_signal_source"),
        Index("ix_review_signals_entity", "entity_id"),
    )


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


# ── entity_aliases ─────────────────────────────────────────────────────────────
class EntityAlias(Base):
    """
    T1: 实体别名表。
    用于多语言模糊匹配（pg_trgm）和实体映射管线（T7 auto_map_entities_to_clusters）。
    """

    __tablename__ = "entity_aliases"

    alias_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    alias_text: Mapped[str] = mapped_column(Text, nullable=False, comment="原始别名文本")
    alias_lang: Mapped[Optional[str]] = mapped_column(
        String(10), comment="ja / en / zh / romaji"
    )
    alias_type: Mapped[Optional[str]] = mapped_column(
        String(20), comment="official / common / romaji / short / deprecated"
    )
    normalized_text: Mapped[Optional[str]] = mapped_column(
        Text, comment="小写+去音标+去空格的标准化文本，用于 pg_trgm 索引"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_entity_aliases_entity_id", "entity_id"),
        Index("ix_entity_aliases_normalized_trgm", "normalized_text",
              postgresql_using="gin",
              postgresql_ops={"normalized_text": "gin_trgm_ops"}),
        Index("uq_entity_alias_text", "entity_id", "alias_text", unique=True),
    )


# ── entity_field_provenance ───────────────────────────────────────────────────
class EntityFieldProvenance(Base):
    """
    T3: 字段溯源表。
    记录每个实体各字段的数据来源、置信度和审核状态，支持 refresh SLA（T15）。
    """

    __tablename__ = "entity_field_provenance"

    provenance_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    field_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="如 typical_duration_minutes / price_band / opening_hours_json"
    )
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="official / platform / ai_estimated / manual / rule_derived"
    )
    source_ref: Mapped[Optional[str]] = mapped_column(
        Text, comment="URL 或来源标识"
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), comment="0.00-1.00"
    )
    review_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unreviewed",
        comment="unreviewed / approved / rejected / stale"
    )
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_efp_entity_id", "entity_id"),
        Index("ix_efp_review_status", "review_status"),
        Index("uq_efp_entity_field_source", "entity_id", "field_name", "source_type", unique=True),
    )


# ── entity_mapping_reviews (T10) ─────────────────────────────────────────────
class EntityMappingReview(Base):
    """
    T10: 实体映射审核队列。

    由 auto_map_entities_to_clusters 管线写入（fuzzy match / rejected）。
    支持人工审核、AI 二次学习、覆盖率统计。

    审核流：
      pending → approved / rejected / remapped
      approved  → 写入 circle_entity_roles（或确认已有行）
      rejected  → 标记 rejected，不映射
      remapped  → 人工指定另一 entity_id
    """

    __tablename__ = "entity_mapping_reviews"

    review_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 映射来源
    circle_id: Mapped[str] = mapped_column(
        String(80), nullable=False, comment="来源城市圈 ID"
    )
    cluster_id: Mapped[Optional[str]] = mapped_column(
        String(80), comment="来源活动簇 ID"
    )

    # 原始搜索词
    anchor_name: Mapped[str] = mapped_column(
        String(300), nullable=False, comment="管线搜索的锚点名称"
    )

    # 自动匹配结果
    matched_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="SET NULL"),
        comment="管线自动匹配到的 entity_id（可能是错误的）",
    )
    match_level: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="exact / alias / fuzzy / rejected — 管线匹配层级"
    )
    match_method: Mapped[Optional[str]] = mapped_column(
        String(50), comment="trgm_medium / substring / name_local_exact 等"
    )
    similarity_score: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 3), comment="0.000-1.000 管线匹配相似度"
    )

    # 审核状态
    review_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="pending / approved / rejected / remapped"
    )
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # 人工指定的正确 entity（remapped 时填写）
    corrected_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="SET NULL"),
        comment="人工修正后的 entity_id",
    )
    corrected_role: Mapped[Optional[str]] = mapped_column(
        String(30), comment="人工指定的角色（anchor_poi / secondary_poi 等）"
    )
    review_note: Mapped[Optional[str]] = mapped_column(
        Text, comment="审核备注"
    )

    # 管线运行批次标识
    pipeline_run_id: Mapped[Optional[str]] = mapped_column(
        String(50), comment="管线运行批次 ID，方便溯源"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_emr_review_status", "review_status"),
        Index("ix_emr_circle_cluster", "circle_id", "cluster_id"),
        Index("ix_emr_matched_entity", "matched_entity_id"),
        Index("ix_emr_pipeline_run", "pipeline_run_id"),
    )