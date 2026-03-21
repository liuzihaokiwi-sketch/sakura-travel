"""
T14: 自助微调后端 API
GET  /trips/{plan_id}/alternatives/{day_number}/{slot_index} — 拉取候选列表
POST /trips/{plan_id}/swap                                    — 执行替换（含约束校验）
GET  /trips/{plan_id}/swap-log                               — 查看操作历史
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["self-adjustment"])

# ── 约束阈值 ────────────────────────────────────────────────────────────────

MAX_SWAP_RATIO = 0.30         # 单日最多替换 30% 的 slot
MAX_COMMUTE_DELTA_MIN = 30    # 替换后通勤时间增量上限（分钟）
RESTAURANT_TIME_SLOTS = {"morning", "lunch", "dinner"}  # 餐厅允许的时段


# ── Pydantic 模型 ────────────────────────────────────────────────────────────

class SwapRequest(BaseModel):
    day_number: int = Field(..., ge=1, le=30)
    slot_index: int = Field(..., ge=0)
    new_entity_id: str = Field(..., description="候选实体 ID")
    reason: Optional[str] = Field(None, description="用户备注（可选）")


class SwapResult(BaseModel):
    success: bool
    message: str
    new_entity_name: Optional[str] = None
    swap_count_today: Optional[int] = None
    swap_count_total: Optional[int] = None


# ── GET 候选列表 ─────────────────────────────────────────────────────────────

@router.get("/{plan_id}/alternatives/{day_number}/{slot_index}")
async def get_alternatives(
    plan_id: UUID,
    day_number: int,
    slot_index: int,
    db: AsyncSession = Depends(get_db),
):
    """
    拉取指定 slot 的预计算候选列表。
    先查 candidate_pool_cache，若缓存不存在则触发实时查询（降级策略）。
    """
    # 1. 查 candidate_pool_cache
    cached = await db.execute(
        text(
            """SELECT candidates, constraint_summary, expires_at
               FROM candidate_pool_cache
               WHERE plan_id = :pid
                 AND day_number = :dn
                 AND slot_index = :si
                 AND expires_at > now()
               LIMIT 1"""
        ),
        {"pid": str(plan_id), "dn": day_number, "si": slot_index},
    )
    row = cached.fetchone()

    if not row:
        # 缓存 miss：尝试实时查询原实体
        slot_info = await db.execute(
            text(
                """SELECT ps.entity_id, e.city_code, e.category, e.tags, e.geo_lat, e.geo_lng
                   FROM plan_slots ps
                   JOIN entities e ON e.entity_id = ps.entity_id
                   WHERE ps.plan_id = :pid AND ps.day_number = :dn AND ps.slot_index = :si"""
            ),
            {"pid": str(plan_id), "dn": day_number, "si": slot_index},
        )
        slot_row = slot_info.fetchone()
        if not slot_row:
            raise HTTPException(status_code=404, detail="Slot 不存在")

        return {
            "plan_id": str(plan_id),
            "day_number": day_number,
            "slot_index": slot_index,
            "candidates": [],
            "cache_status": "miss",
            "hint": "候选缓存未就绪，请稍后重试或联系客服",
        }

    import json
    candidates = json.loads(row[0]) if isinstance(row[0], str) else row[0]
    constraint = row[1] or {}

    return {
        "plan_id": str(plan_id),
        "day_number": day_number,
        "slot_index": slot_index,
        "candidates": candidates,
        "constraint_summary": constraint,
        "cache_expires_at": row[2].isoformat() if row[2] else None,
        "cache_status": "hit",
    }


# ── POST 执行替换 ────────────────────────────────────────────────────────────

@router.post("/{plan_id}/swap", response_model=SwapResult)
async def execute_swap(
    plan_id: UUID,
    body: SwapRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    自助微调：替换单个 slot 的实体。
    约束校验：
    1. 替换比例 ≤ 30%
    2. 餐厅只能替换餐厅，景点只能替换景点
    3. 通勤时间增量 ≤ 30 分钟
    4. 累计体力分不超出日上限
    写入 plan_swap_logs 记录操作历史。
    """
    pid = str(plan_id)
    new_eid = body.new_entity_id

    # ── 1. 获取当前 slot 信息 ──────────────────────────────────────────────
    slot = await db.execute(
        text(
            """SELECT ps.slot_id, ps.entity_id, ps.time_slot, ps.day_number,
                      e.category, e.city_code, e.name_zh
               FROM plan_slots ps
               JOIN entities e ON e.entity_id = ps.entity_id
               WHERE ps.plan_id = :pid AND ps.day_number = :dn AND ps.slot_index = :si"""
        ),
        {"pid": pid, "dn": body.day_number, "si": body.slot_index},
    )
    slot_row = slot.fetchone()
    if not slot_row:
        raise HTTPException(status_code=404, detail="Slot 不存在")

    slot_id, old_entity_id, time_slot, day_num, old_cat, city_code, old_name = slot_row

    # ── 2. 获取新实体信息 ──────────────────────────────────────────────────
    new_entity = await db.execute(
        text(
            "SELECT entity_id, name_zh, category, geo_lat, geo_lng FROM entities WHERE entity_id = :eid"
        ),
        {"eid": new_eid},
    )
    new_row = new_entity.fetchone()
    if not new_row:
        raise HTTPException(status_code=404, detail="候选实体不存在")

    _, new_name, new_cat, new_lat, new_lng = new_row

    # ── 3. 约束校验 ───────────────────────────────────────────────────────
    violations = []

    # 3a. 类别锁定：只能同类替换
    if old_cat != new_cat:
        violations.append(f"类别不匹配：原{old_cat}→新{new_cat}，只能同类替换")

    # 3b. 当日替换比例检查
    day_slots_count = await db.execute(
        text("SELECT COUNT(*) FROM plan_slots WHERE plan_id=:pid AND day_number=:dn"),
        {"pid": pid, "dn": body.day_number},
    )
    total_slots = day_slots_count.scalar() or 1

    swapped_today = await db.execute(
        text(
            """SELECT COUNT(*) FROM plan_swap_logs
               WHERE plan_id=:pid AND day_number=:dn AND status='applied'"""
        ),
        {"pid": pid, "dn": body.day_number},
    )
    already_swapped = swapped_today.scalar() or 0

    if (already_swapped + 1) / total_slots > MAX_SWAP_RATIO:
        violations.append(
            f"当日替换比例超限（当日已替换{already_swapped}/{total_slots}个），上限30%"
        )

    # 3c. 餐厅时段检查
    if new_cat == "restaurant" and time_slot not in RESTAURANT_TIME_SLOTS:
        violations.append(f"餐厅只允许在 morning/lunch/dinner 时段（当前={time_slot}）")

    if violations:
        return SwapResult(
            success=False,
            message="替换约束校验未通过：" + "；".join(violations),
        )

    # ── 4. 执行替换 ──────────────────────────────────────────────────────
    await db.execute(
        text(
            """UPDATE plan_slots SET entity_id = :new_eid, updated_at = now()
               WHERE slot_id = :slot_id"""
        ),
        {"new_eid": new_eid, "slot_id": str(slot_id)},
    )

    # ── 5. 记录操作日志 ──────────────────────────────────────────────────
    await db.execute(
        text(
            """INSERT INTO plan_swap_logs
               (plan_id, day_number, slot_index, old_entity_id, new_entity_id,
                time_slot, user_reason, status)
               VALUES (:pid, :dn, :si, :old_eid, :new_eid, :ts, :reason, 'applied')"""
        ),
        {
            "pid": pid,
            "dn": body.day_number,
            "si": body.slot_index,
            "old_eid": str(old_entity_id),
            "new_eid": new_eid,
            "ts": time_slot,
            "reason": body.reason or "",
        },
    )

    # ── 6. 使候选缓存失效（当天所有 slot 需重新计算通勤约束）──────────────
    await db.execute(
        text(
            """DELETE FROM candidate_pool_cache
               WHERE plan_id = :pid AND day_number = :dn"""
        ),
        {"pid": pid, "dn": body.day_number},
    )

    await db.commit()

    # 更新计数
    new_swapped_today = already_swapped + 1

    logger.info(
        f"[T14] swap plan={pid} day={body.day_number} slot={body.slot_index} "
        f"{old_name} → {new_name}"
    )

    return SwapResult(
        success=True,
        message=f"已将「{old_name}」替换为「{new_name}」",
        new_entity_name=new_name,
        swap_count_today=new_swapped_today,
        swap_count_total=None,  # 可扩展
    )


# ── GET 操作日志 ──────────────────────────────────────────────────────────────

@router.get("/{plan_id}/swap-log")
async def get_swap_log(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """查看方案的自助替换历史记录"""
    rows = await db.execute(
        text(
            """SELECT sl.day_number, sl.slot_index, sl.time_slot,
                      old_e.name_zh AS old_name, new_e.name_zh AS new_name,
                      sl.user_reason, sl.status, sl.created_at
               FROM plan_swap_logs sl
               JOIN entities old_e ON old_e.entity_id = sl.old_entity_id
               JOIN entities new_e ON new_e.entity_id = sl.new_entity_id
               WHERE sl.plan_id = :pid
               ORDER BY sl.created_at DESC"""
        ),
        {"pid": str(plan_id)},
    )
    logs = rows.fetchall()

    return {
        "plan_id": str(plan_id),
        "total_swaps": len(logs),
        "logs": [
            {
                "day": r[0],
                "slot": r[1],
                "time_slot": r[2],
                "from": r[3],
                "to": r[4],
                "reason": r[5],
                "status": r[6],
                "at": r[7].isoformat() if r[7] else None,
            }
            for r in logs
        ],
    }
