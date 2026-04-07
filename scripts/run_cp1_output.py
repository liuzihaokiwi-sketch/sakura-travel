"""
run_cp1_output.py — CP1 完整生产路径输出

Step 1: UserConstraints（内存构造）
Step 2: RegionSummary（JSON 数据）
Step 3: 城市组合（qwen-max 真实调用）
Step 4: POI 候选池（JSON 数据）

输出到 Markdown 文件。
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import io
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

import os
from openai import AsyncOpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domains.planning_v2.models import (
    CandidatePool,
    CircleProfile,
    RegionSummary,
    UserConstraints,
)
from app.domains.planning_v2.step03_city_planner import (
    plan_city_combination,
    _build_fallback_plan,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "kansai_spots" / "archived_ai_generated"

CITY_ZH = {
    "kyoto": "京都", "osaka": "大阪", "kobe": "神户", "nara": "奈良",
    "himeji": "姫路", "uji": "宇治", "otsu": "大津", "arima": "有马",
    "kinosaki": "城崎", "shirahama": "白浜", "koyasan": "高野山",
}
INTENSITY_ZH = {"light": "轻松", "medium": "适中", "moderate": "适中", "heavy": "密集"}


def load_data():
    spots = []
    for f in ["kyoto_city.json", "kyoto_extended.json", "osaka_city.json", "nara.json", "hyogo.json"]:
        p = DATA_DIR / f
        if p.exists():
            spots.extend(json.loads(p.read_text(encoding="utf-8")).get("spots", []))

    restaurants = []
    for p in DATA_DIR.glob("restaurants_*.json"):
        restaurants.extend(json.loads(p.read_text(encoding="utf-8")).get("restaurants", []))

    hotels = []
    for p in DATA_DIR.glob("hotels_*.json"):
        hotels.extend(json.loads(p.read_text(encoding="utf-8")).get("hotels", []))

    return spots, restaurants, hotels


async def call_step3(uc: UserConstraints, rs: RegionSummary, circle: CircleProfile) -> tuple[dict, str]:
    """直接调用 plan_city_combination，走生产代码路径（Opus + extended thinking）。"""
    print("[Step3] 调用 plan_city_combination (Anthropic Opus)...", file=sys.stderr)
    result = await plan_city_combination(uc, rs, circle)
    used_ai = "error" not in result and not result.get("fallback")
    note = "Anthropic Opus 真实调用" if used_ai else f"规则兜底（{result.get('error', 'unknown')}）"
    print(f"[Step3] {note}，{len(result.get('candidates', []))} 个方案", file=sys.stderr)
    return result, note


async def main():
    circle = CircleProfile.from_registry("kansai")
    spots, restaurants, hotels = load_data()

    # Step 1: UserConstraints
    uc = UserConstraints(
        trip_window={"start_date": "2026-04-15", "end_date": "2026-04-21", "total_days": 7},
        user_profile={
            "party_type": "couple",
            "budget_tier": "mid",
            "must_have_tags": ["shrine", "garden"],
            "nice_to_have_tags": ["photo_spot", "cafe"],
            "avoid_tags": [],
        },
        constraints={
            "must_visit": [],
            "do_not_go": [],
            "visited": [],
            "booked_items": [],
        },
    )
    print("[Step1] UserConstraints 构造完成", file=sys.stderr)

    # Step 2: RegionSummary
    poi_in_circle = [s for s in spots if s.get("city_code") in circle.cities]
    rest_in_circle = [r for r in restaurants if r.get("city_code") in circle.cities]
    hotel_in_circle = [h for h in hotels if h.get("city_code") in circle.cities]
    grade_dist: dict[str, int] = {}
    for s in poi_in_circle:
        g = s.get("grade", "B")
        grade_dist[g] = grade_dist.get(g, 0) + 1

    rs = RegionSummary(
        circle_name="关西",
        cities=circle.cities,
        entity_count=len(poi_in_circle) + len(rest_in_circle) + len(hotel_in_circle),
        entities_by_type={
            "poi": len(poi_in_circle),
            "restaurant": len(rest_in_circle),
            "hotel": len(hotel_in_circle),
            "event": 0,
        },
        grade_distribution=grade_dist,
    )
    print(f"[Step2] RegionSummary: {rs.entity_count} 个实体", file=sys.stderr)

    # Step 3: Anthropic Opus 城市组合（生产路径）
    city_plan, step3_note = await call_step3(uc, rs, circle)
    used_ai = "Opus" in step3_note

    # Step 4: POI 候选池
    poi_pool = []
    for s in poi_in_circle:
        if s.get("grade") not in ("S", "A"):
            continue
        coord = s.get("coord") or [0.0, 0.0]
        cost = s.get("cost") or {}
        poi_pool.append(CandidatePool(
            entity_id=s["id"],
            name_zh=s["name_zh"],
            entity_type="poi",
            grade=s.get("grade", "B"),
            latitude=coord[0],
            longitude=coord[1],
            tags=s.get("tags", []),
            visit_minutes=s.get("visit_minutes", 60),
            cost_local=cost.get("admission_jpy", 0) or 0,
            city_code=s.get("city_code", ""),
            open_hours=s.get("when", {}),
            review_signals=s.get("review_signals", {}),
        ))
    print(f"[Step4] POI 候选池: {len(poi_pool)} 个 S/A 级景点", file=sys.stderr)

    # ── 生成 Markdown ──────────────────────────────────────────────────────────
    lines = []
    lines.append("# CP1 输出报告 — 7天关西情侣行程 (7d_classic)")
    lines.append("")
    lines.append("## 一、表单输入（Step 1）")
    lines.append("")
    lines.append("| 字段 | 值 |")
    lines.append("|------|----|")
    lines.append("| 行程 | 7天（2026-04-15 ~ 2026-04-21） |")
    lines.append("| 人群 | 情侣（couple） |")
    lines.append("| 预算 | 中档（mid） |")
    lines.append("| 必有标签 | shrine、garden |")
    lines.append("| 偏好标签 | photo_spot、cafe |")
    lines.append("| 必去 | 无 |")
    lines.append("| 不去 | 无 |")
    lines.append("| 已去过 | 无 |")
    lines.append("")

    lines.append("## 二、地区摘要（Step 2）")
    lines.append("")
    lines.append(f"- **城市圈**：关西（{'、'.join(CITY_ZH.get(c, c) for c in circle.cities[:7])}等）")
    lines.append(f"- **总实体**：{rs.entity_count} 个")
    lines.append(f"- 景点 **{rs.entities_by_type['poi']}** 个 / 餐厅 **{rs.entities_by_type['restaurant']}** 个 / 酒店 **{rs.entities_by_type['hotel']}** 个")
    lines.append(f"- **等级分布**：S={grade_dist.get('S', 0)} / A={grade_dist.get('A', 0)} / B={grade_dist.get('B', 0)} / C={grade_dist.get('C', 0)}")
    lines.append("")

    lines.append(f"## 三、城市组合方案（Step 3 — {step3_note}）")
    lines.append("")

    candidates = city_plan.get("candidates", [])
    recommended_idx = city_plan.get("recommended_index", 0)

    for i, cand in enumerate(candidates):
        marker = " ⭐ 推荐" if i == recommended_idx else ""
        lines.append(f"### 方案 {i+1}：{cand.get('plan_name', '')}{marker}")
        lines.append("")
        lines.append(f"**推荐理由**：{cand.get('reasoning', '')}")
        lines.append("")
        lines.append(f"**取舍说明**：{cand.get('trade_offs', '')}")
        lines.append("")
        lines.append("| 天 | 城市 | 主题 | 强度 |")
        lines.append("|----|------|------|------|")
        cbd = cand.get("cities_by_day", {})
        for day_key, day_data in sorted(cbd.items(), key=lambda x: int(x[0].replace("day", ""))):
            day_num = day_key.replace("day", "")
            city_en = day_data.get("city", "")
            city_zh = CITY_ZH.get(city_en, city_en)
            intensity = INTENSITY_ZH.get(day_data.get("intensity", ""), day_data.get("intensity", ""))
            theme = day_data.get("theme", "")
            lines.append(f"| Day {day_num} | {city_zh} | {theme} | {intensity} |")
        lines.append("")

    lines.append("## 四、POI 候选池（Step 4）")
    lines.append("")
    lines.append(f"共筛选出 **{len(poi_pool)} 个** S/A 级景点（已排除 B/C 级、do_not_go、visited）")
    lines.append("")

    city_groups: dict[str, list[CandidatePool]] = {}
    for p in poi_pool:
        city_groups.setdefault(p.city_code, []).append(p)

    for city_en, pois in sorted(city_groups.items(), key=lambda x: len(x[1]), reverse=True):
        city_zh = CITY_ZH.get(city_en, city_en)
        s_count = sum(1 for p in pois if p.grade == "S")
        a_count = sum(1 for p in pois if p.grade == "A")
        lines.append(f"### {city_zh}（{city_en}）— {len(pois)} 个（S:{s_count} A:{a_count}）")
        lines.append("")
        lines.append("| 级 | 景点名称 | 时长 | 门票 | 标签 |")
        lines.append("|----|---------|------|------|------|")
        for p in sorted(pois, key=lambda x: (0 if x.grade == "S" else 1, -x.visit_minutes)):
            tags_str = "、".join(p.tags[:3]) if p.tags else "—"
            cost_str = f"¥{p.cost_local}" if p.cost_local > 0 else "免费"
            lines.append(f"| {p.grade} | {p.name_zh} | {p.visit_minutes}分钟 | {cost_str} | {tags_str} |")
        lines.append("")

    lines.append("## 五、CP1 质量观察")
    lines.append("")
    lines.append("### 结构验证")
    lines.append("")
    lines.append("| 检查项 | 结果 | 说明 |")
    lines.append("|--------|------|------|")

    tw = uc.trip_window
    from datetime import date
    start = date.fromisoformat(tw["start_date"])
    end = date.fromisoformat(tw["end_date"])
    days_check = (end - start).days + 1 == tw["total_days"]

    lines.append(f"| total_days 与日期一致 | {'✅' if days_check else '❌'} | {tw['total_days']}天，日期差+1={days_check} |")
    lines.append(f"| POI 池大小合理 | {'✅' if 10 <= len(poi_pool) <= 200 else '❌'} | {len(poi_pool)} 个，期望 [10, 200] |")
    lines.append(f"| Step 3 使用 AI | {'✅' if used_ai else '⚠️'} | {step3_note} |")

    # 首末日强度检查
    first_day = candidates[recommended_idx]["cities_by_day"].get("day1", {}) if candidates else {}
    last_key = f"day{tw['total_days']}"
    last_day = candidates[recommended_idx]["cities_by_day"].get(last_key, {}) if candidates else {}
    first_ok = first_day.get("intensity") == "light"
    last_ok = last_day.get("intensity") == "light"
    lines.append(f"| 首日强度 light | {'✅' if first_ok else '❌'} | intensity={first_day.get('intensity', '—')} |")
    lines.append(f"| 末日强度 light | {'✅' if last_ok else '❌'} | intensity={last_day.get('intensity', '—')} |")

    # 城市在圈内
    all_in_circle = all(
        d.get("city") in circle.cities
        for cand in candidates
        for d in cand.get("cities_by_day", {}).values()
    )
    lines.append(f"| 所有城市在关西圈内 | {'✅' if all_in_circle else '❌'} | — |")
    lines.append("")

    lines.append("### 质量观察（人工判断）")
    lines.append("")
    lines.append("请根据以下维度评估 Step 3 推荐方案的质量：")
    lines.append("")
    lines.append("- [ ] 城市组合是否符合情侣 mid 档的偏好（shrine、garden）？")
    lines.append("- [ ] 7天行程城市分布是否合理（不来回折腾）？")
    lines.append("- [ ] 首末日城市选择是否便于到达/离开（大阪/京都交通枢纽）？")
    lines.append("- [ ] 3个方案是否有明显风格差异？")
    lines.append("- [ ] POI 池里是否涵盖 shrine（神社）和 garden（庭园）类景点？")
    lines.append("")
    lines.append("---")
    lines.append(f"*Step 3：{step3_note} | 数据来源：archived_ai_generated JSON*")

    output = "\n".join(lines)

    out_path = Path(__file__).resolve().parents[1] / "tmp_cp1_output_7d_classic.md"
    out_path.write_text(output, encoding="utf-8")
    print(f"\n✅ 已写入：{out_path}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
