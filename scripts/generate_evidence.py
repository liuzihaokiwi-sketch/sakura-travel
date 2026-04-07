#!/usr/bin/env python
"""
Phase 2B: generate_evidence.py
对 selected + borderline 的候选用 Sonnet 生成结构化证据块。

输入:
  data/kansai_spots/restaurants_ledger_phase2a.json
  data/kansai_spots/hotels_ledger_phase2a.json
  data/kansai_spots/spots_ledger_phase2a.json

输出 (in-place update):
  data/kansai_spots/restaurants_ledger_phase2b.json
  data/kansai_spots/hotels_ledger_phase2b.json
  data/kansai_spots/spots_ledger_phase2b.json

运行方式:
  python scripts/generate_evidence.py --type restaurants [--batch-size 15] [--dry-run]
  python scripts/generate_evidence.py --type hotels
  python scripts/generate_evidence.py --type spots
"""
import argparse
import json
import sys
import time
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = Path("data/kansai_spots/phase2_ledger")

SYSTEM_PROMPT = """你是关西旅行选品专家，为中国20-40岁游客制作付费手账本（纸质，298/348元）。

任务: 对每个候选条目生成结构化证据块，支持编辑做最终选品判断。

产品标准: "十个日本旅游专家联合做的攻略"级别。每条推荐必须经得起专业质疑。

铁律:
- 不编造数据。评分/价格/坐标/营业时间等事实字段如果不知道就填 null，绝不猜测
- quality_evidence: 用该城市×菜系×预算层内的相对位置描述，不说全局绝对分数
- traveler_fit_evidence: 从中国游客视角，说清楚为什么这类用户会满意（或不满意）
- execution_evidence: 只写实际执行摩擦（定休日/排队/预约难度/交通），没有摩擦就写"正常"
- risk_watch: none/mild/medium/high，只有有具体风险证据才升级
- grade_suggestion: S/A/B/C，参考 MASTER_GUIDE 定义（S=城市名片，A=值得专程，B=行程增色，C=顺路）
- one_line_editorial_note: 用一句话说清"为什么选/为什么不选"，要有具体依据
"""

BATCH_PROMPT_TEMPLATE = """以下是 {n} 个候选条目（{category}，{city}），请对每个生成证据块。

候选列表:
{candidates_json}

**输出格式**: 严格 JSON 数组，每个元素对应一个候选（顺序一一对应）：
[
  {{
    "name_ja": "原样返回",
    "quality_evidence": "string, 50-120字，用组内相对位置描述",
    "traveler_fit_modifier": 数字 -0.5到+0.5,
    "traveler_fit_evidence": "string, 30-80字，中国游客视角",
    "execution_penalty": 数字 -1.0到0,
    "execution_evidence": "string, 20-60字，实际执行摩擦",
    "risk_watch": "none/mild/medium/high",
    "risk_detail": "string或null",
    "editorial_exclusion": false/true,
    "editorial_exclusion_reason": "string或null",
    "one_line_editorial_note": "string, 一句话选品依据",
    "grade_suggestion": "S/A/B/C",
    "selection_tags": ["city_icon"和/或"traveler_hot"和/或"local_benchmark"，可为空数组]
  }},
  ...
]

只输出 JSON 数组，不要任何解释文字。"""


def call_sonnet(prompt: str, system: str) -> str:
    """调用 Sonnet API，返回原始文本"""
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def parse_response(text: str) -> list:
    """从 Sonnet 输出中提取 JSON 数组"""
    text = text.strip()
    # 找 [ ... ] 范围
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON array found in response: {text[:200]}")
    return json.loads(text[start:end])


def build_candidate_info(entry: dict, category: str, slot_peers: list) -> dict:
    """构建给 Sonnet 的候选摘要"""
    base = {
        "name_ja": entry["name_ja"],
        "city": entry["city_code"],
        "area": entry.get("area", ""),
        "base_quality_score": entry["base_quality_score"],
        "score_basis": entry["score_basis"],
    }
    if category == "restaurants":
        base.update({
            "cuisine": entry.get("cuisine_normalized", ""),
            "budget_tier": entry["budget_tier"],
            "tabelog_score": entry.get("tabelog_score"),
            "michelin": entry.get("michelin"),
            "slot": entry["selection_slot"],
            "slot_peers_count": len(slot_peers),
            "slot_peers_top3": [p["name_ja"] for p in sorted(slot_peers, key=lambda x: -x["house_score"])[:3]
                                 if p["name_ja"] != entry["name_ja"]],
        })
    elif category == "hotels":
        base.update({
            "hotel_type": entry.get("hotel_type", ""),
            "price_level": entry["price_level"],
            "michelin_keys": entry.get("michelin_keys"),
            "ota_rating": entry.get("ota_rating"),
            "key_features": entry.get("key_features", ""),
            "slot": entry["selection_slot"],
        })
    elif category == "spots":
        base.update({
            "main_type": entry.get("main_type", ""),
            "sub_type": entry.get("sub_type", ""),
            "japan_guide_level": entry.get("japan_guide_level", ""),
            "slot": entry["selection_slot"],
        })
    return base


def process_batch(batch: list, category: str, city: str, slot_map: dict, dry_run: bool) -> list:
    """处理一批候选，返回 evidence 结果列表"""
    candidates = [build_candidate_info(e, category, slot_map.get(e["selection_slot"], [])) for e in batch]
    prompt = BATCH_PROMPT_TEMPLATE.format(
        n=len(batch),
        category={"restaurants": "餐厅", "hotels": "酒店", "spots": "景点"}[category],
        city=city,
        candidates_json=json.dumps(candidates, ensure_ascii=False, indent=2),
    )

    if dry_run:
        print(f"    [dry-run] Would call Sonnet for {len(batch)} items in {city}")
        # 返回占位数据
        return [{
            "name_ja": e["name_ja"],
            "quality_evidence": f"[dry-run] {e.get('score_basis', '')} score {e['base_quality_score']}",
            "traveler_fit_modifier": 0.0,
            "traveler_fit_evidence": "[dry-run]",
            "execution_penalty": 0.0,
            "execution_evidence": "[dry-run]",
            "risk_watch": "none",
            "risk_detail": None,
            "editorial_exclusion": False,
            "editorial_exclusion_reason": None,
            "one_line_editorial_note": "[dry-run] placeholder",
            "grade_suggestion": "B",
            "selection_tags": [],
        } for e in batch]

    try:
        text = call_sonnet(prompt, SYSTEM_PROMPT)
        results = parse_response(text)
        if len(results) != len(batch):
            print(f"    [warn] Expected {len(batch)} results, got {len(results)}", file=sys.stderr)
        return results
    except Exception as e:
        print(f"    [error] Batch failed: {e}", file=sys.stderr)
        return []


def merge_evidence(entry: dict, evidence: dict) -> dict:
    """将 Sonnet 返回的证据合并回 entry"""
    if not evidence:
        return entry
    fields = [
        "quality_evidence", "traveler_fit_modifier", "traveler_fit_evidence",
        "execution_penalty", "execution_evidence", "risk_watch", "risk_detail",
        "editorial_exclusion", "editorial_exclusion_reason", "one_line_editorial_note",
        "grade_suggestion", "selection_tags",
    ]
    for f in fields:
        if f in evidence:
            entry[f] = evidence[f]

    # 重算 house_score（含 traveler_fit + execution）
    tf = entry.get("traveler_fit_modifier") or 0.0
    rp = entry.get("execution_penalty") or 0.0
    entry["house_score"] = round(
        entry["base_quality_score"] + tf + entry["indie_support_score"] + rp, 3
    )
    return entry


def run(category: str, batch_size: int, dry_run: bool):
    in_path = DATA_DIR / f"{category}_ledger_phase2a.json"
    out_path = DATA_DIR / f"{category}_ledger_phase2b.json"

    print(f"\n{'='*70}")
    print(f"Phase 2B: {category} evidence generation")
    print(f"{'='*70}")

    with open(in_path, encoding="utf-8") as f:
        entries = json.load(f)

    # 只处理 selected + borderline
    to_process = [e for e in entries if e["selection_status"] in ("selected", "borderline")]
    print(f"  Total entries: {len(entries)}")
    print(f"  To process (selected+borderline): {len(to_process)}")

    # 按 city_code 分组
    by_city = defaultdict(list)
    for e in to_process:
        by_city[e["city_code"]].append(e)

    # 构建 slot_map 供 peer 查找
    slot_map = defaultdict(list)
    for e in entries:
        slot_map[e["selection_slot"]].append(e)

    # 建索引以便回写
    entry_map = {e["name_ja"] + "|" + e["city_code"]: e for e in entries}

    processed = 0
    failed = 0

    for city, city_entries in sorted(by_city.items()):
        print(f"\n  [{city}] {len(city_entries)} entries")
        # 按 batch_size 分批
        for i in range(0, len(city_entries), batch_size):
            batch = city_entries[i: i + batch_size]
            print(f"    Batch {i//batch_size + 1}: {len(batch)} items...", end=" ", flush=True)

            results = process_batch(batch, category, city, slot_map, dry_run)

            if not results:
                failed += len(batch)
                print("[FAILED]")
                continue

            # 按 name_ja 匹配回写（顺序可能有偏差）
            result_map = {r["name_ja"]: r for r in results}
            for entry in batch:
                key = entry["name_ja"] + "|" + entry["city_code"]
                ev = result_map.get(entry["name_ja"])
                if ev:
                    merge_evidence(entry_map[key], ev)
                    processed += 1
                else:
                    failed += 1
                    print(f"\n    [warn] No result for: {entry['name_ja']}", file=sys.stderr)

            print(f"[ok] ({processed} done so far)")

            # 避免 API rate limit
            if not dry_run:
                time.sleep(1)

    print(f"\n  Processed: {processed}, Failed: {failed}")

    # 写输出
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"  [ok] {out_path}")

    # 统计 grade 分布
    from collections import Counter
    grade_dist = Counter(e.get("grade_suggestion") for e in entries if e.get("grade_suggestion"))
    if grade_dist:
        print("\n  Grade suggestion distribution:")
        for g in ["S", "A", "B", "C"]:
            print(f"    {grade_dist.get(g, 0):4d}  {g}")

    risk_dist = Counter(e.get("risk_watch") for e in entries if e.get("risk_watch"))
    if risk_dist:
        print("\n  Risk watch distribution:")
        for k, v in sorted(risk_dist.items(), key=lambda x: -x[1]):
            print(f"    {v:4d}  {k}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["restaurants", "hotels", "spots"], required=True)
    parser.add_argument("--batch-size", type=int, default=15)
    parser.add_argument("--dry-run", action="store_true", help="Simulate without calling API")
    args = parser.parse_args()

    run(args.type, args.batch_size, args.dry_run)
