from __future__ import annotations

from typing import Optional

"""
Layer D – City Circle Planning (城市圈规划层)
4 tables: city_circles, activity_clusters, circle_entity_roles, hotel_strategy_presets
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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ── city_circles ──────────────────────────────────────────────────────────────
class CityCircle(Base):
    """
    城市圈定义 — 按旅行可组合性而非行政区划定义的旅行圈。

    如 `kansai_classic_circle`：京都+大阪+奈良+神户+有马温泉。
    每个圈有自己的天数区间、核心基点、常见扩展节点。
    """

    __tablename__ = "city_circles"

    circle_id: Mapped[str] = mapped_column(
        String(80), primary_key=True,
        comment="如 kansai_classic_circle / tokyo_metropolitan_circle",
    )
    name_zh: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(100))

    # 核心基点与扩展节点
    base_city_codes: Mapped[list] = mapped_column(
        JSONB, nullable=False,
        comment='["kyoto","osaka"] — 核心驻点城市',
    )
    extension_city_codes: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment='["nara","kobe","uji"] — 可日归/短途扩展城市',
    )

    # 适用参数
    min_days: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    max_days: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=10)
    recommended_days_range: Mapped[Optional[str]] = mapped_column(
        String(20), comment="5-8",
    )
    tier: Mapped[str] = mapped_column(
        String(20), nullable=False, default="hot",
        comment="hot / warm / niche — 优先建模等级",
    )

    # 适合画像（用于 city_circle_selector 评分）
    fit_profiles: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='{"party_types":["couple","family_child"],"themes":["temple","food"]}',
    )
    # 到达/离开友好的机场列表
    friendly_airports: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment='["KIX","ITM"] — 本圈高效可达的机场',
    )
    # 季节强度（影响选圈评分）
    season_strength: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='{"spring":0.9,"summer":0.6,"autumn":0.95,"winter":0.5}',
    )
    # 备注
    notes: Mapped[Optional[str]] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )

    # Relationships
    clusters: Mapped[list["ActivityCluster"]] = relationship(
        "ActivityCluster", back_populates="circle",
    )
    hotel_presets: Mapped[list["HotelStrategyPreset"]] = relationship(
        "HotelStrategyPreset", back_populates="circle",
    )


# ── activity_clusters ─────────────────────────────────────────────────────────
class ActivityCluster(Base):
    """
    活动簇 — 由多个实体组成的体验集合，是规划的最小调度单元。

    如"东山祇园经典线"由清水寺 + 二年坂 + 八坂神社 + 祇园组成。
    一个簇不是一个实体，而是一条体验线。
    """

    __tablename__ = "activity_clusters"

    cluster_id: Mapped[str] = mapped_column(
        String(80), primary_key=True,
        comment="如 kyo_higashiyama_gion_classic / osa_usj_themepark",
    )
    circle_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("city_circles.circle_id", ondelete="CASCADE"),
        nullable=False,
    )

    name_zh: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(200))

    # 等级：S=默认强主活动, A=条件性主活动, B=体验型主活动
    level: Mapped[str] = mapped_column(
        String(1), nullable=False, default="A",
        comment="S / A / B",
    )

    # 体验参数
    default_duration: Mapped[Optional[str]] = mapped_column(
        String(20), comment="full_day / half_day / quarter_day — 展示标签，内部用分钟字段",
    )
    # 推荐时长范围（天）
    duration_range_days: Mapped[Optional[str]] = mapped_column(
        String(20), comment="0.5-1.0",
    )
    # ── 分钟级时长字段（内部编排用）────────────────────────────────────────────
    # core_visit_minutes: 核心游玩时长（不含排队缓冲）
    core_visit_minutes: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        comment="核心游玩时长（分钟），不含排队/拍照缓冲",
    )
    # queue_buffer_minutes: 排队缓冲
    queue_buffer_minutes: Mapped[Optional[int]] = mapped_column(
        SmallInteger, default=0,
        comment="排队缓冲分钟数，热门景点旺季可达 60+",
    )
    # photo_buffer_minutes: 摄影缓冲（photo 用户专用）
    photo_buffer_minutes: Mapped[Optional[int]] = mapped_column(
        SmallInteger, default=0,
        comment="重摄影用户额外耗时（分钟）",
    )
    # meal_buffer_minutes: 簇本身绑定餐饮（如伏见稻荷参道午餐）
    meal_buffer_minutes: Mapped[Optional[int]] = mapped_column(
        SmallInteger, default=0,
        comment="簇绑定餐饮耗时，不含独立餐厅选择",
    )
    # fatigue_weight: 体力负担系数（0.5=轻松 / 1.0=正常 / 1.5=耗体力）
    fatigue_weight: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), default=1.0,
        comment="体力消耗系数：0.5轻松/1.0正常/1.5耗体力，影响带老人/小孩折扣",
    )
    # queue_risk_level: 排队风险
    queue_risk_level: Mapped[Optional[str]] = mapped_column(
        String(10), default="low",
        comment="none / low / medium / high — 旺季排队风险",
    )
    # photo_intensity: 摄影价值（影响 photo 用户的 photo_buffer 是否激活）
    photo_intensity: Mapped[Optional[str]] = mapped_column(
        String(10), default="medium",
        comment="low / medium / high / extreme — 摄影价值",
    )
    # best_time_window: 最佳游览时间段
    best_time_window: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="如 '07:00-09:00' (早间) / 'evening' / 'anytime'",
    )
    # 核心走廊区域
    primary_corridor: Mapped[Optional[str]] = mapped_column(
        String(100), comment="如 higashiyama / arashiyama",
    )
    # 适合的季节
    seasonality: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment='["all_year","sakura","autumn_leaves"]',
    )
    # 适合画像
    profile_fit: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment='["first_timer","couple","photo","culture"]',
    )

    # ── 个性化新列（_add_columns.py 追加）───────────────────────────────────
    # must_have_tags: 必须命中的用户 tag，才有资格提升权重
    must_have_tags: Mapped[Optional[list]] = mapped_column(
        JSONB, default=list,
        comment='["photo","sakura"] — 用户 tag 完全命中时给予 niche bonus',
    )
    # capacity_units: 规划容量单位（1.0=一整天, 0.5=半天）
    capacity_units: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 1), default=1.0,
        comment="1.0=全天 / 0.5=半天，用于日程容量计算",
    )
    # meal_break_minutes: 簇本身包含的餐饮中断（区别于 meal_buffer_minutes）
    meal_break_minutes: Mapped[Optional[int]] = mapped_column(
        SmallInteger, default=0,
        comment="簇内餐饮中断时长（分钟），与 meal_buffer_minutes 不同",
    )
    # transit_minutes: 到达该簇的平均交通时间
    transit_minutes: Mapped[Optional[int]] = mapped_column(
        SmallInteger, default=30,
        comment="从典型基础出发点到簇起点的参考交通时间（分钟）",
    )
    # slack_minutes: 弹性缓冲时间
    slack_minutes: Mapped[Optional[int]] = mapped_column(
        SmallInteger, default=20,
        comment="弹性缓冲（迷路/休息/意外）分钟数",
    )
    # season_fit: 季节适配（较 seasonality 更简单的 list 格式）
    season_fit: Mapped[Optional[list]] = mapped_column(
        JSONB, default=list,
        comment='["spring","autumn","all"] — 适合的季节',
    )
    # day_type_hint: 推荐日程位置提示
    day_type_hint: Mapped[Optional[str]] = mapped_column(
        String(30), default="normal",
        comment="normal / half_day / half_day_pm — 调度位置建议",
    )
    # typical_start_time: 建议出发时间
    typical_start_time: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="如 '06:30' / '09:00' — 建议出发时间（HH:MM）",
    )
    # description_zh: 中文简要说明
    description_zh: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="簇的中文简要描述，用于 PDF / 前端展示",
    )

    # 调度属性
    trip_role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="anchor",
        comment="anchor / enrichment / buffer — 锚点/丰富/缓冲",
    )
    can_drive_hotel: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否会影响酒店选址决策",
    )
    time_window_strength: Mapped[str] = mapped_column(
        String(10), nullable=False, default="medium",
        comment="weak / medium / strong — 时间窗约束强度",
    )
    reservation_pressure: Mapped[str] = mapped_column(
        String(10), nullable=False, default="low",
        comment="none / low / medium / high",
    )
    secondary_attach_capacity: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=2,
        comment="能挂接几个次要活动",
    )

    # 降级策略
    downgrade_description: Mapped[Optional[str]] = mapped_column(
        Text, comment="天数紧时如何压缩",
    )
    # 升级触发条件
    upgrade_triggers: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='{"tags":["theme_park","nintendo"],"party_types":["family_child"]}',
    )
    # 默认是否被选入（S级通常为True）
    default_selected: Mapped[bool] = mapped_column(Boolean, default=False)

    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )

    # Relationships
    circle: Mapped["CityCircle"] = relationship(
        "CityCircle", back_populates="clusters",
    )
    entity_roles: Mapped[list["CircleEntityRole"]] = relationship(
        "CircleEntityRole", back_populates="cluster",
    )

    __table_args__ = (
        Index("ix_activity_clusters_circle", "circle_id"),
        Index("ix_activity_clusters_level", "level"),
    )


# ── circle_entity_roles ───────────────────────────────────────────────────────
class CircleEntityRole(Base):
    """
    实体在城市圈/活动簇中的角色映射。

    同一实体在不同圈/簇中可以扮演不同角色：
    - 清水寺在京都城市圈的东山祇园线中是 anchor_poi
    - 同一清水寺在 "3天速刷关西" 中可能只是 secondary_poi
    """

    __tablename__ = "circle_entity_roles"

    role_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
    )
    circle_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("city_circles.circle_id", ondelete="CASCADE"),
        nullable=False,
    )
    cluster_id: Mapped[Optional[str]] = mapped_column(
        String(80),
        ForeignKey("activity_clusters.cluster_id", ondelete="SET NULL"),
        comment="所属活动簇（anchor/secondary 通常有，meal/fallback 可能没有）",
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entity_base.entity_id", ondelete="CASCADE"),
        nullable=False,
    )

    # 角色
    role: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="anchor_poi / secondary_poi / meal_destination / meal_route / "
                "meal_backup / hotel_anchor / rainy_fallback / photo_spot / "
                "shopping / buffer",
    )

    # 簇内排序（anchor_poi 通常 sort_order=0）
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)

    # 是否是该簇的典型锚点
    is_cluster_anchor: Mapped[bool] = mapped_column(Boolean, default=False)

    # 可选元数据
    role_notes: Mapped[Optional[str]] = mapped_column(
        String(500), comment="角色说明，如'雨天替代方案'",
    )

    # T13: 决策解释字段（不挂 entity_base，因为同实体在不同角色下解释口径不同）
    why_selected: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="选入理由（编辑/算法输出），如'春季樱花期 S 级锚点，全圈不可缺'"
    )
    what_to_expect: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="在此角色下的体验描述，如'清水寺舞台俯瞰京都全景，拍摄黄金时段 16:30-17:30'"
    )
    booking_or_arrival_hint: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="预约/到达提示，如'无需预约，建议开园前 30 分钟到达排队'"
    )

    # Relationships
    cluster: Mapped[Optional["ActivityCluster"]] = relationship(
        "ActivityCluster", back_populates="entity_roles",
    )

    __table_args__ = (
        UniqueConstraint("circle_id", "cluster_id", "entity_id", "role",
                         name="uq_circle_cluster_entity_role"),
        Index("ix_cer_circle_entity", "circle_id", "entity_id"),
        Index("ix_cer_cluster", "cluster_id"),
    )


# ── hotel_strategy_presets ────────────────────────────────────────────────────
class HotelStrategyPreset(Base):
    """
    圈级酒店住法预设。

    每个城市圈可能有多种住法策略（如单基点 vs 双基点），
    hotel_base_builder 根据用户画像和主要活动选择最优住法。
    """

    __tablename__ = "hotel_strategy_presets"

    preset_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
    )
    circle_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("city_circles.circle_id", ondelete="CASCADE"),
        nullable=False,
    )

    name_zh: Mapped[str] = mapped_column(String(200), nullable=False)

    # 适用天数区间
    min_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    max_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # 住法定义
    bases: Mapped[list] = mapped_column(
        JSONB, nullable=False,
        comment="""
        [
          {"base_city":"kyoto","area":"kawaramachi","nights":4,
           "served_cluster_ids":["kyo_higashiyama_gion_classic","kyo_arashiyama_sagano"]},
          {"base_city":"osaka","area":"namba","nights":2,
           "served_cluster_ids":["osa_usj_themepark","osa_minami_food_night"]}
        ]
        """,
    )

    # 适合的画像
    fit_party_types: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment='["couple","solo","family_child"]',
    )
    fit_budget_levels: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment='["mid","premium"]',
    )

    # 换酒店指标
    switch_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0,
        comment="住法中换酒店次数",
    )
    switch_cost_minutes: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0,
        comment="换酒店总通勤耗时估计（分钟）",
    )
    last_night_airport_minutes: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        comment="最后一晚到主要离境机场的预估分钟数",
    )

    # 优先级（数值越小越优先）
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=50)

    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )

    # Relationships
    circle: Mapped["CityCircle"] = relationship(
        "CityCircle", back_populates="hotel_presets",
    )

    __table_args__ = (
        Index("ix_hotel_presets_circle", "circle_id"),
    )
