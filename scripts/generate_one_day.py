"""
🗾 一日攻略生成器 (Demo)
========================

从本地数据库取高分景点/餐厅/酒店，调用 AI 生成一日攻略。

用法:
  python scripts/generate_one_day.py tokyo
  python scripts/generate_one_day.py kyoto --scene sakura
  python scripts/generate_one_day.py osaka --scene food
"""
import asyncio
import json
import os
import ssl
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


DB_URL = os.getenv("DATABASE_URL", "")
AI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
AI_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL_STRONG", os.getenv("AI_MODEL_STANDARD", "gpt-4o"))


async def fetch_top_entities(session: AsyncSession, city: str):
    """获取城市高分实体"""
    
    # POI top 8
    pois = (await session.execute(text("""
        SELECT eb.name_zh, eb.name_ja, eb.name_en, es.final_score, eb.entity_type
        FROM entity_base eb
        LEFT JOIN entity_scores es ON eb.entity_id = es.entity_id
        WHERE eb.city_code = :city AND eb.entity_type = 'poi'
        ORDER BY es.final_score DESC NULLS LAST
        LIMIT 8
    """), {"city": city})).fetchall()

    # 餐厅 top 5
    restaurants = (await session.execute(text("""
        SELECT eb.name_zh, eb.name_ja, eb.name_en, es.final_score, r.cuisine_type
        FROM entity_base eb
        LEFT JOIN entity_scores es ON eb.entity_id = es.entity_id
        LEFT JOIN restaurants r ON eb.entity_id = r.entity_id
        WHERE eb.city_code = :city AND eb.entity_type = 'restaurant'
        ORDER BY es.final_score DESC NULLS LAST
        LIMIT 5
    """), {"city": city})).fetchall()

    # 酒店 top 3
    hotels = (await session.execute(text("""
        SELECT eb.name_zh, eb.name_ja, eb.name_en, es.final_score, h.star_rating
        FROM entity_base eb
        LEFT JOIN entity_scores es ON eb.entity_id = es.entity_id
        LEFT JOIN hotels h ON eb.entity_id = h.entity_id
        WHERE eb.city_code = :city AND eb.entity_type = 'hotel'
        ORDER BY es.final_score DESC NULLS LAST
        LIMIT 3
    """), {"city": city})).fetchall()

    return pois, restaurants, hotels


def format_entities(pois, restaurants, hotels) -> str:
    """格式化实体信息给 AI"""
    lines = []
    lines.append("## 可选景点 (按评分排序)")
    for i, p in enumerate(pois, 1):
        name = p[0] or p[1] or "未知"
        desc = (p[2] or "")[:60]
        score = p[3] or 0
        lines.append(f"  {i}. {name} (评分:{score:.0f}) {desc}")

    lines.append("\n## 可选餐厅")
    for i, r in enumerate(restaurants, 1):
        name = r[0] or r[1] or "未知"
        cuisine = r[4] or "日料"
        score = r[3] or 0
        lines.append(f"  {i}. {name} ({cuisine}, 评分:{score:.0f})")

    lines.append("\n## 推荐住宿")
    for i, h in enumerate(hotels, 1):
        name = h[0] or h[1] or "未知"
        star = h[4] or "?"
        score = h[3] or 0
        lines.append(f"  {i}. {name} ({star}星, 评分:{score:.0f})")

    return "\n".join(lines)


async def call_ai(city: str, scene: str, entity_info: str) -> str:
    """调用 AI 生成一日攻略"""
    
    scene_hints = {
        "general": "经典观光路线",
        "sakura": "樱花季赏花路线，优先安排有樱花的景点",
        "food": "美食探索路线，以吃为主线串联景点",
        "culture": "文化深度游，神社/寺庙/博物馆",
        "family": "亲子友好路线，适合带小孩",
        "shopping": "购物+观光路线",
    }
    scene_desc = scene_hints.get(scene, scene)

    prompt = f"""你是一位资深日本旅行规划师，请根据以下数据为中国游客生成一份【{city.upper()} 一日攻略】。

场景: {scene_desc}

{entity_info}

请生成一份完整的一日行程，要求:
1. 时间安排从 09:00 到 21:00，精确到半小时
2. 选择 4-5 个景点 + 2 餐 (午餐+晚餐) + 推荐住宿
3. 考虑地理位置的合理性，相近的景点安排在一起
4. 每个景点给出：推荐游览时长、一句话亮点、实用小贴士
5. 包含交通方式建议 (地铁/步行/公交)
6. 末尾给出：预算估算 (门票+餐饮+交通) 和注意事项

输出格式：Markdown，使用 emoji 让内容更生动。
语言：中文，景点名附带日文原名。
"""

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{AI_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {AI_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": AI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 3000,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def main():
    city = sys.argv[1] if len(sys.argv) > 1 else "tokyo"
    scene = "general"
    for i, arg in enumerate(sys.argv):
        if arg == "--scene" and i + 1 < len(sys.argv):
            scene = sys.argv[i + 1]

    print(f"\n🗾 生成 {city.upper()} 一日攻略 (场景: {scene})")
    print(f"{'='*50}\n")

    # 1. 连接数据库
    print("📊 从数据库获取高分实体...")
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        pois, restaurants, hotels = await fetch_top_entities(session, city)

    await engine.dispose()

    print(f"   景点: {len(pois)} 个, 餐厅: {len(restaurants)} 个, 酒店: {len(hotels)} 个")

    if not pois:
        print(f"\n❌ {city} 没有景点数据，无法生成攻略")
        return

    entity_info = format_entities(pois, restaurants, hotels)
    print(f"\n📋 实体摘要:\n{entity_info}\n")

    # 2. 调用 AI 生成
    print(f"🤖 调用 AI ({AI_MODEL}) 生成攻略...")
    result = await call_ai(city, scene, entity_info)

    # 3. 输出
    print(f"\n{'='*50}")
    print(result)
    print(f"{'='*50}")

    # 4. 保存文件
    output_dir = Path("output/guides")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{city}_oneday_{scene}.md"
    output_file.write_text(result, encoding="utf-8")
    print(f"\n💾 已保存到: {output_file}")


asyncio.run(main())
