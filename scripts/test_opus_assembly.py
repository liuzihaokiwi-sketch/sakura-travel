"""
Opus 装配端到端测试。

完全走真实流程：
  loader 读文件 → 硬筛 → Opus 第一步（路线+酒店）→ Opus 第二步（配餐+校验）→ 打印结果

用法：
  cd d:/projects/projects/travel-ai
  .venv/Scripts/python scripts/test_opus_assembly.py

不需要 DB，不需要 worker，直接调 opus_assembler。
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# ── 路径设置 ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# 加载项目 .env（override=True 确保用项目的阿里云 key）
from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=True)

# saiai 代理只允许 CC 客户端，直接走阿里云 qwen-max
os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
os.environ.pop("ANTHROPIC_API_KEY", None)
# 确保 DASHSCOPE_API_KEY 设好（从 OPENAI_API_KEY 取）
if not os.environ.get("DASHSCOPE_API_KEY"):
    os.environ["DASHSCOPE_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("test_opus")

# ── 测试用例 ──────────────────────────────────────────────────────────────────

TEST_CONSTRAINTS = {
    "dates": {
        "start": "2026-05-10",
        "end": "2026-05-16",   # 7天
        "arrival_slot": "afternoon",
        "departure_slot": "morning",
    },
    "party": {
        "adults": 2,
        "children": 0,
        "elderly": 0,
    },
    "vibe": "classic",
    "density": "balanced",
    "pre_booked": [],
    "skip_tags": [],
    "skip_entities": [],
    "include_entities": [],
    "notes": "",
}

TEST_BUDGET_PROFILE = {
    "dining_tier": "local_good",   # street / local_good / fine / top
    "dining_preference": "taste_first",
    "hotel_tier": "comfort",
}


# ── 主流程 ────────────────────────────────────────────────────────────────────

async def main() -> None:
    from app.domains.templates.loader import get_template_loader
    from app.domains.planning_v2.opus_assembler import (
        assemble_route_and_hotels,
        assemble_restaurants,
    )

    # ── 1. 加载数据 ───────────────────────────────────────────────────────────
    logger.info("加载模板数据...")
    loader = get_template_loader()
    policy = loader.load_policy()

    assembly_rules_path = ROOT / "content" / "kansai" / "assembly_rules.json"
    assembly_rules = (
        json.loads(assembly_rules_path.read_text(encoding="utf-8"))
        if assembly_rules_path.exists()
        else {"rules": []}
    )

    cities = loader.list_cities()
    logger.info("发现城市：%s", cities)

    city_days_map: dict = {}
    city_hotels_map: dict = {}
    city_restaurants_map: dict = {}

    for city in cities:
        city_days_map[city] = loader.load_city_days(city)
        try:
            city_hotels_map[city] = loader.load_city_hotels(city)
        except Exception:
            city_hotels_map[city] = {}
        try:
            city_restaurants_map[city] = loader.load_city_restaurants(city)
        except Exception:
            city_restaurants_map[city] = {}

    # 统计候选池规模
    for city in cities:
        n_templates = len(city_days_map[city].get("day_templates", []))
        n_hotels = len(city_hotels_map[city].get("hotels", []))
        n_restaurants = len(city_restaurants_map[city].get("restaurants", []))
        logger.info("  %s: %d模板 / %d酒店 / %d餐厅", city, n_templates, n_hotels, n_restaurants)

    # ── 2. Opus 第一步：路线 + 酒店 ──────────────────────────────────────────
    logger.info("\n========== 第一步：Opus 装配路线+酒店 ==========")
    step1 = await assemble_route_and_hotels(
        constraints=TEST_CONSTRAINTS,
        policy=policy,
        assembly_rules=assembly_rules,
        city_days_map=city_days_map,
        city_hotels_map=city_hotels_map,
    )

    print("\n【第一步结果】")
    print(f"条件摘要：{step1.get('condition_summary', '')}")
    print(f"城市分配：{json.dumps(step1.get('city_allocation', []), ensure_ascii=False)}")
    print(f"酒店选择：{json.dumps(step1.get('hotel_selections', {}), ensure_ascii=False)}")
    print(f"\nOpus 决策说明：")
    for d in step1.get("decisions", []):
        print(f"  • {d}")

    print(f"\n每日方案（{len(step1.get('daily_plans', []))} 天）：")
    for dp in step1.get("daily_plans", []):
        print(f"  Day {dp['day']} [{dp.get('city','')}] {dp.get('template_id','')} — {dp.get('title','')}")
        print(f"    {dp.get('description','')}")

    print(f"\n可添加体验：")
    for ae in step1.get("addable_experiences", []):
        print(f"  {ae.get('icon','')} {ae.get('label','')} — {ae.get('description','')}")

    # ── 3. Opus 第二步：配餐 + 校验 ──────────────────────────────────────────
    logger.info("\n========== 第二步：Opus 配餐+校验 ==========")
    enriched_plans = await assemble_restaurants(
        daily_plans=step1.get("daily_plans", []),
        constraints=TEST_CONSTRAINTS,
        city_restaurants_map=city_restaurants_map,
        budget_profile=TEST_BUDGET_PROFILE,
        policy=policy,
        city_days_map=city_days_map,
    )

    print("\n【第二步结果：配餐】")
    for dp in enriched_plans:
        meals = dp.get("meal_selections", {})
        lunch = meals.get("lunch", {})
        dinner = meals.get("dinner", {})
        print(f"  Day {dp['day']} [{dp.get('city','')}] {dp.get('template_id','')}")
        if lunch:
            print(f"    午餐: {lunch.get('restaurant_id','')} ({lunch.get('meal_role','')}) — {lunch.get('reason','')}")
        if dinner:
            print(f"    晚餐: {dinner.get('restaurant_id','')} ({dinner.get('meal_role','')}) — {dinner.get('reason','')}")

    # 汇总输出完整 JSON 供检查
    output_path = ROOT / "logs" / "opus_assembly_test.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {"step1": step1, "step2": enriched_plans},
            f,
            ensure_ascii=False,
            indent=2,
        )
    logger.info("完整结果已写入 %s", output_path)


if __name__ == "__main__":
    asyncio.run(main())
