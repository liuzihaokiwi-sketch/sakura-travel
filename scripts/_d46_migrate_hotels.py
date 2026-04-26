"""把 D40 旧 schema 酒店数据迁移到 D46 新 schema。

输入：japan/kansai/hotels/_seeds/_d46_filtered.json（D46 三道筛后 201 家）
输出：japan/kansai/hotels/data/hotels__kansai.json（D46 新 schema）

转换规则：
- budget_tier: comfort→comfort, premier→quality, luxury→luxury, ultra_luxury→top
- hotel_type: convenient→city, ryokan/shukubo/machiya/experience→experience
- experience 6 组归类（写在 note.亮点 第一项）：
  - ryokan + arima/kinosaki/shirahama → 温泉旅馆
  - ryokan + 京都市内（kyoto/arashiyama 等）→ 老铺旅馆 或 温泉度假
  - shukubo → 宿坊
  - machiya → 町家
  - experience + onsen 关键字 → 温泉度假
  - 其他 experience → 设计精品
- price_range_jpy {low, high} → price_cny_per_night [平季中位, 旺季中位]
  汇率：1 JPY = 0.05 RMB（保守取整 50/100）
- area: 旧 area 字段对照 area_registry·英文优先
- city: 中文小写映射（kyoto→京都/osaka→大阪/...）
- 所有迁移记录都标 可信度=single_source，最后核实=2026-04-26
- 数据来源默认填 ['https://hotels.ctrip.com/']（占位·后续覆盖真实 URL）

特别处理：
- 旧 area 多为日文/英文混用（"shijo_kawaramachi"等），保留英文 snake_case
- near_attractions 旧 schema 没有，留空数组（后续 entity 反向挂）
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "japan/kansai/hotels/_seeds/_d46_filtered.json"
DST = REPO / "japan/kansai/hotels/data/hotels__kansai.json"

CITY_ZH = {
    "kyoto": "京都",
    "osaka": "大阪",
    "kobe": "神户",
    "nara": "奈良",
    "arima": "神户",  # 有马属于神户行政
    "kinosaki": "城崎",
    "koyasan": "高野山",
    "shirahama": "白浜",
    "himeji": "姬路",
}

# 旧 budget_tier → 新 tier
TIER_MAP = {
    "economy": None,  # 已被砍·应该不会出现
    "comfort": "comfort",
    "premier": "quality",
    "luxury": "luxury",
    "ultra_luxury": "top",
}

# JPY → RMB 汇率（2026-04 取 0.048·近似 0.05·便于取整）
JPY_TO_CNY = 0.048


def round_to_50_or_100(n: float) -> int:
    """精度取整到 50 或 100·按 SOP §3.1。"""
    if n < 1000:
        return int(round(n / 50) * 50)
    return int(round(n / 100) * 100)


def map_price_jpy_to_cny(pj: dict | None) -> list[int]:
    """price_range_jpy {low, high} → [平季中位, 旺季中位]。

    旧数据里 low/high 是日元真实区间·当作 [淡季最低, 旺季中位]。
    按 SOP 要平季中位，估算：平季 ≈ 淡季 × 1.3。
    """
    if not pj or "low" not in pj or "high" not in pj:
        return [0, 0]
    low = pj["low"]
    high = pj["high"]
    # 平季中位 ≈ 淡季 × 1.3·旺季 = high
    regular = round_to_50_or_100(low * 1.3 * JPY_TO_CNY)
    peak = round_to_50_or_100(high * JPY_TO_CNY)
    if regular >= peak:
        peak = round_to_50_or_100(regular * 1.5)
    if regular == peak:
        peak = regular + 100
    return [regular, peak]


def classify_tier_from_price(regular_cny: int) -> str | None:
    """根据平季中位 RMB 兜底归档（如果旧 budget_tier 缺失）。"""
    if regular_cny < 600:
        return "comfort"
    elif regular_cny < 1700:
        return "quality"
    elif regular_cny < 4000:
        return "luxury"
    else:
        return "top"


def classify_experience_group(h: dict) -> str:
    """归 6 组之一·写在 note.亮点 第一项。"""
    ht = h.get("hotel_type")
    city = h.get("city", "")
    area = h.get("area", "")
    name_zh = h.get("name_zh", "")
    name_ja = h.get("name_ja", "")
    name_combined = (name_zh + name_ja).lower()

    # 宿坊
    if ht == "shukubo":
        return "宿坊"
    # 町家
    if ht == "machiya":
        return "町家"
    # ryokan：按区域分老铺/温泉/温泉度假
    if ht == "ryokan":
        if city in ("arima", "kinosaki", "shirahama"):
            return "温泉旅馆"
        if city == "koyasan":
            return "宿坊"
        # 京都市内 ryokan：顶奢老铺 vs 普通和风
        if city == "kyoto":
            # 京都顶奢老铺关键词
            if any(k in name_zh for k in ["俵屋", "柊家", "炭屋", "丸福", "金乃音", "西富家"]):
                return "老铺旅馆"
            if "温泉" in name_zh or "湯" in name_ja or "tsubaki" in name_combined:
                return "温泉度假"
            return "老铺旅馆"
        return "温泉旅馆"
    # experience：按关键词区分
    if ht == "experience":
        if any(k in name_zh + area for k in ["温泉", "翠岚", "六甲", "spa"]):
            return "温泉度假"
        if "町家" in name_zh or "machiya" in name_combined:
            return "町家"
        return "设计精品"
    return "设计精品"


def map_type(ht: str | None) -> str:
    """hotel_type → type"""
    if ht == "convenient":
        return "city"
    return "experience"


def gen_id(h: dict) -> str:
    """生成 D46 id: {城市拼音简写}_{区域}_{酒店名拼音}。

    旧 id 形如 hotel_000·没有信息·重新生成。
    """
    city_pinyin = {
        "kyoto": "kyo",
        "osaka": "osk",
        "kobe": "kbe",
        "nara": "nra",
        "arima": "arm",
        "kinosaki": "kns",
        "koyasan": "kya",
        "shirahama": "shr",
        "himeji": "hmj",
    }
    city = city_pinyin.get(h.get("city", ""), "xxx")
    area = h.get("area", "unknown")
    # area 转拼音/英文（已英文的保留·中文转 pinyin 简写）
    area_clean = re.sub(r"[^a-z0-9_]", "", area.lower())[:20] or "unk"

    # 酒店名取拼音简写（从英文/罗马字优先）
    name_ja = h.get("name_ja", "")
    name_zh = h.get("name_zh", "")

    # 如果 name_ja 有罗马字（含英文）就用罗马字
    name_clean = ""
    for ch in name_ja:
        if ch.isascii() and ch.isalnum():
            name_clean += ch.lower()
        elif name_clean and (name_clean[-1] != '_'):
            name_clean += '_'
    name_clean = name_clean.strip('_')[:30]
    if not name_clean or len(name_clean) < 3:
        # 退而求其次：用 name_zh 的拼音首字母
        name_clean = "".join(ch for ch in name_zh.lower() if ch.isascii() and ch.isalnum())[:20]
    if not name_clean:
        # 用旧 id
        old_id = h.get("id", "")
        name_clean = old_id.replace("hotel_", "h")

    return f"{city}_{area_clean}_{name_clean}"[:64]


def migrate(h: dict) -> dict:
    new = {}

    # 系统字段
    old_city = h.get("city", "")
    new["id"] = gen_id(h)
    new["city"] = CITY_ZH.get(old_city, old_city)
    new["area"] = h.get("area", "")
    new["near_attractions"] = []  # 待补·留空

    # tier
    old_tier = h.get("budget_tier")
    tier = TIER_MAP.get(old_tier)

    # type
    new["type"] = map_type(h.get("hotel_type"))

    # 价格
    new["price_cny_per_night"] = map_price_jpy_to_cny(h.get("price_range_jpy"))

    # tier 兜底（如果旧 tier 缺·按平季中位归档）
    if not tier:
        tier = classify_tier_from_price(new["price_cny_per_night"][0])
    new["tier"] = tier

    new["season_months"] = None
    new["depth"] = "skeleton"  # 迁移后默认 skeleton·人工核实后升级

    # note 块
    note = {}
    name_zh = h.get("name_zh", "")
    name_ja = h.get("name_ja", "")
    if name_zh and name_ja:
        note["店名"] = f"{name_zh}（{name_ja}）"
    elif name_zh:
        note["店名"] = name_zh
    elif name_ja:
        note["店名"] = name_ja
    else:
        note["店名"] = h.get("id", "未命名")

    # 简介：用旧 editor_note·非空才放·空写占位
    editor = h.get("editor_note", "").strip()
    if editor and editor != "住过一次就知道什么叫真正的款待":  # 砍掉套话
        note["简介"] = editor

    # 亮点：第一项是体验型 6 组（如果是 experience）·然后从 vibe_tags + facility_tags 摘
    highlights = []
    if new["type"] == "experience":
        highlights.append(classify_experience_group(h))

    # 从 vibe_tags 和 facility_tags 取 2-3 个
    vibe = h.get("vibe_tags", []) or []
    facility = h.get("facility_tags", []) or []
    for tag in (vibe + facility)[:3]:
        if isinstance(tag, str) and tag and tag not in highlights:
            # 翻译常见英文标签到中文
            tag_zh = {
                "romantic": "浪漫氛围",
                "modern": "现代感",
                "traditional": "传统和风",
                "luxury": "奢华",
                "budget_friendly": "性价比",
                "concierge": "礼宾服务",
                "spa": "Spa",
                "kitchen": "带厨房",
                "washing_machine": "洗衣机",
                "free_breakfast": "含早",
                "onsen": "天然温泉",
                "pool": "泳池",
            }.get(tag, tag)
            highlights.append(tag_zh)

    if highlights:
        note["亮点"] = highlights[:5]

    # 地址：用 nearest_station + 距离
    station = h.get("nearest_station", "")
    distance = h.get("nearest_station_distance_m")
    if station:
        if distance:
            note["地址"] = f"最近站：{station}（步行 {int(distance/80)} 分钟左右）"
        else:
            note["地址"] = f"最近站：{station}"

    # 含早
    breakfast = h.get("breakfast")
    if breakfast == "included":
        note["含早"] = "含"
    elif breakfast == "optional":
        note["含早"] = "可选"
    elif breakfast == "none":
        note["含早"] = "无"

    # 价格：占位·skeleton 不必 full
    pj = h.get("price_range_jpy")
    if pj:
        note["价格"] = f"日元区间 ¥{pj.get('low', 0):,}-{pj.get('high', 0):,}/晚（待 OTA 三时段核实）"

    new["note"] = note

    # 元数据
    new["可信度"] = "single_source"  # 迁移自旧池·D40 携程打标·标 single·待人工 verify
    new["数据来源"] = ["https://hotels.ctrip.com/"]  # 占位·后续真实 URL
    new["最后核实"] = "2026-04-26"

    return new


def main():
    with open(SRC, encoding="utf-8") as f:
        old = json.load(f)
    print(f"载入旧池: {len(old)} 家")

    new_pool = [migrate(h) for h in old]

    # ID 去重检查
    ids = [h["id"] for h in new_pool]
    from collections import Counter
    dups = [i for i, n in Counter(ids).items() if n > 1]
    if dups:
        print(f"⚠ ID 重复 {len(dups)} 个·自动加后缀:")
        seen = {}
        for h in new_pool:
            base = h["id"]
            if base in seen:
                seen[base] += 1
                h["id"] = f"{base}_{seen[base]}"
            else:
                seen[base] = 0

    DST.parent.mkdir(parents=True, exist_ok=True)
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(new_pool, f, ensure_ascii=False, indent=2)

    print(f"✓ 写入: {DST.relative_to(REPO)}")
    print(f"✓ 总数: {len(new_pool)}")

    # 分布统计
    from collections import Counter
    print("\n=== 新 tier 分布 ===")
    for t, n in Counter(h["tier"] for h in new_pool).most_common():
        print(f"  {t}: {n}")
    print("\n=== type 分布 ===")
    for t, n in Counter(h["type"] for h in new_pool).most_common():
        print(f"  {t}: {n}")
    print("\n=== city × tier 矩阵 ===")
    cities = ["京都", "大阪", "神户", "奈良", "城崎", "高野山", "白浜"]
    tiers = ["comfort", "quality", "luxury", "top"]
    mat = Counter((h["city"], h["tier"]) for h in new_pool)
    print(f'  {"city":8} | ' + ' | '.join(f'{t:8}' for t in tiers) + ' | sum')
    for c in cities:
        row = [mat.get((c, t), 0) for t in tiers]
        print(f'  {c:8} | ' + ' | '.join(f'{n:8}' for n in row) + f' | {sum(row)}')


if __name__ == "__main__":
    main()
