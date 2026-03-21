"""
4 维产品模型 — Four-Dimension Product Model (M8)

对照文档 buchong §6，定义 4 个维度：
  1. theme_family    — 主题家族（7 种）
  2. budget_focus    — 预算偏向（5 种，已在 TripProfile 存在）
  3. pace_preference — 节奏偏好（3 种，TripProfile 已有）
  4. trip_style      — 行程类型（3 种）

本模块提供：
  - 枚举定义
  - 从 TripProfile / user_input 推断 theme_family 的规则
  - assembler 变体选择（根据 4 维决定生成策略）
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional


# ── 枚举定义 ──────────────────────────────────────────────────────────────────

class ThemeFamily(str, Enum):
    """主题家族：决定片段库搜索权重 + 软规则权重包"""
    CLASSIC_FIRST    = "classic_first"     # 首次来日，打卡经典
    NATURE_RELAXED   = "nature_relaxed"    # 自然风光 + 轻松节奏
    FOOD_SHOPPING    = "food_shopping"     # 美食购物驱动
    CULTURE_DEEP     = "culture_deep"      # 文化深度探访（重访用户）
    LUXURY_EXPERIENCE = "luxury_experience" # 高端体验（premium+纪念日）
    AESTHETIC_CULTURE = "aesthetic_culture" # 审美出片 + 文化融合
    LOCAL_DEEP       = "local_deep"        # 本地深度（二刷用户）
    ONSEN_RETREAT    = "onsen_retreat"     # 温泉度假
    FAMILY_RELAXED   = "family_relaxed"   # 亲子/带父母，体力优先
    CULTURE_OFFBEAT  = "culture_offbeat"   # 小众文化目的地


class BudgetFocus(str, Enum):
    """预算偏向：决定住宿/餐饮/体验的分配比例"""
    BETTER_STAY       = "better_stay"
    BETTER_FOOD       = "better_food"
    BETTER_EXPERIENCE = "better_experience"
    BALANCED          = "balanced"
    BEST_VALUE        = "best_value"


class PacePreference(str, Enum):
    RELAXED  = "relaxed"
    MODERATE = "moderate"
    ACTIVE   = "active"


class TripStyle(str, Enum):
    ONE_CITY   = "one_city"
    MULTI_CITY = "multi_city"
    CIRCUIT    = "circuit"     # 环线（出发=终点不同城市）


# ── 主题家族推断规则 ──────────────────────────────────────────────────────────

def infer_theme_family(profile: dict[str, Any]) -> ThemeFamily:
    """
    从 TripProfile 数据（或 user_input）推断 theme_family。
    规则按优先级从高到低执行，第一个匹配的返回。

    Parameters
    ----------
    profile : dict
        TripProfile 字典或 user_input 字典
    """
    experience    = profile.get("japan_experience", "first_time")
    budget        = profile.get("budget_level", "mid")
    pace          = profile.get("pace_preference", "moderate")
    party_type    = profile.get("party_type", "")
    special_occ   = profile.get("special_occasion", "")
    trip_purpose  = profile.get("trip_purpose", "")
    must_have     = profile.get("must_have_tags", []) or []
    city_codes    = _extract_city_codes(profile)
    has_elderly   = profile.get("has_elderly", False)
    avoid_tags    = profile.get("avoid_tags", []) or []

    # 规则 1：带父母/亲子低体力
    if has_elderly or party_type == "family" and pace == "relaxed":
        return ThemeFamily.FAMILY_RELAXED

    # 规则 2：高端纪念日
    if budget in ("premium", "luxury") and special_occ in ("anniversary", "honeymoon", "proposal"):
        return ThemeFamily.LUXURY_EXPERIENCE

    # 规则 3：审美出片
    if trip_purpose == "aesthetic_photo" or any(
        t in must_have for t in ["photo", "aesthetic", "fushimi_inari_night", "tofukuji_momiji"]
    ):
        return ThemeFamily.AESTHETIC_CULTURE

    # 规则 4：温泉度假
    if any(t in must_have for t in ["onsen_ryokan", "onsen", "ryokan"]):
        return ThemeFamily.ONSEN_RETREAT

    # 规则 5：二刷本地深度
    if experience == "repeat_visitor" and any(t in avoid_tags for t in [
        "asakusa", "tokyo_tower", "shibuya_crossing"
    ]):
        return ThemeFamily.LOCAL_DEEP

    # 规则 6：文化深度（重访用户）
    if experience == "repeat_visitor" and any(t in must_have for t in [
        "tea_ceremony", "noh_theater", "high_end_kaiseki", "kabuki"
    ]):
        return ThemeFamily.CULTURE_DEEP

    # 规则 7：美食购物
    if any(t in must_have for t in [
        "dotonbori", "kuromon_market", "shinsaibashi", "tsukiji"
    ]) or party_type == "friends":
        return ThemeFamily.FOOD_SHOPPING

    # 规则 8：自然放松（北海道/箱根/冲绳）
    if any(c in city_codes for c in ["hokkaido", "hakone", "okinawa", "nikko"]):
        if pace == "relaxed":
            return ThemeFamily.NATURE_RELAXED

    # 规则 9：小众文化目的地
    OFFBEAT_CITIES = {"kanazawa", "takayama", "matsumoto", "nagano", "hiroshima"}
    if set(city_codes) & OFFBEAT_CITIES:
        return ThemeFamily.CULTURE_OFFBEAT

    # 默认：首次经典
    return ThemeFamily.CLASSIC_FIRST


# ── Assembler 变体选择 ─────────────────────────────────────────────────────────

class AssemblerVariant:
    """
    根据 4 维产品模型决定生成器行为：
      - generation_mode: fragment_first / ai_first / hybrid
      - soft_rule_pack:  对应的软规则权重包 ID
      - template_variant: standard / premium / nature / family
      - max_pois_per_day: 日均景点数上限
    """
    def __init__(
        self,
        generation_mode: str,
        soft_rule_pack: str,
        template_variant: str,
        max_pois_per_day: int,
        notes: str = "",
    ):
        self.generation_mode   = generation_mode
        self.soft_rule_pack    = soft_rule_pack
        self.template_variant  = template_variant
        self.max_pois_per_day  = max_pois_per_day
        self.notes             = notes

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation_mode": self.generation_mode,
            "soft_rule_pack": self.soft_rule_pack,
            "template_variant": self.template_variant,
            "max_pois_per_day": self.max_pois_per_day,
            "notes": self.notes,
        }


# 变体映射表：(theme_family, budget_level) → AssemblerVariant
_VARIANT_MAP: dict[tuple[str, str], AssemblerVariant] = {
    # 首次经典
    (ThemeFamily.CLASSIC_FIRST, "budget"):  AssemblerVariant("fragment_first", "classic_budget",    "standard", 4),
    (ThemeFamily.CLASSIC_FIRST, "mid"):     AssemblerVariant("fragment_first", "classic_mid",       "standard", 4),
    (ThemeFamily.CLASSIC_FIRST, "premium"): AssemblerVariant("fragment_first", "classic_premium",   "premium",  3),
    # 自然放松
    (ThemeFamily.NATURE_RELAXED, "mid"):    AssemblerVariant("hybrid",         "nature_relaxed",    "nature",   2),
    (ThemeFamily.NATURE_RELAXED, "premium"):AssemblerVariant("hybrid",         "nature_premium",    "premium",  2),
    # 美食购物
    (ThemeFamily.FOOD_SHOPPING, "mid"):     AssemblerVariant("fragment_first", "food_shopping",     "standard", 5),
    # 文化深度
    (ThemeFamily.CULTURE_DEEP, "premium"):  AssemblerVariant("ai_first",       "culture_deep",      "premium",  3),
    (ThemeFamily.CULTURE_DEEP, "mid"):      AssemblerVariant("hybrid",         "culture_mid",       "standard", 3),
    # 高端体验
    (ThemeFamily.LUXURY_EXPERIENCE, "premium"): AssemblerVariant("ai_first",   "luxury",            "premium",  2, "纪念日/蜜月特殊说明"),
    (ThemeFamily.LUXURY_EXPERIENCE, "luxury"):  AssemblerVariant("ai_first",   "luxury_plus",       "premium",  2),
    # 审美出片
    (ThemeFamily.AESTHETIC_CULTURE, "mid"):  AssemblerVariant("hybrid",        "aesthetic",         "standard", 3),
    # 本地深度
    (ThemeFamily.LOCAL_DEEP, "mid"):         AssemblerVariant("ai_first",      "local_deep",        "standard", 3, "避免经典打卡点"),
    # 温泉度假
    (ThemeFamily.ONSEN_RETREAT, "premium"):  AssemblerVariant("fragment_first","onsen_premium",     "premium",  2),
    (ThemeFamily.ONSEN_RETREAT, "mid"):      AssemblerVariant("fragment_first","onsen_mid",         "nature",   2),
    # 亲子/低体力
    (ThemeFamily.FAMILY_RELAXED, "mid"):     AssemblerVariant("hybrid",        "family_relaxed",    "family",   2, "无障碍优先"),
    # 小众目的地
    (ThemeFamily.CULTURE_OFFBEAT, "mid"):    AssemblerVariant("ai_first",      "offbeat",           "standard", 3, "片段库可能无覆盖"),
}

_DEFAULT_VARIANT = AssemblerVariant("hybrid", "classic_mid", "standard", 4)


def select_assembler_variant(
    theme_family: ThemeFamily | str,
    budget_level: str = "mid",
) -> AssemblerVariant:
    """
    根据 theme_family + budget_level 选择最匹配的 AssemblerVariant。
    找不到精确匹配时降级到同 theme_family 的 mid，再降级到 default。
    """
    tf = ThemeFamily(theme_family) if isinstance(theme_family, str) else theme_family
    # 精确匹配
    v = _VARIANT_MAP.get((tf, budget_level))
    if v:
        return v
    # 降级到 mid
    v = _VARIANT_MAP.get((tf, "mid"))
    if v:
        return v
    # 全局默认
    return _DEFAULT_VARIANT


def resolve_product_model(profile: dict[str, Any]) -> dict[str, Any]:
    """
    一步获取完整 4 维产品模型决策。

    Parameters
    ----------
    profile : dict
        TripProfile 或 user_input 字典

    Returns
    -------
    dict with keys:
        theme_family, budget_focus, pace_preference, trip_style,
        assembler_variant (dict)
    """
    theme   = infer_theme_family(profile)
    budget  = profile.get("budget_level", "mid")
    variant = select_assembler_variant(theme, budget)

    return {
        "theme_family":    theme.value,
        "budget_focus":    profile.get("budget_focus", BudgetFocus.BALANCED.value),
        "pace_preference": profile.get("pace_preference", PacePreference.MODERATE.value),
        "trip_style":      profile.get("trip_style", TripStyle.ONE_CITY.value),
        "assembler_variant": variant.to_dict(),
    }


# ── 辅助 ──────────────────────────────────────────────────────────────────────

def _extract_city_codes(profile: dict) -> list[str]:
    cities = profile.get("cities", []) or profile.get("city_codes", [])
    if not cities:
        return []
    if isinstance(cities[0], dict):
        return [c.get("city_code", "") for c in cities]
    return list(cities)
