"""D47 area 错配检查（语义层）.

在 store id 的 area 段 跟 店名/地址里的地名 不一致时报警。

例：kyo_arashiyama_h372 但店名「高雄山荘」→ 应该是 takao
"""
from __future__ import annotations

import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DATA = Path("japan/kansai/hotels/data/hotels__kansai.json")

# area 关键词映射（地名/店名出现这些词 → 应该归这个 area）
AREA_KEYWORDS = {
    "takao": ["高雄", "栂尾", "槙尾", "神護寺", "高山寺", "西明寺"],
    "kibune": ["貴船", "贵船", "鞍馬", "鞍马"],
    "ohara": ["大原", "三千院", "寂光院"],
    "uji": ["宇治", "平等院"],
    "arashiyama": ["岚山", "嵐山", "嵯峨", "嵯峨野", "渡月桥", "渡月橋", "天龙寺", "天龍寺", "保津川"],
    "fushimi": ["伏見", "伏见", "稲荷", "稻荷"],
    "higashiyama": ["东山", "東山", "清水", "高台寺", "二年坂", "三年坂"],
    "gion": ["祇园", "祇園", "花见小路", "花見小路"],
    "gion_higashiyama": ["祇园", "祇園", "花见小路", "花見小路", "东山", "東山", "清水", "高台寺"],
    "kyoto_station": ["京都站", "京都駅", "梅小路", "東寺", "东寺", "東本願寺", "东本愿寺"],
    "shijo_kawaramachi": ["四条河原町", "河原町", "先斗町", "先斗町"],
    "kitayama": ["北区", "北山", "上賀茂", "上贺茂", "下鴨", "下鸭", "金閣寺", "金阁寺", "鷹峯", "鹰峰"],
    "nakagyo": ["中京", "中京区", "二条", "京都市役所", "御池", "新京极", "新京極"],
    "nijo_central": ["二条城", "二条", "中京"],
    "nara_park_area": ["奈良公园", "奈良公園", "東大寺", "东大寺", "春日大社"],
    "horyuji": ["法隆寺", "斑鳩", "斑鸠"],
    "kobe_kitano": ["北野", "北野異人館", "北野异人馆"],
    "kitano_shinkobe": ["北野", "新神戸", "新神户", "北野異人館", "北野异人馆"],
    "kobe_sannomiya": ["三宮", "三宫", "旧居留地"],
    "sannomiya": ["三宮", "三宫", "旧居留地"],
    "harborland_meriken": ["ハーバーランド", "メリケン", "メリケンパーク", "神户港", "神戸港"],
    "arima_onsen": ["有馬温泉", "有马温泉", "有馬", "有马"],
    "arima": ["有馬温泉", "有马温泉", "有馬", "有马"],
    "kinosaki_onsen": ["城崎温泉", "城崎", "城之埼"],
    "kinosaki": ["城崎温泉", "城崎", "城之埼"],
    "koyasan": ["高野山", "高野"],
}


# 城市约束：area 只在该城市候选中找
CITY_AREA_KW = {
    "京都": ["takao", "kibune", "ohara", "uji", "arashiyama", "fushimi",
            "higashiyama", "gion", "kyoto_station", "shijo_kawaramachi", "kitayama"],
    "大阪": ["umeda", "namba", "dotonbori", "shinsaibashi", "tennoji",
            "honmachi", "bay_area", "midosuji", "tempozan", "shinchi"],
    "神户": ["kobe_kitano", "kobe_sannomiya"],
    "奈良": ["nara_park_area", "horyuji"],
    "有马": ["arima_onsen"],
    "城崎": ["kinosaki_onsen"],
    "高野山": ["koyasan"],
}


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))

    suspect = []
    for h in data:
        hid = h["id"]
        area = h.get("area", "")
        city = h.get("city", "")
        name = h.get("note", {}).get("店名", "")
        addr = h.get("note", {}).get("地址", "")
        text = f"{name} {addr}"

        # 当前 area 应该出现的关键词
        my_kws = AREA_KEYWORDS.get(area, [])
        my_match = any(kw in text for kw in my_kws)

        # 限定到本城市的 area 候选
        city_areas = CITY_AREA_KW.get(city, [])

        # 不属于当前 area 的、但出现关键词的别 area
        wrong_area = []
        for other_area, kws in AREA_KEYWORDS.items():
            if other_area == area:
                continue
            # 排除非本城 area
            if city_areas and other_area not in city_areas:
                continue
            for kw in kws:
                if kw in text:
                    wrong_area.append((other_area, kw))
                    break

        # 只在「我没匹配 + 别 area 强匹配」时算可疑
        if not my_match and wrong_area:
            suspect.append((hid, area, name[:40], wrong_area))

    print(f"total={len(data)} | suspect={len(suspect)}")
    print()
    print(f"{'id':60} {'cur':25} {'name':40} → {'wrong_area_hits'}")
    for hid, area, name, wa in suspect:
        wa_str = ", ".join(f"{a}({k})" for a, k in wa[:3])
        print(f"{hid:60} {area:25} {name:40} → {wa_str}")


if __name__ == "__main__":
    main()
