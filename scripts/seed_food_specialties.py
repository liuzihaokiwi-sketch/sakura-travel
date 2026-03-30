"""
B5: 录入北海道各城市特色菜系
数据来源：权威旅游资料 (Japan Guide, Visit Hokkaido, Tabelog 分类) + 人工整理

运行：python scripts/seed_food_specialties.py
"""
from __future__ import annotations

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

# importance: signature(标志性) / regional(地区特色) / common(普通)
# source: 'human' 表示人工整理
FOOD_SPECIALTIES = [
    # ── 札幌 ──────────────────────────────────────────────────────────────────
    {
        "city_code": "sapporo",
        "cuisine": "味噌拉面",
        "cuisine_en": "Miso Ramen",
        "cuisine_ja": "味噌ラーメン",
        "importance": "signature",
        "description_zh": "札幌是日本味噌拉面的发源地，拉面横丁（すすきの）是必去之地。特点是浓郁的味噌汤底配合黄油和玉米。",
        "source": "human",
    },
    {
        "city_code": "sapporo",
        "cuisine": "成吉思汗烤肉",
        "cuisine_en": "Jingisukan (Genghis Khan BBQ)",
        "cuisine_ja": "ジンギスカン",
        "importance": "signature",
        "description_zh": "北海道特有的羊肉烤肉，用铁锅烤鲜嫩羊肉，配蔬菜。札幌啤酒园是著名体验地。",
        "source": "human",
    },
    {
        "city_code": "sapporo",
        "cuisine": "汤咖喱",
        "cuisine_en": "Soup Curry",
        "cuisine_ja": "スープカレー",
        "importance": "signature",
        "description_zh": "发源于札幌的北海道特色美食，比普通咖喱更稀，配有大块蔬菜和肉，富有层次感。",
        "source": "human",
    },
    {
        "city_code": "sapporo",
        "cuisine": "海鲜丼",
        "cuisine_en": "Seafood Rice Bowl",
        "cuisine_ja": "海鮮丼",
        "importance": "signature",
        "description_zh": "北海道海产丰富，二条市场和场外市场的海鲜丼品质极佳，海胆、蟹肉、三文鱼籽是必尝食材。",
        "source": "human",
    },
    {
        "city_code": "sapporo",
        "cuisine": "白色恋人饼干",
        "cuisine_en": "Shiroi Koibito Cookies",
        "cuisine_ja": "白い恋人",
        "importance": "regional",
        "description_zh": "北海道最著名伴手礼，夹心白巧克力的薄饼干，在白色恋人公园有工厂参观。",
        "source": "human",
    },
    {
        "city_code": "sapporo",
        "cuisine": "北海道牛奶甜品",
        "cuisine_en": "Hokkaido Milk Sweets",
        "cuisine_ja": "北海道ミルクスイーツ",
        "importance": "regional",
        "description_zh": "北海道牛奶品质日本第一，各种软冰淇淋、奶制甜点是当地特色。",
        "source": "human",
    },
    {
        "city_code": "sapporo",
        "cuisine": "寿司",
        "cuisine_en": "Sushi",
        "cuisine_ja": "寿司",
        "importance": "regional",
        "description_zh": "北海道海产丰富，札幌寿司品质极高，尤其是海胆、蟹肉握寿司。",
        "source": "human",
    },
    {
        "city_code": "sapporo",
        "cuisine": "鲜毛蟹",
        "cuisine_en": "Hokkaido Crab",
        "cuisine_ja": "毛ガニ/ズワイガニ",
        "importance": "regional",
        "description_zh": "北海道毛蟹和松叶蟹品质极佳，市场和餐厅均有新鲜提供。",
        "source": "human",
    },

    # ── 小樽 ──────────────────────────────────────────────────────────────────
    {
        "city_code": "otaru",
        "cuisine": "寿司",
        "cuisine_en": "Sushi",
        "cuisine_ja": "寿司",
        "importance": "signature",
        "description_zh": "小樽被誉为日本数一数二的寿司之都，寿司屋通集中了众多高品质寿司店，以当日捕捞的北海道海产见长。",
        "source": "human",
    },
    {
        "city_code": "otaru",
        "cuisine": "小樽运河啤酒",
        "cuisine_en": "Otaru Beer",
        "cuisine_ja": "小樽ビール",
        "importance": "regional",
        "description_zh": "运河沿岸的小樽运河食堂有自酿啤酒，搭配运河风景是独特体验。",
        "source": "human",
    },
    {
        "city_code": "otaru",
        "cuisine": "海鲜烧",
        "cuisine_en": "Grilled Seafood",
        "cuisine_ja": "海鮮焼き",
        "importance": "regional",
        "description_zh": "小樽三角市场等地有新鲜海产烧烤，边烤边吃北海道海产。",
        "source": "human",
    },

    # ── 函馆 ──────────────────────────────────────────────────────────────────
    {
        "city_code": "hakodate",
        "cuisine": "盐味拉面",
        "cuisine_en": "Shio Ramen (Salt Ramen)",
        "cuisine_ja": "塩ラーメン",
        "importance": "signature",
        "description_zh": "函馆是盐味拉面的发源地，清澈的鱼介汤底，清爽不腻，与札幌味噌拉面风格迥异。",
        "source": "human",
    },
    {
        "city_code": "hakodate",
        "cuisine": "朝市海鲜",
        "cuisine_en": "Hakodate Morning Market Seafood",
        "cuisine_ja": "朝市の海鮮",
        "importance": "signature",
        "description_zh": "函馆朝市是日本三大朝市之一，每天清晨有新鲜海产，海胆、蟹、墨鱼等一应俱全。",
        "source": "human",
    },
    {
        "city_code": "hakodate",
        "cuisine": "墨鱼料理",
        "cuisine_en": "Squid Dishes",
        "cuisine_ja": "イカ料理",
        "importance": "signature",
        "description_zh": "函馆港是日本最大的墨鱼渔港之一，活墨鱼刺身是当地招牌。",
        "source": "human",
    },
    {
        "city_code": "hakodate",
        "cuisine": "幸运小丑汉堡",
        "cuisine_en": "Lucky Pierrot Burger",
        "cuisine_ja": "ラッキーピエロ",
        "importance": "regional",
        "description_zh": "函馆当地连锁快餐品牌，超高人气，成吉思汗汉堡是招牌，出了函馆就吃不到。",
        "source": "human",
    },

    # ── 旭川 ──────────────────────────────────────────────────────────────────
    {
        "city_code": "asahikawa",
        "cuisine": "酱油拉面",
        "cuisine_en": "Shoyu Ramen (Soy Sauce Ramen)",
        "cuisine_ja": "醤油ラーメン",
        "importance": "signature",
        "description_zh": "旭川是日本酱油拉面的代表城市，汤头浓郁，面条较硬，与北海道其他地区拉面风格不同。旭川拉面村是知名打卡地。",
        "source": "human",
    },
    {
        "city_code": "asahikawa",
        "cuisine": "成吉思汗烤肉",
        "cuisine_en": "Jingisukan",
        "cuisine_ja": "ジンギスカン",
        "importance": "regional",
        "description_zh": "旭川也有高品质成吉思汗烤肉，当地农场直供的羊肉品质极高。",
        "source": "human",
    },

    # ── 富良野 ────────────────────────────────────────────────────────────────
    {
        "city_code": "furano",
        "cuisine": "富良野哈密瓜",
        "cuisine_en": "Furano Melon",
        "cuisine_ja": "富良野メロン",
        "importance": "signature",
        "description_zh": "富良野出产日本最顶级的哈密瓜，在农场直接切开吃是必体验。各种哈密瓜甜品遍地都是。",
        "source": "human",
    },
    {
        "city_code": "furano",
        "cuisine": "富良野奶酪",
        "cuisine_en": "Furano Cheese",
        "cuisine_ja": "富良野チーズ",
        "importance": "signature",
        "description_zh": "富良野奶牛牧场的天然奶酪，富良野奶酪工厂有参观和品尝，披萨、奶酪拼盘是当地特色。",
        "source": "human",
    },
    {
        "city_code": "furano",
        "cuisine": "薰衣草甜品",
        "cuisine_en": "Lavender Sweets",
        "cuisine_ja": "ラベンダースイーツ",
        "importance": "regional",
        "description_zh": "7-8月薰衣草盛开时，各种薰衣草冰淇淋、软糖、茶饮随处可见，是夏季必尝。",
        "source": "human",
    },

    # ── 美瑛 ──────────────────────────────────────────────────────────────────
    {
        "city_code": "biei",
        "cuisine": "美瑛蔬菜料理",
        "cuisine_en": "Biei Vegetable Cuisine",
        "cuisine_ja": "美瑛野菜料理",
        "importance": "signature",
        "description_zh": "美瑛是蔬菜产地，当地农家餐厅以新鲜蔬菜料理见长，土豆、玉米、南瓜等大地の恵み。",
        "source": "human",
    },

    # ── 登别 ──────────────────────────────────────────────────────────────────
    {
        "city_code": "noboribetsu",
        "cuisine": "温泉旅馆怀石料理",
        "cuisine_en": "Ryokan Kaiseki",
        "cuisine_ja": "旅館の懐石料理",
        "importance": "signature",
        "description_zh": "登别是温泉胜地，泡温泉入住旅馆，享用以北海道海产和山珍为主的多道怀石料理是主要体验。",
        "source": "human",
    },
    {
        "city_code": "noboribetsu",
        "cuisine": "蟹料理",
        "cuisine_en": "Crab Cuisine",
        "cuisine_ja": "カニ料理",
        "importance": "regional",
        "description_zh": "登别温泉区不少旅馆以蟹料理自助餐（かにの食べ放題）著名。",
        "source": "human",
    },

    # ── 洞爷湖 ────────────────────────────────────────────────────────────────
    {
        "city_code": "toya",
        "cuisine": "温泉旅馆料理",
        "cuisine_en": "Onsen Ryokan Cuisine",
        "cuisine_ja": "温泉旅館料理",
        "importance": "signature",
        "description_zh": "洞爷湖温泉区的高档旅馆提供精致的北海道食材怀石料理，以湖景搭配晚餐是特色体验。",
        "source": "human",
    },
    {
        "city_code": "toya",
        "cuisine": "洞爷湖工厂蔬菜",
        "cuisine_en": "Lake Toya Farm Vegetables",
        "cuisine_ja": "洞爷湖農場野菜",
        "importance": "regional",
        "description_zh": "周边农场的新鲜蔬菜和乳制品，在当地市场和餐厅均有供应。",
        "source": "human",
    },

    # ── 网走 ──────────────────────────────────────────────────────────────────
    {
        "city_code": "abashiri",
        "cuisine": "流氷海鲜",
        "cuisine_en": "Drift Ice Season Seafood",
        "cuisine_ja": "流氷の海鮮",
        "importance": "signature",
        "description_zh": "1-3月流冰期间，鄂霍次克海的毛蟹和牡蛎品质达到顶峰，是冬季来访的最大饮食亮点。",
        "source": "human",
    },
    {
        "city_code": "abashiri",
        "cuisine": "网走监狱番茄",
        "cuisine_en": "Abashiri Prison Tomato Products",
        "cuisine_ja": "網走刑務所トマト",
        "importance": "regional",
        "description_zh": "网走刑务所农场出产的番茄产品，包括番茄汁和酱，是当地独特伴手礼。",
        "source": "human",
    },

    # ── 钏路 ──────────────────────────────────────────────────────────────────
    {
        "city_code": "kushiro",
        "cuisine": "钏路炉端烧",
        "cuisine_en": "Kushiro Robata-yaki",
        "cuisine_ja": "炉ばた焼き",
        "importance": "signature",
        "description_zh": "钏路是日本炉端烧（围炉烤鱼海鲜）的发源地，錦町地区的炉端焼き一条街是必去美食区。",
        "source": "human",
    },
    {
        "city_code": "kushiro",
        "cuisine": "钏路拉面",
        "cuisine_en": "Kushiro Ramen",
        "cuisine_ja": "釧路ラーメン",
        "importance": "signature",
        "description_zh": "细面配淡色酱油汤底，是钏路独特的拉面风格，与北海道其他地区的浓重口味形成对比。",
        "source": "human",
    },
]


async def main() -> None:
    async with AsyncSessionLocal() as session:
        print("[B5] Seeding city food specialties...")
        count = 0
        for item in FOOD_SPECIALTIES:
            await session.execute(text("""
                INSERT INTO city_food_specialties
                  (city_code, cuisine, cuisine_en, cuisine_ja, importance,
                   description_zh, source)
                VALUES
                  (:city_code, :cuisine, :cuisine_en, :cuisine_ja, :importance,
                   :description_zh, :source)
                ON CONFLICT (city_code, cuisine) DO UPDATE SET
                  cuisine_en = EXCLUDED.cuisine_en,
                  cuisine_ja = EXCLUDED.cuisine_ja,
                  importance = EXCLUDED.importance,
                  description_zh = EXCLUDED.description_zh,
                  source = EXCLUDED.source
            """), item)
            count += 1

        await session.commit()
        print(f"  OK: {count} food specialties inserted/updated")

        # Verify
        r = await session.execute(text(
            "SELECT city_code, COUNT(*), COUNT(CASE WHEN importance='signature' THEN 1 END) "
            "FROM city_food_specialties GROUP BY city_code ORDER BY city_code"
        ))
        print("\nFood specialties by city:")
        for row in r.fetchall():
            print(f"  {row[0]:<15} total={row[1]} signature={row[2]}")

    print("\nB5 DONE")


if __name__ == "__main__":
    asyncio.run(main())
