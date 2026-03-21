"""
用户事件追踪 — 埋点定义与写入

定义所有前端/后端埋点事件类型和 schema，
写入 user_events 表供学习回路消费。
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.soft_rules import UserEvent

logger = logging.getLogger(__name__)


# ── 事件类型枚举 ──────────────────────────────────────────────────────────────

class EventType(str, Enum):
    # 预览转化
    PREVIEW_VIEW = "preview_view"                     # 打开预览页
    PREVIEW_STAY = "preview_stay_duration"             # 预览页停留时长
    PREVIEW_CTA_CLICK = "preview_cta_click"            # 点击 CTA
    PREVIEW_SCROLL_DEPTH = "preview_scroll_depth"      # 滚动深度

    # 付费
    PAYMENT_START = "payment_start"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAIL = "payment_fail"

    # 自助微调
    SWAP_VIEW_CANDIDATES = "swap_view_candidates"      # 查看替换候选
    SWAP_EXECUTE = "swap_execute"                      # 执行替换
    SWAP_UNDO = "swap_undo"                            # 撤销替换
    SWAP_BLOCKED = "swap_blocked"                      # 替换被安全检查阻止

    # 交付页
    DELIVERY_VIEW = "delivery_view"
    DELIVERY_DAY_EXPAND = "delivery_day_expand"        # 展开某天
    DELIVERY_ITEM_TAP = "delivery_item_tap"            # 点击某条目

    # 分享
    SHARE_CARD_GENERATE = "share_card_generate"
    SHARE_CARD_CLICK = "share_card_click"              # 分享链接被点击
    SHARE_REFERRAL_SIGNUP = "share_referral_signup"     # 从分享链接注册

    # 正式修改
    FORMAL_MODIFY_REQUEST = "formal_modify_request"
    FORMAL_MODIFY_COMPLETE = "formal_modify_complete"

    # 微信
    WECHAT_CTA_CLICK = "wechat_cta_click"
    WECHAT_ADDED = "wechat_added"

    # 反馈
    FEEDBACK_SUBMIT = "feedback_submit"
    NPS_SUBMIT = "nps_submit"


# ── 事件 Schema 定义 ──────────────────────────────────────────────────────────

EVENT_SCHEMAS: dict[str, dict[str, str]] = {
    EventType.PREVIEW_VIEW: {
        "plan_id": "str (required)",
        "referrer": "str (optional) — direct/share/wechat",
    },
    EventType.PREVIEW_STAY: {
        "plan_id": "str (required)",
        "duration_seconds": "int (required)",
        "scroll_depth_pct": "float (optional)",
    },
    EventType.PREVIEW_CTA_CLICK: {
        "plan_id": "str (required)",
        "cta_position": "str — header/inline/floating/day_teaser",
    },
    EventType.SWAP_VIEW_CANDIDATES: {
        "item_id": "int (required)",
        "entity_type": "str",
        "candidates_count": "int",
    },
    EventType.SWAP_EXECUTE: {
        "item_id": "int (required)",
        "old_entity_id": "str",
        "new_entity_id": "str",
        "impact_level": "str — green/yellow/red",
        "score_change_pct": "float",
    },
    EventType.SWAP_UNDO: {
        "item_id": "int (required)",
        "restored_entity_id": "str",
    },
    EventType.SHARE_CARD_GENERATE: {
        "plan_id": "str (required)",
        "card_type": "str — highlight/restaurant/day_summary/cover/route",
    },
    EventType.FEEDBACK_SUBMIT: {
        "plan_id": "str (required)",
        "rating": "int (1-5)",
        "tags": "list[str] (optional)",
        "comment": "str (optional)",
    },
    EventType.NPS_SUBMIT: {
        "plan_id": "str",
        "score": "int (0-10)",
        "reason": "str (optional)",
    },
}


# ── 写入函数 ──────────────────────────────────────────────────────────────────

async def track_event(
    db: AsyncSession,
    event_type: str | EventType,
    event_data: dict[str, Any],
    user_id: str | uuid.UUID | None = None,
    session_id: str | None = None,
) -> None:
    """
    写入用户事件到 user_events 表。

    Args:
        db: 数据库会话
        event_type: 事件类型
        event_data: 事件数据（自由 JSON）
        user_id: 用户 ID（可选）
        session_id: 会话 ID（未登录用户用）
    """
    if isinstance(event_type, EventType):
        event_type = event_type.value

    uid = None
    if user_id:
        uid = uuid.UUID(str(user_id)) if isinstance(user_id, str) else user_id

    try:
        await db.execute(
            insert(UserEvent).values(
                user_id=uid,
                session_id=session_id,
                event_type=event_type,
                event_data=event_data,
            )
        )
        # 不单独 commit，由调用方决定
    except Exception as e:
        logger.error("Failed to track event %s: %s", event_type, e)


# ── 批量写入 ──────────────────────────────────────────────────────────────────

async def track_events_batch(
    db: AsyncSession,
    events: list[dict[str, Any]],
) -> int:
    """
    批量写入事件。

    Args:
        events: [{"event_type": ..., "event_data": ..., "user_id": ..., "session_id": ...}, ...]

    Returns:
        成功写入的数量
    """
    count = 0
    for evt in events:
        try:
            await track_event(
                db=db,
                event_type=evt["event_type"],
                event_data=evt.get("event_data", {}),
                user_id=evt.get("user_id"),
                session_id=evt.get("session_id"),
            )
            count += 1
        except Exception as e:
            logger.error("Batch track failed for event: %s", e)
    return count
