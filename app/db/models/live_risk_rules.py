"""
app/db/models/live_risk_rules.py — 实时风险规则表（L4-03）

存储风险监控规则，供 LiveRiskMonitor 引擎消费。
不接外部 API，只建骨架。

输入：无（数据模型定义）
输出：LiveRiskRule ORM 模型
依赖：app.db.base.Base
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class LiveRiskRule(Base):
    """
    实时风险监控规则表。

    rule_code 命名规范：
      LR_WEATHER_001   — 天气相关
      LR_CLOSURE_001   — 场所关闭
      LR_TRAIN_001     — 交通延误/停运
      LR_CROWD_001     — 人流拥挤预警
      LR_EVENT_001     — 节事冲突

    trigger_window：
      T-72h  — 出行前 72 小时
      T-24h  — 出行前 24 小时
      T-6h   — 出行前 6 小时
      T-0h   — 当天实时

    action_type：
      badge              — 在行程页面显示警示 badge
      suggest_alternative — 提示替代方案
      force_recompute    — 触发重新规划
      notify_user        — 推送通知给用户
      info_only          — 仅记录，不主动展示
    """
    __tablename__ = "live_risk_rules"

    rule_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    rule_code: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True,
        comment="如 LR_WEATHER_001"
    )

    # ── 触发条件 ──────────────────────────────────────────────────────────────
    risk_source: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="weather / transport / venue / event"
    )
    trigger_window: Mapped[str] = mapped_column(
        String(16), nullable=False, default="T-24h",
        comment="T-72h / T-24h / T-6h / T-0h"
    )
    trigger_condition: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment='如 {"type":"rain_probability_gt","threshold":0.7}'
    )

    # ── 动作 ──────────────────────────────────────────────────────────────────
    action_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="badge / suggest_alternative / force_recompute / notify_user / info_only"
    )
    action_params: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment='如 {"badge_text":"⚠️可能下雨","fallback_entity_id":"xxx"}'
    )

    # ── 作用范围 ──────────────────────────────────────────────────────────────
    applies_to_entity_types: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment='如 ["poi","activity"]'
    )
    applies_to_corridors: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True,
        comment='如 ["kyo_arashiyama"]；null = 全走廊'
    )

    # ── 元数据 ────────────────────────────────────────────────────────────────
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=50,
        comment="优先级（数值越大越先执行）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_live_risk_rules_source_active", "risk_source", "is_active"),
        Index("ix_live_risk_rules_window_active", "trigger_window", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<LiveRiskRule {self.rule_code} source={self.risk_source} "
            f"action={self.action_type}>"
        )
