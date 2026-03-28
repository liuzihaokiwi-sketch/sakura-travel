"""
arq Job: send_booking_reminders
每天早9点运行，发出预约提醒通知：
  - 出发前 7 天：提醒需提前预约的景点/餐厅
  - 出发前 1 天：最后提醒 + 未预约警告
  - 已过期（出发日已过）：清除待推送标记

数据来源：
  orders (status=done/generating/validated) + detail_forms (travel_start_date)
  行程中标记了 requires_advance_booking=true 或 risk_flags 含 requires_reservation 的实体
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 内部通知发送（复用企业微信渠道）
# ─────────────────────────────────────────────────────────────────────────────

async def _send_wecom(message: str) -> bool:
    """发送企业微信机器人通知（同 flights notifier，独立实现避免循环依赖）"""
    webhook = getattr(settings, "wecom_webhook_url", None)
    if not webhook:
        logger.debug("未配置 WECOM_WEBHOOK_URL，跳过通知")
        return False

    import httpx
    payload = {"msgtype": "markdown", "markdown": {"content": message}}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook, json=payload)
            resp.raise_for_status()
            return resp.json().get("errcode") == 0
    except Exception as e:
        logger.warning("企微通知失败: %s", e)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 获取需要提醒的订单
# ─────────────────────────────────────────────────────────────────────────────

async def _get_orders_due_for_reminder(
    session: AsyncSession,
    days_ahead: int,
) -> list[dict]:
    """
    返回出发日距今 `days_ahead` 天的订单列表。
    只查 status IN (done, generating, validated, detail_submitted) 的订单。
    """
    target_date = (date.today() + timedelta(days=days_ahead)).isoformat()

    result = await session.execute(
        text("""
            SELECT
                o.order_id::text,
                df.travel_start_date,
                df.cities,
                df.form_id::text,
                u.phone,
                u.nickname,
                u.openid
            FROM orders o
            JOIN detail_forms df ON df.order_id = o.order_id
            LEFT JOIN users u ON u.user_id = o.user_id
            WHERE o.status IN ('done', 'generating', 'validated', 'detail_submitted')
              AND df.travel_start_date = :target_date
              AND df.is_complete = true
        """),
        {"target_date": target_date},
    )
    rows = result.mappings().all()
    return [dict(r) for r in rows]


async def _get_bookable_entities_for_cities(
    session: AsyncSession,
    city_codes: list[str],
) -> list[dict]:
    """
    返回指定城市中需要提前预约的 S/A 级实体（景点+餐厅）。
    优先选 quality_tier IN (S, A) 且 booking_method = online_advance / phone。
    """
    if not city_codes:
        return []

    result = await session.execute(
        text("""
            SELECT
                eb.entity_id::text,
                eb.name_zh,
                eb.entity_type,
                eb.city_code,
                eb.quality_tier,
                eb.booking_method,
                eb.risk_flags,
                COALESCE(p.booking_url, r.booking_url) AS booking_url,
                COALESCE(p.advance_booking_days, r.advance_booking_days) AS advance_booking_days
            FROM entity_base eb
            LEFT JOIN pois p ON p.entity_id = eb.entity_id
            LEFT JOIN restaurants r ON r.entity_id = eb.entity_id
            WHERE eb.city_code = ANY(:city_codes)
              AND eb.is_active = true
              AND eb.quality_tier IN ('S', 'A')
              AND (
                eb.booking_method IN ('online_advance', 'phone')
                OR eb.risk_flags @> '["requires_reservation"]'::jsonb
                OR p.requires_advance_booking = true
                OR r.requires_reservation = true
              )
            ORDER BY eb.quality_tier, eb.entity_type
            LIMIT 20
        """),
        {"city_codes": city_codes},
    )
    rows = result.mappings().all()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# 消息构建
# ─────────────────────────────────────────────────────────────────────────────

def _build_reminder_message(
    order: dict,
    entities: list[dict],
    days_left: int,
) -> str:
    nickname = order.get("nickname") or "旅行者"
    start_date = order.get("travel_start_date", "")
    urgency = "🚨 **最后提醒**" if days_left <= 1 else "📅 **出行提醒**"

    lines = [
        f"{urgency}",
        f"👤 {nickname}，您的行程将于 **{start_date}** 出发（还有 {days_left} 天）",
        "",
        "以下景点/餐厅**需要提前预约**，请尽快确认：",
    ]

    for e in entities:
        name = e.get("name_zh", "")
        booking_url = e.get("booking_url") or ""
        advance_days = e.get("advance_booking_days")
        entity_type = "🏛️" if e.get("entity_type") == "poi" else "🍽️"

        line = f"  {entity_type} **{name}**"
        if advance_days is not None and advance_days > 0:
            line += f"（建议提前 {advance_days} 天预约）"
        if booking_url:
            line += f" — [预约链接]({booking_url})"
        lines.append(line)

    lines.extend([
        "",
        f"📋 订单号: `{str(order.get('order_id', ''))[:8]}...`",
    ])
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────────────────────

async def send_booking_reminders(ctx: dict) -> dict:
    """
    arq Job: 发送预约提醒。
    每天早9点调用，检查7天前和1天前的出发订单。
    """
    logger.info("send_booking_reminders 开始")
    stats = {"checked": 0, "reminded": 0, "skipped": 0, "errors": 0}

    async with AsyncSessionLocal() as session:
        for days_ahead in (7, 1):
            try:
                orders = await _get_orders_due_for_reminder(session, days_ahead)
                for order in orders:
                    stats["checked"] += 1
                    try:
                        cities_raw = order.get("cities") or []
                        city_codes = [
                            c.get("city_code") for c in cities_raw
                            if isinstance(c, dict) and c.get("city_code")
                        ]
                        if not city_codes:
                            stats["skipped"] += 1
                            continue

                        entities = await _get_bookable_entities_for_cities(session, city_codes)
                        if not entities:
                            stats["skipped"] += 1
                            continue

                        msg = _build_reminder_message(order, entities, days_ahead)
                        sent = await _send_wecom(msg)
                        if sent:
                            stats["reminded"] += 1
                            logger.info(
                                "预约提醒已发 order=%s days_ahead=%d entities=%d",
                                str(order.get("order_id", ""))[:8],
                                days_ahead,
                                len(entities),
                            )
                        else:
                            stats["skipped"] += 1
                    except Exception as e:
                        logger.warning("处理订单提醒失败 order=%s: %s", order.get("order_id"), e)
                        stats["errors"] += 1
            except Exception as e:
                logger.error("查询 days_ahead=%d 订单失败: %s", days_ahead, e)
                stats["errors"] += 1

    logger.info("send_booking_reminders 完成: %s", stats)
    return stats
