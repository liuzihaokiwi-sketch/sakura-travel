"""
report_schema.py — ReportPayloadV2 Pydantic 类型定义

对应设计文档 A_内容架构与生成链路改造设计.md §5-§7
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


# ── 城市圈字段（vNext 扩充）────────────────────────────────────────────────────

class SelectedCircleInfo(BaseModel):
    """city_circle_selector 选出的城市圈信息，注入 ReportMeta"""
    circle_id: str
    name_zh: str
    base_city_codes: List[str] = Field(default_factory=list)
    extension_city_codes: List[str] = Field(default_factory=list)
    recommended_days_range: Optional[str] = None
    # 选圈理由
    selection_score: Optional[float] = None
    selection_reasons: List[str] = Field(default_factory=list)


class DayFrameInfo(BaseModel):
    """route_skeleton_builder.DayFrame 的精简 Pydantic 表示，注入 DaySection"""
    day_type: str = "normal"          # arrival / normal / departure / transfer
    sleep_base: str = ""
    primary_corridor: str = ""
    secondary_corridor: Optional[str] = None
    main_driver: Optional[str] = None  # cluster_id
    main_driver_name: str = ""
    day_capacity_units: float = 1.0
    transfer_budget_minutes: int = 120
    fallback_corridor: Optional[str] = None
    intensity: str = "balanced"
    title_hint: str = ""


class HotelBaseInfo(BaseModel):
    """hotel_base_builder 输出的住法策略，注入 DesignBrief"""
    strategy_name: str = ""
    preset_id: Optional[int] = None
    bases: List[dict] = Field(default_factory=list,
        description='[{"city":"kyoto","area":"kawaramachi","nights":4}, ...]')
    switch_count: int = 0
    last_night_airport_minutes: Optional[int] = None


# ── 元数据 ────────────────────────────────────────────────────────────────────

class ReportMeta(BaseModel):
    trip_id: str
    destination: str
    total_days: int
    language: Literal["zh-CN", "en", "ja"] = "zh-CN"
    render_mode: Literal["web", "pdf", "shared"] = "web"
    schema_version: Literal["v2"] = "v2"
    # 城市圈字段（vNext）
    circle: Optional[SelectedCircleInfo] = None


# ── 画像摘要 ──────────────────────────────────────────────────────────────────

class HotelConstraintSummary(BaseModel):
    city: str
    check_in_day: Optional[int] = None
    check_out_day: Optional[int] = None
    hotel_name: Optional[str] = None
    area: Optional[str] = None
    is_fixed: bool = False


class ProfileSummary(BaseModel):
    party_type: str
    pace_preference: Literal["light", "balanced", "dense"] = "balanced"
    budget_bias: str = ""
    trip_goals: List[str] = Field(default_factory=list)
    hard_constraints: List[str] = Field(default_factory=list)
    avoid_list: List[str] = Field(default_factory=list)
    hotel_constraints: List[HotelConstraintSummary] = Field(default_factory=list)


# ── 设计简报（总纲第一页真相源）────────────────────────────────────────────────

class DesignBrief(BaseModel):
    route_strategy: List[str] = Field(default_factory=list, description="如'先东后西''最后一天轻收尾'")
    tradeoffs: List[str] = Field(default_factory=list, description="如'放弃 teamLab，保留节奏与晚餐体验'")
    stay_strategy: List[str] = Field(default_factory=list, description="如'全程单酒店，减少搬运行李'")
    budget_strategy: List[str] = Field(default_factory=list, description="如'高价餐集中后半段'")
    execution_principles: List[str] = Field(default_factory=list, description="如'每天最多 2 个区域'")
    # 城市圈字段（vNext）
    hotel_base: Optional[HotelBaseInfo] = None


# ── 总览 ──────────────────────────────────────────────────────────────────────

class RouteSummaryCard(BaseModel):
    day_index: int
    title: str
    primary_area: str
    intensity: Literal["light", "balanced", "dense"] = "balanced"


class DayIntensity(BaseModel):
    day_index: int
    label: str       # "轻松" | "均衡" | "偏满"
    score: float = 0.5   # 0.0-1.0


class AnchorEvent(BaseModel):
    day_index: int
    label: str
    is_bookable: bool = False


class HotelChange(BaseModel):
    day_index: int
    from_area: Optional[str] = None
    to_area: str
    reason: Optional[str] = None


class OverviewSection(BaseModel):
    route_summary: List[RouteSummaryCard] = Field(default_factory=list)
    intensity_map: List[DayIntensity] = Field(default_factory=list)
    anchor_events: List[AnchorEvent] = Field(default_factory=list)
    hotel_changes: List[HotelChange] = Field(default_factory=list)
    trip_highlights: List[str] = Field(default_factory=list)


# ── 预约提醒 ──────────────────────────────────────────────────────────────────

class BookingAlertItem(BaseModel):
    entity_id: Optional[str] = None
    entity_name: str = ""
    entity_type: str = ""                # poi / restaurant / hotel / activity
    label: str
    booking_level: Literal["must_book", "should_book", "good_to_book", "walkin_ok"] = "good_to_book"
    booking_method: Optional[str] = None  # online_advance / phone / walk_in
    booking_url: Optional[str] = None
    advance_booking_days: Optional[int] = None
    visit_day: Optional[int] = None       # 行程第几天使用
    deadline_date: Optional[str] = None   # YYYY-MM-DD 实际截止日期（需 departure_date）
    queue_wait_min: Optional[int] = None  # 不预约时典型排队时间
    deadline_hint: str = ""
    impact_if_missed: str = ""
    fallback_label: Optional[str] = None


# ── 每天骨架 ──────────────────────────────────────────────────────────────────

class DaySlot(BaseModel):
    slot_index: int
    kind: Literal["poi", "restaurant", "hotel", "activity", "transit", "buffer"]
    entity_id: Optional[str] = None
    title: str
    area: str = ""
    start_time_hint: Optional[str] = None
    duration_mins: Optional[int] = None
    booking_required: bool = False
    weather_dependency: Literal["low", "medium", "high"] = "low"
    replaceable: bool = True
    replacement_pool: List[str] = Field(default_factory=list)


class DayRisk(BaseModel):
    risk_type: str       # "queue" | "weather" | "closure" | "crowd" | "booking"
    description: str
    mitigation: str = ""


class HighlightCard(BaseModel):
    name: str
    description: str
    photo_tip: Optional[str] = None
    nearby_bonus: Optional[str] = None


class ExecutionNotes(BaseModel):
    risk_warnings: List[str] = Field(default_factory=list)
    weather_plan: str = ""
    energy_plan: str = ""
    clothing_tip: str = ""


class PlanBOption(BaseModel):
    trigger: str          # 触发条件，如"下雨" | "体力不足"
    alternative: str      # 替代方案描述
    entity_ids: List[str] = Field(default_factory=list)


class DaySection(BaseModel):
    day_index: int
    title: str
    primary_area: str
    secondary_area: Optional[str] = None
    day_goal: str
    intensity: Literal["light", "balanced", "dense"] = "balanced"
    start_anchor: str = ""
    end_anchor: str = ""
    must_keep: str = ""
    first_cut: str = ""
    route_integrity_score: float = 1.0    # 0.0-1.0，区域跳跃扣分
    risks: List[DayRisk] = Field(default_factory=list)
    slots: List[DaySlot] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)
    highlights: List[HighlightCard] = Field(default_factory=list)
    execution_notes: ExecutionNotes = Field(default_factory=ExecutionNotes)
    plan_b: List[PlanBOption] = Field(default_factory=list)
    trigger_tags: List[str] = Field(default_factory=list)


# ── 条件页 ────────────────────────────────────────────────────────────────────

class ConditionalSection(BaseModel):
    section_type: Literal["hotel", "restaurant", "transport", "photo", "budget", "extra"]
    trigger_reason: str
    related_day_indexes: List[int] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)


# ── 质量标记 ──────────────────────────────────────────────────────────────────

class QualityFlags(BaseModel):
    str_01_overview_complete: bool = True
    str_02_daily_complete: bool = True
    str_03_title_consistent: bool = True
    str_04_no_duplicates: bool = True
    str_05_conditionals_valid: bool = True
    warnings: List[str] = Field(default_factory=list)


# ── 版本信息 ──────────────────────────────────────────────────────────────────

class VersioningInfo(BaseModel):
    generated_at: str
    generator_version: str = "v2"
    profile_version: Optional[str] = None


# ── L3-01 新增：渲染层支撑模型 ────────────────────────────────────────────────

class PreferenceFulfillmentItem(BaseModel):
    """用户偏好兑现条目"""
    preference_text: str
    fulfillment_type: Literal["fully_met", "partially_met", "traded_off", "not_applicable"]
    evidence: str
    object_ref: Optional[str] = None
    explanation: str = ""


class SkippedOption(BaseModel):
    """被跳过的备选项"""
    name: str
    entity_type: str               # poi / restaurant / hotel
    why_skipped: str
    would_fit_if: Optional[str] = None


class ChapterSummary(BaseModel):
    """章节摘要，供目录 / 章节 opener 使用"""
    chapter_id: str
    title: str
    subtitle: Optional[str] = None
    goal: str = ""
    mood: str = ""
    covered_days: List[int] = Field(default_factory=list)


class EmotionalGoal(BaseModel):
    """每天情绪目标"""
    day_index: int
    mood_keyword: str              # "惊喜" / "安静" / "探索" / "放松" / "热闹"
    mood_sentence: str


class RiskWatchItem(BaseModel):
    """风险监控条目"""
    entity_id: Optional[str] = None
    risk_type: str                 # "closed_day" / "reservation_needed" / "seasonal" / "weather"
    description: str
    action_required: Optional[str] = None
    day_index: Optional[int] = None


# ── 多圈支持（F3）────────────────────────────────────────────────────────────

# (SelectedCircleInfo 已在上方定义，复用)


# ── 顶层报告 Payload ──────────────────────────────────────────────────────────

class ReportPayloadV2(BaseModel):
    model_config = ConfigDict(extra="allow")

    meta: ReportMeta
    profile_summary: ProfileSummary
    design_brief: DesignBrief
    overview: OverviewSection
    booking_alerts: List[BookingAlertItem] = Field(default_factory=list)
    prep_notes: dict = Field(default_factory=dict)   # 复用 STATIC_PREP
    days: List[DaySection]
    conditional_sections: List[ConditionalSection] = Field(default_factory=list)
    quality_flags: QualityFlags = Field(default_factory=QualityFlags)
    versioning: VersioningInfo
    # ── L3-01 新增字段 ──────────────────────────────────────────────────────
    preference_fulfillment: List[PreferenceFulfillmentItem] = Field(default_factory=list)
    skipped_options: List[SkippedOption] = Field(default_factory=list)
    chapter_summaries: List[ChapterSummary] = Field(default_factory=list)
    emotional_goals: List[EmotionalGoal] = Field(default_factory=list)
    risk_watch_items: List[RiskWatchItem] = Field(default_factory=list)
    selection_evidence: List[dict] = Field(default_factory=list)
    photo_themes: List[dict] = Field(
        default_factory=list, description="拍摄主题 [{theme, spots, tips}]"
    )
    supplemental_items: List[dict] = Field(
        default_factory=list, description="补充景点（未排进主行程的推荐）"
    )
    # ── F3 多圈支持 ──────────────────────────────────────────────────────────
    circles: List[SelectedCircleInfo] = Field(
        default_factory=list,
        description="多圈行程时，按顺序列出所有城市圈",
    )
    day_circle_map: Dict[int, str] = Field(
        default_factory=dict,
        description="day_index → circle_id 映射，ChapterPlanner 用",
    )

