"""
decision_writer.py — E1: 阶段决策快照回写

每个阶段调 write_decision()，将结构化输入/输出/备选方案写入 generation_decisions。
与 trace_writer (trace 维度) 互补：trace 记"过程"，decision 记"结论"。

设计原则：
  - 每次写入一行，不做 batch
  - plan_id 可能在 skeleton 之后才有，所以支持延迟回写
  - input_hash 在 normalized_profile 阶段计算，后续阶段继承
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def compute_profile_hash(profile_dict: dict) -> str:
    """计算画像的 SHA-256 哈希。"""
    canonical = json.dumps(profile_dict, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _serialize_decision_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple, set, int, float, bool)):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except Exception:
            return str(value)
    return str(value)


async def write_decision(
    session: AsyncSession,
    *,
    trip_request_id: uuid.UUID,
    plan_id: Optional[uuid.UUID] = None,
    input_hash: Optional[str] = None,
    stage: str,
    key: str,
    value: Any = None,
    alternatives: Optional[list[dict]] = None,
    reason: str = "",
) -> None:
    """
    写入一条决策快照。

    Args:
        stage: 决策阶段 (normalized_profile / circle_selection / ...)
        key:   决策点   (selected_circle_id / selected_major_count / ...)
        value: 决策结果值（会被 str()）
        alternatives: 备选方案列表 [{id, score, reason}, ...]
        reason: 选择理由
    """
    from app.db.models.derived import GenerationDecision

    try:
        dec = GenerationDecision(
            trip_request_id=trip_request_id,
            plan_id=plan_id,
            input_hash=input_hash,
            decision_stage=stage,
            decision_key=key,
            decision_value=_serialize_decision_value(value),
            alternatives_considered=alternatives,
            decision_reason=reason[:2000] if reason else None,
            is_current=True,
        )
        session.add(dec)
        await session.flush()
    except Exception as exc:
        logger.warning("write_decision failed stage=%s key=%s: %s", stage, key, exc)


async def write_stage_snapshot(
    session: AsyncSession,
    *,
    trip_request_id: uuid.UUID,
    plan_id: Optional[uuid.UUID] = None,
    input_hash: Optional[str] = None,
    stage: str,
    snapshot: dict,
) -> None:
    """
    写入整个阶段的完整快照（多条 decision 的便捷封装）。

    snapshot 中每个 key-value 对写一行 generation_decisions。
    特殊 key：
      _alternatives → 转到 alternatives_considered
      _reason       → 转到 decision_reason
    """
    alternatives = snapshot.pop("_alternatives", None)
    reason = snapshot.pop("_reason", "")

    for k, v in snapshot.items():
        if k.startswith("_"):
            continue
        await write_decision(
            session,
            trip_request_id=trip_request_id,
            plan_id=plan_id,
            input_hash=input_hash,
            stage=stage,
            key=k,
            value=v,
            alternatives=alternatives if k == next(iter(snapshot)) else None,
            reason=reason if k == next(iter(snapshot)) else "",
        )


async def write_standard_decision(
    session: AsyncSession,
    *,
    trip_request_id: uuid.UUID,
    plan_id: Optional[uuid.UUID] = None,
    input_hash: Optional[str] = None,
    stage: str,
    verdict: str,
    reason: str = "",
    operator_action: str | None = None,
    status_bucket: str | None = None,
    payload: dict[str, Any] | None = None,
    alternatives: Optional[list[dict]] = None,
) -> None:
    await write_decision(
        session,
        trip_request_id=trip_request_id,
        plan_id=plan_id,
        input_hash=input_hash,
        stage=stage,
        key="result",
        value={
            "verdict": verdict,
            "reason": reason,
            "operator_action": operator_action,
            "status_bucket": status_bucket,
            "payload": payload or {},
        },
        alternatives=alternatives,
        reason=reason,
    )


async def invalidate_previous_decisions(
    session: AsyncSession,
    trip_request_id: uuid.UUID,
) -> int:
    """将之前的决策标记为非当前（重跑前调用）。"""
    from sqlalchemy import update
    from app.db.models.derived import GenerationDecision

    result = await session.execute(
        update(GenerationDecision)
        .where(
            GenerationDecision.trip_request_id == trip_request_id,
            GenerationDecision.is_current == True,
        )
        .values(is_current=False)
    )
    await session.flush()
    return result.rowcount
