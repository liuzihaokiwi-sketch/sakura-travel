"""
app/core/wechat_notify.py

企业微信群机器人通知模块（WeChat Work group robot webhook）。

功能：
  - send_text: 发送纯文本消息
  - send_markdown: 发送 Markdown 消息
  - notify_order_status: 订单状态变更通知
  - notify_generation_failed: 行程生成失败告警
  - notify_review_needed: 行程需人工审核告警

设计原则：
  - 全部非阻塞：通知失败仅 log，不影响主流程
  - Feature flag: 通过 ENABLE_WECHAT_NOTIFY=true 开启（默认关闭）
  - Webhook URL: 通过 WECHAT_WORK_WEBHOOK_URL 环境变量配置
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _is_enabled() -> bool:
    """Check if WeChat Work notifications are enabled via feature flag."""
    return os.environ.get("ENABLE_WECHAT_NOTIFY", "").lower() == "true"


def _get_webhook_url() -> str:
    """Get webhook URL from environment variable."""
    return os.environ.get("WECHAT_WORK_WEBHOOK_URL", "")


# ─── Low-level senders ────────────────────────────────────────────────────────


async def send_text(content: str) -> bool:
    """Send a plain text message via WeChat Work group robot.

    Returns True on success, False on failure or when notifications are disabled.
    """
    if not _is_enabled():
        logger.debug("WeChat Work notifications disabled, skipping text message")
        return False

    webhook_url = _get_webhook_url()
    if not webhook_url:
        logger.debug("WECHAT_WORK_WEBHOOK_URL not configured, skipping")
        return False

    import httpx

    payload = {
        "msgtype": "text",
        "text": {"content": content},
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
            result = resp.json()
            if result.get("errcode") != 0:
                logger.warning(
                    "WeChat Work API error: errcode=%s errmsg=%s",
                    result.get("errcode"),
                    result.get("errmsg"),
                )
                return False
            return True
    except Exception as exc:
        logger.warning("WeChat Work text notification failed: %s", exc)
        return False


async def send_markdown(content: str) -> bool:
    """Send a markdown message via WeChat Work group robot.

    Returns True on success, False on failure or when notifications are disabled.
    """
    if not _is_enabled():
        logger.debug("WeChat Work notifications disabled, skipping markdown message")
        return False

    webhook_url = _get_webhook_url()
    if not webhook_url:
        logger.debug("WECHAT_WORK_WEBHOOK_URL not configured, skipping")
        return False

    import httpx

    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content},
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
            result = resp.json()
            if result.get("errcode") != 0:
                logger.warning(
                    "WeChat Work API error: errcode=%s errmsg=%s",
                    result.get("errcode"),
                    result.get("errmsg"),
                )
                return False
            return True
    except Exception as exc:
        logger.warning("WeChat Work markdown notification failed: %s", exc)
        return False


# ─── Business-level notifications ─────────────────────────────────────────────

_STATUS_LABEL = {
    "paid": ("💰", "已付款"),
    "generating": ("⚙️", "生成中"),
    "review": ("👀", "待人工审核"),
    "completed": ("🎉", "生成完成"),
    "delivered": ("📦", "已交付"),
    "failed": ("🚨", "生成失败"),
    "cancelled": ("❌", "已取消"),
}


async def notify_order_status(
    trip_id: str,
    status: str,
    details: dict[str, Any] | None = None,
) -> bool:
    """Send a formatted order status update notification.

    Args:
        trip_id: Trip request ID.
        status: New status string (e.g. "paid", "generating", "completed").
        details: Optional dict with extra context (e.g. nickname, order_id, old_status).
    """
    details = details or {}
    emoji, label = _STATUS_LABEL.get(status, ("📌", status))
    nickname = details.get("nickname", "")
    old_status = details.get("old_status", "")

    lines = [f"{emoji} **订单状态变更**"]
    lines.append(f"行程ID: `{trip_id[:8]}...`")
    if nickname:
        lines.append(f"用户: {nickname}")
    if old_status:
        old_emoji, old_label = _STATUS_LABEL.get(old_status, ("", old_status))
        lines.append(f"状态: {old_label} → **{label}**")
    else:
        lines.append(f"状态: **{label}**")

    # Append any extra detail fields
    for key in ("order_id", "plan_id", "reason"):
        if key in details:
            lines.append(f"{key}: `{details[key]}`")

    content = "\n".join(lines)
    return await send_markdown(content)


async def notify_generation_failed(
    trip_id: str,
    error: str,
    step: str,
) -> bool:
    """Send a generation failure alert.

    Args:
        trip_id: Trip request ID.
        error: Error description.
        step: Pipeline step where failure occurred (e.g. "city_circle_pipeline",
              "delivery_pipeline", "review_pipeline").
    """
    content = (
        f"🚨 **行程生成失败**\n"
        f"行程ID: `{trip_id[:8]}...`\n"
        f"失败环节: `{step}`\n"
        f"错误信息: {error[:500]}\n"
        f"⚠️ 请及时处理并联系用户"
    )
    return await send_markdown(content)


async def notify_review_needed(
    trip_id: str,
    reason: str,
    score: float,
) -> bool:
    """Send a review-needed alert when a plan requires human intervention.

    Args:
        trip_id: Trip request ID.
        reason: Why the plan needs review.
        score: Quality score from the quality gate or review pipeline.
    """
    content = (
        f"👀 **行程需要人工审核**\n"
        f"行程ID: `{trip_id[:8]}...`\n"
        f"质量评分: {score:.1f}\n"
        f"原因: {reason[:300]}\n"
        f"👉 请进入后台审核队列处理"
    )
    return await send_markdown(content)
