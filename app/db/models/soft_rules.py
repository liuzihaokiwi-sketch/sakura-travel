from __future__ import annotations

from typing import Optional

"""
Soft Rules Layer – 软规则评分系统 + 混入的其他层级表

核心软规则表（正确归属此文件）：
  entity_soft_scores, editorial_seed_overrides, soft_rule_explanations,
  segment_weight_packs, audience_fit, soft_rule_feedback_log

已废弃（DEPRECATED，无代码读写）：
  preview_trigger_scores, swap_candidate_soft_scores,
  stage_weight_packs, product_config, feature_flags, user_events

归属错误（历史原因留在此文件，逻辑上应属其他层）：
  entity_operating_facts → 应属 catalog 层（营业事实是硬数据）
  area_profiles → 应属 city_circles 层（区域画像）
  transport_links → 应属 corridors 层（交通连接）
  timeslot_rules → 应合并到 temporal 层 entity_temporal_profiles
  seasonal_events → 应属 temporal 层（季节活动）
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
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


# ── entity_soft_scores ─────────────────────────────────────────────────────────
class EntitySoftScore(Base):
    """实体级12维度软规则分"""

    __tablename__ = "entity_soft_scores"

    entity_type: Mapped[str] = mapped_column(
        String(20), primary_key=True, comment="poi / hotel / restaurant"
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        primary_key=True,
    )
    # 12个软规则维度分，每个0-10
    emotional_value: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="情绪价值/氛围感 0-10"
    )
    shareability: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="分享感/出片回报 0-10"
    )
    relaxation_feel: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="松弛感/不赶感 0-10"
    )
    memory_point: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="记忆点强度 0-10"
    )
    localness: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="当地感/不模板感 0-10"
    )
    smoothness: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="顺滑感/少折腾感 0-10"
    )
    food_certainty: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="餐饮确定感 0-10"
    )
    night_completion: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="夜间完成度 0-10"
    )
    recovery_friendliness: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="恢复友好度 0-10"
    )
    weather_resilience_soft: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="雨天韧性 0-10"
    )
    professional_judgement_feel: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="专业判断感 0-10"
    )
    preview_conversion_power: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), comment="免费Day1杀伤力 0-10"
    )
    score_sources: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="每个维度的来源 ai/stat/manual"
    )
    score_version: Mapped[Optional[str]] = mapped_column(
        String(50), comment="评分引擎版本号"
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index(
            "ix_entity_soft_scores_type_calculated",
            "entity_type",
            "calculated_at",
        ),
    )


# ── editorial_seed_overrides ───────────────────────────────────────────────────
class EditorialSeedOverride(Base):
    """人工修正种子值"""

    __tablename__ = "editorial_seed_overrides"

    entity_type: Mapped[str] = mapped_column(
        String(20), primary_key=True, comment="poi / hotel / restaurant"
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        primary_key=True,
    )
    dimension_id: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment="维度标识，如 emotional_value"
    )
    override_value: Mapped[float] = mapped_column(
        Numeric(3, 1), nullable=False, comment="0-10"
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, comment="修正理由")
    editor_id: Mapped[Optional[str]] = mapped_column(String(100), comment="编辑ID")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ── soft_rule_explanations ─────────────────────────────────────────────────────
class SoftRuleExplanation(Base):
    """每次评分的可解释性记录"""

    __tablename__ = "soft_rule_explanations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    dimension_id: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False, comment="0-10")
    explanation: Mapped[Optional[str]] = mapped_column(Text, comment="一句话理由")
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="ai / stat / manual"
    )
    score_version: Mapped[Optional[str]] = mapped_column(
        String(50), comment="评分引擎版本号"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index(
            "ix_soft_rule_explanations_entity_dimension",
            "entity_type",
            "entity_id",
            "dimension_id",
        ),
    )


# ── segment_weight_packs ───────────────────────────────────────────────────────
class SegmentWeightPack(Base):
    """客群权重包"""

    __tablename__ = "segment_weight_packs"

    pack_id: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment="客群标识，如 couple"
    )
    name_cn: Mapped[str] = mapped_column(String(100), nullable=False, comment="中文名")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="核心目标描述")
    weights: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="12维度权重"
    )
    top_dimensions: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="最在意的维度列表"
    )
    low_dimensions: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="不太在意的维度列表"
    )
    day1_trigger: Mapped[Optional[str]] = mapped_column(
        Text, comment="Day1敏感触发点"
    )
    repurchase_trigger: Mapped[Optional[str]] = mapped_column(
        Text, comment="复购触发点"
    )
    tuning_sensitivity: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="微调敏感模块"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ── stage_weight_packs ─────────────────────────────────────────────────────────
class StageWeightPack(Base):
    """DEPRECATED: 阶段权重包 — 零读写，阶段区分逻辑未实现"""

    __tablename__ = "stage_weight_packs"

    pack_id: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment="阶段标识，如 preview_day1"
    )
    name_cn: Mapped[str] = mapped_column(String(100), nullable=False, comment="中文名")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="核心目标描述")
    weights: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="12维度权重"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ── soft_rule_feedback_log ─────────────────────────────────────────────────────
class SoftRuleFeedbackLog(Base):
    """软规则反馈日志"""

    __tablename__ = "soft_rule_feedback_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    feedback_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="反馈类型，如 preview_view / swap_triggered"
    )
    feedback_value: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="反馈值，如停留秒数/满意度分"
    )
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, comment="元数据")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index(
            "ix_soft_rule_feedback_log_entity_type",
            "entity_id",
            "feedback_type",
        ),
    )


# ── area_profiles ──────────────────────────────────────────────────────────────
class AreaProfile(Base):
    """区域画像"""

    __tablename__ = "area_profiles"

    area_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    city_code: Mapped[str] = mapped_column(String(50), nullable=False)
    area_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="商业/住宅/观光/美食"
    )
    best_time_slots: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="最佳时段列表"
    )
    peak_months: Mapped[Optional[dict]] = mapped_column(JSONB, comment="旺季月份")
    crowd_pattern_json: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="人流模式"
    )
    nearest_station: Mapped[Optional[str]] = mapped_column(
        String(100), comment="最近车站"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "ix_area_profiles_city_code",
            "city_code",
        ),
    )


# ── timeslot_rules ─────────────────────────────────────────────────────────────
class TimeslotRule(Base):
    """时段规则"""

    __tablename__ = "timeslot_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    valid_slots: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="有效时段 morning/afternoon/evening/night"
    )
    best_slot: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="最佳时段"
    )
    closed_slots: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="关闭时段列表"
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, comment="原因说明")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "ix_timeslot_rules_entity_id",
            "entity_id",
        ),
    )


# ── seasonal_events ────────────────────────────────────────────────────────────
class SeasonalEvent(Base):
    """季节活动"""

    __tablename__ = "seasonal_events"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    city_code: Mapped[str] = mapped_column(String(50), nullable=False)
    area_code: Mapped[Optional[str]] = mapped_column(String(50))
    event_name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    crowd_impact: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="high/medium/low"
    )
    booking_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    best_timing_tips: Mapped[Optional[str]] = mapped_column(Text, comment="最佳时机提示")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "ix_seasonal_events_city_date",
            "city_code",
            "start_date",
            "end_date",
        ),
    )


# ── transport_links ────────────────────────────────────────────────────────────
class TransportLink(Base):
    """交通连接"""

    __tablename__ = "transport_links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    origin_area: Mapped[str] = mapped_column(String(50), nullable=False)
    dest_area: Mapped[str] = mapped_column(String(50), nullable=False)
    mode: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="交通方式 train/bus/taxi/walk"
    )
    typical_duration_min: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="典型时长（分钟）"
    )
    cost_jpy: Mapped[Optional[int]] = mapped_column(Integer, comment="费用（日元）")
    rush_hour_penalty_min: Mapped[Optional[int]] = mapped_column(
        Integer, comment="高峰时段额外时长（分钟）"
    )
    last_train_time: Mapped[Optional[str]] = mapped_column(
        String(10), comment="末班车时间 HH:MM"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "ix_transport_links_origin_dest",
            "origin_area",
            "dest_area",
        ),
    )


# ── audience_fit ───────────────────────────────────────────────────────────────
class AudienceFit(Base):
    """客群适配"""

    __tablename__ = "audience_fit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    audience_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="couple/family/solo/senior/group"
    )
    fit_score: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, comment="适配分 1-5"
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, comment="适配理由")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "ix_audience_fit_entity_audience",
            "entity_id",
            "audience_type",
        ),
    )


# ── entity_operating_facts ─────────────────────────────────────────────────────
class EntityOperatingFact(Base):
    """营业事实"""

    __tablename__ = "entity_operating_facts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    day_of_week: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="星期几 mon/tue/wed/thu/fri/sat/sun"
    )
    open_time: Mapped[Optional[str]] = mapped_column(String(10), comment="开门时间 HH:MM")
    close_time: Mapped[Optional[str]] = mapped_column(String(10), comment="关门时间 HH:MM")
    last_entry_time: Mapped[Optional[str]] = mapped_column(
        String(10), comment="最后入场时间 HH:MM"
    )
    holiday_schedule: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="节假日安排"
    )
    reservation_window_days: Mapped[Optional[int]] = mapped_column(
        Integer, comment="预订提前天数"
    )
    typical_wait_min: Mapped[Optional[int]] = mapped_column(
        Integer, comment="典型等待时间（分钟）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "ix_entity_operating_facts_entity_day",
            "entity_id",
            "day_of_week",
        ),
    )


# product_config / feature_flags / user_events — DEPRECATED model classes removed.
# DB tables are dropped via migration 20260330_100000_drop_deprecated_tables.
# If you need these tables back, restore from git history.