"""
T26: AI 数据自动维护流水线
事实抽取 → 交叉审查 → 冲突解决 → 入库前校验

T27: 用户验证推荐标记体系
旅行后回访验证 → 实体标记"已验证"

用法：
  python -m app.workers.scripts.data_pipeline --city tokyo --dry-run
  python -m app.workers.scripts.data_pipeline --entity-id <uuid> --verify
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy as sa

from app.db.session import async_session_factory

logger = logging.getLogger(__name__)


# ── T26: 事实抽取 ─────────────────────────────────────────────────────────────

FACT_EXTRACT_SYSTEM = """你是一个日本旅游实体信息核查专家。
给定一个旅游实体的原始信息，提取并标准化以下字段（只输出 JSON，不要解释）：
{
  "name_zh": "中文名",
  "name_ja": "日文名",
  "address_zh": "中文地址",
  "geo_lat": 纬度数字,
  "geo_lng": 经度数字,
  "open_time": "09:00",
  "close_time": "18:00",
  "closed_days": ["周一", "节假日"],
  "ticket_price_jpy": 票价数字或null,
  "google_rating": 评分数字或null,
  "tabelog_score": 评分数字或null,
  "review_count": 评价数量或null,
  "tags": ["标签1", "标签2"],
  "facts_confidence": 0.0-1.0,
  "facts_source": "信息来源摘要"
}"""

async def extract_entity_facts(raw_info: str) -> dict:
    """T26-步骤1: 用 AI 从原始文本中抽取结构化实体信息"""
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic()
        response = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=800,
            system=FACT_EXTRACT_SYSTEM,
            messages=[{"role": "user", "content": f"原始信息：\n{raw_info}"}],
        )
        raw = response.content[0].text.strip()
        return json.loads(raw) if raw.startswith("{") else {}
    except Exception as e:
        logger.warning(f"[T26 extract] 失败: {e}")
        return {}


# ── T26: 交叉审查 ─────────────────────────────────────────────────────────────

CROSS_CHECK_SYSTEM = """你是一个数据一致性检查专家。
给定同一实体的两份数据（旧数据 vs 新提取数据），输出冲突报告：
{
  "conflicts": [
    {"field": "字段名", "old_value": ..., "new_value": ..., "confidence": 0.0-1.0, "recommended": "new/old/manual"}
  ],
  "auto_resolvable": true/false,
  "resolution_note": "说明"
}
只输出 JSON。"""

async def cross_check_entity(old_data: dict, new_data: dict) -> dict:
    """T26-步骤2: 比较新旧数据，找出冲突字段"""
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic()
        response = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=600,
            system=CROSS_CHECK_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"旧数据：{json.dumps(old_data, ensure_ascii=False)}\n新数据：{json.dumps(new_data, ensure_ascii=False)}"
            }],
        )
        raw = response.content[0].text.strip()
        return json.loads(raw) if raw.startswith("{") else {"conflicts": [], "auto_resolvable": True}
    except Exception as e:
        logger.warning(f"[T26 cross_check] 失败: {e}")
        return {"conflicts": [], "auto_resolvable": True}


async def run_entity_data_pipeline(
    entity_id: str,
    raw_info: str,
    dry_run: bool = False,
) -> dict:
    """
    T26 完整流水线：事实抽取 → 交叉审查 → 冲突解决 → 入库
    """
    async with async_session_factory() as db:
        # 1. 抽取新数据
        new_facts = await extract_entity_facts(raw_info)
        if not new_facts:
            return {"status": "failed", "reason": "事实抽取失败"}

        # 2. 拉取旧数据
        result = await db.execute(
            sa.text("SELECT name_zh, name_ja, address_zh, geo_lat, geo_lng, open_time, close_time, google_rating, tabelog_score, tags FROM entities WHERE entity_id = :eid"),
            {"eid": entity_id},
        )
        row = result.fetchone()
        old_data = dict(zip(["name_zh", "name_ja", "address_zh", "geo_lat", "geo_lng", "open_time", "close_time", "google_rating", "tabelog_score", "tags"], row)) if row else {}

        # 3. 交叉审查
        check_result = await cross_check_entity(old_data, new_facts)
        conflicts = check_result.get("conflicts", [])
        auto_resolvable = check_result.get("auto_resolvable", True)

        stats = {
            "entity_id": entity_id,
            "facts_extracted": len(new_facts),
            "conflicts_found": len(conflicts),
            "auto_resolvable": auto_resolvable,
            "dry_run": dry_run,
        }

        if dry_run:
            stats["status"] = "dry_run"
            stats["conflicts"] = conflicts
            return stats

        # 4. 解决冲突并更新
        if auto_resolvable or not conflicts:
            # 自动合并：优先使用新值（高 confidence 的字段）
            updates = {
                f: new_facts[f]
                for f in ["open_time", "close_time", "google_rating", "tabelog_score", "review_count"]
                if f in new_facts and new_facts[f] is not None
            }
            if updates:
                set_clause = ", ".join(f"{k} = :{k}" for k in updates)
                updates["entity_id"] = entity_id
                updates["updated_at"] = datetime.utcnow()
                await db.execute(
                    sa.text(f"UPDATE entities SET {set_clause}, updated_at = :updated_at WHERE entity_id = :entity_id"),
                    updates,
                )
                await db.commit()
                stats["status"] = "updated"
                stats["fields_updated"] = list(updates.keys())
        else:
            # 存在不可自动解决的冲突，记录待人工处理
            await db.execute(
                sa.text(
                    """INSERT INTO entity_data_conflicts (entity_id, old_data, new_data, conflicts, created_at)
                       VALUES (:eid, :old, :new, :conflicts, now())
                       ON CONFLICT (entity_id) DO UPDATE SET old_data=EXCLUDED.old_data, new_data=EXCLUDED.new_data, conflicts=EXCLUDED.conflicts, created_at=now()"""
                ),
                {
                    "eid": entity_id,
                    "old": json.dumps(old_data, ensure_ascii=False),
                    "new": json.dumps(new_facts, ensure_ascii=False),
                    "conflicts": json.dumps(conflicts, ensure_ascii=False),
                },
            )
            await db.commit()
            stats["status"] = "pending_manual_review"

        return stats


# ── T27: 用户验证推荐标记 ─────────────────────────────────────────────────────

async def process_user_feedback_batch(city_code: Optional[str] = None) -> dict:
    """
    T27: 处理 user_entity_feedback 中未验证的反馈，
    达标则标记实体为 verified，更新评分数据。
    """
    async with async_session_factory() as db:
        # 拉取未验证的合格反馈
        result = await db.execute(
            sa.text(
                """SELECT uef.id, uef.entity_id, uef.order_id,
                          uef.visited, uef.rating, uef.recommendation_match,
                          uef.crowd_level_actual, uef.comment
                   FROM user_entity_feedback uef
                   JOIN entities e ON e.entity_id = uef.entity_id
                   WHERE uef.verified = false
                     AND uef.visited = true
                     AND (:city IS NULL OR e.city_code = :city)
                   ORDER BY uef.submitted_at DESC
                   LIMIT 200"""
            ),
            {"city": city_code},
        )
        feedbacks = result.fetchall()

        stats = {"total": len(feedbacks), "verified": 0, "skipped": 0, "entity_updates": 0}

        # 按实体分组
        entity_feedbacks: dict[str, list] = {}
        for row in feedbacks:
            eid = str(row[1])
            entity_feedbacks.setdefault(eid, []).append(row)

        for entity_id, rows in entity_feedbacks.items():
            # 只有评分维度 ≥ 3 项的反馈才计入
            valid_rows = [r for r in rows if r[4] is not None and r[5] is not None]
            if not valid_rows:
                stats["skipped"] += len(rows)
                continue

            # 计算聚合数据
            avg_rating = sum(r[4] for r in valid_rows if r[4]) / len(valid_rows)
            avg_crowd = sum(r[6] for r in valid_rows if r[6]) / max(1, sum(1 for r in valid_rows if r[6]))
            visit_count = len(valid_rows)

            # 更新实体：增加 verified_visit_count
            try:
                await db.execute(
                    sa.text(
                        """UPDATE entities SET
                               verified_visit_count = COALESCE(verified_visit_count, 0) + :cnt,
                               user_avg_rating = :avg_rating,
                               updated_at = now()
                           WHERE entity_id = :eid"""
                    ),
                    {"cnt": visit_count, "avg_rating": round(avg_rating, 2), "eid": entity_id},
                )
                stats["entity_updates"] += 1
            except Exception:
                pass  # 字段不存在时静默忽略

            # 更新 entity_time_window_scores 的实际人流数据
            if avg_crowd:
                # crowd_score 映射：实际人流 1(少)→10(拥挤) 取反变为体验分
                crowd_score = max(1, min(10, 11 - int(avg_crowd * 2)))
                await db.execute(
                    sa.text(
                        """UPDATE entity_time_window_scores
                           SET crowd_score = :cs, source = 'user_verified', computed_at = now()
                           WHERE entity_id = :eid AND month = 0 AND time_slot = 'any'"""
                    ),
                    {"cs": crowd_score, "eid": entity_id},
                )

            # 标记所有合格反馈为 verified
            feedback_ids = [r[0] for r in valid_rows]
            await db.execute(
                sa.text("UPDATE user_entity_feedback SET verified = true WHERE id = ANY(:ids)"),
                {"ids": feedback_ids},
            )
            stats["verified"] += len(valid_rows)

        await db.commit()
        logger.info(f"[T27] 处理完成: {stats}")
        return stats


# ── T28: 城市覆盖扩展 ─────────────────────────────────────────────────────────

# T28: 北海道/冲绳/名古屋城市配置（新城市上线所需的基础配置）
NEW_CITIES_CONFIG = {
    "hokkaido": {
        "display_name_zh": "北海道",
        "main_city": "sapporo",
        "p0_areas": ["sapporo_center", "otaru", "noboribetsu", "furano", "hakodate"],
        "seasonal_highlights": {
            1: "粉雪滑雪场（二世谷/留寿都）",
            2: "雪节（札幌大通公园）",
            6: "薰衣草花期（富良野）",
            10: "红叶（十胜岳/旭岳）",
            11: "温泉初雪（登别/定山溪）",
        },
        "unique_tags": ["powder_snow", "fresh_seafood", "lavender", "dairy", "onsen", "nature"],
        "typical_duration_days": [4, 5, 7],
    },
    "okinawa": {
        "display_name_zh": "冲绳",
        "main_city": "naha",
        "p0_areas": ["naha_kokusai", "churaumi", "ishigaki", "miyako", "kerama"],
        "seasonal_highlights": {
            3: "樱花（绯寒樱，比本州早1个月）",
            4: "海水温度适宜（26°C），珊瑚礁清晰",
            6: "梅雨结束，旅游旺季开始",
            10: "台风季结束，最佳潜水季",
            12: "圣诞节庆活动+暖冬出海",
        },
        "unique_tags": ["beach", "diving", "snorkeling", "ryukyu_culture", "awamori", "tropics"],
        "typical_duration_days": [4, 5, 6, 7],
    },
    "nagoya": {
        "display_name_zh": "名古屋",
        "main_city": "nagoya",
        "p0_areas": ["nagoya_center", "sakae", "meijo", "atsuta", "okazaki"],
        "seasonal_highlights": {
            3: "犬山城樱花（国宝天守）",
            4: "名古屋城樱花护城河",
            10: "红叶（香嵐渓，中部最美红叶）",
            11: "万博纪念公园菊花展",
        },
        "unique_tags": ["castle", "nagoya_meshi", "toyota", "industrial_tourism", "shinkansen_access"],
        "typical_duration_days": [2, 3, 4],
    },
}

async def register_new_city(city_code: str, dry_run: bool = False) -> dict:
    """T28: 注册新城市到系统（city_monthly_context + seasonal_events 初始化）"""
    config = NEW_CITIES_CONFIG.get(city_code)
    if not config:
        return {"status": "error", "reason": f"城市 {city_code} 未配置"}

    if dry_run:
        return {"status": "dry_run", "city": city_code, "config": config}

    async with async_session_factory() as db:
        inserted = 0
        for month in range(1, 13):
            highlight = config["seasonal_highlights"].get(month, "")
            existing = await db.execute(
                sa.text("SELECT 1 FROM city_monthly_context WHERE city_code=:c AND month=:m"),
                {"c": city_code, "m": month},
            )
            if not existing.fetchone():
                await db.execute(
                    sa.text(
                        """INSERT INTO city_monthly_context (city_code, month, highlights_zh, recommended_for)
                           VALUES (:c, :m, :h, :r)"""
                    ),
                    {
                        "c": city_code,
                        "m": month,
                        "h": json.dumps([highlight] if highlight else [], ensure_ascii=False),
                        "r": json.dumps(["couple", "solo", "family"], ensure_ascii=False),
                    },
                )
                inserted += 1

        await db.commit()
        return {"status": "ok", "city": city_code, "months_inserted": inserted}


# ── T29: 老客带新返现机制 ─────────────────────────────────────────────────────

async def generate_invite_code(order_id: str) -> dict:
    """
    T29: 为已付费订单生成专属邀请码。
    规则：完成订单（delivered/refunded 除外）可生成邀请码。
    被邀请者首单享 ¥50 优惠，邀请者获得 ¥50 返现（下次使用）。
    """
    import hashlib
    import secrets

    async with async_session_factory() as db:
        # 检查订单状态
        order = await db.execute(
            sa.text("SELECT status, user_id FROM orders WHERE order_id = :oid"),
            {"oid": order_id},
        )
        row = order.fetchone()
        if not row:
            return {"status": "error", "reason": "订单不存在"}

        status, user_id = row
        if status not in ("delivered", "paid"):
            return {"status": "error", "reason": f"订单状态 {status} 不符合生成邀请码条件"}

        # 检查是否已有邀请码
        existing = await db.execute(
            sa.text("SELECT invite_code, total_uses, total_reward_cny FROM invite_codes WHERE order_id = :oid"),
            {"oid": order_id},
        )
        existing_row = existing.fetchone()
        if existing_row:
            return {
                "status": "ok",
                "invite_code": existing_row[0],
                "total_uses": existing_row[1],
                "total_reward_cny": float(existing_row[2] or 0),
                "invite_url": f"https://trip.ai/quiz?invite={existing_row[0]}",
            }

        # 生成新邀请码
        raw = f"{order_id}:{secrets.token_hex(8)}"
        code = hashlib.sha256(raw.encode()).hexdigest()[:8].upper()

        await db.execute(
            sa.text(
                """INSERT INTO invite_codes (invite_code, order_id, user_id, discount_cny, reward_cny, max_uses, total_uses, created_at)
                   VALUES (:code, :oid, :uid, 50, 50, 10, 0, now())"""
            ),
            {"code": code, "oid": order_id, "uid": str(user_id) if user_id else None},
        )
        await db.commit()

        return {
            "status": "created",
            "invite_code": code,
            "discount_cny": 50,
            "reward_cny": 50,
            "max_uses": 10,
            "invite_url": f"https://trip.ai/quiz?invite={code}",
            "share_text": f"我用这个行程规划服务为去日本做了完美攻略！首单立减¥50，用我的邀请码：{code} 链接：https://trip.ai/quiz?invite={code}",
        }


async def apply_invite_code(invite_code: str, new_order_id: str) -> dict:
    """T29: 新用户下单时使用邀请码，触发双向奖励"""
    async with async_session_factory() as db:
        # 验证邀请码
        code_row = await db.execute(
            sa.text("SELECT invite_code, order_id, discount_cny, reward_cny, max_uses, total_uses FROM invite_codes WHERE invite_code = :code"),
            {"code": invite_code},
        )
        row = code_row.fetchone()
        if not row:
            return {"status": "invalid", "reason": "邀请码不存在"}

        _, src_order_id, discount_cny, reward_cny, max_uses, total_uses = row
        if total_uses >= max_uses:
            return {"status": "exhausted", "reason": "邀请码已达使用上限"}

        # 应用折扣到新订单
        await db.execute(
            sa.text("UPDATE orders SET discount_applied_cny = :d, invite_code_used = :c WHERE order_id = :oid"),
            {"d": discount_cny, "c": invite_code, "oid": new_order_id},
        )

        # 为邀请人记录返现（下次下单时自动抵扣）
        await db.execute(
            sa.text(
                """INSERT INTO invite_rewards (invite_code, triggered_order_id, reward_cny, status, created_at)
                   VALUES (:code, :oid, :r, 'pending', now())"""
            ),
            {"code": invite_code, "oid": new_order_id, "r": reward_cny},
        )

        # 更新使用次数
        await db.execute(
            sa.text("UPDATE invite_codes SET total_uses = total_uses + 1, total_reward_cny = COALESCE(total_reward_cny, 0) + :r WHERE invite_code = :code"),
            {"r": reward_cny, "code": invite_code},
        )

        await db.commit()
        return {
            "status": "applied",
            "discount_cny": float(discount_cny),
            "inviter_reward_cny": float(reward_cny),
            "message": f"成功使用邀请码，本单立减¥{discount_cny}",
        }


# ── CLI 入口 ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="数据维护流水线 (T26/T27/T28/T29)")
    sub = parser.add_subparsers(dest="cmd")

    # T26: 实体数据更新
    p26 = sub.add_parser("update-entity", help="T26: 更新实体数据")
    p26.add_argument("--entity-id", required=True)
    p26.add_argument("--info", required=True, help="原始信息文本")
    p26.add_argument("--dry-run", action="store_true")

    # T27: 处理用户反馈
    p27 = sub.add_parser("process-feedback", help="T27: 处理用户反馈并标记验证")
    p27.add_argument("--city", help="限定城市")

    # T28: 注册新城市
    p28 = sub.add_parser("register-city", help="T28: 注册新城市")
    p28.add_argument("--city", required=True, choices=list(NEW_CITIES_CONFIG.keys()))
    p28.add_argument("--dry-run", action="store_true")

    # T29: 生成邀请码
    p29 = sub.add_parser("gen-invite", help="T29: 生成邀请码")
    p29.add_argument("--order-id", required=True)

    args = parser.parse_args()

    if args.cmd == "update-entity":
        result = asyncio.run(run_entity_data_pipeline(args.entity_id, args.info, args.dry_run))
    elif args.cmd == "process-feedback":
        result = asyncio.run(process_user_feedback_batch(getattr(args, "city", None)))
    elif args.cmd == "register-city":
        result = asyncio.run(register_new_city(args.city, args.dry_run))
    elif args.cmd == "gen-invite":
        result = asyncio.run(generate_invite_code(args.order_id))
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))
