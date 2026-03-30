"""
C2: 从 C1 的评论原文中提取维度评分 + 生成摘要

读取 source_snapshots.review_batch → AI 提取维度 → 存入:
  entity_review_signals (positive_tags / negative_tags / queue_risk_level)
  entity_descriptions   (description_type: why_go / practical_tip / skip_if)

AI: DashScope deepseek-v3.2（省钱，中日文理解好）
注意：Anthropic API 不能高并发，这里用 semaphore 限速，最多 3 并发

运行: python scripts/extract_review_dimensions.py [--limit 20] [--dry-run]
"""
from __future__ import annotations

import asyncio, argparse, json, logging, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import openai
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

logging.basicConfig(level=logging.WARNING)

# DashScope (阿里云) — 不限并发，但我们保守一点
DASHSCOPE_CLIENT = openai.AsyncOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "sk-df19f2a1b7e94841a968063ea047117f"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
MODEL = "deepseek-v3.2"

# 最多 3 并发（DashScope 比较稳定，可以适当提高）
SEM = asyncio.Semaphore(3)

SYSTEM_PROMPT = """你是旅游评价分析专家。请从给定的 Google 评论中提取结构化信息。

评论可能是日文或中文。请用 JSON 格式返回以下字段：

对于餐厅 (restaurant)：
{
  "dimensions": {
    "signature_dish_clarity": "clear|unclear|none",
    "queue_risk": "none|low|medium|high",
    "reservation_difficulty": "none|easy|hard",
    "language_friendliness": "english_ok|japanese_only|no_info",
    "payment_method": "cash_and_card|cash_only|no_info",
    "value_perception": "excellent|good|average|poor|no_info"
  },
  "why_go": "一句话：为什么值得去（15字以内）",
  "practical_tip": "一句话：实用提醒，如预约/排队/停车（20字以内）",
  "skip_if": "一句话：什么情况下可以不去（15字以内，如无明显缺点填null）",
  "positive_tags": ["标签1", "标签2"],
  "negative_tags": ["标签1", "标签2"]
}

对于景点 (poi)：
{
  "dimensions": {
    "best_timing": "morning|afternoon|evening|any",
    "weather_sensitivity": "rain_ok|rain_ruins|outdoor_only|indoor_ok",
    "physical_demand": "easy|moderate|strenuous",
    "photo_value": "excellent|good|average|low",
    "crowd_pattern": "always_crowded|peak_crowded|rarely_crowded|no_info",
    "child_friendly": "great|ok|not_suitable|no_info",
    "season_dependency": "year_round|specific_season|no_info"
  },
  "why_go": "一句话：为什么值得去（15字以内）",
  "practical_tip": "一句话：最佳时间或注意事项（20字以内）",
  "skip_if": "一句话：什么情况下可以不去（15字以内，无明显缺点填null）",
  "positive_tags": ["标签1", "标签2"],
  "negative_tags": ["标签1", "标签2"]
}

对于酒店 (hotel)：
{
  "dimensions": {
    "location_convenience": "excellent|good|average|poor",
    "room_condition": "excellent|good|average|poor|no_info",
    "bath_quality": "excellent|good|average|poor|no_info",
    "breakfast_quality": "excellent|good|average|poor|no_info",
    "soundproofing": "good|average|poor|no_info",
    "value_perception": "excellent|good|average|poor",
    "best_for": "couple|family|business|solo|any"
  },
  "why_go": "一句话：为什么值得住（15字以内）",
  "practical_tip": "一句话：入住建议（20字以内）",
  "skip_if": "一句话：什么情况下不推荐（15字以内，无明显缺点填null）",
  "positive_tags": ["标签1", "标签2"],
  "negative_tags": ["标签1", "标签2"]
}

规则：
- 只从评论中可以看出来的填写，看不出来的用 "no_info" 或 null
- 负面标签：需要至少 2 条评论提到才采信
- why_go / practical_tip 必须填写；skip_if 可以为 null
- positive_tags / negative_tags 各 1-4 个，用中文
- 直接返回 JSON，不要解释"""


def _filter_reviews(reviews: list) -> list:
    """过滤低质量评论"""
    filtered = []
    for r in reviews:
        text = (r.get("text") or "").strip()
        if len(text) < 5:
            continue
        # 纯情绪判断（没有具体描述）
        if len(text) < 15 and not any(c in text for c in "好吃美味景色服务早餐排队"):
            continue
        filtered.append(r)
    return filtered


async def extract_dimensions(
    entity_id: str,
    entity_type: str,
    entity_name: str,
    reviews: list,
) -> dict | None:
    """调用 AI 提取维度"""
    filtered = _filter_reviews(reviews)
    if not filtered:
        return None

    # 准备评论文本
    review_texts = []
    for i, r in enumerate(filtered[:5], 1):
        text = (r.get("text") or "").strip()
        rating = r.get("rating", "?")
        lang = r.get("language", "")
        review_texts.append(f"[{i}] ★{rating} ({lang}): {text[:300]}")

    combined = "\n".join(review_texts)
    user_msg = f"实体名称: {entity_name}\n实体类型: {entity_type}\n\n评论原文:\n{combined}"

    async with SEM:
        try:
            resp = await DASHSCOPE_CLIENT.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=600,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logging.warning(f"AI extraction failed for {entity_name}: {e}")
            return None


async def save_results(session, entity_id: str, entity_type: str, result: dict) -> None:
    """保存提取结果到 DB"""
    # 1. entity_review_signals
    dims = result.get("dimensions", {})
    pos_tags = result.get("positive_tags", [])
    neg_tags = result.get("negative_tags", [])
    queue_risk = dims.get("queue_risk") if entity_type == "restaurant" else None

    await session.execute(text("""
        INSERT INTO entity_review_signals
          (entity_id, rating_source, positive_tags, negative_tags,
           summary_tags, queue_risk_level, confidence_score)
        VALUES
          (:eid, 'google_reviews', CAST(:pos AS jsonb), CAST(:neg AS jsonb),
           CAST(:summary AS jsonb), :qrisk, 0.7)
        ON CONFLICT (entity_id, rating_source) DO UPDATE SET
          positive_tags = EXCLUDED.positive_tags,
          negative_tags = EXCLUDED.negative_tags,
          summary_tags = EXCLUDED.summary_tags,
          queue_risk_level = EXCLUDED.queue_risk_level,
          updated_at = NOW()
    """), {
        "eid": entity_id,
        "pos": json.dumps(pos_tags, ensure_ascii=False),
        "neg": json.dumps(neg_tags, ensure_ascii=False),
        "summary": json.dumps(dims, ensure_ascii=False),
        "qrisk": queue_risk if queue_risk in ("none", "low", "medium", "high") else None,
    })

    # 2. entity_descriptions
    for dtype, content in [
        ("review_why_go", result.get("why_go")),
        ("review_practical_tip", result.get("practical_tip")),
        ("review_skip_if", result.get("skip_if")),
    ]:
        if not content:
            continue
        await session.execute(text("""
            INSERT INTO entity_descriptions
              (entity_id, source_kind, description_type, content, language,
               confidence_score, needs_review, is_active)
            VALUES
              (:eid, 'google_reviews', :dtype, :content, 'zh', 0.7, false, true)
            ON CONFLICT DO NOTHING
        """), {"eid": entity_id, "dtype": dtype, "content": content})


async def process_entity(snapshot: dict) -> tuple[str, bool]:
    """处理单个实体的评论批次，返回 (entity_name, success)"""
    payload = snapshot["payload"]
    entity_id = str(payload.get("entity_id", ""))
    entity_type = payload.get("entity_type", "poi")
    entity_name = payload.get("entity_name", entity_id[:8])
    reviews = payload.get("reviews", [])

    if not entity_id or not reviews:
        return entity_name, False

    result = await extract_dimensions(entity_id, entity_type, entity_name, reviews)
    if not result:
        return entity_name, False

    # 每个实体用独立 session，避免并发冲突
    try:
        async with AsyncSessionLocal() as session:
            await save_results(session, entity_id, entity_type, result)
            await session.commit()
        return entity_name, True
    except Exception as e:
        logging.warning(f"Save failed for {entity_name}: {e}")
        return entity_name, False


async def main(limit: int = 100, dry_run: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        # 加载所有 review_batch
        rows = (await session.execute(text("""
            SELECT object_id, raw_payload
            FROM source_snapshots
            WHERE object_type = 'review_batch'
            ORDER BY fetched_at
            LIMIT :limit
        """), {"limit": limit})).fetchall()

        print(f"[C2] Processing {len(rows)} review batches...")

        snapshots = []
        for row in rows:
            payload = row[1] if isinstance(row[1], dict) else json.loads(row[1] or "{}")
            snapshots.append({"object_id": row[0], "payload": payload})

        if dry_run:
            # 只测试第一个
            if snapshots:
                s = snapshots[0]
                payload = s["payload"]
                reviews = payload.get("reviews", [])
                print(f"  DRY RUN: testing entity {payload.get('entity_name')} ({payload.get('entity_type')})")
                result = await extract_dimensions(
                    str(payload.get("entity_id", "")),
                    payload.get("entity_type", "poi"),
                    payload.get("entity_name", "?"),
                    reviews,
                )
                if result:
                    print(f"  Result: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
                else:
                    print("  No result")
            return

        # 并发处理（3 并发，DashScope 稳，每个实体独立 session）
        tasks = [process_entity(s) for s in snapshots]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success = 0
        failed = 0
        for r in results:
            if isinstance(r, Exception):
                logging.warning(f"Task exception: {r}")
                failed += 1
            elif r[1]:
                success += 1
            else:
                failed += 1

        print(f"  OK: {success} extracted, {failed} failed")

        # 验证（用新 session）
        r = await session.execute(text(
            "SELECT COUNT(*) FROM entity_review_signals WHERE rating_source='google_reviews'"
        ))
        print(f"  entity_review_signals[google_reviews]: {r.scalar()}")
        r2 = await session.execute(text(
            "SELECT description_type, COUNT(*) FROM entity_descriptions GROUP BY description_type ORDER BY description_type"
        ))
        print("  entity_descriptions:")
        for row in r2.fetchall():
            print(f"    {row[0]}: {row[1]}")

    print("\nC2 DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(limit=args.limit, dry_run=args.dry_run))
