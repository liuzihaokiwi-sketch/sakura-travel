from __future__ import annotations

from typing import Optional

"""
Data Sources Layer — 数据源注册 & 覆盖管理

表：
  data_source_registry   — 所有外部数据源的元数据
  entity_source_scores   — 每个实体在各平台的评分
  city_data_coverage     — 城市×品类的采集进度跟踪
  city_food_specialties  — 各城市特色菜系
  discovery_candidates   — 攻略网站扫描出的候选地点
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


# ── data_source_registry ──────────────────────────────────────────────────────
class DataSourceRegistry(Base):
    """数据源注册：每个外部平台的元数据"""

    __tablename__ = "data_source_registry"

    source_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False,
        comment="tabelog / japan_guide / google_places / dianping / ..."
    )
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="rating / infrastructure / perception / official"
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    base_url: Mapped[Optional[str]] = mapped_column(String(500))
    # countries / cities 覆盖范围，存为 JSON 数组
    coverage: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment='{"countries": ["JP"], "cities": ["sapporo", ...]}'
    )
    entity_types: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='["restaurant", "poi", "hotel"]'
    )
    priority: Mapped[int] = mapped_column(
        SmallInteger, default=50,
        comment="权威度排序，数字越小越优先"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rate_limit: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment='{"requests_per_minute": 10, "daily_limit": 500}'
    )
    auth_config: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment='{"api_key_env": "GOOGLE_PLACES_API_KEY"}'
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ── entity_source_scores ──────────────────────────────────────────────────────
class EntitySourceScore(Base):
    """实体的多平台评分记录"""

    __tablename__ = "entity_source_scores"
    __table_args__ = (
        UniqueConstraint("entity_id", "source_name", name="uq_entity_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_name: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="tabelog / jalan / dianping / japan_guide / google_places ..."
    )
    raw_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="原始评分（各平台量纲不同）"
    )
    normalized_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="归一化到 0-100"
    )
    review_count: Mapped[Optional[int]] = mapped_column(Integer)
    extra: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="平台特有字段：Tabelog 菜系分类、Japan Guide 星级等"
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ── city_data_coverage ────────────────────────────────────────────────────────
class CityDataCoverage(Base):
    """城市×品类的采集进度跟踪"""

    __tablename__ = "city_data_coverage"
    __table_args__ = (
        UniqueConstraint("city_code", "entity_type", "sub_category", name="uq_city_coverage"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_code: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="poi / restaurant / hotel"
    )
    sub_category: Mapped[Optional[str]] = mapped_column(
        String(50), comment="ramen / budget_hotel / shrine 等"
    )

    # 目标 & 进度
    target_count: Mapped[int] = mapped_column(Integer, nullable=False)
    current_count: Mapped[int] = mapped_column(Integer, default=0)
    verified_count: Mapped[int] = mapped_column(Integer, default=0)

    # 数据源覆盖
    sources_used: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='["tabelog", "google_places"]'
    )
    sources_pending: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='["jalan", "retty"]'
    )

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)


# ── city_food_specialties ─────────────────────────────────────────────────────
class CityFoodSpecialty(Base):
    """各城市特色菜系/名物"""

    __tablename__ = "city_food_specialties"
    __table_args__ = (
        UniqueConstraint("city_code", "cuisine", name="uq_city_cuisine"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_code: Mapped[str] = mapped_column(String(50), nullable=False)
    cuisine: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="味噌拉面 / 成吉思汗 / 汤咖喱 ..."
    )
    cuisine_en: Mapped[Optional[str]] = mapped_column(String(100))
    cuisine_ja: Mapped[Optional[str]] = mapped_column(String(100))
    importance: Mapped[str] = mapped_column(
        String(20), nullable=False, default="regional",
        comment="signature / regional / common"
    )
    description_zh: Mapped[Optional[str]] = mapped_column(Text)
    # 推荐餐厅 entity_id 列表
    recommended_entities: Mapped[Optional[list]] = mapped_column(JSONB)
    source: Mapped[Optional[str]] = mapped_column(
        String(50), comment="human / guide_scraper / ai_extracted"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ── discovery_candidates ──────────────────────────────────────────────────────
class DiscoveryCandidate(Base):
    """攻略网站扫描出的候选地点（尚未入库为正式实体）"""

    __tablename__ = "discovery_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name_raw: Mapped[str] = mapped_column(
        String(300), nullable=False,
        comment="从攻略文本抓到的原始名称"
    )
    name_normalized: Mapped[Optional[str]] = mapped_column(String(300))

    # 出现情况
    source_count: Mapped[int] = mapped_column(
        Integer, default=1,
        comment="被几个不同来源提及"
    )
    sources: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='["letsgojp.cn", "gltjp.com"]'
    )
    mention_contexts: Mapped[Optional[list]] = mapped_column(
        JSONB, comment="每次提及的上下文片段"
    )

    # 关联到已有实体（如果有）
    matched_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="SET NULL"),
        nullable=True,
    )
    match_confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2), comment="0-1 匹配置信度"
    )

    entity_type_guess: Mapped[Optional[str]] = mapped_column(
        String(20), comment="poi / restaurant / hotel"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending",
        comment="pending / matched / new_entity / rejected"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
