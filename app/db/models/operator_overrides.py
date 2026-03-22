"""
app/db/models/operator_overrides.py — 运营干预表（L4-01）

支持运营人员在不改代码的情况下控制推荐行为。

输入：无（数据模型定义）
输出：OperatorOverride ORM 模型
依赖：app.db.base.Base
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class OperatorOverride(Base):
    """
    运营干预记录表。

    scope 层级：
      - entity   → 针对单个 POI/Hotel/Restaurant
      - cluster  → 针对一个 ActivityCluster
      - circle   → 针对整个城市圈
      - corridor → 针对走廊（如嵐山、哲学之道）
      - global   → 全局生效

    override_type：
      - block     — 屏蔽，不出现在任何行程
      - boost     — 加权，同等条件下优先推荐
      - demote    — 降权，同等条件下靠后
      - pin       — 钉住，对特定画像强制推荐
      - swap_lock — 锁定，不允许"换一个"替换
      - note      — 标注，在报告中追加说明文字
    """
    __tablename__ = "operator_overrides"

    override_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # ── 作用范围 ─────────────────────────────────────────────────────────────
    scope: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="entity / cluster / circle / corridor / global"
    )
    target_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True,
        comment="entity_id / cluster_id / circle_id / corridor_id; null=global"
    )

    # ── 干预类型 ─────────────────────────────────────────────────────────────
    override_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="block / boost / demote / pin / swap_lock / note"
    )

    # ── 干预参数 ─────────────────────────────────────────────────────────────
    weight_delta: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="boost/demote 时的分数增减，如 +10 / -20"
    )
    note_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="note 类型的说明文字，追加到报告中"
    )
    pin_conditions: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment='pin 时的匹配条件，如 {"party_type":"couple","season":"spring"}'
    )

    # ── 生效时间 ─────────────────────────────────────────────────────────────
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(),
        comment="生效开始时间"
    )
    effective_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="结束时间，null = 永久生效"
    )

    # ── 原因 ─────────────────────────────────────────────────────────────────
    reason_code: Mapped[str] = mapped_column(
        String(64), nullable=False, default="manual",
        comment="seasonal / maintenance / quality_issue / promotion / safety / manual"
    )
    reason_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="人工说明"
    )

    # ── 操作者 ────────────────────────────────────────────────────────────────
    created_by: Mapped[str] = mapped_column(
        String(128), nullable=False, default="system",
        comment="操作者（admin user email 或 'system'）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="软删除标志"
    )

    # ── 时间戳 ────────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    # ── 索引 ──────────────────────────────────────────────────────────────────
    __table_args__ = (
        Index(
            "ix_operator_overrides_scope_target_active",
            "scope", "target_id", "is_active",
        ),
        Index(
            "ix_operator_overrides_type_active",
            "override_type", "is_active",
        ),
        Index(
            "ix_operator_overrides_effective_until",
            "effective_until",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OperatorOverride id={self.override_id} "
            f"type={self.override_type} scope={self.scope} target={self.target_id}>"
        )

    def is_currently_active(self, now: Optional[datetime] = None) -> bool:
        """检查此干预当前是否生效（结合 is_active + 时间窗）"""
        if not self.is_active:
            return False
        from datetime import timezone as tz
        ts = now or datetime.now(tz.utc)
        if self.effective_from and ts < self.effective_from:
            return False
        if self.effective_until and ts > self.effective_until:
            return False
        return True
