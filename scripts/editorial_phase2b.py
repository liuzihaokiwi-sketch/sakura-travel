"""
Editorial judgment for restaurants_ledger_phase2b.json.
Processes selected/borderline items in batches of 20 (sorted by city_code),
calls claude-opus-4-6 to fill: one_line_editorial_note, grade, selection_tags.
"""

import json
import time
import anthropic

LEDGER_PATH = "data/kansai_spots/phase2_ledger/restaurants_ledger_phase2b.json"
BATCH_SIZE = 20

SYSTEM_PROMPT = """你是关西旅行选品专家，为中国20-40岁游客制作付费手账本（298/348元）。

评级标准：
- S = 城市名片（城市最高水准，值得专程来吃）
- A = 值得专程（同类型首选）
- B = 行程增色（顺路好选择）
- C = 顺路即可（不值得专程但可以去）

打分参考：
- base_quality_score >= 4.5 → 倾向 S/A
- base_quality_score 3.8–4.4 → 倾向 A/B
- base_quality_score < 3.8 → 倾向 B/C
- 有 michelin 加一档
- 知名菜系（怀石/寿司/天妇罗）在主要城市 → 倾向更高档
- street_food / cafe / bakery → B/C 为主
- akashiyaki 在明石市 → 城市名片，考虑 A/S
- borderline 条目打分不低于 C

selection_tags 可选值（可多选或空列表）：
- city_icon：城市象征性地标级别
- traveler_hot：中国游客高度关注
- local_benchmark：本地人认可的标杆

输出格式：严格 JSON 数组，每项对应输入的一条记录，顺序一致。
[
  {
    "name_ja": "原样复制",
    "grade": "S|A|B|C",
    "selection_tags": [],
    "one_line_editorial_note": "一句话，说清为什么选/不选，有具体依据"
  },
  ...
]

注意：
- one_line_editorial_note 要有判断依据，不要空泛（如"性价比高"没有依据）
- 说清楚"为什么选这家而不是别家"
- 中文输出
"""


def build_batch_prompt(items: list[dict]) -> str:
    records = []
    for item in items:
        records.append({
            "name_ja": item.get("name_ja", ""),
            "city_code": item.get("city_code", ""),
            "area": item.get("area", ""),
            "corridor": item.get("corridor", ""),
            "cuisine_normalized": item.get("cuisine_normalized", ""),
            "budget_tier": item.get("budget_tier", ""),
            "tabelog_score": item.get("tabelog_score"),
            "michelin": item.get("michelin"),
            "base_quality_score": item.get("base_quality_score"),
            "score_basis": item.get("score_basis", ""),
            "house_score": item.get("house_score"),
            "selection_status": item.get("selection_status", ""),
            "quality_evidence": item.get("quality_evidence", ""),
            "data_confidence": item.get("data_confidence", ""),
        })
    return (
        "请对以下餐厅条目逐一给出编辑判断。输出严格 JSON 数组，顺序与输入一致。\n\n"
        + json.dumps(records, ensure_ascii=False, indent=2)
    )


def parse_response(text: str) -> list[dict]:
    """Extract JSON array from response text."""
    text = text.strip()
    # Find the first [ and last ]
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in response: {text[:200]}")
    return json.loads(text[start : end + 1])


def main():
    client = anthropic.Anthropic()

    with open(LEDGER_PATH, encoding="utf-8") as f:
        data = json.load(f)

    # Collect indices and items to process
    to_process = [
        (i, item)
        for i, item in enumerate(data)
        if item.get("selection_status") in ("selected", "borderline")
    ]

    # Sort by city_code for stable batching
    to_process.sort(key=lambda x: x[1].get("city_code", ""))

    print(f"Total to process: {len(to_process)}")

    total_batches = (len(to_process) + BATCH_SIZE - 1) // BATCH_SIZE
    processed = 0
    errors = 0

    for batch_num in range(total_batches):
        batch = to_process[batch_num * BATCH_SIZE : (batch_num + 1) * BATCH_SIZE]
        indices = [idx for idx, _ in batch]
        items = [item for _, item in batch]

        cities = sorted(set(item.get("city_code", "") for item in items))
        print(
            f"\nBatch {batch_num + 1}/{total_batches} — "
            f"{len(items)} items — cities: {cities}"
        )

        prompt = build_batch_prompt(items)

        try:
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=8000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                response = stream.get_final_message()

            text_blocks = [b.text for b in response.content if b.type == "text"]
            full_text = "\n".join(text_blocks)

            results = parse_response(full_text)

            if len(results) != len(items):
                print(
                    f"  WARNING: expected {len(items)} results, got {len(results)}"
                )
                # Try to match by name_ja
                result_map = {r.get("name_ja", ""): r for r in results}
                for orig_idx, item in zip(indices, items):
                    r = result_map.get(item.get("name_ja", ""))
                    if r:
                        data[orig_idx]["grade"] = r.get("grade")
                        data[orig_idx]["one_line_editorial_note"] = r.get(
                            "one_line_editorial_note"
                        )
                        data[orig_idx]["selection_tags"] = r.get("selection_tags", [])
                        data[orig_idx]["opus_reviewed"] = True
                        processed += 1
                    else:
                        print(f"  MISSING result for: {item.get('name_ja')}")
                        errors += 1
            else:
                for orig_idx, item, r in zip(indices, items, results):
                    data[orig_idx]["grade"] = r.get("grade")
                    data[orig_idx]["one_line_editorial_note"] = r.get(
                        "one_line_editorial_note"
                    )
                    data[orig_idx]["selection_tags"] = r.get("selection_tags", [])
                    data[orig_idx]["opus_reviewed"] = True
                    processed += 1

            # Show sample output
            for r in results[:2]:
                print(
                    f"  {r.get('name_ja', '')} → {r.get('grade')} | "
                    f"{r.get('selection_tags')} | {r.get('one_line_editorial_note', '')[:60]}"
                )

            # Save incrementally after each batch
            with open(LEDGER_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            tokens_used = response.usage.output_tokens
            print(f"  OK — output_tokens={tokens_used}, processed so far: {processed}")

        except Exception as e:
            print(f"  ERROR in batch {batch_num + 1}: {e}")
            errors += 1
            # Brief pause before continuing
            time.sleep(3)
            continue

        # Brief pause between batches to stay within rate limits
        if batch_num < total_batches - 1:
            time.sleep(1)

    print(f"\nDone. processed={processed}, errors={errors}, total={len(to_process)}")


if __name__ == "__main__":
    main()
