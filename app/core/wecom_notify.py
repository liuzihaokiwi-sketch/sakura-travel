"""
app/core/wecom_notify.py

企业微信机器人通知统一入口。

使用场景：
  - 订单状态变更（paid / generating / completed / failed）
  - 行程生成完成
  - 人工审核需介入
  - 系统异常告警

调用方式（全部非阻塞，失败不抛异常）：
  await notify_order_status(order_id, old_status, new_status, nickname)
  await notify_trip_done(trip_request_id, plan_id, duration_days, nickname)
  await notify_trip_failed(trip_request_id, reason, nickname)
  await notify_review_required(trip_request_id, score, reason)
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ─── 底层发送 ─────────────────────────────────────────────────────────────────

async def _send(message: str) -> bool:
    from app.core.config import settings
    webhook = settings.wecom_webhook_url
    if not webhook:
        return False

    import httpx
    payload = {"msgtype": "markdown", "markdown": {"content": message}}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(webhook, json=payload)
            resp.raise_for_status()
            return resp.json().get("errcode") == 0
    except Exception as e:
        logger.debug("企微通知失败: %s", e)
        return False


# ─── 订单状态变更 ─────────────────────────────────────────────────────────────

_STATUS_EMOJI = {
    "paid":           "💰",
    "detail_submitted": "📝",
    "validated":      "✅",
    "generating":     "⚙️",
    "review":         "👀",
    "completed":      "🎉",
    "delivered":      "📦",
    "failed":         "🚨",
    "cancelled":      "❌",
}

_STATUS_ZH = {
    "paid":           "已付款",
    "detail_submitted": "详情已提交",
    "validated":      "信息已校验",
    "generating":     "生成中",
    "review":         "待人工审核",
    "completed":      "生成完成",
    "delivered":      "已交付",
    "failed":         "生成失败",
    "cancelled":      "已取消",
}


async def notify_order_status(
    order_id: str,
    old_status: str,
    new_status: str,
    nickname: Optional[str] = None,
) -> None:
    """订单状态变更通知（只通知关键节点）。"""
    # 只通知值得关注的状态变更
    interesting = {"paid", "generating", "review", "completed", "delivered", "failed", "cancelled"}
    if new_status not in interesting:
        return

    emoji = _STATUS_EMOJI.get(new_status, "📌")
    zh = _STATUS_ZH.get(new_status, new_status)
    user_str = f"用户: {nickname}" if nickname else ""
    old_zh = _STATUS_ZH.get(old_status, old_status)

    msg = (
        f"{emoji} **订单状态变更**\n"
        f"订单: `{order_id[:8]}...`\n"
        f"{user_str}\n"
        f"状态: {old_zh} → **{zh}**"
    ).strip()

    await _send(msg)


# ─── 行程生成完成 ─────────────────────────────────────────────────────────────

async def notify_trip_done(
    trip_request_id: str,
    plan_id: str,
    duration_days: int,
    nickname: Optional[str] = None,
) -> None:
    """行程生成完成通知，运营侧可进入 review。"""
    user_str = f"用户: **{nickname}**\n" if nickname else ""
    msg = (
        f"🎉 **行程生成完成**\n"
        f"{user_str}"
        f"行程 ID: `{str(trip_request_id)[:8]}...`\n"
        f"计划 ID: `{str(plan_id)[:8]}...`\n"
        f"天数: {duration_days} 天\n"
        f"👉 请进入后台 Review 界面审核"
    )
    await _send(msg)


# ─── 行程生成失败 ─────────────────────────────────────────────────────────────

async def notify_trip_failed(
    trip_request_id: str,
    reason: str,
    nickname: Optional[str] = None,
) -> None:
    """行程生成失败告警（需要人工介入）。"""
    user_str = f"用户: {nickname}\n" if nickname else ""
    msg = (
        f"🚨 **行程生成失败**\n"
        f"{user_str}"
        f"行程 ID: `{str(trip_request_id)[:8]}...`\n"
        f"原因: `{reason}`\n"
        f"⚠️ 请及时处理并联系用户"
    )
    await _send(msg)


# ─── 需要人工审核 ─────────────────────────────────────────────────────────────

async def notify_review_required(
    trip_request_id: str,
    score: Optional[float] = None,
    reason: Optional[str] = None,
    nickname: Optional[str] = None,
) -> None:
    """质量门控未通过，需人工审核。"""
    score_str = f"质量评分: {score:.1f}\n" if score is not None else ""
    reason_str = f"原因: {reason}\n" if reason else ""
    user_str = f"用户: {nickname}\n" if nickname else ""
    msg = (
        f"👀 **行程需要人工审核**\n"
        f"{user_str}"
        f"行程 ID: `{str(trip_request_id)[:8]}...`\n"
        f"{score_str}"
        f"{reason_str}"
        f"👉 请进入后台审核队列处理"
    )
    await _send(msg)
