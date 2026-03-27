from __future__ import annotations

from typing import Optional

"""
Detail Forms Layer – 付费后详细表单（6步分步填写）
2 tables: detail_forms, detail_form_steps

对应文档 §5-6：付费后用户分 6 步提交详细旅行信息。
每步独立保存，支持中断续填。

6 步结构：
  Step 1: 目的地与日期（cities + travel_dates + duration）
  Step 2: 同行人信息（party_type + party_size + ages + special_needs）
  Step 3: 预算与住宿（budget_level + budget_total + accommodation_pref）
  Step 4: 兴趣偏好（must_have_tags + nice_to_have + avoid_tags + food_pref）
  Step 5: 行程节奏（pace + wake_up_time + must_visit + free_text_wishes）
  Step 6: 航班与交通（flight_info + arrival_airport + jr_pass + pocket_wifi）
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
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ── detail_forms ──────────────────────────────────────────────────────────────
class DetailForm(Base):
    """付费后详细表单主表 — 每个 submission 对应一张表单"""

    __tablename__ = "detail_forms"

    form_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    # 关联到 quiz_submissions（raw SQL 表，用 UUID 字符串关联）
    submission_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True,
        comment="quiz_submissions.id — 一对一关联"
    )
    # 关联到 orders（付费后才创建 detail_form）
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.order_id", ondelete="SET NULL"),
        comment="付费订单 ID"
    )

    # ── 表单进度 ──
    current_step: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1,
        comment="当前填到第几步 (1-6)"
    )
    is_complete: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="是否全部 6 步填写完成"
    )

    # ── Step 1: 目的地与日期 ──
    cities: Mapped[Optional[list]] = mapped_column(
        JSONB,
        comment='[{"city_code": "tokyo", "city_name": "东京", "nights": 3, "place_id": "xxx"}, ...]'
    )
    requested_city_circle: Mapped[Optional[str]] = mapped_column(
        String(80), comment="Layer 2 canonical requested city circle"
    )
    travel_start_date: Mapped[Optional[str]] = mapped_column(
        String(10), comment="YYYY-MM-DD"
    )
    travel_end_date: Mapped[Optional[str]] = mapped_column(
        String(10), comment="YYYY-MM-DD"
    )
    duration_days: Mapped[Optional[int]] = mapped_column(SmallInteger)
    date_flexible: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="日期是否灵活"
    )

    # ── Step 2: 同行人信息 ──
    party_type: Mapped[Optional[str]] = mapped_column(
        String(30),
        comment="solo / couple / family_with_kids / family_no_kids / friends / senior"
    )
    party_size: Mapped[Optional[int]] = mapped_column(SmallInteger)
    party_ages: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='[28, 30] 或 [35, 38, 5, 3]'
    )
    has_elderly: Mapped[bool] = mapped_column(Boolean, default=False)
    has_children: Mapped[bool] = mapped_column(Boolean, default=False)
    children_ages: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='[5, 3]'
    )
    special_needs: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='{"wheelchair": false, "dietary": ["vegetarian"], "allergy": ["shellfish"]}'
    )

    # ── Step 3: 预算与住宿 ──
    budget_level: Mapped[Optional[str]] = mapped_column(
        String(10), comment="budget / mid / premium / luxury"
    )
    budget_total_jpy: Mapped[Optional[int]] = mapped_column(
        Integer, comment="总预算 (JPY)"
    )
    budget_total_cny: Mapped[Optional[int]] = mapped_column(
        Integer, comment="人均总预算 (CNY)"
    )
    budget_focus: Mapped[Optional[str]] = mapped_column(
        String(30),
        comment="better_stay / better_food / better_experience / balanced / best_value"
    )
    accommodation_pref: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='{"type": "hotel", "star_min": 3, "prefer_onsen": true, "location_pref": "near_station"}'
    )
    hotel_area_pref: Mapped[Optional[str]] = mapped_column(Text)
    hotel_booking_status: Mapped[Optional[str]] = mapped_column(String(20))
    booked_hotels: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='[{"name": "xx", "area": "kyoto_station", "check_in": "2026-04-01"}]'
    )

    # ── Step 4: 兴趣偏好 ──
    must_have_tags: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='["ramen", "temple", "shopping"]'
    )
    nice_to_have_tags: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='["photo_spot", "cafe"]'
    )
    avoid_tags: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='["crowded", "tourist_trap"]'
    )
    food_preferences: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='{"must_try": ["sushi", "wagyu"], "avoid": ["raw_fish"], "budget_per_meal": 3000}'
    )
    food_restrictions: Mapped[Optional[list]] = mapped_column(JSONB)
    food_restrictions_note: Mapped[Optional[str]] = mapped_column(Text)
    theme_family: Mapped[Optional[str]] = mapped_column(
        String(30),
        comment="classic_first / couple_aesthetic / food_shopping / onsen_healing / culture_deep / family_easy"
    )

    # ── Step 5: 行程节奏 ──
    pace: Mapped[Optional[str]] = mapped_column(
        String(20), comment="relaxed / moderate / packed"
    )
    wake_up_time: Mapped[Optional[str]] = mapped_column(
        String(10), comment="early / normal / late"
    )
    must_visit_places: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='["fushimi_inari", "teamlab"]'
    )
    visited_places: Mapped[Optional[list]] = mapped_column(
        JSONB, comment='["already_visited_place_a", "already_visited_place_b"]'
    )
    must_go_places: Mapped[Optional[list]] = mapped_column(JSONB)
    dont_want_places: Mapped[Optional[list]] = mapped_column(JSONB)
    pace_preference: Mapped[Optional[str]] = mapped_column(String(20))
    trip_style: Mapped[Optional[str]] = mapped_column(String(20))
    stamina_level: Mapped[Optional[str]] = mapped_column(String(10))
    fixed_events: Mapped[Optional[list]] = mapped_column(JSONB)
    free_text_wishes: Mapped[Optional[str]] = mapped_column(
        Text, comment="用户自由输入的期望（限 500 字）"
    )

    # ── Step 6: 航班与交通 ──
    flight_info: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='{"outbound": {"flight": "CX500", "arrive": "14:30", "airport": "NRT"}, "return": {...}}'
    )
    arrival_airport: Mapped[Optional[str]] = mapped_column(
        String(10), comment="NRT / HND / KIX / NGO / CTS"
    )
    arrival_date: Mapped[Optional[str]] = mapped_column(String(10))
    arrival_time: Mapped[Optional[str]] = mapped_column(String(5))
    arrival_place: Mapped[Optional[str]] = mapped_column(String(100))
    departure_airport: Mapped[Optional[str]] = mapped_column(
        String(10), comment="NRT / HND / KIX / NGO / CTS"
    )
    departure_date: Mapped[Optional[str]] = mapped_column(String(10))
    departure_time: Mapped[Optional[str]] = mapped_column(String(5))
    departure_place: Mapped[Optional[str]] = mapped_column(String(100))
    has_jr_pass: Mapped[Optional[bool]] = mapped_column(Boolean)
    transport_locked: Mapped[Optional[bool]] = mapped_column(Boolean)
    jr_pass_type: Mapped[Optional[str]] = mapped_column(String(50))
    has_pocket_wifi: Mapped[Optional[bool]] = mapped_column(Boolean)
    transport_notes: Mapped[Optional[str]] = mapped_column(Text)
    transport_pref: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='{"jr_pass": true, "pocket_wifi": true, "suica": true, "prefer_taxi": false}'
    )

    # ── 元数据 ──
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="全部 6 步填完的时间"
    )

    # ── relationships ──
    steps: Mapped[list["DetailFormStep"]] = relationship(
        "DetailFormStep", back_populates="form", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_detail_forms_submission", "submission_id"),
        Index("ix_detail_forms_order", "order_id"),
        Index("ix_detail_forms_complete", "is_complete"),
    )


# ── detail_form_steps ─────────────────────────────────────────────────────────
class DetailFormStep(Base):
    """每步提交的原始快照 — 用于审计追溯和断点续填"""

    __tablename__ = "detail_form_steps"

    step_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    form_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("detail_forms.form_id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, comment="步骤号 1-6"
    )
    step_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="该步骤提交的原始 JSON 数据"
    )
    is_valid: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="前端校验是否通过"
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    form: Mapped["DetailForm"] = relationship("DetailForm", back_populates="steps")

    __table_args__ = (
        Index("ix_detail_form_steps_form", "form_id"),
        Index("ix_detail_form_steps_form_step", "form_id", "step_number"),
    )


# ── JSON Schema 定义（供前端 + 校验引擎使用） ──────────────────────────────────

DETAIL_FORM_STEP_SCHEMAS = {
    1: {
        "title": "目的地与日期",
        "required": ["cities", "duration_days"],
        "fields": {
            "cities": {"type": "array", "minItems": 1, "description": "目的地城市列表"},
            "travel_start_date": {"type": "string", "format": "date", "description": "出发日期"},
            "travel_end_date": {"type": "string", "format": "date", "description": "返回日期"},
            "duration_days": {"type": "integer", "minimum": 3, "maximum": 21, "description": "天数"},
            "date_flexible": {"type": "boolean", "description": "日期是否灵活"},
        },
    },
    2: {
        "title": "同行人信息",
        "required": ["party_type", "party_size"],
        "fields": {
            "party_type": {
                "type": "string",
                "enum": ["solo", "couple", "family_with_kids", "family_no_kids", "friends", "senior"],
                "description": "同行类型",
            },
            "party_size": {"type": "integer", "minimum": 1, "maximum": 20, "description": "人数"},
            "party_ages": {"type": "array", "items": {"type": "integer"}, "description": "每人年龄"},
            "has_elderly": {"type": "boolean", "description": "是否有老人"},
            "has_children": {"type": "boolean", "description": "是否有小孩"},
            "children_ages": {"type": "array", "items": {"type": "integer"}, "description": "小孩年龄"},
            "special_needs": {"type": "object", "description": "特殊需求"},
        },
    },
    3: {
        "title": "预算与住宿",
        "required": ["budget_level"],
        "fields": {
            "budget_level": {
                "type": "string",
                "enum": ["budget", "mid", "premium", "luxury"],
                "description": "预算档位",
            },
            "budget_total_cny": {"type": "integer", "minimum": 1000, "description": "人均总预算"},
            "budget_focus": {
                "type": "string",
                "enum": ["better_stay", "better_food", "better_experience", "balanced", "best_value"],
                "description": "预算偏向",
            },
            "accommodation_pref": {"type": "object", "description": "住宿偏好"},
        },
    },
    4: {
        "title": "兴趣偏好",
        "required": [],
        "fields": {
            "must_have_tags": {"type": "array", "description": "必须包含的标签"},
            "nice_to_have_tags": {"type": "array", "description": "最好包含的标签"},
            "avoid_tags": {"type": "array", "description": "要避免的标签"},
            "food_preferences": {"type": "object", "description": "饮食偏好"},
            "theme_family": {
                "type": "string",
                "enum": [
                    "classic_first", "couple_aesthetic", "food_shopping",
                    "onsen_healing", "culture_deep", "family_easy",
                ],
                "description": "主题风格",
            },
        },
    },
    5: {
        "title": "行程节奏",
        "required": [],
        "fields": {
            "pace": {
                "type": "string",
                "enum": ["relaxed", "moderate", "packed"],
                "description": "行程节奏",
            },
            "wake_up_time": {
                "type": "string",
                "enum": ["early", "normal", "late"],
                "description": "起床时间偏好",
            },
            "must_visit_places": {"type": "array", "description": "必去地点"},
            "free_text_wishes": {"type": "string", "maxLength": 500, "description": "自由期望"},
        },
    },
    6: {
        "title": "航班与交通",
        "required": [],
        "fields": {
            "flight_info": {"type": "object", "description": "航班信息"},
            "arrival_airport": {
                "type": "string",
                "enum": ["NRT", "HND", "KIX", "NGO", "CTS"],
                "description": "到达机场",
            },
            "departure_airport": {
                "type": "string",
                "enum": ["NRT", "HND", "KIX", "NGO", "CTS"],
                "description": "离开机场",
            },
            "has_jr_pass": {"type": "boolean", "description": "是否购买 JR Pass"},
            "transport_pref": {"type": "object", "description": "交通偏好"},
        },
    },
}
