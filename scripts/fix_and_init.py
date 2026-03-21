"""创建路线模板 + 修复数据问题 + 模拟用户数据"""
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(Path(__file__).parent.parent)

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DB_URL = os.getenv("DATABASE_URL", "")

# ══════════════════════════════════════════════════════════════════════
# 1. 创建路线模板 JSON
# ══════════════════════════════════════════════════════════════════════

def create_templates():
    os.makedirs("data/route_templates", exist_ok=True)

    tokyo_1d = {
        "template_code": "tokyo_classic_1d",
        "name_zh": "东京经典1日",
        "city_code": "tokyo",
        "total_days": 1,
        "meta": {
            "template_code": "tokyo_classic_1d",
            "city_code": "tokyo",
            "city_codes": ["tokyo"],
            "total_days": 1,
            "tagline_zh": "一天走遍东京精华",
        },
        "scene_variants": {
            "sakura": {"tag_weight_overrides": {"sakura": 5, "park": 3}, "filter_exclude_tags": {}, "tagline_suffix_zh": "樱花季"},
            "food": {"tag_weight_overrides": {"gourmet": 5, "ramen": 3}, "filter_exclude_tags": {}, "tagline_suffix_zh": "美食版"},
            "family": {"tag_weight_overrides": {"family": 5}, "filter_exclude_tags": {"nightlife": 3}, "tagline_suffix_zh": "亲子版"},
            "couple": {"tag_weight_overrides": {"romantic": 5}, "filter_exclude_tags": {}, "tagline_suffix_zh": "情侣版"},
        },
        "days": [{
            "day": 1,
            "theme_zh": "东京经典一日精华",
            "area_zh": "浅草-上野-秋叶原-银座",
            "city_code": "tokyo",
            "transport_notes_zh": "全程东京Metro一日券600日元",
            "time_blocks": [
                {"slot_id": "d1_morning_1", "time": "09:00", "duration_min": 90, "slot_type": "poi",
                 "tags_required": ["temple", "culture", "iconic"], "area_hint": "asakusa",
                 "fallback_entity_id": None, "note_zh": "标志性寺庙"},
                {"slot_id": "d1_morning_2", "time": "10:45", "duration_min": 90, "slot_type": "poi",
                 "tags_required": ["museum", "culture", "park"], "area_hint": "ueno",
                 "fallback_entity_id": None, "note_zh": "博物馆或公园"},
                {"slot_id": "d1_lunch", "time": "12:30", "duration_min": 60, "slot_type": "restaurant",
                 "tags_required": ["restaurant", "japanese"], "area_hint": "ueno",
                 "fallback_entity_id": None, "note_zh": "午餐"},
                {"slot_id": "d1_afternoon_1", "time": "14:00", "duration_min": 90, "slot_type": "poi",
                 "tags_required": ["shopping", "anime", "electronics"], "area_hint": "akihabara",
                 "fallback_entity_id": None, "note_zh": "动漫电器街"},
                {"slot_id": "d1_afternoon_2", "time": "16:00", "duration_min": 90, "slot_type": "poi",
                 "tags_required": ["shopping", "landmark"], "area_hint": "ginza",
                 "fallback_entity_id": None, "note_zh": "银座商圈"},
                {"slot_id": "d1_dinner", "time": "18:00", "duration_min": 75, "slot_type": "restaurant",
                 "tags_required": ["restaurant", "sushi"], "area_hint": "ginza",
                 "fallback_entity_id": None, "note_zh": "晚餐"},
                {"slot_id": "d1_evening", "time": "19:30", "duration_min": 90, "slot_type": "poi",
                 "tags_required": ["nightview", "tower", "observation"], "area_hint": None,
                 "fallback_entity_id": None, "note_zh": "夜景收尾"},
            ],
        }],
    }

    with open("data/route_templates/tokyo_classic_1d.json", "w", encoding="utf-8") as f:
        json.dump(tokyo_1d, f, ensure_ascii=False, indent=2)
    print("  ✅ tokyo_classic_1d.json")

    # 3日模板
    tokyo_3d = {
        "template_code": "tokyo_classic_3d",
        "name_zh": "东京精华3日",
        "city_code": "tokyo",
        "total_days": 3,
        "meta": {
            "template_code": "tokyo_classic_3d",
            "city_code": "tokyo",
            "city_codes": ["tokyo"],
            "total_days": 3,
            "tagline_zh": "三天玩转东京",
        },
        "scene_variants": tokyo_1d["scene_variants"],
        "days": [
            tokyo_1d["days"][0],
            {
                "day": 2, "theme_zh": "新宿涩谷潮流日", "area_zh": "新宿-涩谷-原宿",
                "city_code": "tokyo", "transport_notes_zh": "JR山手线",
                "time_blocks": [
                    {"slot_id": "d2_morning", "time": "09:30", "duration_min": 90, "slot_type": "poi",
                     "tags_required": ["shrine", "garden", "park"], "area_hint": "shinjuku",
                     "fallback_entity_id": None, "note_zh": "新宿御苑"},
                    {"slot_id": "d2_mid", "time": "11:30", "duration_min": 60, "slot_type": "poi",
                     "tags_required": ["culture", "trendy", "shopping"], "area_hint": "harajuku",
                     "fallback_entity_id": None, "note_zh": "原宿"},
                    {"slot_id": "d2_lunch", "time": "12:30", "duration_min": 60, "slot_type": "restaurant",
                     "tags_required": ["restaurant", "ramen"], "area_hint": "harajuku",
                     "fallback_entity_id": None, "note_zh": "午餐"},
                    {"slot_id": "d2_afternoon", "time": "14:00", "duration_min": 120, "slot_type": "poi",
                     "tags_required": ["shopping", "trendy"], "area_hint": "shibuya",
                     "fallback_entity_id": None, "note_zh": "涩谷"},
                    {"slot_id": "d2_dinner", "time": "18:00", "duration_min": 75, "slot_type": "restaurant",
                     "tags_required": ["restaurant", "izakaya"], "area_hint": "shinjuku",
                     "fallback_entity_id": None, "note_zh": "居酒屋晚餐"},
                ],
            },
            {
                "day": 3, "theme_zh": "东京湾休闲日", "area_zh": "台场-丰洲-东京站",
                "city_code": "tokyo", "transport_notes_zh": "百合海鸥线",
                "time_blocks": [
                    {"slot_id": "d3_morning", "time": "09:30", "duration_min": 120, "slot_type": "poi",
                     "tags_required": ["entertainment", "modern", "family"], "area_hint": "odaiba",
                     "fallback_entity_id": None, "note_zh": "台场"},
                    {"slot_id": "d3_lunch", "time": "12:00", "duration_min": 60, "slot_type": "restaurant",
                     "tags_required": ["restaurant", "seafood"], "area_hint": "toyosu",
                     "fallback_entity_id": None, "note_zh": "丰洲午餐"},
                    {"slot_id": "d3_afternoon", "time": "14:00", "duration_min": 120, "slot_type": "poi",
                     "tags_required": ["shopping", "souvenir"], "area_hint": "tokyo_station",
                     "fallback_entity_id": None, "note_zh": "东京站购物"},
                    {"slot_id": "d3_dinner", "time": "18:00", "duration_min": 75, "slot_type": "restaurant",
                     "tags_required": ["restaurant", "japanese"], "area_hint": "marunouchi",
                     "fallback_entity_id": None, "note_zh": "晚餐"},
                ],
            },
        ],
    }
    with open("data/route_templates/tokyo_classic_3d.json", "w", encoding="utf-8") as f:
        json.dump(tokyo_3d, f, ensure_ascii=False, indent=2)
    print("  ✅ tokyo_classic_3d.json")


# ══════════════════════════════════════════════════════════════════════
# 2. 修复数据库问题
# ══════════════════════════════════════════════════════════════════════

async def fix_data_issues():
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ── 2a. 修复 entity_scores: 归一化到 0-100 ──
        print("\n  🔧 修复 entity_scores 归一化...")
        # 查看当前分数范围
        r = await session.execute(text(
            "SELECT min(final_score), max(final_score), avg(final_score) FROM entity_scores"
        ))
        row = r.fetchone()
        min_s, max_s, avg_s = row[0] or 0, row[1] or 100, row[2] or 50
        print(f"     当前范围: {min_s:.1f} ~ {max_s:.1f}, 平均: {avg_s:.1f}")

        if max_s > 0 and max_s != 100:
            # 线性归一化到 0-100
            await session.execute(text("""
                UPDATE entity_scores
                SET final_score = ROUND((final_score / :max_val) * 100, 1)
                WHERE final_score IS NOT NULL
            """), {"max_val": float(max_s)})
            print(f"     ✅ 已归一化到 0-100 (除以 {max_s:.1f})")

        # ── 2b. 补充 area_name (用已知区域映射) ──
        print("\n  🔧 补充 area_name...")
        area_keywords = {
            "tokyo": {
                "asakusa": ["浅草", "Asakusa", "Senso-ji"],
                "ueno": ["上野", "Ueno", "Ameyoko"],
                "akihabara": ["秋叶原", "Akihabara", "Electric"],
                "ginza": ["银座", "Ginza", "Yurakucho"],
                "shinjuku": ["新宿", "Shinjuku", "Kabukicho"],
                "shibuya": ["涩谷", "Shibuya", "Hachiko"],
                "harajuku": ["原宿", "Harajuku", "Omotesando", "表参道"],
                "roppongi": ["六本木", "Roppongi"],
                "odaiba": ["台场", "Odaiba", "お台場"],
                "ikebukuro": ["池袋", "Ikebukuro"],
                "tokyo_station": ["东京站", "Tokyo Station", "丸の内", "Marunouchi"],
                "tsukiji": ["筑地", "Tsukiji", "築地"],
                "toyosu": ["丰洲", "Toyosu", "豊洲"],
                "shinagawa": ["品川", "Shinagawa"],
            }
        }
        for city, areas in area_keywords.items():
            for area_name, keywords in areas.items():
                for kw in keywords:
                    await session.execute(text("""
                        UPDATE entity_base
                        SET area_name = :area
                        WHERE city_code = :city
                          AND area_name IS NULL
                          AND (name_zh LIKE :pat OR name_ja LIKE :pat OR name_en LIKE :pat
                               OR address_ja LIKE :pat)
                    """), {"area": area_name, "city": city, "pat": f"%{kw}%"})

        r = await session.execute(text(
            "SELECT count(*) FROM entity_base WHERE area_name IS NOT NULL"
        ))
        print(f"     ✅ 有 area_name 的实体: {r.scalar()} 个")

        # ── 2c. 补充基础标签 (根据 entity_type + name 推断) ──
        print("\n  🔧 补充基础标签...")
        tag_rules = [
            # (entity_type, name_pattern, tags)
            ("poi", "%寺%", ["temple", "culture"]),
            ("poi", "%Temple%", ["temple", "culture"]),
            ("poi", "%神社%", ["shrine", "culture"]),
            ("poi", "%Shrine%", ["shrine", "culture"]),
            ("poi", "%公园%", ["park", "nature"]),
            ("poi", "%Park%", ["park", "nature"]),
            ("poi", "%御苑%", ["garden", "park", "nature"]),
            ("poi", "%Garden%", ["garden", "nature"]),
            ("poi", "%博物%", ["museum", "culture"]),
            ("poi", "%Museum%", ["museum", "culture"]),
            ("poi", "%美术%", ["museum", "art", "culture"]),
            ("poi", "%Art%", ["museum", "art"]),
            ("poi", "%塔%", ["tower", "observation", "nightview"]),
            ("poi", "%Tower%", ["tower", "observation", "nightview"]),
            ("poi", "%展望%", ["observation", "nightview"]),
            ("poi", "%Sky%", ["observation", "nightview"]),
            ("poi", "%温泉%", ["onsen", "relaxation"]),
            ("poi", "%Onsen%", ["onsen", "relaxation"]),
            ("poi", "%market%", ["shopping", "market"]),
            ("poi", "%市場%", ["shopping", "market"]),
            ("poi", "%商店街%", ["shopping", "street"]),
            ("restaurant", "%ラーメン%", ["ramen"]),
            ("restaurant", "%Ramen%", ["ramen"]),
            ("restaurant", "%寿司%", ["sushi"]),
            ("restaurant", "%Sushi%", ["sushi"]),
            ("restaurant", "%鮨%", ["sushi"]),
            ("restaurant", "%居酒屋%", ["izakaya"]),
            ("restaurant", "%焼肉%", ["yakiniku"]),
            ("restaurant", "%天ぷら%", ["tempura"]),
            ("restaurant", "%うどん%", ["udon"]),
            ("restaurant", "%そば%", ["soba"]),
            ("restaurant", "%カフェ%", ["cafe"]),
            ("restaurant", "%Cafe%", ["cafe"]),
        ]

        tags_added = 0
        for etype, pattern, tags in tag_rules:
            # 找符合条件的实体
            r = await session.execute(text("""
                SELECT entity_id FROM entity_base
                WHERE entity_type = :etype
                  AND (name_zh LIKE :pat OR name_ja LIKE :pat OR name_en LIKE :pat)
            """), {"etype": etype, "pat": pattern})
            entity_ids = [row[0] for row in r.fetchall()]

            for eid in entity_ids:
                for tag in tags:
                    # 幂等插入
                    exists = await session.execute(text("""
                        SELECT 1 FROM entity_tags
                        WHERE entity_id = :eid AND tag_namespace = 'auto' AND tag_value = :tag
                    """), {"eid": eid, "tag": tag})
                    if not exists.fetchone():
                        await session.execute(text("""
                            INSERT INTO entity_tags (entity_id, tag_namespace, tag_value)
                            VALUES (:eid, 'auto', :tag)
                            ON CONFLICT DO NOTHING
                        """), {"eid": eid, "tag": tag})
                        tags_added += 1

        print(f"     ✅ 新增 {tags_added} 个标签")

        await session.commit()

    # ── 3. 模拟用户数据 (TripRequest + 相关记录) ──
    print("\n  🔧 创建模拟用户数据...")

    async with async_session() as session:
        # 检查 trip_requests 表结构
        r = await session.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'trip_requests' ORDER BY ordinal_position
        """))
        columns = [row[0] for row in r.fetchall()]
        print(f"     trip_requests 列: {columns}")

        if not columns:
            print("     ⚠️ trip_requests 表不存在，跳过模拟数据")
        else:
            # 检查是否已有模拟数据
            r = await session.execute(text("SELECT count(*) FROM trip_requests"))
            existing = r.scalar()
            if existing > 0:
                print(f"     已有 {existing} 条，跳过")
            else:
                trip_id = str(uuid.uuid4())
                now_ts = datetime.now(tz=timezone.utc)

                # 构建 INSERT (根据实际列)
                id_col = "trip_request_id" if "trip_request_id" in columns else "id"

                raw_input_data = json.dumps({
                    "cities": [{"city_code": "tokyo", "nights": 1}],
                    "scene": "general",
                    "travelers": 2,
                    "budget": "medium",
                    "interests": ["culture", "food", "shopping"],
                    "is_demo": True,
                }, ensure_ascii=False)

                # 仅用实际存在的列
                insert_cols = [id_col, "status", "created_at", "updated_at"]
                insert_vals = [":id", "'demo'", ":now", ":now"]
                params = {"id": trip_id, "now": now_ts}

                if "retry_count" in columns:
                    insert_cols.append("retry_count")
                    insert_vals.append("0")

                if "raw_input" in columns:
                    insert_cols.append("raw_input")
                    insert_vals.append(":raw_input")
                    params["raw_input"] = raw_input_data

                sql = f"INSERT INTO trip_requests ({', '.join(insert_cols)}) VALUES ({', '.join(insert_vals)})"
                await session.execute(text(sql), params)
                await session.commit()
                print(f"     ✅ 模拟 TripRequest: {trip_id}")

    await engine.dispose()


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════

async def main():
    print("🛠️  数据修复与初始化\n")

    print("📋 Step 1: 创建路线模板 JSON...")
    create_templates()

    print("\n📋 Step 2: 导入模板到数据库...")
    # 用 load_route_templates 的逻辑
    from app.db.models.derived import RouteTemplate
    from app.db.session import AsyncSessionLocal

    tmpl_dir = Path("data/route_templates")
    json_files = sorted(tmpl_dir.glob("*.json"))
    print(f"  找到 {len(json_files)} 个模板文件")

    async with AsyncSessionLocal() as session:
        for path in json_files:
            data = json.loads(path.read_text(encoding="utf-8"))
            name_zh = data["name_zh"]
            from sqlalchemy import select
            existing = await session.scalar(
                select(RouteTemplate).where(RouteTemplate.name_zh == name_zh)
            )
            if existing:
                existing.template_data = data
                existing.is_active = True
                print(f"  ✅ 更新模板: {name_zh}")
            else:
                session.add(RouteTemplate(
                    name_zh=name_zh,
                    city_code=data["city_code"],
                    duration_days=data["total_days"],
                    template_data=data,
                    is_active=True,
                ))
                print(f"  ✅ 创建模板: {name_zh}")
        await session.commit()

    print("\n📋 Step 3: 修复数据库问题...")
    await fix_data_issues()

    print("\n🎉 所有修复完成！")


asyncio.run(main())
