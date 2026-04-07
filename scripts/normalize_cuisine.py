#!/usr/bin/env python
"""
N1: cuisine_type 归一化
将 141 种原始值映射到 ~35 个标准菜系码。
输出:
  data/kansai_spots/restaurants_normalized.csv  — 归一化后的餐厅数据
  data/kansai_spots/cuisine_mapping.json        — 映射表（供下个城市圈复用）
"""
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# 标准菜系码 → 中文说明
STANDARD_CUISINES = {
    # 和食系
    "nihon_ryori": "日本料理/怀石/割烹",
    "kaiseki": "怀石料理",
    "sushi": "寿司",
    "unagi": "鳗鱼料理",
    "tempura": "天妇罗",
    "tonkatsu": "炸猪排",
    "kushiage": "串炸/串揚げ",
    "yakitori": "烤鸡串",
    "yakiniku": "烧肉",
    "teppanyaki": "铁板烧/和牛牛排",
    "wagyu": "和牛牛排",
    "shabu_sukiyaki": "涮锅/寿喜烧",
    "kani": "螃蟹料理",
    "fugu": "河豚料理",
    "soba": "荞麦面",
    "udon": "乌冬面",
    "ramen": "拉面",
    "okonomiyaki": "大阪烧/お好み焼き",
    "takoyaki": "章鱼烧",
    "donburi": "丼饭",
    "tofu": "豆腐料理",
    "kamameshi": "釜饭",
    "obanzai": "おばんざい/京都家常菜",
    "seafood": "海鲜料理",
    "akashiyaki": "明石焼き",
    "yoshoku": "日式洋食",
    "izakaya": "居酒屋",
    # 甜品/咖啡系
    "cafe": "咖啡/喫茶",
    "matcha_sweets": "抹茶甜品",
    "wagashi": "和果子",
    "sweets": "甜品/蛋糕/冰品",
    "bakery": "面包/パン",
    "street_food": "小吃/食べ歩き",
    # 洋食系
    "french": "法餐",
    "italian": "意餐",
    "curry": "咖喱",
    "western": "西餐/其他洋食",
    # 其他
    "chinese": "中华料理",
    "local_cuisine": "当地特色料理",
    "other": "其他",
}

# 原始值 → 标准码 映射表
# 规则: 日文、英文、混合值全部归一
MAPPING = {
    # 日本料理/怀石/割烹
    "日本料理": "nihon_ryori",
    "kaiseki": "kaiseki",
    "茶粥/懐石": "kaiseki",
    "湯豆腐/懐石": "kaiseki",
    "牛料理/日本料理": "nihon_ryori",
    "そば/日本料理": "soba",
    "茶粥/洋食": "nihon_ryori",
    "カニ会席/旅館": "kani",
    "カニ料理/旅館": "kani",

    # 寿司
    "sushi": "sushi",
    "鮨": "sushi",
    "寿司": "sushi",
    "鮨/創作": "sushi",
    "柿の葉寿司": "sushi",
    "三輪そうめん/柿の葉寿司": "sushi",
    "柿の葉寿司/茶粥": "sushi",
    "てこね寿司": "sushi",

    # 鳗鱼
    "eel": "unagi",

    # 天妇罗
    "tempura": "tempura",
    "天ぷら": "tempura",

    # 炸猪排
    "tonkatsu": "tonkatsu",

    # 串炸
    "kushiage": "kushiage",
    "kushikatsu": "kushiage",
    "串カツ": "kushiage",
    "串揚げ": "kushiage",

    # 烤鸡串
    "yakitori": "yakitori",
    "焼鳥": "yakitori",
    "食べ歩き/焼鳥": "street_food",

    # 烧肉
    "yakiniku": "yakiniku",

    # 铁板烧/和牛
    "teppanyaki": "teppanyaki",
    "鉄板焼/ステーキ": "teppanyaki",
    "鉄板焼き/お好み焼き": "teppanyaki",

    # 和牛牛排
    "wagyu": "wagyu",

    # 涮锅/寿喜烧
    "hot_pot": "shabu_sukiyaki",

    # 螃蟹
    "カニ料理": "kani",

    # 河豚
    "fugu": "fugu",

    # 荞麦面
    "soba": "soba",
    "そば": "soba",
    "soba_udon": "soba",
    "抹茶/茶蕎麦": "soba",

    # 乌冬面
    "udon": "udon",
    "うどん": "udon",
    "伊勢うどん": "udon",
    "かすうどん": "udon",
    "うどん/丼": "udon",

    # 拉面
    "ramen": "ramen",
    "ラーメン": "ramen",
    "スリランカカレー": "curry",

    # 大阪烧
    "okonomiyaki": "okonomiyaki",
    "お好み焼き": "okonomiyaki",
    "たこ焼き/お好み焼き": "okonomiyaki",

    # 章鱼烧
    "takoyaki": "takoyaki",
    "たこ焼き": "takoyaki",
    "食べ歩き/たこ焼き": "street_food",
    "食べ歩き/たこたまご": "street_food",

    # 丼饭
    "donburi": "donburi",
    "oyakodon": "donburi",
    "食べ歩き/大鶏排": "street_food",

    # 豆腐料理
    "tofu": "tofu",
    "tofu_cuisine": "tofu",
    "湯豆腐": "tofu",
    "湯豆腐/おばんざい": "tofu",

    # 釜饭
    "kamameshi": "kamameshi",

    # おばんざい
    "obanzai": "obanzai",
    "おばんざい": "obanzai",
    "おばんざい/野菜ビュッフェ": "obanzai",
    "おばんざい/和食": "obanzai",
    "おばんざい/京野菜": "obanzai",
    "和スイーツ/カフェ": "matcha_sweets",

    # 海鲜
    "seafood": "seafood",
    "食べ歩き/海鮮串": "street_food",
    "食べ歩き/海鮮": "street_food",
    "食べ歩き/川魚": "street_food",
    "食べ歩き/焼魚": "street_food",

    # 明石焼き
    "akashiyaki": "akashiyaki",
    "明石焼き": "akashiyaki",

    # 日式洋食
    "yoshoku": "yoshoku",
    "洋食": "yoshoku",
    "洋食/ステーキ": "yoshoku",
    "洋食/オムライス": "yoshoku",
    "洋食/ビフカツ": "yoshoku",
    "カレー/洋食": "curry",
    "茶粥/洋食": "nihon_ryori",

    # 居酒屋
    "izakaya": "izakaya",

    # 咖啡/喫茶
    "cafe": "cafe",
    "カフェ": "cafe",
    "喫茶": "cafe",
    "喫茶/モーニング": "cafe",
    "古民家カフェ": "cafe",
    "カフェ/カヌレ": "cafe",
    "カフェ/洋菓子": "cafe",
    "カフェ/ホットケーキ": "cafe",
    "カフェ/和スイーツ": "matcha_sweets",
    "パン/カフェ": "bakery",
    "tea": "cafe",

    # 抹茶甜品
    "matcha_sweets": "matcha_sweets",
    "抹茶スイーツ": "matcha_sweets",
    "抹茶/茶蕎麦": "matcha_sweets",

    # 和果子
    "wagashi": "wagashi",
    "和菓子": "wagashi",
    "和菓子/フルーツ大福": "wagashi",
    "mochi": "wagashi",
    "pickles": "wagashi",

    # 甜品/冰品
    "sweets": "sweets",
    "スイーツ/プリン": "sweets",
    "スイーツ/チーズケーキ": "sweets",
    "スイーツ/エッグタルト": "sweets",
    "スイーツ/ソフトクリーム": "sweets",
    "shaved_ice": "sweets",
    "かき氷": "sweets",
    "洋菓子/シュークリーム": "sweets",
    "和スイーツ": "sweets",

    # 面包
    "bakery": "bakery",
    "パン": "bakery",
    "パン/ベーグル": "bakery",
    "パン/大仏あんぱん": "bakery",

    # 小吃/食べ歩き
    "street_food": "street_food",
    "食べ歩き/コロッケ": "street_food",
    "食べ歩き/川魚": "street_food",
    "食べ歩き/イイダコ串": "street_food",
    "食べ歩き/だし巻": "street_food",
    "食べ歩き/ソフトクリーム": "street_food",
    "食べ歩き/牛串": "street_food",
    "食べ歩き/さつま揚げ": "street_food",
    "食べ歩き/ドーナツ": "street_food",

    # 法餐
    "french": "french",
    "フレンチ": "french",
    "フレンチ/イノベーティブ": "french",

    # 意餐
    "italian": "italian",
    "イタリアン": "italian",
    "イタリアン/イノベーティブ": "italian",
    "イタリアン/奈良食材": "italian",

    # 咖喱
    "curry": "curry",
    "スパイスカレー": "curry",
    "欧風カレー": "curry",
    "スリランカカレー": "curry",

    # 西餐/其他洋食
    "ステーキ": "teppanyaki",
    "ハンバーガー": "western",
    "イノベーティブ": "western",
    "イノベーティブ/スペイン": "western",
    "イタリアン/イノベーティブ": "italian",
    "フレンチ/イノベーティブ": "french",
    "イノベーティブ/スペイン": "western",

    # 中华
    "chinese": "chinese",
    "中華": "chinese",
    "中華料理": "chinese",
    "中華/豚まん": "chinese",
    "中華/焼小籠包": "chinese",
    "中華/肉まん": "chinese",
    "中華/北京ダック": "chinese",
    "中華/角煮バーガー": "chinese",

    # 本地特色
    "local_cuisine": "local_cuisine",
    "local_specialty": "local_cuisine",

    # 复合/其他
    "牛料理/日本料理": "nihon_ryori",
    "カニ会席/旅館": "kani",
    "食べ歩き/海鮮串": "street_food",
    "ŷ風カレー": "curry",
}


def normalize(raw):
    """返回标准菜系码，匹配不到的返回 'other' 并打印警告"""
    code = MAPPING.get(raw)
    if code:
        return code
    # 尝试部分匹配
    for key, val in MAPPING.items():
        if raw in key or key in raw:
            return val
    print(f"  [warn] unmapped: {raw!r}", file=sys.stderr)
    return "other"


def main():
    src = Path("data/kansai_spots/discovery_pool/restaurants_merged_final.csv")
    dst_csv = Path("data/kansai_spots/discovery_pool/restaurants_normalized.csv")
    dst_mapping = Path("data/kansai_spots/config/cuisine_mapping.json")

    print("[N1] cuisine_type normalization")
    print(f"  Input: {src}")

    rows = []
    with open(src, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames + ["cuisine_normalized"]
        for row in reader:
            raw = row["cuisine_type"]
            row["cuisine_normalized"] = normalize(raw)
            rows.append(row)

    # 写归一化 CSV
    with open(dst_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [ok] {dst_csv} ({len(rows)} rows)")

    # 写映射 JSON（供下个城市圈复用）
    mapping_out = {
        "_note": "原始 cuisine_type -> 标准菜系码，下个城市圈复用时更新此文件",
        "_standard_codes": STANDARD_CUISINES,
        "mappings": MAPPING,
    }
    with open(dst_mapping, "w", encoding="utf-8") as f:
        json.dump(mapping_out, f, ensure_ascii=False, indent=2)
    print(f"  [ok] {dst_mapping}")

    # 统计
    from collections import Counter
    norm_counter = Counter(r["cuisine_normalized"] for r in rows)
    raw_counter = Counter(r["cuisine_type"] for r in rows)
    other_rows = [r for r in rows if r["cuisine_normalized"] == "other"]

    print(f"\n  Before: {len(raw_counter)} unique cuisine_type values")
    print(f"  After:  {len(norm_counter)} unique cuisine_normalized values")
    print(f"\n  [Distribution after normalization]")
    for k, v in sorted(norm_counter.items(), key=lambda x: -x[1]):
        print(f"    {v:4d}  {k}")

    if other_rows:
        print(f"\n  [warn] {len(other_rows)} rows mapped to 'other':")
        for r in other_rows:
            print(f"    {r['name_ja']} | {r['cuisine_type']}")
    else:
        print("\n  [ok] No unmapped values")


if __name__ == "__main__":
    main()
