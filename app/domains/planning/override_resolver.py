"""
app/domains/planning/override_resolver.py — 运营干预解析器（L4-02）

查询服务，供 Layer 2 各模块调用，带内存缓存。

输入：AsyncSession（数据库连接）
输出：OverrideResolver 实例，提供 is_blocked / get_weight_delta / get_notes / should_pin

接入点（待后续任务接入，此模块只提供接口）：
  - eligibility_gate.py:       is_blocked() → EG 规则追加
  - major_activity_ranker.py:  get_weight_delta() → 加到 context_fit 分
  - secondary_filler.py:       is_blocked() → 候选池过滤
  - report_generator.py:       get_notes() → 追加到报告

依赖：
  app.db.models.operator_overrides.OperatorOverride
  sqlalchemy.ext.asyncio.AsyncSession
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.operator_overrides import OperatorOverride

logger = logging.getLogger(__name__)


class OverrideResolver:
    """
    运营干预解析器，带内存缓存。

    使用方式：
        resolver = OverrideResolver(session)
        await resolver.load_active()          # 加载到内存
        if resolver.is_blocked(entity_id):    # 判断屏蔽
            skip(entity_id)
        delta = resolver.get_weight_delta(entity_id)  # 获取加减权
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        # scope → target_id → list[OperatorOverride]
        self._cache: dict[str, dict[str, list[OperatorOverride]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._loaded = False

    async def load_active(self) -> None:
        """
        从 DB 加载所有当前生效的 override 到内存缓存。

        生效条件：
          - is_active = True
          - effective_from <= NOW
          - effective_until IS NULL 或 effective_until > NOW
        """
        now = datetime.now(timezone.utc)
        stmt = select(OperatorOverride).where(
            OperatorOverride.is_active == True,  # noqa: E712
            OperatorOverride.effective_from <= now,
        )
        result = await self._session.execute(stmt)
        overrides = result.scalars().all()

        self._cache.clear()
        skipped = 0
        for ov in overrides:
            # 额外检查 effective_until（Python 侧，处理时区问题）
            if ov.effective_until and ov.effective_until < now:
                skipped += 1
                continue
            scope = ov.scope or "entity"
            tid = ov.target_id or "__global__"
            self._cache[scope][tid].append(ov)

        self._loaded = True
        logger.info(
            "[OverrideResolver] 加载完成: %d 条生效干预（跳过 %d 条过期）",
            sum(len(v) for d in self._cache.values() for v in d.values()),
            skipped,
        )

    def get_overrides(
        self, scope: str, target_id: str
    ) -> list[OperatorOverride]:
        """查某个目标的所有生效干预（含 global 级别）"""
        if not self._loaded:
            logger.warning("[OverrideResolver] 未调用 load_active()，结果可能不准确")
        result = list(self._cache.get(scope, {}).get(target_id, []))
        # 同时附加 global 级别干预
        global_ov = list(self._cache.get("global", {}).get("__global__", []))
        return result + global_ov

    def is_blocked(self, entity_id: str) -> bool:
        """
        判断实体是否被屏蔽（override_type = 'block'）。

        检查顺序：entity → cluster（暂不展开）→ global
        """
        entity_ovs = self.get_overrides("entity", entity_id)
        for ov in entity_ovs:
            if ov.override_type == "block":
                logger.debug("[OverrideResolver] entity %s is BLOCKED", entity_id)
                return True
        return False

    def is_swap_locked(self, entity_id: str) -> bool:
        """判断实体是否被锁定（不允许"换一个"替换）"""
        entity_ovs = self.get_overrides("entity", entity_id)
        return any(ov.override_type == "swap_lock" for ov in entity_ovs)

    def get_weight_delta(self, entity_id: str) -> float:
        """
        获取实体的分数增减值（boost/demote 叠加）。

        多条 override 叠加求和，上限 ±50 防止极端数据。
        返回 0.0 表示无干预。
        """
        entity_ovs = self.get_overrides("entity", entity_id)
        total_delta = 0.0
        for ov in entity_ovs:
            if ov.override_type in ("boost", "demote") and ov.weight_delta is not None:
                total_delta += ov.weight_delta
        # 钳位防止极端值
        return max(-50.0, min(50.0, total_delta))

    def get_notes(self, entity_id: str) -> list[str]:
        """
        获取实体的运营备注列表（override_type = 'note'）。

        用于在报告中追加说明文字。
        """
        entity_ovs = self.get_overrides("entity", entity_id)
        return [
            ov.note_text
            for ov in entity_ovs
            if ov.override_type == "note" and ov.note_text
        ]

    def should_pin(self, entity_id: str, profile: dict) -> bool:
        """
        判断实体是否应被 pin（强制推荐）到该用户画像。

        pin_conditions 支持的字段：
          - party_type: str 精确匹配
          - season: str 精确匹配
          - budget_level: str 精确匹配
          - pace: str 精确匹配
        """
        entity_ovs = self.get_overrides("entity", entity_id)
        for ov in entity_ovs:
            if ov.override_type != "pin":
                continue
            conds = ov.pin_conditions or {}
            if not conds:
                # 无条件 pin
                return True
            # 检查所有条件是否都满足
            match = all(
                profile.get(k) == v
                for k, v in conds.items()
            )
            if match:
                logger.debug(
                    "[OverrideResolver] entity %s is PINNED for profile %s",
                    entity_id, conds,
                )
                return True
        return False

    def get_all_blocked_entity_ids(self) -> set[str]:
        """返回所有被 block 的 entity_id 集合（批量过滤用）"""
        blocked = set()
        for tid, ovs in self._cache.get("entity", {}).items():
            if any(ov.override_type == "block" for ov in ovs):
                blocked.add(tid)
        return blocked

    def get_all_swap_locked_entity_ids(self) -> set[str]:
        """返回所有被 swap_lock 的 entity_id 集合"""
        locked = set()
        for tid, ovs in self._cache.get("entity", {}).items():
            if any(ov.override_type == "swap_lock" for ov in ovs):
                locked.add(tid)
        return locked

    def summary(self) -> dict:
        """返回缓存摘要（调试用）"""
        counts: dict[str, int] = defaultdict(int)
        for scope, targets in self._cache.items():
            for ovs in targets.values():
                for ov in ovs:
                    counts[ov.override_type] += 1
        return dict(counts)
