"""
page_assets.py — T12: 页面资产层

page_hero_registry 存储各页面的英雄图/封面图配置，
支持多种渲染模式（web / pdf / mini_program）下的视觉优先级和裁剪安全区。
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PageHeroRegistry(Base):
    """
    T12: 页面英雄图注册表。

    page_type 枚举：
      - itinerary_cover   行程封面
      - day_header        每日头图
      - city_splash       城市圈落地页
      - cluster_card      活动簇卡片
      - entity_detail     实体详情页

    object_id：对应页面主体对象 ID（plan_id / entity_id / circle_id 等字符串化）
    render_mode：web / pdf / mini_program / shared_image

    visual_priority：同一 page_type + object_id + render_mode 组合下的排序（0 最高）
    crop_safe_area：裁剪安全区，格式 {"top": 0.1, "bottom": 0.2, "left": 0, "right": 0}
    """

    __tablename__ = "page_hero_registry"

    hero_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 页面定位
    page_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="itinerary_cover / day_header / city_splash / cluster_card / entity_detail"
    )
    object_id: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="对应主体对象 ID（plan_id / entity_id / circle_id 等）"
    )
    render_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="web",
        comment="web / pdf / mini_program / shared_image"
    )

    # 媒体资源
    media_url: Mapped[str] = mapped_column(Text, nullable=False, comment="图片/视频 URL")
    media_type: Mapped[str] = mapped_column(
        String(10), nullable=False, default="image",
        comment="image / video"
    )
    media_source: Mapped[Optional[str]] = mapped_column(
        String(50), comment="google / editorial / user / unsplash"
    )

    # 可选关联实体（如果图片来自某 entity_base）
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="SET NULL"),
    )

    # 视觉配置
    visual_priority: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="同 page_type+object_id+render_mode 下排序，0 最高优先"
    )
    crop_safe_area: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='裁剪安全区 {"top": 0.1, "bottom": 0.2, "left": 0, "right": 0}'
    )
    alt_text_zh: Mapped[Optional[str]] = mapped_column(String(500), comment="无障碍替代文字")
    color_palette: Mapped[Optional[list]] = mapped_column(
        JSONB, comment="主色调 ['#1a1a2e', '#16213e', ...]，用于渲染背景色"
    )

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_hero_page_object", "page_type", "object_id"),
        Index("ix_hero_render_mode", "render_mode"),
        Index("ix_hero_entity_id", "entity_id"),
        UniqueConstraint("page_type", "object_id", "render_mode", "visual_priority",
                         name="uq_hero_page_render_priority"),
    )
