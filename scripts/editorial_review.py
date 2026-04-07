"""
Editorial review for hotels and spots in phase2b ledger.
Generates: one_line_editorial_note, grade, selection_tags for selected/borderline entries.
"""

import json
import sys
import time

import anthropic

HOTEL_FILE = "data/kansai_spots/phase2_ledger/hotels_ledger_phase2b.json"
SPOT_FILE = "data/kansai_spots/phase2_ledger/spots_ledger_phase2b.json"

HOTEL_SYSTEM = """你是关西旅行选品专家，为中国20-40岁游客制作付费手账本（298/348元）。

对每个酒店候选条目，生成编辑判断：
- one_line_editorial_note：一句话说清"为什么选/不选"，要有具体依据（品牌背书、位置优势、温泉体验、性价比等）
- grade：S/A/B/C
  S=城市名片，该城市住宿首选（米其林3钥、顶级旅馆、不可替代的地标体验）
  A=值得专程选择（品质卓越或体验独特，高于同类平均）
  B=行程增色（适合特定场景或预算的好选择）
  C=顺路即可（普通商务酒店或无明显差异化的存在）
- selection_tags：从 [city_icon, traveler_hot, local_benchmark] 中选0-3个
  city_icon=城市代表性住宿地标
  traveler_hot=中国游客口碑热门
  local_benchmark=业内标杆品质

评分参考：
- michelin_keys: 3→S，2→S或A，1→A或B
- ryokan + 温泉地区 → 重点强调温泉体验
- business_hotel → 主要B/C
- 位置极佳（景区核心/交通枢纽）可加分一档

输出 JSON 数组，每个元素格式：
{"name_ja": "...", "grade": "A", "one_line_editorial_note": "...", "selection_tags": ["city_icon"]}

只输出 JSON，不要解释。"""

SPOT_SYSTEM = """你是关西旅行选品专家，为中国20-40岁游客制作付费手账本（298/348元）。

对每个景点候选条目，生成编辑判断：
- one_line_editorial_note：一句话说清"为什么选/不选"，要有具体依据（历史意义、视觉震撼、体验深度、适合人群等）
- grade：S/A/B/C
  S=城市名片，该城市景点首选（UNESCO/国宝级/不可替代的标志性体验）
  A=值得专程（深度体验或独特魅力，超越普通打卡）
  B=行程增色（有主题或特色，适合有余裕的行程）
  C=顺路即可（普通或可替代的景点）
- selection_tags：从 [city_icon, traveler_hot, local_benchmark] 中选0-3个
  city_icon=城市代表性地标
  traveler_hot=中国游客口碑热门
  local_benchmark=专业认可的标杆景点

评分参考：
- japan_guide top → S或A
- japan_guide recommended → A或B
- japan_guide featured → B或C
- 京都/奈良的 history_religion 类 top 级 → 强调文化深度
- animal_science/art_museum类 → 考虑受众匹配度

输出 JSON 数组，每个元素格式：
{"name_ja": "...", "grade": "A", "one_line_editorial_note": "...", "selection_tags": ["city_icon"]}

只输出 JSON，不要解释。"""


def build_hotel_prompt(batch):
    items = []
    for h in batch:
        item = {
            "name_ja": h.get("name_ja", ""),
            "city_code": h.get("city_code", ""),
            "area": h.get("area", ""),
            "hotel_type": h.get("hotel_type", ""),
            "price_level": h.get("price_level", ""),
            "michelin_keys": h.get("michelin_keys"),
            "ota_rating": h.get("ota_rating"),
            "nightly_jpy_min": h.get("nightly_jpy_min"),
            "key_features": h.get("key_features", ""),
            "quality_evidence": h.get("quality_evidence", ""),
            "selection_status": h.get("selection_status", ""),
        }
        items.append(item)
    return f"以下是待判断的酒店候选条目，请对每条生成编辑判断：\n{json.dumps(items, ensure_ascii=False, indent=2)}"


def build_spot_prompt(batch):
    items = []
    for s in batch:
        item = {
            "name_ja": s.get("name_ja", ""),
            "name_en": s.get("name_en", ""),
            "city_code": s.get("city_code", ""),
            "area": s.get("area", ""),
            "main_type": s.get("main_type", ""),
            "sub_type": s.get("sub_type", ""),
            "japan_guide_level": s.get("japan_guide_level"),
            "quality_evidence": s.get("quality_evidence", ""),
            "selection_status": s.get("selection_status", ""),
        }
        items.append(item)
    return f"以下是待判断的景点候选条目，请对每条生成编辑判断：\n{json.dumps(items, ensure_ascii=False, indent=2)}"


def call_api(client, system_prompt, user_prompt, batch_label):
    print(f"  Calling API for {batch_label}...", flush=True)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error for {batch_label}: {e}", flush=True)
        print(f"  Raw response (first 500 chars): {text[:500]}", flush=True)
        return []


def apply_hotel_results(hotels, results_by_name):
    updated = 0
    for h in hotels:
        if h["selection_status"] not in ("selected", "borderline"):
            continue
        name = h.get("name_ja", "")
        if name in results_by_name:
            r = results_by_name[name]
            h["grade"] = r.get("grade")
            h["one_line_editorial_note"] = r.get("one_line_editorial_note")
            h["selection_tags"] = r.get("selection_tags", [])
            h["opus_reviewed"] = True
            updated += 1
    return updated


def apply_spot_results(spots, results_by_name):
    updated = 0
    for s in spots:
        if s["selection_status"] not in ("selected", "borderline"):
            continue
        name = s.get("name_ja", "")
        if name in results_by_name:
            r = results_by_name[name]
            s["grade"] = r.get("grade")
            s["one_line_editorial_note"] = r.get("one_line_editorial_note")
            s["selection_tags"] = r.get("selection_tags", [])
            s["opus_reviewed"] = True
            updated += 1
    return updated


def process_hotels(client):
    with open(HOTEL_FILE, encoding="utf-8") as f:
        hotels = json.load(f)

    target = [h for h in hotels if h["selection_status"] in ("selected", "borderline")]
    print(f"Hotels to process: {len(target)}", flush=True)

    all_results = {}
    batch_size = 20
    for i in range(0, len(target), batch_size):
        batch = target[i : i + batch_size]
        label = f"hotels batch {i//batch_size + 1} ({i+1}-{min(i+batch_size, len(target))})"
        prompt = build_hotel_prompt(batch)
        results = call_api(client, HOTEL_SYSTEM, prompt, label)
        for r in results:
            if r.get("name_ja"):
                all_results[r["name_ja"]] = r
        print(f"  Got {len(results)} results", flush=True)
        if i + batch_size < len(target):
            time.sleep(1)

    total_updated = apply_hotel_results(hotels, all_results)
    print(f"Hotels updated: {total_updated}/{len(target)}", flush=True)

    with open(HOTEL_FILE, "w", encoding="utf-8") as f:
        json.dump(hotels, f, ensure_ascii=False, indent=2)
    print(f"Saved {HOTEL_FILE}", flush=True)


def process_spots(client):
    with open(SPOT_FILE, encoding="utf-8") as f:
        spots = json.load(f)

    target = [s for s in spots if s["selection_status"] in ("selected", "borderline")]
    print(f"Spots to process: {len(target)}", flush=True)

    all_results = {}
    batch_size = 20
    for i in range(0, len(target), batch_size):
        batch = target[i : i + batch_size]
        label = f"spots batch {i//batch_size + 1} ({i+1}-{min(i+batch_size, len(target))})"
        prompt = build_spot_prompt(batch)
        results = call_api(client, SPOT_SYSTEM, prompt, label)
        for r in results:
            if r.get("name_ja"):
                all_results[r["name_ja"]] = r
        print(f"  Got {len(results)} results", flush=True)
        if i + batch_size < len(target):
            time.sleep(1)

    total_updated = apply_spot_results(spots, all_results)
    print(f"Spots updated: {total_updated}/{len(target)}", flush=True)

    with open(SPOT_FILE, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)
    print(f"Saved {SPOT_FILE}", flush=True)


def main():
    client = anthropic.Anthropic()

    print("=== Processing Hotels ===", flush=True)
    process_hotels(client)

    print("\n=== Processing Spots ===", flush=True)
    process_spots(client)

    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
