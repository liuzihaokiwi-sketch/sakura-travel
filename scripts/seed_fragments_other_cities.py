"""
D2: 为富良野/洞爷湖/钏路/网走/二世古各补1个片段（已有1个，补到2个）

这些城市 D1 已做了 1 个片段，这里补充第 2 个，实现"每城市 2-3 个"的目标。
所有实体 entity_id 均来自 entity_base（is_active=true）。

运行: python scripts/seed_fragments_other_cities.py
"""
import asyncio, sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import text
from app.db.session import AsyncSessionLocal


# 片段定义：从已有 entity_id 中选真实实体
# entity_id 均已在前面验证存在
FRAGMENTS = [
    # ── 富良野 第2片段：农场与手工艺半日 ────────────────────────────────────
    {
        "city_code": "furano",
        "corridor": None,
        "fragment_type": "half_day",
        "theme": "Furano Farm & Craft",
        "title_zh": "富良野农场·手工艺半日",
        "summary_zh": "富田农场直击薰衣草/向日葵花海，Ningle Terrace森林手工艺小屋，体验富良野本地匠人文化。",
        "total_duration": 180,
        "best_season": ["summer"],
        "weather_ok": True,
        "suitable_for": ["couple", "family", "solo"],
        "pace": "relaxed",
        "energy_level": "low",
        "items": [
            {
                "entity_id": "0148c582-8b7e-425a-8f40-9e74390b6ac6",
                "entity_name": "富田農場",
                "type": "poi",
                "start": "09:00",
                "duration": 90,
                "note": "夏季薰衣草/向日葵花海，入场免费，纪念品店必买薰衣草系列"
            },
            {
                "entity_id": "38830209-b29c-41b5-ba01-22d1fff6d063",
                "entity_name": "ニングルテラス",
                "type": "poi",
                "start": "11:00",
                "duration": 60,
                "note": "森林中的手工艺小屋群，北海道地道工艺品，傍晚有灯光氛围"
            },
        ],
    },

    # ── 洞爷湖 第2片段：火山科学馆与湖畔半日 ────────────────────────────────
    {
        "city_code": "toya",
        "corridor": None,
        "fragment_type": "half_day",
        "theme": "Toya Volcano Museum & Lakeside",
        "title_zh": "洞爷湖火山博物馆·湖畔散步",
        "summary_zh": "洞爷湖火山科学馆了解2000年北海道火山爆发历史，湖畔道路悠闲散步，欣赏火山口湖景色。",
        "total_duration": 180,
        "best_season": ["spring", "summer", "autumn"],
        "weather_ok": True,
        "suitable_for": ["couple", "family", "senior"],
        "pace": "relaxed",
        "energy_level": "low",
        "items": [
            {
                "entity_id": "13d694ec-b7c8-4876-aadd-c16a47934980",
                "entity_name": "洞爷湖ビジターセンター・火山科学館",
                "type": "poi",
                "start": "10:00",
                "duration": 75,
                "note": "2000年有珠山喷发记录，展示火山地貌，小孩可互动体验"
            },
            {
                "entity_id": "0576329e-30d4-4370-928f-ffeb15d31d21",
                "entity_name": "長寿と幸せの手湯",
                "type": "poi",
                "start": "11:30",
                "duration": 30,
                "note": "湖畔免费手浴，泡手汤顺便欣赏洞爷湖景色"
            },
        ],
    },

    # ── 钏路 第2片段：钏路湿原与丹顶鹤 ─────────────────────────────────────
    {
        "city_code": "kushiro",
        "corridor": None,
        "fragment_type": "full_day",
        "theme": "Kushiro Marshland & Red-crowned Crane",
        "title_zh": "钏路湿原·丹顶鹤全日",
        "summary_zh": "日本最大湿原—钏路湿原国立公园，冬季可见野生丹顶鹤（白鹤台），夏季绿意无边，钏路港海鲜午餐不可错过。",
        "total_duration": 300,
        "best_season": ["winter", "spring", "summer"],
        "weather_ok": False,
        "suitable_for": ["couple", "nature_lover", "photographer"],
        "pace": "moderate",
        "energy_level": "moderate",
        "items": [
            {
                "entity_id": "10b91054-60c2-4861-bb8d-108ce7d878b8",
                "entity_name": "鶴見公園",
                "type": "poi",
                "start": "08:00",
                "duration": 60,
                "note": "冬季（1-3月）丹顶鹤聚集，早晨7-9点最佳观鸟时机"
            },
            {
                "entity_id": "3385ca48-004b-4ae0-86db-a0a438e49e93",
                "entity_name": "釧路市立博物館",
                "type": "poi",
                "start": "10:00",
                "duration": 90,
                "note": "了解湿原生态和丹顶鹤文化，有湿原鸟瞰展示"
            },
            {
                "entity_id": "30d2f13a-cc88-4779-8b6a-c9f5ca84eb23",
                "entity_name": "港文館",
                "type": "poi",
                "start": "14:00",
                "duration": 60,
                "note": "钏路港历史建筑改建，眺望港口景色，傍晚有美丽晚霞"
            },
        ],
    },

    # ── 网走 第2片段：流冰体验与温泉半日 ────────────────────────────────────
    {
        "city_code": "abashiri",
        "corridor": None,
        "fragment_type": "half_day",
        "theme": "Abashiri Drift Ice & Onsen",
        "title_zh": "网走流冰体验·温泉半日",
        "summary_zh": "1-3月世界奇观流冰季，监狱博物馆了解北海道历史，流冰漂流体验，入浴能望见鄂霍次克海的温泉。",
        "total_duration": 180,
        "best_season": ["winter"],
        "weather_ok": False,
        "suitable_for": ["couple", "adventure", "photographer"],
        "pace": "moderate",
        "energy_level": "moderate",
        "items": [
            {
                "entity_id": "06219c0c-5ce5-492b-83fb-bf00acef6d76",
                "entity_name": "網走監獄歴史館",
                "type": "poi",
                "start": "09:00",
                "duration": 90,
                "note": "明治时代监狱建筑群，全日本保存最完整的监狱博物馆"
            },
            {
                "entity_id": "0a315ab8-19c2-418a-96c7-3537a1fb1710",
                "entity_name": "原生亭温泉",
                "type": "poi",
                "start": "14:00",
                "duration": 60,
                "note": "网走郊外温泉，部分浴池可远望鄂霍次克海"
            },
        ],
    },

    # ── 二世古 第2片段：夏季户外半日 ────────────────────────────────────────
    {
        "city_code": "niseko",
        "corridor": None,
        "fragment_type": "half_day",
        "theme": "Niseko Summer Nature Walk",
        "title_zh": "二世古夏季自然·神仙沼半日",
        "summary_zh": "夏季二世古摆脱滑雪印象：神仙沼高原湿地木栈道健行，狩太神社参拜，京极涌水品尝北海道最甘甜的泉水。",
        "total_duration": 180,
        "best_season": ["summer", "autumn"],
        "weather_ok": False,
        "suitable_for": ["couple", "nature_lover", "solo"],
        "pace": "relaxed",
        "energy_level": "low",
        "items": [
            {
                "entity_id": "111908a2-af21-4320-9e71-d879fd0ad8d5",
                "entity_name": "神仙沼",
                "type": "poi",
                "start": "09:00",
                "duration": 90,
                "note": "高原湿地，有木栈道可深入观赏，秋天红叶绝美。需步行约20分钟"
            },
            {
                "entity_id": "112026a4-ac7d-44b0-a987-5887d13e6525",
                "entity_name": "京極温泉 京極ふれあい交流センター",
                "type": "poi",
                "start": "11:30",
                "duration": 75,
                "note": "京极町名水泡汤，用北海道天然涌水泡温泉，价格实惠"
            },
        ],
    },
]


async def main() -> None:
    async with AsyncSessionLocal() as session:
        print("[D2] Seeding additional city fragments...")

        # 验证所有 entity_id 存在
        all_eids = []
        for frag in FRAGMENTS:
            for item in frag.get("items", []):
                all_eids.append(item["entity_id"])

        invalid = []
        for eid in all_eids:
            r = await session.execute(text(
                "SELECT 1 FROM entity_base WHERE entity_id=:eid AND is_active=true"
            ), {"eid": eid})
            if not r.fetchone():
                invalid.append(eid)

        if invalid:
            print(f"  ERROR: {len(invalid)} invalid entity_ids: {invalid}")
            return

        print(f"  All {len(all_eids)} entity_ids verified")

        # 插入片段
        count = 0
        for frag in FRAGMENTS:
            # best_season / weather_ok / suitable_for are all varchar[] — skip for now,
            # insert only non-array cols to avoid asyncpg type inference issues
            await session.execute(text("""
                INSERT INTO day_fragments
                  (city_code, corridor, fragment_type, theme, title_zh, summary_zh,
                   items, total_duration, pace, energy_level, is_verified)
                VALUES
                  (:city_code, :corridor, :fragment_type, :theme, :title_zh, :summary_zh,
                   CAST(:items AS jsonb), :total_duration,
                   :pace, :energy_level, true)
            """), {
                "city_code": frag["city_code"],
                "corridor": frag.get("corridor"),
                "fragment_type": frag["fragment_type"],
                "theme": frag["theme"],
                "title_zh": frag["title_zh"],
                "summary_zh": frag["summary_zh"],
                "items": json.dumps(frag["items"], ensure_ascii=False),
                "total_duration": frag["total_duration"],
                "pace": frag.get("pace", "moderate"),
                "energy_level": frag.get("energy_level", "moderate"),
            })
            count += 1
            print(f"  + {frag['city_code']}: {frag['title_zh']}")

        await session.commit()
        print(f"\n  Inserted {count} fragments")

        # 验证
        r = await session.execute(text(
            "SELECT city_code, COUNT(*) FROM day_fragments GROUP BY city_code ORDER BY city_code"
        ))
        print("\nday_fragments by city:")
        for row in r.fetchall():
            print(f"  {row[0]:<15}: {row[1]}")

    print("\nD2 DONE")


if __name__ == "__main__":
    asyncio.run(main())
