from __future__ import annotations

from typing import Optional
"""
Business Layer – 用户、订单、行程请求
8 tables: users, product_sku, orders, trip_requests, trip_profiles,
          trip_versions, review_jobs, review_actions
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


# ── users ─────────────────────────────────────────────────────────────────────
class User(Base):
    """用户表（Phase 2 接入认证后完善）"""

    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    # 微信/手机号登录，暂用 openid 作为唯一标识
    openid: Mapped[Optional[str]] = mapped_column(String(200), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")

    __table_args__ = (Index("ix_users_openid", "openid"),)


# ── product_sku ───────────────────────────────────────────────────────────────
class ProductSku(Base):
    """产品 SKU 定义（¥20 引流款 / ¥128 标准个性化 / ¥298 主题深度游等）"""

    __tablename__ = "product_sku"

    sku_id: Mapped[str] = mapped_column(String(50), primary_key=True, comment="如 basic_20 / standard_128")
    sku_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_cny: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    sku_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="template / personalized / themed"
    )
    features: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="{'has_restaurant': bool, 'has_hotel_filter': bool, 'custom_input': bool, ...}"
    )
    max_days: Mapped[Optional[int]] = mapped_column(SmallInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="sku")


# ── orders ────────────────────────────────────────────────────────────────────
class Order(Base):
    """订单表"""

    __tablename__ = "orders"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL")
    )
    sku_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("product_sku.sku_id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="new",
        comment="new / sample_viewed / paid / detail_filling / detail_submitted / validating / needs_fix / validated / generating / done / delivered / cancelled / refunded"
    )
    amount_cny: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    payment_channel: Mapped[Optional[str]] = mapped_column(
        String(30), comment="wechat / alipay / stripe"
    )
    payment_tx_id: Mapped[Optional[str]] = mapped_column(String(200), comment="支付流水号")
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="orders")
    sku: Mapped["ProductSku"] = relationship("ProductSku", back_populates="orders")

    __table_args__ = (
        Index("ix_orders_user", "user_id"),
        Index("ix_orders_status", "status"),
    )


# ── trip_requests ─────────────────────────────────────────────────────────────
class TripRequest(Base):
    """用户行程请求（核心入口）"""

    __tablename__ = "trip_requests"

    trip_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL")
    )
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.order_id", ondelete="SET NULL")
    )
    sku_id: Mapped[Optional[str]] = mapped_column(String(50))

    # 用户原始输入（Phase 2 支持自然语言，Phase 0 用结构化表单）
    raw_input: Mapped[dict] = mapped_column(JSONB, nullable=False, comment="用户原始提交的表单数据")

    # 处理状态
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="new",
        comment="new / sample_viewed / paid / detail_filling / detail_submitted / validating / needs_fix / validated / generating / done / delivered / cancelled / refunded"
    )
    last_job_error: Mapped[Optional[str]] = mapped_column(Text, comment="最后一次 job 报错摘要")
    retry_count: Mapped[int] = mapped_column(SmallInteger, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    profile: Mapped[Optional["TripProfile"]] = relationship(
        "TripProfile", back_populates="trip_request", uselist=False
    )

    __table_args__ = (
        Index("ix_trip_requests_user", "user_id"),
        Index("ix_trip_requests_status", "status"),
    )


# ── trip_profiles ─────────────────────────────────────────────────────────────
class TripProfile(Base):
    """标准化行程画像（normalize_trip_profile job 输出结果）"""

    __tablename__ = "trip_profiles"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    trip_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_requests.trip_request_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # 标准化旅行信息
    cities: Mapped[list] = mapped_column(
        JSONB, nullable=False, comment="[{'city_code': 'tokyo', 'nights': 3}, ...]"
    )
    travel_dates: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="{'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}"
    )
    duration_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # 旅行者画像
    party_type: Mapped[Optional[str]] = mapped_column(
        String(30), comment="solo / couple / family_child / family_no_child / group / senior"
    )
    party_size: Mapped[Optional[int]] = mapped_column(SmallInteger)
    budget_level: Mapped[Optional[str]] = mapped_column(
        String(10), comment="budget / mid / premium / luxury"
    )
    budget_total_cny: Mapped[Optional[int]] = mapped_column(Integer)

    # 偏好标签（由推导规则 + 用户输入合并）
    must_have_tags: Mapped[list] = mapped_column(JSONB, default=list)
    nice_to_have_tags: Mapped[list] = mapped_column(JSONB, default=list)
    avoid_tags: Mapped[list] = mapped_column(JSONB, default=list)

    # 预算偏向（用户 Quiz 中选择）
    budget_focus: Mapped[Optional[str]] = mapped_column(
        String(30),
        comment="better_stay / better_food / better_experience / balanced / best_value",
    )

    # 特殊需求
    special_requirements: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="无障碍需求、饮食限制等"
    )

    normalized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    trip_request: Mapped["TripRequest"] = relationship(
        "TripRequest", back_populates="profile"
    )

    __table_args__ = (Index("ix_trip_profiles_request", "trip_request_id"),)


# ── trip_versions ─────────────────────────────────────────────────────────────
class TripVersion(Base):
    """行程版本历史（用户修改 / 重新生成时保留历史）"""

    __tablename__ = "trip_versions"

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    trip_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_requests.trip_request_id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("itinerary_plans.plan_id", ondelete="SET NULL")
    )
    version_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(
        String(200), comment="initial / user_edit / re_plan / ..."
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (Index("ix_trip_versions_request", "trip_request_id"),)


# ── review_jobs ───────────────────────────────────────────────────────────────
class ReviewJob(Base):
    """人工审核任务（编辑审核行程 / 实体标注 / 渲染校对）"""

    __tablename__ = "review_jobs"

    review_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    job_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="plan_review / entity_label / render_check / ..."
    )
    target_id: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="被审核对象的 ID（plan_id / entity_id 等）"
    )
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="pending / in_review / approved / rejected / needs_revision"
    )
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), comment="审核员 ID")
    priority: Mapped[int] = mapped_column(SmallInteger, default=5, comment="1-10，越大越高")
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    actions: Mapped[list["ReviewAction"]] = relationship(
        "ReviewAction", back_populates="review_job"
    )

    __table_args__ = (
        Index("ix_review_jobs_status_priority", "status", "priority"),
        Index("ix_review_jobs_target", "target_type", "target_id"),
    )


# ── review_actions ────────────────────────────────────────────────────────────
class ReviewAction(Base):
    """审核操作记录（每次编辑操作一行）"""

    __tablename__ = "review_actions"

    action_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("review_jobs.review_job_id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="approve / reject / edit_field / add_note / set_boost / ..."
    )
    actor: Mapped[Optional[str]] = mapped_column(String(100))
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, comment="操作的具体内容")
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    review_job: Mapped["ReviewJob"] = relationship("ReviewJob", back_populates="actions")

    __table_args__ = (Index("ix_review_actions_job", "review_job_id"),)
