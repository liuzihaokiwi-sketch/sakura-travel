from __future__ import annotations

from typing import Optional

"""
Guide Fragments Layer – 片段攻略库
6 tables: guide_fragments, fragment_entities, fragment_embeddings,
          fragment_compatibility, fragment_usage_stats, fragment_distillation_queue

对应文档 §11-13：经过验证的攻略片段（route/decision/experience 等）
可被复用到新行程中，减少 AI 重复生成，提高质量一致性。

片段类型：
  - route:      路线片段（如"东京经典 3 日路线第 2 天"）
  - decision:   决策片段（如"为什么选这个酒店而不是那个"）
  - experience: 体验片段（如"浅草寺早起避人攻略"）
  - logistics:  后勤片段（如"关西机场到京都的 3 种方式对比"）
  - dining:     餐饮片段（如"东京站周边预算晚餐推荐"）
  - tips:       实用贴士（如"东京地铁换乘避坑指南"）
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ── guide_fragments ───────────────────────────────────────────────────────────
class GuideFragment(Base):
    """攻略片段主表 — 经过验证的可复用内容块"""

    __tablename__ = "guide_fragments"

    fragment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # ── 片段分类 ──
    fragment_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="route / decision / experience / logistics / dining / tips"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="片段标题（如'东京经典Day2：浅草→上野→秋叶原'）"
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text, comment="片段摘要（用于检索展示，≤200字）"
    )

    # ── 适用范围（metadata filter 用） ──
    city_code: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="tokyo / kyoto / osaka / hokkaido / ..."
    )
    area_code: Mapped[Optional[str]] = mapped_column(
        String(30), comment="shinjuku / asakusa / gion / namba / ..."
    )
    theme_families: Mapped[Optional[list]] = mapped_column(
        JSONB,
        comment='["classic_first", "couple_aesthetic"] — 适用的主题风格'
    )
    party_types: Mapped[Optional[list]] = mapped_column(
        JSONB,
        comment='["couple", "solo", "friends"] — 适用的同行类型'
    )
    budget_levels: Mapped[Optional[list]] = mapped_column(
        JSONB,
        comment='["mid", "premium"] — 适用的预算档位'
    )
    season_tags: Mapped[Optional[list]] = mapped_column(
        JSONB,
        comment='["spring", "cherry_blossom", "all_year"] — 适用季节'
    )
    day_index_hint: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        comment="建议放在行程的第几天（0=到达日, null=不限）"
    )
    duration_slot: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="morning / afternoon / evening / full_day / half_day"
    )

    # ── 片段正文 ──
    body_skeleton: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="片段的骨架结构 JSON（实体列表 + 时间轴 + 交通 + 注意事项）"
    )
    body_prose: Mapped[Optional[str]] = mapped_column(
        Text, comment="润色后的可读文案（用于直接展示或 AI 微调）"
    )
    body_html: Mapped[Optional[str]] = mapped_column(
        Text, comment="渲染好的 HTML 片段（可直接嵌入报告）"
    )

    # ── 质量与来源 ──
    quality_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=5.0,
        comment="片段质量分 0-10（基于用户反馈 + 人工评审）"
    )
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="manual",
        comment="manual / ai_generated / distilled / imported"
    )
    source_trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        comment="从哪个已交付行程中提炼出来的"
    )
    author: Mapped[Optional[str]] = mapped_column(
        String(100), comment="编辑/审核人"
    )
    version: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1,
        comment="片段版本号（每次修改+1）"
    )

    # ── 时效与适用性（对齐 template_asset_system_spec） ──
    time_sensitivity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="timeless",
        comment="timeless / soft_ttl / hard_ttl / snapshot_bound"
    )
    ttl_days: Mapped[Optional[int]] = mapped_column(
        Integer, comment="soft/hard TTL 天数"
    )
    valid_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="生效起始时间"
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="失效时间"
    )
    refresh_strategy: Mapped[str] = mapped_column(
        String(20), nullable=False, default="none",
        comment="none / downgrade / block / snapshot_refill"
    )

    # ── 状态管理 ──
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft",
        comment="draft / active / deprecated / archived"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── 时间戳 ──
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="最近一次被复用到行程中的时间"
    )

    # ── relationships ──
    entities: Mapped[list["FragmentEntity"]] = relationship(
        "FragmentEntity", back_populates="fragment", cascade="all, delete-orphan"
    )
    embeddings: Mapped[list["FragmentEmbedding"]] = relationship(
        "FragmentEmbedding", back_populates="fragment", cascade="all, delete-orphan"
    )
    usage_stats: Mapped[Optional["FragmentUsageStats"]] = relationship(
        "FragmentUsageStats", back_populates="fragment", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_fragments_city_type", "city_code", "fragment_type"),
        Index("ix_fragments_city_theme", "city_code"),
        Index("ix_fragments_status", "status", "is_active"),
        Index("ix_fragments_quality", "quality_score"),
    )


# ── fragment_entities ─────────────────────────────────────────────────────────
class FragmentEntity(Base):
    """片段引用的实体（POI/餐厅/酒店/活动）"""

    __tablename__ = "fragment_entities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fragment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guide_fragments.fragment_id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_role: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="primary / secondary / alternative / nearby"
    )
    slot_order: Mapped[Optional[int]] = mapped_column(
        SmallInteger, comment="在片段内的排列顺序"
    )
    is_replaceable: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="该实体是否可被同类替换（如餐厅可换，但标志性景点不可换）"
    )

    fragment: Mapped["GuideFragment"] = relationship("GuideFragment", back_populates="entities")

    __table_args__ = (
        Index("ix_fragment_entities_fragment", "fragment_id"),
        Index("ix_fragment_entities_entity", "entity_id"),
        UniqueConstraint("fragment_id", "entity_id", "entity_role", name="uq_frag_entity_role"),
    )


# ── fragment_embeddings ───────────────────────────────────────────────────────
class FragmentEmbedding(Base):
    """片段的向量嵌入（用于语义检索）"""

    __tablename__ = "fragment_embeddings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fragment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guide_fragments.fragment_id", ondelete="CASCADE"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="text-embedding-3-small / text-embedding-3-large / bge-m3"
    )
    embedding_dim: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, comment="向量维度 (1536/3072/1024)"
    )
    # 向量存为 JSONB（float list），后续可改为 pgvector
    embedding_vector: Mapped[list] = mapped_column(
        JSONB, nullable=False,
        comment="float[] — 嵌入向量（后续迁移 pgvector 时改为 vector 类型）"
    )
    source_text: Mapped[Optional[str]] = mapped_column(
        Text, comment="生成嵌入时使用的文本（title + summary + body_skeleton 摘要）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    fragment: Mapped["GuideFragment"] = relationship("GuideFragment", back_populates="embeddings")

    __table_args__ = (
        Index("ix_fragment_embeddings_fragment", "fragment_id"),
        UniqueConstraint("fragment_id", "model_name", name="uq_frag_embed_model"),
    )


# ── fragment_compatibility ────────────────────────────────────────────────────
class FragmentCompatibility(Base):
    """片段间兼容性（同城市不同片段能否拼在一起）"""

    __tablename__ = "fragment_compatibility"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fragment_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guide_fragments.fragment_id", ondelete="CASCADE"),
        nullable=False,
    )
    fragment_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guide_fragments.fragment_id", ondelete="CASCADE"),
        nullable=False,
    )
    compatibility_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="compatible / conflict / sequential_only / same_day_ok"
    )
    compatibility_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5,
        comment="兼容度 0-1（0=完全冲突, 1=完美搭配）"
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(200), comment="兼容/冲突原因说明"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_frag_compat_a", "fragment_a_id"),
        Index("ix_frag_compat_b", "fragment_b_id"),
        UniqueConstraint("fragment_a_id", "fragment_b_id", name="uq_frag_compat_pair"),
    )


# ── fragment_usage_stats ──────────────────────────────────────────────────────
class FragmentUsageStats(Base):
    """片段使用统计（追踪复用效果）"""

    __tablename__ = "fragment_usage_stats"

    fragment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guide_fragments.fragment_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # ── 使用计数 ──
    total_hits: Mapped[int] = mapped_column(Integer, default=0, comment="总命中次数")
    total_adopted: Mapped[int] = mapped_column(Integer, default=0, comment="被采纳次数")
    total_rejected: Mapped[int] = mapped_column(Integer, default=0, comment="被拒绝次数")
    total_replaced_by_human: Mapped[int] = mapped_column(
        Integer, default=0, comment="被人工替换次数"
    )

    # ── 反馈分 ──
    avg_user_rating: Mapped[Optional[float]] = mapped_column(
        Float, comment="用户平均反馈分 (1-5)"
    )
    positive_feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    negative_feedback_count: Mapped[int] = mapped_column(Integer, default=0)

    # ── 效果指标 ──
    conversion_contribution: Mapped[Optional[float]] = mapped_column(
        Float, comment="对成交的贡献度估计 0-1（基于是否在样片中展示过+成交）"
    )

    last_hit_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    fragment: Mapped["GuideFragment"] = relationship("GuideFragment", back_populates="usage_stats")


# ── fragment_distillation_queue ───────────────────────────────────────────────
class FragmentDistillationQueue(Base):
    """片段蒸馏队列 — 从已交付行程中提炼新片段的工作队列"""

    __tablename__ = "fragment_distillation_queue"

    queue_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # ── 来源 ──
    source_trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
        comment="来源行程 ID（trip_request_id 或 plan_id）"
    )
    source_day_index: Mapped[Optional[int]] = mapped_column(
        SmallInteger, comment="来源行程的第几天"
    )
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="auto_detect / user_feedback / ops_review"
    )

    # ── 蒸馏内容 ──
    proposed_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="route / decision / experience / logistics / dining / tips"
    )
    proposed_title: Mapped[Optional[str]] = mapped_column(String(200))
    proposed_body: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="自动提取的骨架草稿"
    )
    proposed_city_code: Mapped[str] = mapped_column(String(30), nullable=False)

    # ── 审核状态 ──
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="pending / approved / rejected / merged"
    )
    reviewer: Mapped[Optional[str]] = mapped_column(String(100))
    review_note: Mapped[Optional[str]] = mapped_column(Text)
    merged_fragment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        comment="审核通过后合并到的 fragment_id"
    )

    # ── 反馈来源 ──
    user_rating: Mapped[Optional[int]] = mapped_column(
        SmallInteger, comment="用户评分 1-5"
    )
    user_feedback_text: Mapped[Optional[str]] = mapped_column(Text)
    feedback_collected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_distill_queue_status", "status"),
        Index("ix_distill_queue_city", "proposed_city_code"),
        Index("ix_distill_queue_source", "source_trip_id"),
    )
