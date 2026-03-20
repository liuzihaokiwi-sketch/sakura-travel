"""
问卷答案 → theme_weights 转换器

数据来源：data/questionnaire_to_theme_weights_rules_v1.json
功能：
  1. QUESTIONNAIRE_SIGNALS — 5道题的选项→权重增量映射
  2. compute_weights_from_answers() — 给定问卷答案，输出归一化后的 theme_weights
  3. POST_PROCESSING_RULES — 业务规则微调（如 family_kids 高时压 nightlife）
"""
from __future__ import annotations

# ── 5道问卷题的信号规则 ────────────────────────────────────────────────────────
# 格式：{question_id: {选项文字: {theme_key: delta}}}

QUESTIONNAIRE_SIGNALS: dict[str, dict[str, dict[str, float]]] = {
    "q1": {  # 最期待哪些体验（主权重入口）
        "购物血拼":    {"shopping": 0.5},
        "美食探店":    {"food": 0.5},
        "泡温泉":      {"onsen_relaxation": 0.6},
        "自然风景":    {"nature_outdoors": 0.5},
        "历史文化":    {"culture_history": 0.5},
        "动漫圣地":    {"anime_pop_culture": 0.7},
        "亲子游乐":    {"family_kids": 0.6},
        "夜生活":      {"nightlife_entertainment": 0.5},
        "拍照出片":    {"photography_scenic": 0.5},
    },
    "q2": {  # 同行人
        "情侣/配偶":   {"photography_scenic": 0.1, "food": 0.1},
        "带小孩":      {"family_kids": 0.4},
        "独自旅行":    {"culture_history": 0.1, "onsen_relaxation": 0.1},
        "带父母/长辈": {"onsen_relaxation": 0.2, "culture_history": 0.1},
    },
    "q3": {  # 是否第一次
        "第一次去":         {"shopping": 0.1, "food": 0.1, "photography_scenic": 0.1},
        "去过一次或多次":   {"culture_history": 0.2, "onsen_relaxation": 0.1},
    },
    "q4": {  # 节奏偏好
        "想住好一点、慢慢玩":  {"onsen_relaxation": 0.3},
        "能多看就多看":        {"photography_scenic": 0.1, "culture_history": 0.1},
        "不赶景点，重体验":    {"food": 0.2, "onsen_relaxation": 0.2, "culture_history": 0.1},
        "想玩热闹一点":        {"nightlife_entertainment": 0.3, "shopping": 0.2},
    },
    "q5": {  # 特别想安排的项目（第二强入口）
        "樱花/红叶":            {"nature_outdoors": 0.3, "photography_scenic": 0.3},
        "富士山/雪景":          {"nature_outdoors": 0.4, "photography_scenic": 0.4},
        "寺庙神社/古街":        {"culture_history": 0.4, "photography_scenic": 0.2},
        "游乐园/动物园/水族馆": {"family_kids": 0.5},
        "买动漫周边/圣地巡礼":  {"anime_pop_culture": 0.6, "shopping": 0.2},
        "会席/怀石/高级和食":   {"food": 0.4, "culture_history": 0.1},
        "温泉旅馆住一晚":       {"onsen_relaxation": 0.5},
        "酒吧/夜景/夜游":       {"nightlife_entertainment": 0.4, "photography_scenic": 0.1},
    },
}

# 所有合法主题维度
ALL_THEMES: tuple[str, ...] = (
    "shopping", "food", "culture_history", "onsen_relaxation",
    "nature_outdoors", "anime_pop_culture", "family_kids",
    "nightlife_entertainment", "photography_scenic",
)


def compute_weights_from_answers(
    answers: dict[str, list[str]],
) -> dict[str, float]:
    """
    根据问卷答案计算 theme_weights（已归一化到 [0, 1]）。

    Args:
        answers: {question_id: [选中的选项文字, ...]}
                 例：{"q1": ["美食探店", "拍照出片"], "q2": ["情侣/配偶"], ...}

    Returns:
        {theme_key: weight (0.0-1.0)}，所有9个维度都有值

    流程：
        1. 累加各题命中选项的 delta
        2. 单维度上限 clamp 到 1.0
        3. 应用业务规则后处理
        4. 归一化（可选，调用方按需使用原始值或归一化值）
    """
    # Step 1: 累加
    raw: dict[str, float] = {t: 0.0 for t in ALL_THEMES}
    for qid, selected_options in answers.items():
        signals = QUESTIONNAIRE_SIGNALS.get(qid, {})
        for option in selected_options:
            deltas = signals.get(option, {})
            for theme, delta in deltas.items():
                raw[theme] = min(1.0, raw[theme] + delta)

    # Step 2: 后处理规则
    raw = _apply_post_processing(raw)

    return raw


def _apply_post_processing(weights: dict[str, float]) -> dict[str, float]:
    """
    应用业务互斥/互补规则（来自 aggregation_rules.post_processing）。
    修改 weights 副本，不影响原始输入。
    """
    w = weights.copy()

    # 规则1：带娃高时，压制夜生活
    if w.get("family_kids", 0) >= 0.6:
        w["nightlife_entertainment"] = min(w.get("nightlife_entertainment", 0), 0.2)

    # 规则2：动漫高时，购物至少保底 0.2
    if w.get("anime_pop_culture", 0) >= 0.7:
        w["shopping"] = max(w.get("shopping", 0), 0.2)

    # 规则3：温泉很高时，压制夜生活
    if w.get("onsen_relaxation", 0) >= 0.8:
        w["nightlife_entertainment"] = min(w.get("nightlife_entertainment", 0), 0.1)

    return w


# ── 预置画像（来自 profiles，用于推荐系统冷启动/测试）────────────────────────────
PRESET_PROFILES: dict[str, dict[str, float]] = {
    "first_time_couple_sakura": {
        "shopping": 0.7, "food": 0.8, "culture_history": 0.3,
        "onsen_relaxation": 0.1, "nature_outdoors": 0.6,
        "anime_pop_culture": 0.0, "family_kids": 0.0,
        "nightlife_entertainment": 0.2, "photography_scenic": 0.8,
    },
    "first_time_family_disney": {
        "shopping": 0.1, "food": 0.4, "culture_history": 0.1,
        "onsen_relaxation": 0.3, "nature_outdoors": 0.3,
        "anime_pop_culture": 0.2, "family_kids": 1.0,
        "nightlife_entertainment": 0.0, "photography_scenic": 0.3,
    },
    "repeat_solo_culture_onsen": {
        "shopping": 0.0, "food": 0.3, "culture_history": 0.9,
        "onsen_relaxation": 0.8, "nature_outdoors": 0.3,
        "anime_pop_culture": 0.0, "family_kids": 0.0,
        "nightlife_entertainment": 0.0, "photography_scenic": 0.2,
    },
    "anime_pilgrimage_shopper": {
        "shopping": 0.8, "food": 0.2, "culture_history": 0.0,
        "onsen_relaxation": 0.0, "nature_outdoors": 0.0,
        "anime_pop_culture": 1.0, "family_kids": 0.0,
        "nightlife_entertainment": 0.2, "photography_scenic": 0.4,
    },
    "retired_couple_onsen_slow": {
        "shopping": 0.1, "food": 0.7, "culture_history": 0.3,
        "onsen_relaxation": 1.0, "nature_outdoors": 0.3,
        "anime_pop_culture": 0.0, "family_kids": 0.0,
        "nightlife_entertainment": 0.0, "photography_scenic": 0.2,
    },
    "photo_couple_fuji_kyoto": {
        "shopping": 0.1, "food": 0.2, "culture_history": 0.5,
        "onsen_relaxation": 0.1, "nature_outdoors": 0.8,
        "anime_pop_culture": 0.0, "family_kids": 0.0,
        "nightlife_entertainment": 0.0, "photography_scenic": 1.0,
    },
}
