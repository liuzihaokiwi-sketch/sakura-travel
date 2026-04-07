"""
normalize_fields.py — Kansai restaurant/hotel data normalization

Tasks:
  N2: area -> corridor mapping for restaurants
  N3: budget_tier refinement — add "premium" tier
  N4: Hotel price_level correction — back-fill from source files
  N5: Hotel hotel_type completion

Output:
  data/kansai_spots/restaurants_normalized.csv  (overwrite)
  data/kansai_spots/hotels_normalized.csv       (new)
  data/kansai_spots/area_corridor_mapping.json  (new)
"""

import sys
import csv
import json
import re
import os
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "kansai_spots")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_csv(path):
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            # Skip comment rows (name_ja starts with #) and rows with all-None values
            if row is None:
                continue
            name = row.get("name_ja") or ""
            if name.startswith("#"):
                continue
            rows.append(row)
        return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_distribution(label, values):
    dist = defaultdict(int)
    for v in values:
        dist[v or "(empty)"] += 1
    print(f"  {label}:")
    for k, n in sorted(dist.items(), key=lambda x: -x[1]):
        print(f"    {k}: {n}")


# ---------------------------------------------------------------------------
# N2: area -> corridor mapping
# ---------------------------------------------------------------------------

# Hand-built mapping: (area_keyword_lowercase -> (city_code, corridor))
# Order matters — more specific keywords first.
_AREA_KEYWORD_MAP = [
    # ---- Kyoto ----
    # higashiyama
    ("higashiyama", "kyoto", "higashiyama"),
    ("東山", "kyoto", "higashiyama"),
    ("清水", "kyoto", "higashiyama"),
    ("kiyomizu", "kyoto", "higashiyama"),
    ("tofukuji", "kyoto", "higashiyama"),
    ("東福寺", "kyoto", "higashiyama"),
    # gion
    ("gion", "kyoto", "gion"),
    ("祇園", "kyoto", "gion"),
    ("先斗町", "kyoto", "gion"),
    ("花見小路", "kyoto", "gion"),
    ("木屋町", "kyoto", "gion"),
    ("河原町", "kyoto", "gion"),
    ("kawaramachi", "kyoto", "gion"),
    ("三条京阪", "kyoto", "gion"),
    ("sanjo", "kyoto", "gion"),
    ("三条", "kyoto", "gion"),
    ("四条", "kyoto", "gion"),
    ("shijo", "kyoto", "gion"),
    ("祇園四条", "kyoto", "gion"),
    # nishiki
    ("錦", "kyoto", "nishiki"),
    ("nishiki", "kyoto", "nishiki"),
    ("烏丸", "kyoto", "nishiki"),
    ("karasuma", "kyoto", "nishiki"),
    ("寺町", "kyoto", "nishiki"),
    ("麸屋町", "kyoto", "nishiki"),
    ("錦市場", "kyoto", "nishiki"),
    # arashiyama
    ("arashiyama", "kyoto", "arashiyama"),
    ("嵐山", "kyoto", "arashiyama"),
    ("嵯峨", "kyoto", "arashiyama"),
    ("sagano", "kyoto", "arashiyama"),
    ("桂", "kyoto", "arashiyama"),
    ("katsura", "kyoto", "arashiyama"),
    ("西京極", "kyoto", "arashiyama"),
    # fushimi
    ("fushimi", "kyoto", "fushimi"),
    ("伏見", "kyoto", "fushimi"),
    ("稲荷", "kyoto", "fushimi"),
    ("inari", "kyoto", "fushimi"),
    ("藤森", "kyoto", "fushimi"),
    # kinkakuji_area
    ("kinkakuji", "kyoto", "kinkakuji_area"),
    ("金閣寺", "kyoto", "kinkakuji_area"),
    ("北野", "kyoto", "kinkakuji_area"),
    ("kitano", "kyoto", "kinkakuji_area"),
    ("西陣", "kyoto", "kinkakuji_area"),
    ("nishijin", "kyoto", "kinkakuji_area"),
    ("北区", "kyoto", "kinkakuji_area"),
    ("鞍馬口", "kyoto", "kinkakuji_area"),
    ("今出川", "kyoto", "kinkakuji_area"),
    # philosopher_path
    ("philosopher", "kyoto", "philosopher_path"),
    ("哲学", "kyoto", "philosopher_path"),
    ("銀閣", "kyoto", "philosopher_path"),
    ("ginkaku", "kyoto", "philosopher_path"),
    ("南禅", "kyoto", "philosopher_path"),
    ("nanzen", "kyoto", "philosopher_path"),
    ("岡崎", "kyoto", "philosopher_path"),
    ("okazaki", "kyoto", "philosopher_path"),
    ("出町柳", "kyoto", "philosopher_path"),
    ("一乗寺", "kyoto", "philosopher_path"),
    ("左京", "kyoto", "philosopher_path"),
    ("下鴨", "kyoto", "philosopher_path"),
    ("shimogamo", "kyoto", "philosopher_path"),
    # kyoto_station
    ("kyoto station", "kyoto", "kyoto_station"),
    ("京都駅", "kyoto", "kyoto_station"),
    ("kyoto_station", "kyoto", "kyoto_station"),
    ("七条", "kyoto", "kyoto_station"),
    ("shichijo", "kyoto", "kyoto_station"),
    ("東寺", "kyoto", "kyoto_station"),
    ("toji", "kyoto", "kyoto_station"),
    ("丹波口", "kyoto", "kyoto_station"),
    ("下京", "kyoto", "kyoto_station"),
    ("梅小路", "kyoto", "kyoto_station"),
    # nijo
    ("nijo", "kyoto", "nijo"),
    ("二条", "kyoto", "nijo"),
    ("御所", "kyoto", "nijo"),
    ("御幸町", "kyoto", "nijo"),
    ("丸太町", "kyoto", "nijo"),
    ("marutamachi", "kyoto", "nijo"),
    ("御所西", "kyoto", "nijo"),
    ("上京", "kyoto", "nijo"),
    ("城市内", "kyoto", "nijo"),
    ("京都市役所", "kyoto", "nijo"),
    ("仏光寺", "kyoto", "nijo"),
    ("上本", "kyoto", "nijo"),
    # uji (city_code=uji)
    ("宇治", "uji", "uji"),
    ("uji", "uji", "uji"),
    # ---- Osaka ----
    # namba_shinsaibashi
    ("namba", "osaka", "namba_shinsaibashi"),
    ("難波", "osaka", "namba_shinsaibashi"),
    ("なんば", "osaka", "namba_shinsaibashi"),
    ("道頓堀", "osaka", "namba_shinsaibashi"),
    ("心斎橋", "osaka", "namba_shinsaibashi"),
    ("shinsaibashi", "osaka", "namba_shinsaibashi"),
    ("法善寺", "osaka", "namba_shinsaibashi"),
    ("千日前", "osaka", "namba_shinsaibashi"),
    ("黒門市場", "osaka", "namba_shinsaibashi"),
    ("アメリカ村", "osaka", "namba_shinsaibashi"),
    ("四ツ橋", "osaka", "namba_shinsaibashi"),
    ("yotsubashi", "osaka", "namba_shinsaibashi"),
    ("大国町", "osaka", "namba_shinsaibashi"),
    ("新世界", "osaka", "namba_shinsaibashi"),
    ("ジャンジャン横丁", "osaka", "namba_shinsaibashi"),
    ("日本橋", "osaka", "namba_shinsaibashi"),
    ("近鉄日本橋", "osaka", "namba_shinsaibashi"),
    ("恵美須", "osaka", "namba_shinsaibashi"),
    ("海老江", "osaka", "namba_shinsaibashi"),
    ("湊川", "osaka", "namba_shinsaibashi"),
    # umeda
    ("umeda", "osaka", "umeda"),
    ("梅田", "osaka", "umeda"),
    ("天神橋", "osaka", "umeda"),
    ("tenjinbashi", "osaka", "umeda"),
    ("北新地", "osaka", "umeda"),
    ("kitashinchi", "osaka", "umeda"),
    ("北浜", "osaka", "umeda"),
    ("kitahama", "osaka", "umeda"),
    ("肥後橋", "osaka", "umeda"),
    ("中之島", "osaka", "umeda"),
    ("なにわ橋", "osaka", "umeda"),
    ("大阪駅", "osaka", "umeda"),
    ("福島", "osaka", "umeda"),
    ("野田", "osaka", "umeda"),
    ("福島区", "osaka", "umeda"),
    ("中津", "osaka", "umeda"),
    ("nakazaki", "osaka", "umeda"),
    ("中崎", "osaka", "umeda"),
    # tennoji
    ("tennoji", "osaka", "tennoji"),
    ("天王寺", "osaka", "tennoji"),
    ("通天閣", "osaka", "tennoji"),
    ("tsutenkaku", "osaka", "tennoji"),
    ("新世界", "osaka", "tennoji"),
    ("四天王寺", "osaka", "tennoji"),
    ("上本町", "osaka", "tennoji"),
    ("玉造", "osaka", "tennoji"),
    # osaka_castle
    ("osaka_castle", "osaka", "osaka_castle"),
    ("大阪城", "osaka", "osaka_castle"),
    ("京橋", "osaka", "osaka_castle"),
    ("kyobashi", "osaka", "osaka_castle"),
    ("天満橋", "osaka", "osaka_castle"),
    ("sakuranomiya", "osaka", "osaka_castle"),
    ("桜ノ宮", "osaka", "osaka_castle"),
    # ---- Kobe ----
    # sannomiya
    ("sannomiya", "kobe", "sannomiya"),
    ("三宮", "kobe", "sannomiya"),
    ("三ノ宮", "kobe", "sannomiya"),
    ("元町", "kobe", "sannomiya"),
    ("motomachi", "kobe", "sannomiya"),
    ("北野", "kobe", "sannomiya"),
    ("異人館", "kobe", "sannomiya"),
    ("ijinkan", "kobe", "sannomiya"),
    ("神戸市", "kobe", "sannomiya"),
    ("shin-kobe", "kobe", "sannomiya"),
    ("新神戸", "kobe", "sannomiya"),
    ("芦屋", "kobe", "sannomiya"),
    ("ashiya", "kobe", "sannomiya"),
    ("夙川", "kobe", "sannomiya"),
    ("西宮", "kobe", "sannomiya"),
    ("打出", "kobe", "sannomiya"),
    ("摩耶", "kobe", "sannomiya"),
    # nankinmachi
    ("南京町", "kobe", "nankinmachi"),
    ("nankinmachi", "kobe", "nankinmachi"),
    # arima (city_code=arima)
    ("有馬", "arima", "arima"),
    ("arima", "arima", "arima"),
    # ---- Nara ----
    # nara_park
    ("nara_park", "nara", "nara_park"),
    ("奈良公園", "nara", "nara_park"),
    ("東大寺", "nara", "nara_park"),
    ("todaiji", "nara", "nara_park"),
    ("春日", "nara", "nara_park"),
    ("kasuga", "nara", "nara_park"),
    ("若草", "nara", "nara_park"),
    ("近鉄奈良", "nara", "nara_park"),
    ("奈良市", "nara", "nara_park"),
    ("nara city", "nara", "nara_park"),
    ("猿沢", "nara", "nara_park"),
    ("奈良ホテル", "nara", "nara_park"),
    ("三輪", "nara", "nara_park"),
    # naramachi
    ("ならまち", "nara", "naramachi"),
    ("naramachi", "nara", "naramachi"),
    ("奈良町", "nara", "naramachi"),
    ("もちいどの", "nara", "naramachi"),
]


def build_area_corridor_map():
    """Build and return the area->corridor mapping dict."""
    mapping = {}
    for keyword, city, corridor in _AREA_KEYWORD_MAP:
        if keyword not in mapping:
            mapping[keyword] = {"city_code": city, "corridor": corridor}
    return mapping


def match_area_to_corridor(area, city_code, mapping_keywords):
    """Match area string to corridor code. Returns (corridor, city_override) or (None, None)."""
    if not area:
        return None, None
    area_lower = area.lower()
    # Try each keyword in priority order
    for keyword, city, corridor in _AREA_KEYWORD_MAP:
        kw_lower = keyword.lower()
        if kw_lower in area_lower or area_lower in kw_lower:
            # City code should match or be compatible (uji/arima have own city_codes)
            if city in (city_code, "uji", "arima") or city == city_code:
                return corridor, city
            elif city_code in ("kyoto", "osaka", "kobe", "nara", "uji", "arima"):
                # Accept cross-city only for known override cities
                if city in ("uji", "arima"):
                    return corridor, city
    # Try again ignoring city_code constraint for remaining keywords
    for keyword, city, corridor in _AREA_KEYWORD_MAP:
        kw_lower = keyword.lower()
        if kw_lower in area_lower:
            return corridor, city
    return None, None


# ---------------------------------------------------------------------------
# N3: budget_tier refinement
# ---------------------------------------------------------------------------

_LUXURY_CUISINES = set()  # handled via michelin check
_PREMIUM_CUISINES = {"kaiseki", "teppanyaki", "wagyu", "fugu", "kani"}
_KEEP_LOW_CUISINES = {
    "ramen", "udon", "soba", "takoyaki", "okonomiyaki",
    "street_food", "bakery", "sweets", "wagashi", "matcha_sweets", "cafe",
}


def refine_budget_tier(row):
    """Return (new_budget_tier, tier_confidence)."""
    original_tier = row.get("budget_tier", "").strip()
    cuisine = (row.get("cuisine_normalized") or row.get("cuisine_type") or "").strip().lower()
    michelin = row.get("michelin", "").strip()

    # Already fixed tiers — keep as-is
    if original_tier in ("luxury", "budget", "street"):
        return original_tier, "original"

    # Michelin -> luxury
    if michelin:
        return "luxury", "michelin_inferred"

    # Cuisine-based premium inference (only if not already street/budget)
    if cuisine in _PREMIUM_CUISINES and original_tier not in ("budget", "street"):
        return "premium", "cuisine_inferred"

    # Keep low tiers for street-food-like cuisines
    if cuisine in _KEEP_LOW_CUISINES:
        return original_tier, "original"

    return original_tier, "original"


# ---------------------------------------------------------------------------
# N4: Hotel price_level back-fill
# ---------------------------------------------------------------------------

_PRICE_REGEX_STAR = re.compile(r"★(\d\.\d)\((\d+)件\)")
_PRICE_REGEX_NIGHT = re.compile(r"1泊(\d{3,6})円")
_PRICE_REGEX_NIGHT2 = re.compile(r"1泊(\d{1,3},\d{3})円")
_MICHELIN_KEYS_REGEX = re.compile(r"(\d)\s+Keys?", re.IGNORECASE)
_FORBES_REGEX = re.compile(r"Forbes\s+(\d)-star", re.IGNORECASE)


def parse_brief_note(note):
    """Extract OTA rating, review count, nightly_jpy_min from brief_note."""
    ota_rating = None
    ota_review_count = None
    nightly_jpy_min = None

    if not note:
        return ota_rating, ota_review_count, nightly_jpy_min

    m = _PRICE_REGEX_STAR.search(note)
    if m:
        ota_rating = m.group(1)
        ota_review_count = m.group(2)

    m2 = _PRICE_REGEX_NIGHT.search(note)
    if m2:
        nightly_jpy_min = int(m2.group(1))
    else:
        m3 = _PRICE_REGEX_NIGHT2.search(note)
        if m3:
            nightly_jpy_min = int(m3.group(1).replace(",", ""))

    return ota_rating, ota_review_count, nightly_jpy_min


def parse_ranking_info(info):
    """Extract michelin_keys and forbes_stars from ranking_info."""
    michelin_keys = None
    forbes_stars = None

    if not info:
        return michelin_keys, forbes_stars

    m = _MICHELIN_KEYS_REGEX.search(info)
    if m:
        michelin_keys = int(m.group(1))

    m2 = _FORBES_REGEX.search(info)
    if m2:
        forbes_stars = int(m2.group(1))

    return michelin_keys, forbes_stars


def jpy_to_price_level(jpy):
    if jpy is None:
        return None
    if jpy >= 30000:
        return "luxury"
    if jpy >= 15000:
        return "expensive"
    if jpy >= 8000:
        return "moderate"
    return "budget"


# ---------------------------------------------------------------------------
# N5: Hotel type inference
# ---------------------------------------------------------------------------

def infer_hotel_type(name_ja):
    """Infer hotel_type from name_ja string."""
    if not name_ja:
        return "city_hotel"

    if "ゲストハウス" in name_ja:
        return "guesthouse"
    if "ホステル" in name_ja:
        return "hostel"
    if "宿坊" in name_ja:
        return "shukubo"
    if "旅館" in name_ja or "荘" in name_ja or "閣" in name_ja or "亭" in name_ja:
        return "ryokan"
    if "ペンション" in name_ja or "宿" in name_ja:
        return "guesthouse"
    if "リゾート" in name_ja:
        return "resort"
    if "ホテル" in name_ja:
        # Check for business hotel keywords
        business_keywords = ["ビジネス", "APA", "Route", "Dormy", "Super", "東横", "トーヨー"]
        for kw in business_keywords:
            if kw in name_ja:
                return "business_hotel"
        return "city_hotel"
    return "city_hotel"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_n2_n3():
    """Process restaurants: corridor mapping + budget_tier refinement."""
    print("[N2+N3] Processing restaurants...")
    path = os.path.join(DATA, "restaurants_normalized.csv")
    rows = read_csv(path)
    print(f"  Loaded {len(rows)} rows")

    corridor_changed = 0
    tier_changed = 0
    tier_confidence_dist = defaultdict(int)
    corridor_dist = defaultdict(int)

    for row in rows:
        # N2: corridor
        corridor, city_override = match_area_to_corridor(
            row.get("area", ""), row.get("city_code", ""), _AREA_KEYWORD_MAP
        )
        row["corridor"] = corridor or ""
        if corridor:
            corridor_changed += 1
        corridor_dist[corridor or "(null)"] += 1

        # N3: budget_tier
        new_tier, confidence = refine_budget_tier(row)
        if new_tier != row.get("budget_tier", ""):
            tier_changed += 1
        row["budget_tier"] = new_tier
        row["tier_confidence"] = confidence
        tier_confidence_dist[confidence] += 1

    print(f"  N2: {corridor_changed}/{len(rows)} rows got a corridor")
    print_distribution("corridor distribution", [r["corridor"] for r in rows])
    print(f"  N3: {tier_changed} rows had budget_tier changed")
    print_distribution("budget_tier distribution", [r["budget_tier"] for r in rows])
    print_distribution("tier_confidence distribution", [r["tier_confidence"] for r in rows])

    # Write output
    fieldnames = list(rows[0].keys())
    for col in ("corridor", "tier_confidence"):
        if col not in fieldnames:
            fieldnames.append(col)
    write_csv(path, rows, fieldnames)
    print(f"  [ok] Wrote {path}")
    return rows


def run_n4_n5():
    """Process hotels: price_level back-fill + hotel_type completion."""
    print("[N4+N5] Processing hotels...")

    # Load base file
    base_path = os.path.join(DATA, "hotels_merged_final.csv")
    rows = read_csv(base_path)
    print(f"  Loaded {len(rows)} rows from hotels_merged_final.csv")

    # Initialize new columns
    for row in rows:
        row["ota_rating"] = ""
        row["ota_review_count"] = ""
        row["nightly_jpy_min"] = ""
        row["michelin_keys"] = ""
        row["forbes_stars"] = ""
        row["hotel_type_confidence"] = "original"

    # Build name_ja index
    name_index = {row["name_ja"]: row for row in rows}

    # N4a: Parse mid_budget and midrange_budget
    mid_paths = [
        os.path.join(DATA, "hotels_mid_budget_candidates.csv"),
        os.path.join(DATA, "hotels_midrange_budget_candidates.csv"),
    ]
    matched_price = 0
    for path in mid_paths:
        src_rows = read_csv(path)
        for src in src_rows:
            name = src.get("name_ja", "").strip()
            note = src.get("brief_note", "").strip()
            if not name or not note:
                continue
            if name in name_index:
                ota_r, ota_c, nightly = parse_brief_note(note)
                target = name_index[name]
                if ota_r and not target["ota_rating"]:
                    target["ota_rating"] = ota_r
                    target["ota_review_count"] = ota_c or ""
                if nightly and not target["nightly_jpy_min"]:
                    target["nightly_jpy_min"] = str(nightly)
                    matched_price += 1
    print(f"  N4a: {matched_price} hotels got nightly_jpy_min from mid/midrange files")

    # N4b: Parse candidate_pool
    pool_path = os.path.join(DATA, "hotels_candidate_pool.csv")
    pool_rows = read_csv(pool_path)
    matched_ranking = 0
    for src in pool_rows:
        name = src.get("name_ja", "").strip()
        info = src.get("ranking_info", "").strip()
        if not name:
            continue
        if name in name_index:
            keys, stars = parse_ranking_info(info)
            target = name_index[name]
            if keys is not None and not target["michelin_keys"]:
                target["michelin_keys"] = str(keys)
                matched_ranking += 1
            if stars is not None and not target["forbes_stars"]:
                target["forbes_stars"] = str(stars)
    print(f"  N4b: {matched_ranking} hotels got michelin_keys from candidate_pool")

    # N4c: Update price_level based on nightly_jpy_min
    price_updated = 0
    for row in rows:
        jpy_str = row.get("nightly_jpy_min", "").strip()
        if jpy_str:
            try:
                jpy = int(jpy_str)
                new_level = jpy_to_price_level(jpy)
                if new_level and new_level != row.get("price_level", ""):
                    row["price_level"] = new_level
                    price_updated += 1
            except ValueError:
                pass
    print(f"  N4c: {price_updated} hotels had price_level updated from nightly price")
    print_distribution("price_level distribution", [r["price_level"] for r in rows])

    # N5: hotel_type completion
    type_inferred = 0
    for row in rows:
        if not row.get("hotel_type", "").strip():
            row["hotel_type"] = infer_hotel_type(row.get("name_ja", ""))
            row["hotel_type_confidence"] = "inferred"
            type_inferred += 1
    print(f"  N5: {type_inferred} hotels had hotel_type inferred")
    print_distribution("hotel_type distribution", [r["hotel_type"] for r in rows])
    print_distribution("hotel_type_confidence", [r["hotel_type_confidence"] for r in rows])

    # Write output
    out_path = os.path.join(DATA, "hotels_normalized.csv")
    fieldnames = list(rows[0].keys())
    for col in ("ota_rating", "ota_review_count", "nightly_jpy_min",
                "michelin_keys", "forbes_stars", "hotel_type_confidence"):
        if col not in fieldnames:
            fieldnames.append(col)
    write_csv(out_path, rows, fieldnames)
    print(f"  [ok] Wrote {out_path}")
    return rows


def run_save_mapping():
    """Save area->corridor mapping JSON for reuse."""
    mapping = {}
    for keyword, city, corridor in _AREA_KEYWORD_MAP:
        mapping[keyword] = {"city_code": city, "corridor": corridor}

    out_path = os.path.join(DATA, "area_corridor_mapping.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"  [ok] Wrote {out_path} ({len(mapping)} keywords)")


if __name__ == "__main__":
    print("=== normalize_fields.py ===")
    run_n2_n3()
    print()
    run_n4_n5()
    print()
    run_save_mapping()
    print()
    print("[ok] All done.")
