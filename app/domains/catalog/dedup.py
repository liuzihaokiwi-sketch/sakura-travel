"""
实体去重引擎

在 upsert_entity 的简单精确匹配之上，提供模糊匹配和地理距离判断：

1. 名称规范化（strip、全角→半角、去除常见后缀）
2. 模糊匹配（Levenshtein 距离 ≤ 2）
3. 地理距离（同城市 500m 内同类型 → 疑似重复）
4. 综合判定 → 返回匹配的 entity 或 None + 可信度标记建议
"""
from __future__ import annotations

import logging
import math
import re
import unicodedata
from typing import Optional, Tuple

from sqlalchemy import select, func, cast, Float
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 名称规范化
# ─────────────────────────────────────────────────────────────────────────────

# 常见后缀：去掉后比较
_STRIP_SUFFIXES = re.compile(
    r"[\s]*(店|支店|本店|本館|別館|分店|旗舰店|总店|新馆|旧馆|（.+?）|\(.+?\))$"
)

# 全角 → 半角映射
_FULLWIDTH_OFFSET = 0xFEE0


def normalize_name(name: str) -> str:
    """
    规范化实体名称用于去重比较

    步骤:
    1. Unicode NFKC 正规化（全角→半角、合字分解）
    2. 去除前后空白
    3. 去除常见后缀（店/支店/本店/本館 等）
    4. 转小写（英文部分）
    5. 压缩连续空白为单个空格
    """
    if not name:
        return ""

    # NFKC: 全角数字→半角、组合字符分解
    s = unicodedata.normalize("NFKC", name)

    # 去除前后空白
    s = s.strip()

    # 去除常见后缀
    s = _STRIP_SUFFIXES.sub("", s).strip()

    # 转小写（英文）
    s = s.lower()

    # 压缩空白
    s = re.sub(r"\s+", " ", s)

    return s


# ─────────────────────────────────────────────────────────────────────────────
# Levenshtein 距离（纯 Python 实现，短字符串足够快）
# ─────────────────────────────────────────────────────────────────────────────

def levenshtein_distance(s1: str, s2: str) -> int:
    """计算两个字符串的编辑距离"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            # 插入、删除、替换
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


# ─────────────────────────────────────────────────────────────────────────────
# 地理距离（Haversine 公式）
# ─────────────────────────────────────────────────────────────────────────────

def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """两个坐标点之间的距离（米）"""
    R = 6_371_000  # 地球半径（米）
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─────────────────────────────────────────────────────────────────────────────
# 模糊去重查询
# ─────────────────────────────────────────────────────────────────────────────

# 匹配结果
MATCH_EXACT = "exact"           # 精确匹配（已有逻辑）
MATCH_FUZZY_NAME = "fuzzy_name" # 名称模糊匹配
MATCH_GEO_NEAR = "geo_near"    # 地理距离近 + 名称相似
MATCH_NONE = "none"             # 无匹配


async def find_fuzzy_duplicate(
    session: AsyncSession,
    name_zh: str,
    city_code: str,
    entity_type: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    name_distance_threshold: int = 2,
    geo_distance_meters: float = 500.0,
) -> Tuple[Optional[EntityBase], str]:
    """
    模糊去重：在精确匹配之外，通过名称模糊匹配和地理距离找到疑似重复实体。

    匹配策略（按优先级）：
    1. 精确 name_zh 匹配 → MATCH_EXACT
    2. 规范化名称精确匹配 → MATCH_EXACT
    3. 有坐标时：500m 内同类型实体 + 名称 Levenshtein ≤ threshold → MATCH_GEO_NEAR
    4. 无坐标时：名称 Levenshtein ≤ threshold → MATCH_FUZZY_NAME
    5. 均无匹配 → MATCH_NONE

    Args:
        session: 数据库会话
        name_zh: 实体中文名
        city_code: 城市代码
        entity_type: 实体类型
        lat, lng: 坐标（可选）
        name_distance_threshold: 名称编辑距离阈值
        geo_distance_meters: 地理距离阈值（米）

    Returns:
        (matched_entity, match_type) — entity 为 None 时 match_type 为 "none"
    """
    normalized_input = normalize_name(name_zh)

    if not normalized_input or not city_code:
        return None, MATCH_NONE

    # ── 1. 精确匹配 ──────────────────────────────────────────────────────────
    result = await session.execute(
        select(EntityBase).where(
            EntityBase.name_zh == name_zh,
            EntityBase.city_code == city_code,
            EntityBase.entity_type == entity_type,
        )
    )
    exact = result.scalar_one_or_none()
    if exact:
        return exact, MATCH_EXACT

    # ── 2. 拉取同城市同类型候选集（限制数量，避免全表扫描）──────────────────
    candidates_result = await session.execute(
        select(EntityBase).where(
            EntityBase.city_code == city_code,
            EntityBase.entity_type == entity_type,
            EntityBase.is_active == True,
        ).limit(500)
    )
    candidates = candidates_result.scalars().all()

    if not candidates:
        return None, MATCH_NONE

    # ── 3. 规范化名称匹配 + 模糊匹配 + 地理距离 ─────────────────────────────
    best_match: Optional[EntityBase] = None
    best_score = float("inf")  # 越小越好
    best_type = MATCH_NONE

    for cand in candidates:
        cand_normalized = normalize_name(cand.name_zh or "")

        # 规范化后精确匹配
        if cand_normalized == normalized_input:
            return cand, MATCH_EXACT

        # 名称编辑距离
        name_dist = levenshtein_distance(normalized_input, cand_normalized)

        # 有坐标时：地理距离 + 名称距离综合判断
        if (lat is not None and lng is not None
                and cand.lat is not None and cand.lng is not None):
            geo_dist = haversine_meters(
                float(lat), float(lng), float(cand.lat), float(cand.lng)
            )

            # 500m 内 + 名称编辑距离 ≤ 阈值 → 疑似重复
            if geo_dist <= geo_distance_meters and name_dist <= name_distance_threshold:
                score = geo_dist + name_dist * 100  # 综合分
                if score < best_score:
                    best_score = score
                    best_match = cand
                    best_type = MATCH_GEO_NEAR

            # 100m 内 + 名称距离 ≤ 4 → 也算（同一栋楼不同写法）
            if geo_dist <= 100 and name_dist <= 4:
                score = geo_dist + name_dist * 50
                if score < best_score:
                    best_score = score
                    best_match = cand
                    best_type = MATCH_GEO_NEAR

        # 无坐标时：纯名称模糊匹配（阈值更严格）
        elif name_dist <= max(1, name_distance_threshold - 1):
            score = name_dist * 200
            if score < best_score:
                best_score = score
                best_match = cand
                best_type = MATCH_FUZZY_NAME

    if best_match:
        logger.info(
            "[dedup] Fuzzy match: '%s' ≈ '%s' (type=%s, score=%.1f)",
            name_zh, best_match.name_zh, best_type, best_score,
        )

    return best_match, best_type
