"""
实体主题亲和度（Entity Theme Affinity）

提供两个功能：
1. SEED_AFFINITY — 内置 seed 数据（20个代表性实体），用于开发阶段和测试
2. get_affinity(entity_name) — 查询实体的 affinity_scores，未收录时返回中性默认值

正式上线后，affinity_scores 应存储在 entity_tags 表（tag_namespace='affinity'）中，
届时此模块作为 fallback 兜底使用。
"""
from __future__ import annotations

# ── 默认中性 affinity（未收录实体的兜底值）──────────────────────────────────────
DEFAULT_AFFINITY: dict[str, int] = {
    "shopping": 1,
    "food": 2,
    "culture_history": 2,
    "onsen_relaxation": 0,
    "nature_outdoors": 1,
    "anime_pop_culture": 0,
    "family_kids": 2,
    "nightlife_entertainment": 1,
    "photography_scenic": 2,
}

# ── Seed 数据（来自 entity_affinity_seed_v1.json，由 GPT 基于 JNTO 生成）─────────
SEED_AFFINITY: dict[str, dict[str, int]] = {
    # ── POI ──────────────────────────────────────────────────────────────────
    "浅草寺": {
        "shopping": 3, "food": 3, "culture_history": 5, "onsen_relaxation": 0,
        "nature_outdoors": 1, "anime_pop_culture": 1, "family_kids": 3,
        "nightlife_entertainment": 1, "photography_scenic": 5,
    },
    "新宿御苑": {
        "shopping": 1, "food": 1, "culture_history": 3, "onsen_relaxation": 0,
        "nature_outdoors": 4, "anime_pop_culture": 0, "family_kids": 4,
        "nightlife_entertainment": 0, "photography_scenic": 4,
    },
    "秋叶原电器街": {
        "shopping": 5, "food": 2, "culture_history": 1, "onsen_relaxation": 0,
        "nature_outdoors": 0, "anime_pop_culture": 5, "family_kids": 2,
        "nightlife_entertainment": 3, "photography_scenic": 3,
    },
    "道顿堀": {
        "shopping": 4, "food": 5, "culture_history": 2, "onsen_relaxation": 0,
        "nature_outdoors": 0, "anime_pop_culture": 1, "family_kids": 3,
        "nightlife_entertainment": 5, "photography_scenic": 4,
    },
    "金阁寺": {
        "shopping": 1, "food": 1, "culture_history": 5, "onsen_relaxation": 0,
        "nature_outdoors": 2, "anime_pop_culture": 0, "family_kids": 3,
        "nightlife_entertainment": 0, "photography_scenic": 5,
    },
    "伏见稻荷大社": {
        "shopping": 2, "food": 1, "culture_history": 5, "onsen_relaxation": 0,
        "nature_outdoors": 2, "anime_pop_culture": 0, "family_kids": 3,
        "nightlife_entertainment": 0, "photography_scenic": 5,
    },
    "富士山五合目": {
        "shopping": 1, "food": 1, "culture_history": 2, "onsen_relaxation": 0,
        "nature_outdoors": 5, "anime_pop_culture": 0, "family_kids": 3,
        "nightlife_entertainment": 0, "photography_scenic": 5,
    },
    "环球影城USJ": {
        "shopping": 4, "food": 4, "culture_history": 0, "onsen_relaxation": 0,
        "nature_outdoors": 0, "anime_pop_culture": 4, "family_kids": 5,
        "nightlife_entertainment": 2, "photography_scenic": 5,
    },
    "登别地狱谷": {
        "shopping": 0, "food": 1, "culture_history": 2, "onsen_relaxation": 4,
        "nature_outdoors": 4, "anime_pop_culture": 0, "family_kids": 3,
        "nightlife_entertainment": 0, "photography_scenic": 4,
    },
    "美山町合掌村": {
        "shopping": 1, "food": 2, "culture_history": 4, "onsen_relaxation": 0,
        "nature_outdoors": 4, "anime_pop_culture": 0, "family_kids": 3,
        "nightlife_entertainment": 0, "photography_scenic": 5,
    },
    # ── Hotel ────────────────────────────────────────────────────────────────
    "新宿华盛顿酒店": {
        "shopping": 3, "food": 2, "culture_history": 1, "onsen_relaxation": 0,
        "nature_outdoors": 0, "anime_pop_culture": 0, "family_kids": 2,
        "nightlife_entertainment": 4, "photography_scenic": 1,
    },
    "京都岚山温泉旅馆": {
        "shopping": 1, "food": 4, "culture_history": 4, "onsen_relaxation": 5,
        "nature_outdoors": 4, "anime_pop_culture": 0, "family_kids": 3,
        "nightlife_entertainment": 1, "photography_scenic": 4,
    },
    "大阪难波东横Inn": {
        "shopping": 4, "food": 4, "culture_history": 1, "onsen_relaxation": 0,
        "nature_outdoors": 0, "anime_pop_culture": 1, "family_kids": 3,
        "nightlife_entertainment": 3, "photography_scenic": 1,
    },
    "东京迪士尼官方酒店": {
        "shopping": 3, "food": 3, "culture_history": 0, "onsen_relaxation": 0,
        "nature_outdoors": 0, "anime_pop_culture": 4, "family_kids": 5,
        "nightlife_entertainment": 2, "photography_scenic": 5,
    },
    "金泽茶屋町精品旅馆": {
        "shopping": 2, "food": 3, "culture_history": 4, "onsen_relaxation": 0,
        "nature_outdoors": 1, "anime_pop_culture": 0, "family_kids": 2,
        "nightlife_entertainment": 1, "photography_scenic": 4,
    },
    # ── Restaurant ───────────────────────────────────────────────────────────
    "筑地场外市场": {
        "shopping": 3, "food": 5, "culture_history": 3, "onsen_relaxation": 0,
        "nature_outdoors": 0, "anime_pop_culture": 0, "family_kids": 3,
        "nightlife_entertainment": 1, "photography_scenic": 4,
    },
    "一兰拉面": {
        "shopping": 0, "food": 4, "culture_history": 1, "onsen_relaxation": 0,
        "nature_outdoors": 0, "anime_pop_culture": 0, "family_kids": 2,
        "nightlife_entertainment": 2, "photography_scenic": 2,
    },
    "京都怀石料理老铺": {
        "shopping": 0, "food": 5, "culture_history": 4, "onsen_relaxation": 0,
        "nature_outdoors": 0, "anime_pop_culture": 0, "family_kids": 2,
        "nightlife_entertainment": 1, "photography_scenic": 3,
    },
    "大阪章鱼烧路边摊区": {
        "shopping": 1, "food": 5, "culture_history": 2, "onsen_relaxation": 0,
        "nature_outdoors": 0, "anime_pop_culture": 0, "family_kids": 3,
        "nightlife_entertainment": 3, "photography_scenic": 3,
    },
    "东京烧肉名店": {
        "shopping": 0, "food": 4, "culture_history": 1, "onsen_relaxation": 0,
        "nature_outdoors": 0, "anime_pop_culture": 0, "family_kids": 2,
        "nightlife_entertainment": 3, "photography_scenic": 2,
    },
}


def get_affinity(entity_name: str) -> dict[str, int]:
    """
    查询实体的 theme affinity scores。
    未收录时返回中性默认值（不抛异常）。
    """
    return SEED_AFFINITY.get(entity_name, DEFAULT_AFFINITY.copy())


def score_entity_context(
    entity_name: str,
    user_weights: dict[str, float],
) -> tuple[float, dict]:
    """
    快捷方法：用实体名称 + 用户权重直接计算 context_score。
    内部调用 compute_context_score，无需外部传入 affinity。
    """
    from app.domains.ranking.scorer import compute_context_score
    affinity = get_affinity(entity_name)
    return compute_context_score(user_weights, affinity)
