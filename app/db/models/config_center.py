"""
config_center.py — 运营配置中心 ORM 模型

包含 5 张表：
  config_packs            配置包主信息（一个包 = 一套权重+阈值+开关）
  config_pack_versions    每次保存的具体 JSON 内容（不可变快照）
  config_scopes           作用域绑定（global/circle/segment/plan_override）
  config_preview_runs     预览对比结果
  config_release_records  发布、灰度、回滚记录
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer,
    String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ── config_packs ──────────────────────────────────────────────────────────────

class ConfigPack(Base):
    """
    配置包主信息。
    一个 pack 代表一套运营配置（权重+阈值+开关），可多版本迭代。
    """
    __tablename__ = "config_packs"

    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    pack_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="weights",
        comment="weights / thresholds / switches / hard_rules / segment / composite"
    )
    # 当前激活版本号（指向 config_pack_versions.version_no）
    active_version_no: Mapped[Optional[int]] = mapped_column(Integer)
    # 当前状态
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft",
        comment="draft / pending_review / approved / canary / active / rolled_back / archived"
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    versions: Mapped[list["ConfigPackVersion"]] = relationship(
        back_populates="pack", cascade="all, delete-orphan"
    )
    scopes: Mapped[list["ConfigScope"]] = relationship(
        back_populates="pack", cascade="all, delete-orphan"
    )
    release_records: Mapped[list["ConfigReleaseRecord"]] = relationship(
        back_populates="pack", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_config_packs_status", "status"),
        Index("ix_config_packs_pack_type", "pack_type"),
    )


# ── config_pack_versions ──────────────────────────────────────────────────────

class ConfigPackVersion(Base):
    """
    配置包的版本快照（不可变）。
    每次"保存草稿"或"发布"都生成一条新记录。
    """
    __tablename__ = "config_pack_versions"

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config_packs.pack_id", ondelete="CASCADE"),
        nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="从 1 开始自增")
    # 核心配置内容 JSON
    weights: Mapped[Optional[dict]] = mapped_column(JSONB, comment="基础权重键值对")
    thresholds: Mapped[Optional[dict]] = mapped_column(JSONB, comment="阈值与上限键值对")
    switches: Mapped[Optional[dict]] = mapped_column(JSONB, comment="规则开关键值对")
    hard_rules: Mapped[Optional[list]] = mapped_column(JSONB, comment="硬规则条目列表")
    # 变更说明
    change_summary: Mapped[Optional[str]] = mapped_column(Text)
    changed_fields: Mapped[Optional[list]] = mapped_column(JSONB, comment="变更的字段名列表")
    reason: Mapped[Optional[str]] = mapped_column(Text)
    # 审批信息
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    preview_run_ids: Mapped[Optional[list]] = mapped_column(JSONB, comment="关联的预览运行 ID 列表")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    pack: Mapped["ConfigPack"] = relationship(back_populates="versions")

    __table_args__ = (
        Index("ix_cpv_pack_version", "pack_id", "version_no", unique=True),
    )


# ── config_scopes ─────────────────────────────────────────────────────────────

class ConfigScope(Base):
    """
    配置作用域绑定。
    一个 pack 可以绑定到多个作用域：global / circle / segment / plan_override。
    优先级：plan_override > segment > circle > global
    """
    __tablename__ = "config_scopes"

    scope_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config_packs.pack_id", ondelete="CASCADE"),
        nullable=False
    )
    scope_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="global / circle / segment / plan_override"
    )
    scope_value: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="scope_type=global 时为 null；其他为 circle_id / segment_name / plan_id"
    )
    # 灰度比例（0.0~1.0），1.0 = 全量
    rollout_pct: Mapped[float] = mapped_column(default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    pack: Mapped["ConfigPack"] = relationship(back_populates="scopes")

    __table_args__ = (
        Index("ix_config_scopes_type_value", "scope_type", "scope_value"),
        Index("ix_config_scopes_active", "is_active"),
    )


# ── config_preview_runs ───────────────────────────────────────────────────────

class ConfigPreviewRun(Base):
    """
    预览对比运行记录。
    存储"旧配置 vs 新配置"对某一订单/eval case 的对比结果。
    """
    __tablename__ = "config_preview_runs"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config_packs.pack_id", ondelete="CASCADE"),
        nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    # 对比对象
    subject_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="order / eval_case"
    )
    subject_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # 对比结果快照
    baseline_result: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="旧配置运行结果摘要"
    )
    candidate_result: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="新配置运行结果摘要"
    )
    diff_summary: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment="差异摘要：major_changed / hotel_changed / score_delta / risk_delta"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="pending / running / done / failed"
    )
    triggered_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_cpr_pack_id", "pack_id"),
        Index("ix_cpr_subject", "subject_type", "subject_id"),
        Index("ix_cpr_status", "status"),
    )


# ── config_release_records ────────────────────────────────────────────────────

class ConfigReleaseRecord(Base):
    """
    发布、灰度、回滚的完整历史记录。
    每次状态流转都生成一条记录（不覆盖）。
    """
    __tablename__ = "config_release_records"

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config_packs.pack_id", ondelete="CASCADE"),
        nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="draft_saved / submitted_review / approved / rejected / "
                "canary_start / canary_promote / activated / rolled_back / archived"
    )
    # 回滚时记录被恢复到的版本
    rollback_to_version_no: Mapped[Optional[int]] = mapped_column(Integer)
    rollback_reason: Mapped[Optional[str]] = mapped_column(Text)
    # 灰度信息
    rollout_scope: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="灰度作用域快照：{type, value, pct}"
    )
    preview_run_ids: Mapped[Optional[list]] = mapped_column(JSONB)
    # 操作人
    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    pack: Mapped["ConfigPack"] = relationship(back_populates="release_records")

    __table_args__ = (
        Index("ix_crr_pack_id", "pack_id"),
        Index("ix_crr_action", "action"),
        Index("ix_crr_created_at", "created_at"),
    )
