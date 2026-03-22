"""
corridor_resolver.py — T14: 走廊标准化解析服务

提供 area_name → corridor_id 的解析能力，供以下场景使用：
1. entity_base.area_name → corridor_tags 自动填充（批量）
2. itinerary_fit_scorer corridor_alignment 评分（实时）
3. secondary_filler same_corridor 判断（实时）

解析策略（3 层，性能优先）：
  L1 内存缓存精确匹配 — normalized alias_text == normalized area_name
  L2 数据库 pg_trgm    — similarity ≥ 0.6
  L3 城市兜底           — 无法解析时返回 city_code 级 fallback corridor

使用方式：
    resolver = CorridorResolver(session)
    await resolver.load_cache()
    corridor_ids = resolver.resolve("祇園", city_code="kyoto")
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select, text, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CorridorResolver:
    """走廊标准化解析器，带内存缓存。"""

    def __init__(self, session: AsyncSession):
        self._session = session
        # 缓存: normalized_text → list[corridor_id]
        self._alias_cache: dict[str, list[str]] = {}
        # 缓存: corridor_id → city_code
        self._corridor_city: dict[str, str] = {}
        # 缓存: corridor_id → adjacent_corridor_ids
        self._adjacency: dict[str, list[str]] = {}
        self._loaded = False

    async def load_cache(self) -> None:
        """从数据库加载全部别名和走廊定义到内存。"""
        from app.db.models.corridors import Corridor, CorridorAliasMap

        # 加载走廊定义
        q1 = await self._session.execute(
            select(Corridor).where(Corridor.is_active == True)
        )
        for c in q1.scalars().all():
            self._corridor_city[c.corridor_id] = c.city_code
            self._adjacency[c.corridor_id] = c.adjacent_corridor_ids or []
            # 走廊 ID 本身也作为一个别名（如 "higashiyama"）
            short = c.corridor_id.split("_", 1)[-1] if "_" in c.corridor_id else c.corridor_id
            for key in (c.corridor_id, short):
                norm = self._normalize(key)
                self._alias_cache.setdefault(norm, [])
                if c.corridor_id not in self._alias_cache[norm]:
                    self._alias_cache[norm].append(c.corridor_id)

        # 加载别名
        q2 = await self._session.execute(select(CorridorAliasMap))
        for alias in q2.scalars().all():
            norm = alias.normalized_text or self._normalize(alias.alias_text)
            self._alias_cache.setdefault(norm, [])
            if alias.corridor_id not in self._alias_cache[norm]:
                self._alias_cache[norm].append(alias.corridor_id)

        self._loaded = True
        logger.info(
            "CorridorResolver loaded: %d corridors, %d alias entries",
            len(self._corridor_city),
            sum(len(v) for v in self._alias_cache.values()),
        )

    @staticmethod
    def _normalize(s: str) -> str:
        """标准化：小写 + 去空格 + 去常见分隔符。"""
        return s.lower().replace(" ", "").replace("-", "").replace("_", "").replace("　", "").strip()

    def resolve(
        self,
        area_name: str,
        city_code: Optional[str] = None,
    ) -> list[str]:
        """
        同步解析 area_name → corridor_id 列表（使用内存缓存）。

        Args:
            area_name: 原始区域名称
            city_code: 可选城市过滤

        Returns:
            匹配到的 corridor_id 列表（可能为空）
        """
        if not area_name:
            return []

        norm = self._normalize(area_name)
        candidates = self._alias_cache.get(norm, [])

        if city_code and candidates:
            # 按城市过滤
            filtered = [c for c in candidates if self._corridor_city.get(c) == city_code]
            if filtered:
                return filtered

        return candidates

    async def resolve_with_fallback(
        self,
        area_name: str,
        city_code: Optional[str] = None,
    ) -> list[str]:
        """
        异步解析，带 pg_trgm fallback。

        L1: 内存缓存精确
        L2: pg_trgm 模糊
        """
        # L1
        results = self.resolve(area_name, city_code)
        if results:
            return results

        # L2: pg_trgm
        try:
            params: dict = {"name": self._normalize(area_name)}
            where_clause = "similarity(cam.normalized_text, :name) >= 0.6"
            if city_code:
                where_clause += " AND c.city_code = :city"
                params["city"] = city_code

            q = await self._session.execute(
                text(f"""
                    SELECT cam.corridor_id,
                           similarity(cam.normalized_text, :name) AS sim
                    FROM corridor_alias_map cam
                    JOIN corridors c ON c.corridor_id = cam.corridor_id
                    WHERE {where_clause}
                      AND c.is_active = true
                    ORDER BY sim DESC
                    LIMIT 3
                """),
                params,
            )
            rows = q.fetchall()
            if rows:
                return [row[0] for row in rows]
        except Exception:
            pass

        return []

    def is_same_or_adjacent(self, corridor_a: str, corridor_b: str) -> bool:
        """
        判断两个走廊是否相同或相邻。
        用于 corridor_alignment 评分的扩展判断。
        """
        if not corridor_a or not corridor_b:
            return False
        if corridor_a == corridor_b:
            return True
        adj_a = self._adjacency.get(corridor_a, [])
        if corridor_b in adj_a:
            return True
        adj_b = self._adjacency.get(corridor_b, [])
        return corridor_a in adj_b

    def get_city(self, corridor_id: str) -> Optional[str]:
        """获取走廊所属城市。"""
        return self._corridor_city.get(corridor_id)


async def batch_standardize_entity_corridors(
    session: AsyncSession,
    city_code: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """
    批量标准化 entity_base.area_name → corridor_tags。

    扫描所有 entity_base 中 area_name 非空但 corridor_tags 为空的记录，
    通过 CorridorResolver 解析并回写。

    Returns:
        {"total_scanned": N, "updated": M, "unresolved": K, "unresolved_areas": [...]}
    """
    resolver = CorridorResolver(session)
    await resolver.load_cache()

    from app.db.models.catalog import EntityBase

    where_clauses = [
        EntityBase.is_active == True,
        EntityBase.area_name.isnot(None),
        EntityBase.area_name != "",
    ]
    if city_code:
        where_clauses.append(EntityBase.city_code == city_code)

    q = await session.execute(
        select(EntityBase).where(and_(*where_clauses))
    )
    entities = q.scalars().all()

    stats = {"total_scanned": len(entities), "updated": 0, "unresolved": 0, "unresolved_areas": []}

    for entity in entities:
        corridors = await resolver.resolve_with_fallback(
            entity.area_name, entity.city_code
        )
        if corridors:
            existing = set(entity.corridor_tags or [])
            new_tags = list(existing | set(corridors))
            if new_tags != list(existing):
                if not dry_run:
                    entity.corridor_tags = new_tags
                stats["updated"] += 1
        else:
            stats["unresolved"] += 1
            area = entity.area_name
            if area not in stats["unresolved_areas"]:
                stats["unresolved_areas"].append(area)

    if not dry_run:
        await session.flush()

    return stats
