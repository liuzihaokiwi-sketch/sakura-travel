"""
display_registry.py — 唯一权威的显示名映射注册表

所有需要将内部 key（corridor / city / area / cuisine / day_type / intensity / meal_type）
转换为中文展示名的模块，统一从这里 import。

规则：
  1. 每新增一个 corridor bare key，只在这里加一次
  2. 其他文件 (run_regression / export_plan_pdf / route_skeleton_builder / meal_flex_filler)
     全部 import 这里的函数/映射，不再自己维护
  3. sanitize() 是最终兜底：任何用户可见文本在渲染前过一遍
"""
from __future__ import annotations


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 走廊 bare key → 中文展示名（authority，25 条 + 旧前缀别名兜底）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORRIDOR_ZH: dict[str, str] = {
    # ── 京都 ──
    "arashiyama":       "岚山·嵯峨野",
    "daigo":            "醍醐（醍醐寺·山樱）",
    "fushimi":          "伏见·稻荷",
    "gion":             "祇园·花见小路",
    "gosho":            "御所·西阵·二条",
    "higashiyama":      "东山·清水寺",
    "kawaramachi":      "河原町·四条",
    "kinugasa":         "衣笠（金阁寺·龙安寺）",
    "kita_ku":          "北区（大德寺·上贺茂）",
    "nijo":             "二条城·西阵",
    "nishikyo":         "西京（桂离宫·松尾大社）",
    "okazaki":          "冈崎·哲学之道",
    "philosopher_path": "哲学之道·南禅寺",
    "zen_garden":       "枯山水庭园线",
    "uji":              "宇治（平等院·抹茶）",
    # ── 大阪 ──
    "namba":            "难波·道顿堀·心斋桥",
    "osakajo":          "大阪城·天满桥",
    "sakurajima":       "此花·USJ",
    "shinsekai":        "新世界·天王寺",
    "osa_nakanoshima":  "中之岛·北滨",
    "tsuruhashi":       "鹤桥·生野韩国城",
    # ── 奈良 / 神户 / 其他 ──
    "nara_park":        "奈良公园·东大寺",
    "kobe_kitano":      "神户·北野·南京町",
    "arima":            "有马温泉",
    "shiga":            "滋贺（MIHO 美术馆）",
    # ── 旧前缀别名（兜底，防止旧数据残留）──
    "kyo_fushimi": "伏见·稻荷", "kyo_arashiyama": "岚山·嵯峨野",
    "kyo_higashiyama": "东山·清水寺", "kyo_gion": "祇园·花见小路",
    "kyo_kawaramachi": "河原町·四条", "kyo_okazaki": "冈崎·哲学之道",
    "kyo_nijo": "二条城·西阵", "kyo_zen_garden": "枯山水庭园线",
    "kyo_nishikyo": "西京（桂离宫·松尾大社）", "kyo_kinugasa": "衣笠（金阁寺·龙安寺）",
    "osa_namba": "难波·道顿堀·心斋桥", "osa_osakajo": "大阪城·天满桥",
    "osa_sakurajima": "此花·USJ", "osa_shinsekai": "新世界·天王寺",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 走廊 → 城市映射
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORRIDOR_TO_CITY: dict[str, str] = {
    # 京都
    "arashiyama": "kyoto", "daigo": "kyoto", "fushimi": "kyoto",
    "gion": "kyoto", "gosho": "kyoto", "higashiyama": "kyoto",
    "kawaramachi": "kyoto", "kinugasa": "kyoto", "kita_ku": "kyoto",
    "nijo": "kyoto", "nishikyo": "kyoto", "okazaki": "kyoto",
    "philosopher_path": "kyoto", "zen_garden": "kyoto", "uji": "kyoto",
    # 大阪
    "namba": "osaka", "osakajo": "osaka", "sakurajima": "osaka",
    "shinsekai": "osaka", "osa_nakanoshima": "osaka", "tsuruhashi": "osaka",
    "umeda": "osaka",
    # 奈良 / 神户 / 滋贺
    "nara_park": "nara",
    "kobe_kitano": "kobe", "arima": "kobe",
    "shiga": "shiga",
    # 旧前缀
    "kyo_fushimi": "kyoto", "kyo_arashiyama": "kyoto", "kyo_higashiyama": "kyoto",
    "kyo_gion": "kyoto", "kyo_kawaramachi": "kyoto", "kyo_okazaki": "kyoto",
    "kyo_nijo": "kyoto", "kyo_zen_garden": "kyoto",
    "kyo_nishikyo": "kyoto", "kyo_kinugasa": "kyoto",
    "osa_namba": "osaka", "osa_osakajo": "osaka",
    "osa_sakurajima": "osaka", "osa_shinsekai": "osaka",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 城市 / sleep_base → 中文展示名
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CITY_ZH: dict[str, str] = {
    "kyoto": "京都", "osaka": "大阪", "nara": "奈良",
    "kobe": "神户", "shiga": "滋贺", "tokyo": "东京",
    # sleep_base → city 映射
    "kawaramachi": "京都", "gion": "京都", "kyoto_station": "京都",
    "namba": "大阪", "shinsaibashi": "大阪", "umeda": "大阪",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 区域 key → 中文展示名
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AREA_ZH: dict[str, str] = {
    "kawaramachi": "京都·河原町", "gion": "京都·祇园",
    "namba": "大阪·难波", "shinsaibashi": "大阪·心斋桥",
    "umeda": "大阪·梅田", "kyoto_station": "京都·京都站",
    "nara": "奈良", "kyoto": "京都", "osaka": "大阪",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 菜系 / day_type / intensity / meal_type → 中文
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CUISINE_ZH: dict[str, str] = {
    "sushi": "寿司", "ramen": "拉面", "yakiniku": "烧肉",
    "tempura": "天妇罗", "kushikatsu": "串炸", "yakitori": "烧鸟",
    "takoyaki": "章鱼烧", "okonomiyaki": "大阪烧", "kaiseki": "怀石",
    "cafe": "咖啡轻食", "udon": "乌冬", "tonkatsu": "炸猪排",
}

DAY_TYPE_ZH: dict[str, str] = {
    "arrival": "到达日", "departure": "返程日", "normal": "全日深游",
    "theme_park": "主题公园日", "transfer": "转场日",
}

INTENSITY_ZH: dict[str, str] = {
    "light": "轻松", "relaxed": "轻松", "balanced": "均衡",
    "moderate": "均衡", "dense": "充实",
}

MEAL_ZH: dict[str, str] = {
    "breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RAW KEY 黑名单（用于断言：出现在用户可见文本中就是泄露）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RAW_KEY_BLACKLIST: list[str] = [
    # 旧前缀
    "kyo_gion", "kyo_fushimi", "kyo_higashiyama", "kyo_kawaramachi",
    "kyo_okazaki", "kyo_arashiyama", "kyo_zen_garden", "kyo_nijo",
    "kyo_nishikyo", "kyo_kinugasa", "kyo_uji",
    "osa_namba", "osa_shinsekai", "osa_osakajo", "osa_sakurajima",
    "osa_nakanoshima",
    # 纯英文 bare key
    "philosopher_path", "gosho", "daigo", "kita_ku",
    "nishikyo", "kinugasa", "zen_garden", "tsuruhashi", "shiga",
    # 内部字段名
    "cluster_id", "circle_id", "entity_id", "base_id",
    "corridor_raw", "corridor_key",
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 公共函数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 合并所有 raw → 中文 映射（用于 sanitize 兜底）
_ALL_RAW_TO_ZH: dict[str, str] = {}
_ALL_RAW_TO_ZH.update(CORRIDOR_ZH)
_ALL_RAW_TO_ZH.update(CITY_ZH)
_ALL_RAW_TO_ZH.update(AREA_ZH)
_ALL_RAW_TO_ZH.update(CUISINE_ZH)


def display_corridor(key: str) -> str:
    """走廊 key → 中文展示名"""
    return CORRIDOR_ZH.get(key, key) if key else ""


def display_city(key: str) -> str:
    """城市/sleep_base key → 中文展示名"""
    return CITY_ZH.get(key, key) if key else ""


def display_area(key: str) -> str:
    """区域 key → 中文展示名"""
    return AREA_ZH.get(key, key) if key else ""


def display_day_type(key: str) -> str:
    """day_type key → 中文展示名"""
    return DAY_TYPE_ZH.get(key, key) if key else ""


def display_intensity(key: str) -> str:
    """intensity key → 中文展示名"""
    return INTENSITY_ZH.get(key, key) if key else ""


def display_meal(key: str) -> str:
    """meal_type key → 中文展示名"""
    return MEAL_ZH.get(key, key) if key else ""


def display_cuisine(key: str) -> str:
    """cuisine key → 中文展示名"""
    return CUISINE_ZH.get(key, key) if key else ""


def corridor_to_city(corridor_key: str) -> str:
    """走廊 key → 所属城市 code"""
    return CORRIDOR_TO_CITY.get(corridor_key, "")


def sanitize(text: str) -> str:
    """最终兜底净化：把任何残留的 raw key 替换为中文。
    按 key 长度降序替换，避免短 key 错误覆盖长 key 的一部分。"""
    if not text:
        return text
    for raw_key in sorted(_ALL_RAW_TO_ZH, key=len, reverse=True):
        if raw_key in text:
            text = text.replace(raw_key, _ALL_RAW_TO_ZH[raw_key])
    return text
