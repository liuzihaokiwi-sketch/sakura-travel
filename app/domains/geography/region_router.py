"""
区域路由器（Region Router）

根据用户画像（user_type + trip_profile）对 12 个日本区域评分并排序，
输出推荐区域列表，作为 Candidate Recall 的前置过滤层。

数据来源：data/japan_region_usertype_matrix_v1.json
设计原则：
  - 纯函数，无 I/O，方便单测
  - 支持 user_type 精确匹配 + fallback 到最近邻
  - 输出按分数降序排列，附带分数和推荐理由
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ── 区域定义（来自 seed data，12 个区域）────────────────────────────────────────

REGIONS: dict[str, str] = {
    "R01": "东京都市圈",
    "R02": "东京近郊文化海滨圈",
    "R03": "富士箱根伊豆圈",
    "R04": "关东山岳温泉圈",
    "R05": "关西经典圈",
    "R06": "北海道圈",
    "R07": "东北季节圈",
    "R08": "北陆深度圈",
    "R09": "日本阿尔卑斯·飞驒圈",
    "R10": "濑户内·广岛圈",
    "R11": "九州温泉火山圈",
    "R12": "冲绳海岛圈",
}

# ── 用户类型 × 区域匹配矩阵（来自 japan_region_usertype_matrix_v1.json）─────────

REGION_MATRIX: dict[str, dict[str, int]] = {
    "first_time_couple": {
        "R01": 92, "R02": 84, "R03": 90, "R04": 75,
        "R05": 95, "R06": 82, "R07": 55, "R08": 68,
        "R09": 70, "R10": 72, "R11": 78, "R12": 80,
    },
    "first_time_family": {
        "R01": 90, "R02": 85, "R03": 82, "R04": 78,
        "R05": 93, "R06": 84, "R07": 60, "R08": 65,
        "R09": 62, "R10": 70, "R11": 80, "R12": 88,
    },
    "repeat_couple": {
        "R01": 72, "R02": 76, "R03": 85, "R04": 83,
        "R05": 78, "R06": 86, "R07": 82, "R08": 92,
        "R09": 87, "R10": 88, "R11": 90, "R12": 84,
    },
    "repeat_solo": {
        "R01": 80, "R02": 78, "R03": 70, "R04": 82,
        "R05": 81, "R06": 84, "R07": 88, "R08": 86,
        "R09": 90, "R10": 87, "R11": 85, "R12": 65,
    },
    "onsen_focused": {
        "R01": 20, "R02": 45, "R03": 92, "R04": 94,
        "R05": 68, "R06": 84, "R07": 88, "R08": 90,
        "R09": 82, "R10": 55, "R11": 96, "R12": 10,
    },
    "culture_deep": {
        "R01": 84, "R02": 80, "R03": 60, "R04": 74,
        "R05": 98, "R06": 68, "R07": 85, "R08": 93,
        "R09": 86, "R10": 82, "R11": 78, "R12": 72,
    },
}

# 各用户类型预计算的 Top-3 推荐区域
TOP_REGIONS: dict[str, list[str]] = {
    "first_time_couple": ["R05", "R01", "R03"],
    "first_time_family": ["R05", "R01", "R12"],
    "repeat_couple":     ["R08", "R11", "R10"],
    "repeat_solo":       ["R09", "R07", "R10"],
    "onsen_focused":     ["R11", "R04", "R03"],
    "culture_deep":      ["R05", "R08", "R09"],
}

# party_type → user_type 的映射（用于从 trip_profile 推断）
PARTY_TYPE_TO_USER_TYPE: dict[str, str] = {
    "couple":           "first_time_couple",   # 默认首次，repeat 通过 is_repeat 覆盖
    "family_child":     "first_time_family",
    "family_no_child":  "first_time_couple",
    "solo":             "repeat_solo",
    "group":            "first_time_couple",
    "senior":           "first_time_family",
}


# ── 输出类型 ──────────────────────────────────────────────────────────────────

@dataclass
class RegionScore:
    region_id: str
    region_name: str
    score: int                  # 0-100
    is_top_pick: bool           # 是否在该用户类型的 Top-3 推荐中


# ── 核心函数 ──────────────────────────────────────────────────────────────────

def resolve_user_type(
    party_type: str | None,
    is_repeat_visitor: bool = False,
    theme_weights: dict[str, float] | None = None,
) -> str:
    """
    从 trip_profile 信息推断用户类型（user_type）。

    优先级：
    1. 主题权重暗示（onsen_relaxation 主导 → onsen_focused；culture_history 主导 → culture_deep）
    2. is_repeat_visitor + party_type 组合
    3. 兜底用 first_time_couple
    """
    weights = theme_weights or {}

    # 主题主导判断（最高权重维度 > 0.4 才触发）
    if weights:
        top_theme = max(weights, key=lambda k: weights[k], default=None)
        top_val = weights.get(top_theme, 0) if top_theme else 0
        if top_theme == "onsen_relaxation" and top_val >= 0.4:
            return "onsen_focused"
        if top_theme == "culture_history" and top_val >= 0.4:
            return "culture_deep"

    # repeat + solo
    if is_repeat_visitor and party_type == "solo":
        return "repeat_solo"

    # repeat + couple/group
    if is_repeat_visitor and party_type in ("couple", "group", "family_no_child"):
        return "repeat_couple"

    # 首次 family
    if party_type in ("family_child", "senior"):
        return "first_time_family"

    # 首次 couple（默认兜底）
    return PARTY_TYPE_TO_USER_TYPE.get(party_type or "", "first_time_couple")


def rank_regions(
    user_type: str,
    top_n: int | None = None,
    min_score: int = 0,
) -> list[RegionScore]:
    """
    对所有区域按 user_type 评分排序，返回 RegionScore 列表（降序）。

    Args:
        user_type: 用户类型 key（见 REGION_MATRIX）
        top_n:     只返回前 N 个，None 返回全部
        min_score: 过滤掉分数低于此值的区域

    Returns:
        RegionScore 列表，按 score 降序
    """
    scores = REGION_MATRIX.get(user_type, REGION_MATRIX["first_time_couple"])
    top_picks = set(TOP_REGIONS.get(user_type, []))

    results = [
        RegionScore(
            region_id=rid,
            region_name=REGIONS[rid],
            score=score,
            is_top_pick=rid in top_picks,
        )
        for rid, score in scores.items()
        if score >= min_score
    ]

    results.sort(key=lambda r: r.score, reverse=True)

    if top_n is not None:
        results = results[:top_n]

    return results


def recommend_regions_for_profile(
    party_type: str | None = None,
    is_repeat_visitor: bool = False,
    theme_weights: dict[str, float] | None = None,
    top_n: int = 3,
    min_score: int = 60,
) -> dict[str, Any]:
    """
    一站式接口：从 trip_profile 推断 user_type，返回推荐区域列表。

    Args:
        party_type:        来自 trip_profiles.party_type
        is_repeat_visitor: 是否二刷（可从 trip_profiles 或用户历史推断）
        theme_weights:     来自 trip_profiles 主题偏好权重
        top_n:             返回前 N 个推荐区域
        min_score:         最低分阈值

    Returns:
        {
          "user_type": str,
          "regions": [{"region_id", "region_name", "score", "is_top_pick"}, ...],
          "city_codes": [str, ...]   # 区域对应的 city_code 列表，用于下游 candidate 召回
        }
    """
    user_type = resolve_user_type(party_type, is_repeat_visitor, theme_weights)
    ranked = rank_regions(user_type, top_n=top_n, min_score=min_score)

    return {
        "user_type": user_type,
        "regions": [
            {
                "region_id": r.region_id,
                "region_name": r.region_name,
                "score": r.score,
                "is_top_pick": r.is_top_pick,
            }
            for r in ranked
        ],
        "city_codes": _regions_to_city_codes([r.region_id for r in ranked]),
    }


# ── 区域 → city_code 映射（供下游 candidate 召回使用）──────────────────────────

_REGION_TO_CITIES: dict[str, list[str]] = {
    "R01": ["tokyo"],
    "R02": ["kamakura", "yokohama", "chiba"],
    "R03": ["hakone", "atami", "shimoda", "fuji"],
    "R04": ["nikko", "kusatsu", "karuizawa"],
    "R05": ["kyoto", "osaka", "nara", "kobe"],
    "R06": ["sapporo", "hakodate", "asahikawa", "kushiro"],
    "R07": ["sendai", "aomori", "akita", "yamagata"],
    "R08": ["kanazawa", "toyama", "fukui"],
    "R09": ["matsumoto", "takayama", "nagano"],
    "R10": ["hiroshima", "okayama", "takamatsu", "naoshima"],
    "R11": ["fukuoka", "beppu", "yufuin", "nagasaki", "kumamoto"],
    "R12": ["naha", "ishigaki", "miyako"],
}


def _regions_to_city_codes(region_ids: list[str]) -> list[str]:
    """将区域 ID 列表展开为 city_code 列表（去重，保持顺序）。"""
    seen: set[str] = set()
    result: list[str] = []
    for rid in region_ids:
        for city in _REGION_TO_CITIES.get(rid, []):
            if city not in seen:
                seen.add(city)
                result.append(city)
    return result


# ── 种子数据加载（可选，覆盖内联数据）──────────────────────────────────────────

# 路线绑定数据（route_id → {cities: [...], regions: [...]}）
_ROUTE_REGION_BINDING: dict[str, dict] = {}

# 路线骨架模板（route_id → template metadata）
_ROUTE_SKELETON_TEMPLATES: dict[str, dict] = {}


def load_seed_data(data_dir: str | None = None) -> dict[str, bool]:
    """
    从 JSON 文件加载区域种子数据，更新模块级全局字典。
    允许在应用启动时（lifespan）调用，用外部 JSON 覆盖内置数据。

    Args:
        data_dir: 数据目录路径（默认为项目根目录 data/）

    Returns:
        各文件加载状态的字典，True = 成功，False = 文件不存在
    """
    import json
    from pathlib import Path

    if data_dir is None:
        data_dir = str(Path(__file__).parent.parent.parent.parent / "data" / "seed")

    data_path = Path(data_dir)
    loaded: dict[str, bool] = {}

    # 1. 加载区域用户类型矩阵（更新 REGION_MATRIX）
    matrix_file = data_path / "japan_region_usertype_matrix_v1.json"
    if matrix_file.exists():
        try:
            with open(matrix_file, encoding="utf-8") as f:
                data = json.load(f)
            REGION_MATRIX.update(data)
            loaded["region_matrix"] = True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"加载 region_matrix 失败: {e}")
            loaded["region_matrix"] = False
    else:
        loaded["region_matrix"] = False  # 不存在，使用内置数据

    # 2. 加载路线-区域绑定
    binding_file = data_path / "route_region_binding_v1.json"
    if binding_file.exists():
        try:
            with open(binding_file, encoding="utf-8") as f:
                _ROUTE_REGION_BINDING.update(json.load(f))
            loaded["route_binding"] = True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"加载 route_binding 失败: {e}")
            loaded["route_binding"] = False
    else:
        loaded["route_binding"] = False

    # 3. 加载路线骨架模板
    skeleton_file = data_path / "p0_route_skeleton_templates_v1.json"
    if skeleton_file.exists():
        try:
            with open(skeleton_file, encoding="utf-8") as f:
                _ROUTE_SKELETON_TEMPLATES.update(json.load(f))
            loaded["route_skeleton"] = True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"加载 route_skeleton 失败: {e}")
            loaded["route_skeleton"] = False
    else:
        loaded["route_skeleton"] = False

    return loaded


def get_cities_for_route(route_id: str) -> list[str]:
    """
    根据 route_region_binding 返回路线覆盖的城市列表。
    若路线未找到，返回空列表。

    Args:
        route_id: 路线 ID（如 "RT_TOKYO_KYOTO"）

    Returns:
        城市代码列表（如 ["tokyo", "kyoto", "osaka"]）
    """
    route = _ROUTE_REGION_BINDING.get(route_id)
    if route is None:
        return []
    return list(route.get("cities", []))


async def get_entities_by_region(
    session: Any,
    region_id: str,
    entity_type: str | None = None,
    limit: int = 100,
) -> list[Any]:
    """
    根据区域 ID 查询该区域内的实体列表。
    区域覆盖城市来自 _REGION_TO_CITIES 字典。

    Args:
        session:     AsyncSession
        region_id:   区域 ID（如 "R01"）
        entity_type: 可选类型过滤 poi/hotel/restaurant
        limit:       返回上限

    Returns:
        EntityBase 对象列表
    """
    from sqlalchemy import select as _select
    from app.db.models.catalog import EntityBase

    city_codes = _REGION_TO_CITIES.get(region_id, [])
    if not city_codes:
        return []

    stmt = (
        _select(EntityBase)
        .where(
            EntityBase.city_code.in_(city_codes),
            EntityBase.is_active == True,  # noqa: E712
        )
        .limit(limit)
    )
    if entity_type:
        stmt = stmt.where(EntityBase.entity_type == entity_type)

    result = await session.execute(stmt)
    return list(result.scalars().all())
