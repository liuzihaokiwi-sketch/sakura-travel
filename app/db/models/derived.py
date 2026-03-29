from __future__ import annotations

from typing import Optional
"""
Layer C – Derived (计算结果层)
13 tables: entity_scores, itinerary_scores, candidate_sets, route_matrix_cache,
           planner_runs, itinerary_plans, itinerary_days, itinerary_items,
           route_templates, render_templates, export_jobs, export_assets, plan_artifacts
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


# ── entity_scores ─────────────────────────────────────────────────────────────
class EntityScore(Base):
    """实体评分（两阶段：系统分 0-100 + 编辑 Boost -8 ~ +8）"""

    __tablename__ = "entity_scores"

    score_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    score_profile: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="general / family / culture / foodie / ..."
    )
    base_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, comment="0-100")
    editorial_boost: Mapped[int] = mapped_column(SmallInteger, default=0, comment="-8 ~ +8")
    final_score: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False,
        comment="base_score + editorial_boost, clamped 0-100"
    )
    score_breakdown: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="各维度得分细节，可解释性用"
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── soft rules v1 新增字段 ──
    preview_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="预览分 0-100"
    )
    context_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="上下文分 0-100"
    )
    soft_rule_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="软规则分 0-100"
    )
    soft_rule_breakdown: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="软规则维度分详情"
    )
    segment_pack_id: Mapped[Optional[str]] = mapped_column(
        String(50), comment="使用的客群权重包"
    )
    stage_pack_id: Mapped[Optional[str]] = mapped_column(
        String(50), comment="使用的阶段权重包"
    )

    __table_args__ = (
        Index("ix_entity_scores_entity_profile", "entity_id", "score_profile"),
    )


# ── itinerary_plans ───────────────────────────────────────────────────────────
class ItineraryPlan(Base):
    """行程方案（每个 trip_request 可有多个版本）"""

    __tablename__ = "itinerary_plans"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    trip_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_requests.trip_request_id", ondelete="CASCADE"),
        nullable=False,
    )
    planner_run_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("planner_runs.planner_run_id", ondelete="SET NULL")
    )
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft",
        comment="draft / reviewed / published / archived"
    )
    plan_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="总天数、总预算、城市列表等汇总"
    )
    report_content: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="3层攻略报告正文: {layer1_overview, layer2_daily, layer3_appendix}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    days: Mapped[list["ItineraryDay"]] = relationship(
        "ItineraryDay", back_populates="plan", order_by="ItineraryDay.day_number"
    )
    scores: Mapped[list["ItineraryScore"]] = relationship(
        "ItineraryScore", back_populates="plan"
    )

    __table_args__ = (Index("ix_itinerary_plans_trip", "trip_request_id"),)


# ── itinerary_scores ──────────────────────────────────────────────────────────
class ItineraryScore(Base):
    """行程组合评分"""

    __tablename__ = "itinerary_scores"

    itinerary_score_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itinerary_plans.plan_id", ondelete="CASCADE"),
        nullable=False,
    )
    overall_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    diversity_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    efficiency_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    budget_fit_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    preference_match_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    score_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    plan: Mapped["ItineraryPlan"] = relationship("ItineraryPlan", back_populates="scores")

    __table_args__ = (Index("ix_itinerary_scores_plan", "plan_id"),)


# ── planner_runs ──────────────────────────────────────────────────────────────
class PlannerRun(Base):
    """规划器运行记录"""

    __tablename__ = "planner_runs"

    planner_run_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    trip_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_requests.trip_request_id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running",
        comment="running / completed / failed"
    )
    algorithm_version: Mapped[Optional[str]] = mapped_column(String(20))
    run_params: Mapped[Optional[dict]] = mapped_column(JSONB)
    run_log: Mapped[Optional[dict]] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_detail: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (Index("ix_planner_runs_trip", "trip_request_id"),)


# ── candidate_sets ────────────────────────────────────────────────────────────
class CandidateSet(Base):
    """候选实体集合"""

    __tablename__ = "candidate_sets"

    candidate_set_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    planner_run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("planner_runs.planner_run_id", ondelete="CASCADE"),
        nullable=False,
    )
    city_code: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    candidate_entity_ids: Mapped[list] = mapped_column(
        JSONB, nullable=False, comment="[uuid, ...] 按 final_score DESC"
    )
    filters_applied: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_candidate_sets_run", "planner_run_id"),)


# ── route_matrix_cache ────────────────────────────────────────────────────────
class RouteMatrixCache(Base):
    """两点间交通时间缓存"""

    __tablename__ = "route_matrix_cache"

    cache_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    origin_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    dest_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    travel_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="transit / walking / driving"
    )
    duration_min: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    distance_km: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_route_matrix_od_mode", "origin_entity_id", "dest_entity_id", "travel_mode"),
    )


# ── itinerary_days ────────────────────────────────────────────────────────────
class ItineraryDay(Base):
    """行程天"""

    __tablename__ = "itinerary_days"

    day_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itinerary_plans.plan_id", ondelete="CASCADE"),
        nullable=False,
    )
    day_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    date: Mapped[Optional[str]] = mapped_column(String(10), comment="YYYY-MM-DD")
    city_code: Mapped[str] = mapped_column(String(50), nullable=False)
    day_theme: Mapped[Optional[str]] = mapped_column(String(100))
    day_summary_zh: Mapped[Optional[str]] = mapped_column(Text)
    hotel_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entity_base.entity_id", ondelete="SET NULL")
    )
    estimated_cost_jpy: Mapped[Optional[int]] = mapped_column(Integer)

    plan: Mapped["ItineraryPlan"] = relationship("ItineraryPlan", back_populates="days")
    items: Mapped[list["ItineraryItem"]] = relationship(
        "ItineraryItem", back_populates="day", order_by="ItineraryItem.sort_order"
    )

    __table_args__ = (Index("ix_itinerary_days_plan", "plan_id"),)


# ── itinerary_items ───────────────────────────────────────────────────────────
class ItineraryItem(Base):
    """行程条目"""

    __tablename__ = "itinerary_items"

    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    day_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("itinerary_days.day_id", ondelete="CASCADE"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    item_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="poi / hotel / restaurant / transit / free_time / note"
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entity_base.entity_id", ondelete="SET NULL")
    )
    start_time: Mapped[Optional[str]] = mapped_column(String(5), comment="HH:MM")
    end_time: Mapped[Optional[str]] = mapped_column(String(5))
    duration_min: Mapped[Optional[int]] = mapped_column(SmallInteger)
    notes_zh: Mapped[Optional[str]] = mapped_column(Text)
    estimated_cost_jpy: Mapped[Optional[int]] = mapped_column(Integer)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── soft rules v1 新增字段 ──
    swap_candidates: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="替换候选列表"
    )

    day: Mapped["ItineraryDay"] = relationship("ItineraryDay", back_populates="items")

    __table_args__ = (Index("ix_itinerary_items_day", "day_id"),)


# ── route_templates ───────────────────────────────────────────────────────────
class RouteTemplate(Base):
    """路线模板（标准化线路，可直接生成 ¥20 引流款行程）"""

    __tablename__ = "route_templates"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    name_zh: Mapped[str] = mapped_column(String(200), nullable=False)
    city_code: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    theme: Mapped[Optional[str]] = mapped_column(String(50))
    sku_tier: Mapped[str] = mapped_column(
        String(10), nullable=False, default="standard",
        comment="standard (¥20) / premium (¥128+)"
    )
    template_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (Index("ix_route_templates_city_sku", "city_code", "sku_tier"),)


# ── render_templates ──────────────────────────────────────────────────────────
class RenderTemplate(Base):
    """渲染模板（HTML/CSS，magazine-style PDF/H5）"""

    __tablename__ = "render_templates"

    render_template_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    template_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    template_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="pdf / h5 / mini_program"
    )
    html_content: Mapped[str] = mapped_column(Text, nullable=False)
    css_content: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ── export_jobs ───────────────────────────────────────────────────────────────
class ExportJob(Base):
    """导出任务（PDF / H5 渲染）"""

    __tablename__ = "export_jobs"

    export_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itinerary_plans.plan_id", ondelete="CASCADE"),
        nullable=False,
    )
    render_template_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("render_templates.render_template_id", ondelete="SET NULL")
    )
    export_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="pdf / h5")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="pending / running / done / failed"
    )
    error_detail: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    assets: Mapped[list["ExportAsset"]] = relationship("ExportAsset", back_populates="job")

    __table_args__ = (
        Index("ix_export_jobs_plan", "plan_id"),
        Index("ix_export_jobs_status", "status"),
    )


# ── export_assets ─────────────────────────────────────────────────────────────
class ExportAsset(Base):
    """导出产物（PDF 文件 URL、H5 链接等）"""

    __tablename__ = "export_assets"

    asset_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    export_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("export_jobs.export_job_id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="pdf / h5 / cover_image"
    )
    storage_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    job: Mapped["ExportJob"] = relationship("ExportJob", back_populates="assets")

    __table_args__ = (Index("ix_export_assets_job", "export_job_id"),)


# ── plan_artifacts ────────────────────────────────────────────────────────────
class PlanArtifact(Base):
    """方案交付物（最终交付给用户的文件/链接）"""

    __tablename__ = "plan_artifacts"

    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itinerary_plans.plan_id", ondelete="CASCADE"),
        nullable=False,
    )
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.order_id", ondelete="SET NULL")
    )
    artifact_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="pdf / h5 / mini_program"
    )
    delivery_url: Mapped[Optional[str]] = mapped_column(Text)
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_plan_artifacts_plan", "plan_id"),)


# ── generation_decisions (T11) ────────────────────────────────────────────────
class GenerationDecision(Base):
    """
    T11: 生成决策记录表。

    每次生成行程时，记录关键决策节点的输入/输出，支持：
    - 重复生成检测（input_hash 相同且 is_current=True → 直接复用）
    - 决策回溯与 debug
    - A/B test 实验归因
    """

    __tablename__ = "generation_decisions"

    decision_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itinerary_plans.plan_id", ondelete="SET NULL"),
    )
    trip_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_requests.trip_request_id", ondelete="SET NULL"),
    )

    # T11 新增：画像哈希 + 当前有效版本标记
    input_hash: Mapped[Optional[str]] = mapped_column(
        String(64), comment="SHA-256(profile_json) — 用于判断是否需要重跑"
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否是当前有效决策版本，重跑时置 False"
    )

    # 决策阶段
    decision_stage: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="circle_selection / major_ranking / hotel_strategy / skeleton_build / ..."
    )
    decision_key: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="具体决策点，如 'selected_circle_id' / 'hotel_preset_id'"
    )
    decision_value: Mapped[Optional[str]] = mapped_column(
        Text, comment="决策结果值（字符串化）"
    )
    alternatives_considered: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="备选方案及评分 [{id, score, reason}, ...]"
    )
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, comment="选择理由（trace 摘要）")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_gen_decisions_plan", "plan_id"),
        Index("ix_gen_decisions_input_hash", "input_hash"),
        Index("ix_gen_decisions_trip_current", "trip_request_id", "is_current"),
    )


# ── booking_reminder_log ─────────────────────────────────────────────────────
class BookingReminderLog(Base):
    """
    预约提醒发送记录表。

    每条记录表示一次提醒（first / second / overdue），
    通过 (trip_request_id, entity_id, reminder_type) 唯一约束避免重复推送。
    """

    __tablename__ = "booking_reminder_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trip_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_requests.trip_request_id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itinerary_plans.plan_id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_name: Mapped[str] = mapped_column(String(200), nullable=False)
    booking_url: Mapped[Optional[str]] = mapped_column(Text)
    reminder_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="first / second / overdue"
    )
    visit_date: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="YYYY-MM-DD actual visit date"
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_booking_reminder_trip", "trip_request_id"),
        Index(
            "uq_booking_reminder_dedup",
            "trip_request_id", "entity_id", "reminder_type",
            unique=True,
        ),
    )
