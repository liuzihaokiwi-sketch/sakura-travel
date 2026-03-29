"""
arq Job: send_booking_reminders

Daily cron (09:00) that scans active trips and sends booking reminders
for entities requiring advance reservation.

Reminder tiers:
  - "first"   : advance_booking_days before the visit date
                 (falls back to 7 days before departure if advance_booking_days is NULL)
  - "second"  : 1 day before the visit date
  - "overdue" : visit date has passed without a prior reminder

Deduplication:
  Uses the booking_reminder_log table with a unique constraint on
  (trip_request_id, entity_id, reminder_type) to guarantee at-most-once
  delivery per tier.

Data flow:
  detail_forms (travel_start_date)
    -> orders (status filter)
      -> trip_requests
        -> itinerary_plans (status = published / reviewed)
          -> itinerary_days (date / day_number)
            -> itinerary_items (entity_id)
              -> entity_base (booking_method, risk_flags)
              LEFT JOIN pois / restaurants (advance_booking_days, booking_url)
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.wechat_notify import send_markdown
from app.db.models.derived import BookingReminderLog
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Default lead-time when entity has no advance_booking_days set
_DEFAULT_ADVANCE_DAYS = 7


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

async def _find_bookable_items(
    session: AsyncSession,
    today: date,
) -> list[dict[str, Any]]:
    """
    Return a flat list of dicts, each representing one (trip, entity, visit_date)
    tuple that may need a booking reminder.

    Only considers:
      - Orders in actionable statuses
      - Completed detail forms with a future (or today) travel_start_date
      - Published / reviewed itinerary plans
      - Items whose entity requires advance booking
    """
    # Raw SQL is used intentionally here because the query spans 7 tables with
    # COALESCE across two extension tables (pois, restaurants).  The ORM
    # equivalent would be significantly harder to read and maintain.
    query = text("""
        SELECT
            tr.trip_request_id,
            ip.plan_id,
            id.day_number,
            id.date           AS day_date,
            ii.entity_id,
            eb.name_zh        AS entity_name,
            eb.entity_type,
            eb.booking_method,
            eb.risk_flags,
            COALESCE(p.advance_booking_days, r.advance_booking_days)
                AS advance_booking_days,
            COALESCE(p.booking_url, r.booking_url)
                AS booking_url,
            df.travel_start_date,
            u.nickname,
            o.order_id
        FROM trip_requests tr
        JOIN orders o
            ON o.order_id = tr.order_id
        JOIN detail_forms df
            ON df.order_id = o.order_id
            AND df.is_complete = true
        JOIN itinerary_plans ip
            ON ip.trip_request_id = tr.trip_request_id
            AND ip.status IN ('published', 'reviewed')
        JOIN itinerary_days id
            ON id.plan_id = ip.plan_id
        JOIN itinerary_items ii
            ON ii.day_id = id.day_id
            AND ii.entity_id IS NOT NULL
        JOIN entity_base eb
            ON eb.entity_id = ii.entity_id
            AND eb.is_active = true
        LEFT JOIN pois p
            ON p.entity_id = eb.entity_id
        LEFT JOIN restaurants r
            ON r.entity_id = eb.entity_id
        LEFT JOIN users u
            ON u.user_id = tr.user_id
        WHERE
            o.status IN (
                'done', 'generating', 'validated',
                'detail_submitted', 'delivered'
            )
            AND df.travel_start_date >= :today_str
            AND (
                eb.booking_method IN ('online_advance', 'phone')
                OR eb.risk_flags @> '["requires_reservation"]'::jsonb
                OR COALESCE(p.requires_advance_booking, false) = true
                OR COALESCE(r.requires_reservation, false) = true
            )
        ORDER BY df.travel_start_date, id.day_number
    """)

    result = await session.execute(query, {"today_str": today.isoformat()})
    return [dict(row._mapping) for row in result]


def _compute_visit_date(
    travel_start_date: str,
    day_date: str | None,
    day_number: int,
) -> date:
    """
    Determine the actual calendar date for a given itinerary day.

    Prefer the explicit ``day_date`` column (YYYY-MM-DD) stored on
    ``itinerary_days``.  Fall back to ``travel_start_date + (day_number - 1)``.
    """
    if day_date:
        try:
            return date.fromisoformat(day_date)
        except ValueError:
            pass
    departure = date.fromisoformat(travel_start_date)
    return departure + timedelta(days=max(day_number - 1, 0))


def _classify_reminder(
    today: date,
    visit_date: date,
    advance_booking_days: int | None,
) -> str | None:
    """
    Return the reminder_type that should fire today, or None if no reminder
    is due.

    Logic:
      - "first"  : fires on the day that is ``advance_booking_days`` before
                    visit_date (default 7 if NULL).
      - "second" : fires 1 day before visit_date.
      - "overdue": fires on or after visit_date (entity not yet reminded).

    We check from most-urgent to least-urgent so the caller can rely on the
    dedup constraint to avoid double-sends.
    """
    days_until = (visit_date - today).days

    if days_until < 0:
        return "overdue"
    if days_until <= 1:
        return "second"

    lead = advance_booking_days if (advance_booking_days and advance_booking_days > 0) else _DEFAULT_ADVANCE_DAYS
    if days_until <= lead:
        return "first"

    return None


# ---------------------------------------------------------------------------
# Dedup: check + insert into booking_reminder_log
# ---------------------------------------------------------------------------

async def _try_record_reminder(
    session: AsyncSession,
    *,
    trip_request_id: str,
    plan_id: str,
    entity_id: str,
    entity_name: str,
    booking_url: str | None,
    reminder_type: str,
    visit_date: str,
) -> bool:
    """
    Attempt to insert a reminder log row.  Returns True if the row was
    inserted (i.e. this reminder has not been sent before), False on
    conflict (duplicate).
    """
    stmt = (
        pg_insert(BookingReminderLog)
        .values(
            trip_request_id=trip_request_id,
            plan_id=plan_id,
            entity_id=entity_id,
            entity_name=entity_name,
            booking_url=booking_url,
            reminder_type=reminder_type,
            visit_date=visit_date,
        )
        .on_conflict_do_nothing(
            index_elements=["trip_request_id", "entity_id", "reminder_type"],
        )
    )
    result = await session.execute(stmt)
    return result.rowcount > 0  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Message builder
# ---------------------------------------------------------------------------

_TYPE_EMOJI = {"poi": "\U0001f3db\ufe0f", "restaurant": "\U0001f37d\ufe0f"}


def _build_reminder_markdown(
    items: list[dict[str, Any]],
    reminder_type: str,
    nickname: str | None,
    travel_start_date: str,
    order_id: str | None,
) -> str:
    """Build a WeChat Work markdown message for a batch of items."""
    urgency_map = {
        "first": "\U0001f4c5 **预约提醒**",
        "second": "\U0001f6a8 **最后预约提醒**",
        "overdue": "\u26a0\ufe0f **预约逾期警告**",
    }
    header = urgency_map.get(reminder_type, "\U0001f4c5 **预约提醒**")
    who = nickname or "旅行者"

    lines: list[str] = [
        header,
        f"\U0001f464 {who}\uff0c出发日期 **{travel_start_date}**",
        "",
    ]

    if reminder_type == "overdue":
        lines.append("以下景点/餐厅的**建议预约日期已过**\uff0c请尽快确认\uff1a")
    elif reminder_type == "second":
        lines.append("**明天出发**\uff0c以下景点/餐厅仍需预约\uff1a")
    else:
        lines.append("以下景点/餐厅**需要提前预约**\uff0c请尽快处理\uff1a")

    for it in items:
        emoji = _TYPE_EMOJI.get(it.get("entity_type", ""), "\U0001f4cd")
        name = it.get("entity_name", "")
        adv = it.get("advance_booking_days")
        url = it.get("booking_url") or ""
        visit = it.get("visit_date", "")

        line = f"  {emoji} **{name}**\uff08\u8bbf\u95ee\u65e5: {visit}\uff09"
        if adv and adv > 0:
            line += f"\uff0c\u5efa\u8bae\u63d0\u524d {adv} \u5929\u9884\u7ea6"
        if url:
            line += f" \u2014 [\u9884\u7ea6\u94fe\u63a5]({url})"
        lines.append(line)

    if order_id:
        lines.extend(["", f"\U0001f4cb \u8ba2\u5355\u53f7: `{str(order_id)[:8]}...`"])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def send_booking_reminders(ctx: dict) -> dict[str, int]:
    """
    arq cron job entry point.

    Scans all active trips with future departure dates, identifies entities
    requiring advance booking, classifies reminders, deduplicates via the
    booking_reminder_log table, and sends WeChat Work notifications.
    """
    logger.info("send_booking_reminders: started")
    today = date.today()
    stats: dict[str, int] = {
        "scanned": 0,
        "reminded": 0,
        "skipped_dup": 0,
        "skipped_not_due": 0,
        "errors": 0,
    }

    async with AsyncSessionLocal() as session:
        try:
            rows = await _find_bookable_items(session, today)
        except Exception:
            logger.exception("send_booking_reminders: query failed")
            stats["errors"] += 1
            return stats

        # Group items by (trip_request_id, reminder_type) for batched messages
        # Key: (trip_request_id, reminder_type)
        # Value: list of item dicts enriched with visit_date and reminder_type
        pending: dict[tuple[str, str], list[dict[str, Any]]] = {}

        for row in rows:
            stats["scanned"] += 1
            try:
                visit_date = _compute_visit_date(
                    row["travel_start_date"],
                    row["day_date"],
                    row["day_number"],
                )
                reminder_type = _classify_reminder(
                    today,
                    visit_date,
                    row["advance_booking_days"],
                )
                if reminder_type is None:
                    stats["skipped_not_due"] += 1
                    continue

                trip_id = str(row["trip_request_id"])
                plan_id = str(row["plan_id"])
                entity_id = str(row["entity_id"])

                inserted = await _try_record_reminder(
                    session,
                    trip_request_id=trip_id,
                    plan_id=plan_id,
                    entity_id=entity_id,
                    entity_name=row["entity_name"] or "",
                    booking_url=row.get("booking_url"),
                    reminder_type=reminder_type,
                    visit_date=visit_date.isoformat(),
                )
                if not inserted:
                    stats["skipped_dup"] += 1
                    continue

                enriched = dict(row)
                enriched["visit_date"] = visit_date.isoformat()
                enriched["reminder_type"] = reminder_type
                key = (trip_id, reminder_type)
                pending.setdefault(key, []).append(enriched)

            except Exception:
                logger.exception(
                    "send_booking_reminders: error processing row entity=%s",
                    row.get("entity_id"),
                )
                stats["errors"] += 1

        # Commit all dedup inserts
        await session.commit()

    # Send batched notifications (outside the DB session)
    for (trip_id, reminder_type), items in pending.items():
        try:
            first = items[0]
            msg = _build_reminder_markdown(
                items=items,
                reminder_type=reminder_type,
                nickname=first.get("nickname"),
                travel_start_date=first.get("travel_start_date", ""),
                order_id=str(first.get("order_id", "")),
            )
            sent = await send_markdown(msg)
            if sent:
                stats["reminded"] += len(items)
                logger.info(
                    "send_booking_reminders: sent %s reminder for trip=%s (%d entities)",
                    reminder_type, trip_id[:8], len(items),
                )
            else:
                # Notification channel disabled or failed; items are still logged
                # so they won't fire again.
                stats["reminded"] += len(items)
                logger.debug(
                    "send_booking_reminders: notification channel inactive, "
                    "logged %d items for trip=%s",
                    len(items), trip_id[:8],
                )
        except Exception:
            logger.exception(
                "send_booking_reminders: notification failed for trip=%s",
                trip_id[:8],
            )
            stats["errors"] += 1

    logger.info("send_booking_reminders: done %s", stats)
    return stats
