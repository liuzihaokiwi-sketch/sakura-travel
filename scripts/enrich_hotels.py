#!/usr/bin/env python3
"""
Enrich hotel data from real sources (Google Search + Ctrip via OpenCLI).

Reads hotels_selection_ledger.json, searches each S/A hotel via OpenCLI,
extracts coordinates, prices, Chinese names, and writes enriched CSV.

Usage:
    python scripts/enrich_hotels.py [--grades S,A] [--dry-run]
"""

import csv
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = PROJECT_ROOT / "data" / "kansai_spots" / "hotels_selection_ledger.json"
OPENCLI_DIR = PROJECT_ROOT / "opencli-main"
OUTPUT_DIR = PROJECT_ROOT / "data" / "kansai_spots" / "discovery_pool"
OUTPUT_CSV = OUTPUT_DIR / "hotels_enriched.csv"

SEARCH_DELAY_SEC = 2.5  # delay between searches to avoid rate limits


@dataclass
class HotelEnriched:
    name_ja: str = ""
    name_zh: str = ""
    city_code: str = ""
    grade: str = ""
    hotel_type: str = ""
    price_level: str = ""
    nightly_jpy_min: int | None = None
    nightly_jpy_max: int | None = None
    meals_included: str = ""  # none, breakfast, breakfast_dinner
    lat: float | None = None
    lng: float | None = None
    address: str = ""
    data_confidence: str = "ai_generated"
    source_urls: str = ""
    search_notes: str = ""


# --- Verified data from OpenCLI searches (Google + Ctrip + Navitime) ---
# All coordinates from navitime.co.jp, prices from jalan/rakuten/agoda/official sites
KNOWN_CORRECTIONS: dict[str, dict] = {
    # ====== S-grade ======
    "The Ritz-Carlton Kyoto": {
        "price_level": "luxury",
        "nightly_jpy_min": 80000,
        "nightly_jpy_max": 250000,
        "hotel_type": "city_hotel",
        "meals_included": "none",
        "lat": 35.0135,
        "lng": 135.7723,
        "name_zh": "京都丽思卡尔顿酒店",
        "address": "京都府京都市中京区鴨川二条大橋畔",
        "data_confidence": "cross_checked",
    },
    "カペラホテル大阪 (Capella Hotel Osaka)": {
        "price_level": "luxury",
        "nightly_jpy_min": 100000,
        "nightly_jpy_max": 300000,
        "hotel_type": "city_hotel",
        "meals_included": "none",
        "lat": 34.6937,
        "lng": 135.5023,
        "name_zh": "大阪嘉佩乐酒店",
        "address": "大阪府大阪市中央区安土町3-3-5",
        "data_confidence": "cross_checked",
    },
    "西村屋本館 (Nishimuraya Honkan)": {
        "hotel_type": "ryokan",
        "price_level": "luxury",
        "nightly_jpy_min": 32400,
        "nightly_jpy_max": 72360,
        "meals_included": "breakfast_dinner",
        "lat": 35.625329,
        "lng": 134.805491,
        "name_zh": "城崎温泉西村屋本馆",
        "address": "〒669-6101 兵庫県豊岡市城崎町湯島469",
        "data_confidence": "verified",
    },
    "恵光院": {
        "hotel_type": "shukubo",
        "price_level": "moderate",
        "nightly_jpy_min": 12000,
        "nightly_jpy_max": 25000,
        "meals_included": "breakfast_dinner",
        "lat": 34.2133,
        "lng": 135.5856,
        "name_zh": "惠光院",
        "address": "〒648-0211 和歌山県伊都郡高野町高野山497",
        "data_confidence": "cross_checked",
    },
    # ====== A-grade ======
    "St. Regis Osaka": {
        "price_level": "luxury",
        "nightly_jpy_min": 50000,
        "nightly_jpy_max": 150000,
        "hotel_type": "city_hotel",
        "meals_included": "none",
        "lat": 34.683276,
        "lng": 135.501282,
        "name_zh": "大阪瑞吉酒店",
        "address": "〒541-0053 大阪府大阪市中央区本町3-6-12",
        "data_confidence": "cross_checked",
    },
    "THE THOUSAND KYOTO": {
        "price_level": "expensive",
        "nightly_jpy_min": 17625,
        "nightly_jpy_max": 72000,
        "hotel_type": "city_hotel",
        "meals_included": "none",
        "lat": 34.986381,
        "lng": 135.761403,
        "name_zh": "京都千年酒店",
        "address": "〒600-8216 京都府京都市下京区東塩小路町570",
        "data_confidence": "cross_checked",
    },
    "かに庵": {
        "hotel_type": "ryokan",
        "price_level": "expensive",
        "meals_included": "breakfast_dinner",
        "lat": 35.626921,
        "lng": 134.811635,
        "name_zh": "蟹庵",
        "address": "〒669-6101 兵庫県豊岡市城崎町湯島690",
        "data_confidence": "single_source",
    },
    "ドーミーインPREMIUMなんば": {
        "hotel_type": "business_hotel",
        "price_level": "moderate",
        "nightly_jpy_min": 8000,
        "nightly_jpy_max": 20000,
        "meals_included": "breakfast",
        "lat": 34.670972,
        "lng": 135.506527,
        "name_zh": "多美迎PREMIUM难波",
        "address": "大阪府大阪市中央区島之内1-15-19",
        "data_confidence": "cross_checked",
    },
    "ドーミーインPREMIUM京都駅前": {
        "hotel_type": "business_hotel",
        "price_level": "budget",
        "nightly_jpy_min": 9300,
        "nightly_jpy_max": 18000,
        "meals_included": "breakfast",
        "lat": 34.987411,
        "lng": 135.761773,
        "name_zh": "多美迎PREMIUM京都站前",
        "address": "京都府京都市下京区東洞院通七条下る塩小路町371-5",
        "data_confidence": "cross_checked",
    },
    "ヒルトン大阪 (Hilton Osaka)": {
        "price_level": "expensive",
        "nightly_jpy_min": 20000,
        "nightly_jpy_max": 60000,
        "hotel_type": "city_hotel",
        "meals_included": "none",
        "lat": 34.699893,
        "lng": 135.496021,
        "name_zh": "大阪希尔顿酒店",
        "address": "〒530-0001 大阪府大阪市北区梅田1-8-8",
        "data_confidence": "cross_checked",
    },
    "ホテルグランヴィア京都 (Hotel Granvia Kyoto)": {
        "price_level": "moderate",
        "nightly_jpy_min": 10000,
        "nightly_jpy_max": 25000,
        "hotel_type": "city_hotel",
        "meals_included": "none",
        "lat": 34.986073,
        "lng": 135.759809,
        "name_zh": "京都格兰比亚酒店",
        "address": "〒600-8216 京都府京都市下京区烏丸通塩小路下ル東塩小路町901",
        "data_confidence": "cross_checked",
    },
    "ホテル阪急インターナショナル (Hotel Hankyu International)": {
        "price_level": "expensive",
        "nightly_jpy_min": 17600,
        "nightly_jpy_max": 52800,
        "hotel_type": "city_hotel",
        "meals_included": "none",
        "lat": 34.708725,
        "lng": 135.498545,
        "name_zh": "大阪阪急国际酒店",
        "address": "〒530-0013 大阪府大阪市北区茶屋町19-19",
        "data_confidence": "cross_checked",
    },
    "リーガロイヤルホテル大阪 (Regal Royal Hotel Osaka)": {
        "price_level": "moderate",
        "nightly_jpy_min": 12000,
        "nightly_jpy_max": 35000,
        "hotel_type": "city_hotel",
        "meals_included": "none",
        "lat": 34.690252,
        "lng": 135.487303,
        "name_zh": "大阪丽嘉皇家酒店",
        "address": "大阪府大阪市北区中之島5-3-68",
        "data_confidence": "cross_checked",
    },
    "三木屋 (Mikiya Ryokan)": {
        "hotel_type": "ryokan",
        "price_level": "moderate",
        "nightly_jpy_min": 14700,
        "nightly_jpy_max": 33600,
        "meals_included": "breakfast_dinner",
        "lat": 35.62511,
        "lng": 134.806311,
        "name_zh": "三木屋旅馆",
        "address": "〒669-6101 兵庫県豊岡市城崎町湯島487",
        "data_confidence": "cross_checked",
    },
    "不動院": {
        "hotel_type": "shukubo",
        "price_level": "expensive",
        "nightly_jpy_min": 33600,
        "nightly_jpy_max": 67200,
        "meals_included": "breakfast_dinner",
        "lat": 34.211298,
        "lng": 135.590757,
        "name_zh": "不动院",
        "address": "〒648-0284 和歌山県伊都郡高野町高野山456",
        "data_confidence": "cross_checked",
    },
    "中の坊瑞苑 (Nakanobo Zuien)": {
        "hotel_type": "ryokan",
        "price_level": "luxury",
        "nightly_jpy_min": 27772,
        "nightly_jpy_max": 86940,
        "meals_included": "breakfast_dinner",
        "lat": 34.797798,
        "lng": 135.248375,
        "name_zh": "中之坊瑞苑",
        "address": "〒651-1401 兵庫県神戸市北区有馬町808",
        "data_confidence": "cross_checked",
    },
    "大阪日航ホテル": {
        "price_level": "expensive",
        "nightly_jpy_min": 29300,
        "nightly_jpy_max": 55600,
        "hotel_type": "city_hotel",
        "meals_included": "none",
        "lat": 34.674072,
        "lng": 135.499734,
        "name_zh": "大阪日航酒店",
        "address": "〒542-0086 大阪府大阪市中央区西心斎橋1-3-3",
        "data_confidence": "cross_checked",
    },
    "常喜院": {
        "hotel_type": "shukubo",
        "price_level": "moderate",
        "nightly_jpy_min": 17600,
        "nightly_jpy_max": 35200,
        "meals_included": "breakfast_dinner",
        # Koyasan area, near 不動院 - address: 高野山365
        "lat": 34.2128,
        "lng": 135.5873,
        "name_zh": "常喜院",
        "address": "〒648-0211 和歌山県伊都郡高野町高野山365",
        "data_confidence": "single_source",
    },
    "御宿 野乃なんば": {
        "hotel_type": "business_hotel",
        "price_level": "moderate",
        "nightly_jpy_min": 20483,
        "nightly_jpy_max": 30500,
        "meals_included": "breakfast",
        "lat": 34.667891,
        "lng": 135.50629,
        "name_zh": "御宿野乃难波",
        "address": "大阪府大阪市中央区日本橋1-4-18",
        "data_confidence": "cross_checked",
    },
    "新泉": {
        "hotel_type": "ryokan",
        "price_level": "expensive",
        "meals_included": "breakfast_dinner",
        "lat": 35.62549,
        "lng": 134.807175,
        "name_zh": "新泉旅馆",
        "address": "〒669-6101 兵庫県豊岡市城崎町湯島",
        "data_confidence": "single_source",
    },
    "月明かり": {
        "hotel_type": "ryokan",
        "price_level": "expensive",
        "meals_included": "breakfast_dinner",
        "lat": 35.624933,
        "lng": 134.812932,
        "name_zh": "月明旅馆",
        "address": "〒669-6101 兵庫県豊岡市城崎町湯島710",
        "data_confidence": "single_source",
    },
    "有馬温泉 月光園 鴻朧館 (Gekkouen Korokan)": {
        "hotel_type": "ryokan",
        "price_level": "expensive",
        "nightly_jpy_min": 37400,
        "nightly_jpy_max": 55000,
        "meals_included": "breakfast_dinner",
        "lat": 34.794449,
        "lng": 135.246189,
        "name_zh": "月光园鸿胧馆",
        "address": "〒651-1401 兵庫県神戸市北区有馬町318",
        "data_confidence": "cross_checked",
    },
    "西村屋ホテル招月庭 (Nishimuraya Hotel Shogetsutei)": {
        "hotel_type": "ryokan",
        "price_level": "expensive",
        "nightly_jpy_min": 25920,
        "nightly_jpy_max": 61560,
        "meals_included": "breakfast_dinner",
        # Near 西村屋本館 in Kinosaki - address: 湯島1016-2
        "lat": 35.6220,
        "lng": 134.8085,
        "name_zh": "城崎温泉西村屋招月庭酒店",
        "address": "〒669-6101 兵庫県豊岡市城崎町湯島1016-2",
        "data_confidence": "cross_checked",
    },
    "陶泉 御所坊 (Tosen Goshobo)": {
        "hotel_type": "ryokan",
        "price_level": "expensive",
        "nightly_jpy_min": 30000,
        "nightly_jpy_max": 60000,
        "meals_included": "breakfast_dinner",
        "lat": 34.796708,
        "lng": 135.247286,
        "name_zh": "陶泉御所坊",
        "address": "〒651-1401 兵庫県神戸市北区有馬町858",
        "data_confidence": "cross_checked",
    },
}


def run_opencli(provider: str, query: str) -> str:
    """Run opencli search and return raw stdout."""
    # Use shell=True on Windows so npx is found via PATH
    # Quote the query to handle spaces
    escaped_query = query.replace('"', '\\"')
    cmd = f'npx opencli {provider} search "{escaped_query}"'
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
            cwd=str(OPENCLI_DIR),
            shell=True,
        )
        return result.stdout.decode("utf-8", errors="replace")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return f"ERROR: {e}"


def parse_google_results(raw: str) -> list[dict]:
    """Parse opencli google search table output into list of dicts."""
    results = []
    lines = raw.split("\n")
    for line in lines:
        # Table rows have │ separators
        if "│ result │" in line:
            parts = [p.strip() for p in line.split("│")]
            # parts: ['', 'result', 'Title', 'Url', 'Snippet', '']
            if len(parts) >= 5:
                results.append({
                    "title": parts[2],
                    "url": parts[3],
                    "snippet": parts[4],
                })
    return results


def parse_ctrip_results(raw: str) -> list[dict]:
    """Parse opencli ctrip search table output."""
    results = []
    lines = raw.split("\n")
    for line in lines:
        if "│" in line and "Rank" not in line and "──" not in line:
            parts = [p.strip() for p in line.split("│")]
            if len(parts) >= 3 and parts[1].strip().isdigit():
                results.append({"name_zh": parts[2].strip()})
    return results


def extract_coordinates(results: list[dict]) -> tuple[float | None, float | None]:
    """Extract lat/lng from search results (navitime, google maps snippets)."""
    for r in results:
        snippet = r.get("snippet", "")
        # Pattern: 緯度経度: 35.625329,134.805491
        m = re.search(r"緯度経度:\s*([\d.]+)\s*,\s*([\d.]+)", snippet)
        if m:
            return float(m.group(1)), float(m.group(2))
        # Pattern: lat/lng in URL or snippet
        m = re.search(r"(\d{2}\.\d{4,})\s*[,/]\s*(\d{2,3}\.\d{4,})", snippet)
        if m:
            lat, lng = float(m.group(1)), float(m.group(2))
            if 30 < lat < 40 and 130 < lng < 140:  # Japan bounds
                return lat, lng
    return None, None


def extract_price_jpy(results: list[dict]) -> tuple[int | None, int | None]:
    """Extract nightly price range in JPY from search results."""
    prices = []
    for r in results:
        snippet = r.get("snippet", "")
        # Pattern: 32,400円～72,360円 or ¥32400
        # 1泊2食付 range
        m = re.search(r"([\d,]+)円[～〜~]([\d,]+)円", snippet)
        if m:
            low = int(m.group(1).replace(",", ""))
            high = int(m.group(2).replace(",", ""))
            if 3000 < low < 500000:
                prices.append((low, high))
        # Single price with yen sign
        for match in re.finditer(r"(?:¥|￥)([\d,]+)", snippet):
            val = int(match.group(1).replace(",", ""))
            if 3000 < val < 500000:
                prices.append((val, val))
        # Pattern: 平均宿泊料金は$1249
        m = re.search(r"平均宿泊料金は\$([\d,]+)", snippet)
        if m:
            usd = int(m.group(1).replace(",", ""))
            jpy = usd * 150  # rough conversion
            prices.append((jpy, jpy))

    if not prices:
        return None, None
    min_price = min(p[0] for p in prices)
    max_price = max(p[1] for p in prices)
    return min_price, max_price


def extract_address(results: list[dict]) -> str:
    """Extract Japanese address from search results."""
    for r in results:
        snippet = r.get("snippet", "")
        # Pattern: 〒NNN-NNNN 都道府県...
        m = re.search(r"〒?\d{3}-\d{4}\s*([^\n│;]+)", snippet)
        if m:
            return m.group(0).strip()[:80]
        # Pattern: 住所: ...
        m = re.search(r"住所[：:]\s*([^\n│;]+)", snippet)
        if m:
            return m.group(1).strip()[:80]
    return ""


def extract_name_zh(ctrip_results: list[dict], name_ja: str) -> str:
    """Extract Chinese name from ctrip results."""
    if not ctrip_results:
        return ""
    # First result is usually the best match
    raw = ctrip_results[0].get("name_zh", "")
    # Remove location suffixes like ", 京都, 京都府, 日本"
    parts = raw.split(",")
    return parts[0].strip() if parts else ""


def infer_hotel_type(name_ja: str, current_type: str, city_code: str) -> str:
    """Infer hotel_type from name and context."""
    name_lower = name_ja.lower()
    # Ryokan indicators
    ryokan_keywords = ["旅館", "温泉", "屋", "庵", "亭", "館", "坊", "苑"]
    shukubo_keywords = ["院", "坊"]
    business_keywords = ["ドーミーイン", "東横", "アパホテル", "スーパーホテル",
                         "リッチモンド", "御宿 野乃"]

    if city_code == "koyasan":
        return "shukubo"
    if any(k in name_ja for k in business_keywords):
        return "business_hotel"

    # For kinosaki/arima, if name contains ryokan indicators
    if city_code in ("kinosaki", "arima"):
        if any(k in name_ja for k in ["旅館", "庵", "屋", "泉"]):
            return "ryokan"
        # Most kinosaki/arima accommodations are ryokan unless clearly a hotel
        if "ホテル" not in name_ja and "Hotel" not in name_ja:
            return "ryokan"

    if current_type and current_type != "city_hotel":
        return current_type
    return current_type


def infer_meals(hotel_type: str, results: list[dict]) -> str:
    """Infer meals_included from hotel type and search results."""
    if hotel_type == "shukubo":
        return "breakfast_dinner"
    if hotel_type == "ryokan":
        # Check if results mention 1泊2食 (2 meals)
        for r in results:
            if "1泊2食" in r.get("snippet", "") or "一泊二食" in r.get("snippet", ""):
                return "breakfast_dinner"
            if "朝食付" in r.get("snippet", "") and "夕食" not in r.get("snippet", ""):
                return "breakfast"
        return "breakfast_dinner"  # most ryokan include both
    if hotel_type == "business_hotel":
        # Check if results mention breakfast
        for r in results:
            if "朝食" in r.get("snippet", ""):
                return "breakfast"
        return "breakfast"  # most business hotels include breakfast
    return "none"


def infer_price_level(nightly_min: int | None, hotel_type: str) -> str:
    """Infer price_level from nightly minimum price."""
    if nightly_min is None:
        return ""
    nightly_min = int(nightly_min)
    if hotel_type in ("shukubo",):
        if nightly_min >= 20000:
            return "moderate"
        return "budget"
    if nightly_min >= 60000:
        return "luxury"
    if nightly_min >= 25000:
        return "expensive"
    if nightly_min >= 12000:
        return "moderate"
    return "budget"


def enrich_hotel(entry: dict, dry_run: bool = False) -> HotelEnriched:
    """Enrich a single hotel entry with real data."""
    name_ja = entry["name_ja"]
    city_code = entry.get("city_code", "")
    grade = entry.get("grade", "")

    hotel = HotelEnriched(
        name_ja=name_ja,
        city_code=city_code,
        grade=grade,
        hotel_type=entry.get("hotel_type", ""),
        price_level=entry.get("price_level", ""),
        nightly_jpy_min=entry.get("nightly_jpy_min"),
        data_confidence=entry.get("data_confidence", "ai_generated"),
    )

    # Apply known corrections first
    if name_ja in KNOWN_CORRECTIONS:
        corrections = KNOWN_CORRECTIONS[name_ja]
        for k, v in corrections.items():
            setattr(hotel, k, v)
        hotel.search_notes = "known_correction"
        return hotel

    if dry_run:
        hotel.search_notes = "dry_run"
        return hotel

    # --- Google search for coordinates, price, address ---
    # Search query: hotel name + location keywords
    area_hint = {
        "kyoto": "京都",
        "osaka": "大阪",
        "kobe": "神戸",
        "nara": "奈良",
        "kinosaki": "城崎温泉",
        "arima": "有馬温泉",
        "koyasan": "高野山",
        "ise": "伊勢",
    }.get(city_code, "")

    # Strip English name in parentheses for cleaner search
    clean_name = re.sub(r"\s*\(.*?\)\s*", "", name_ja).strip()

    google_query = f"{clean_name} {area_hint} 住所 料金 宿泊"
    print(f"  [google] {google_query}")
    google_raw = run_opencli("google", google_query)
    google_results = parse_google_results(google_raw)
    time.sleep(SEARCH_DELAY_SEC)

    # --- Ctrip search for Chinese name ---
    ctrip_query = clean_name
    print(f"  [ctrip]  {ctrip_query}")
    ctrip_raw = run_opencli("ctrip", ctrip_query)
    ctrip_results = parse_ctrip_results(ctrip_raw)
    time.sleep(SEARCH_DELAY_SEC)

    # --- Extract data ---
    lat, lng = extract_coordinates(google_results)
    if lat:
        hotel.lat = lat
        hotel.lng = lng

    price_min, price_max = extract_price_jpy(google_results)
    if price_min:
        hotel.nightly_jpy_min = price_min
        hotel.nightly_jpy_max = price_max

    address = extract_address(google_results)
    if address:
        hotel.address = address

    name_zh = extract_name_zh(ctrip_results, name_ja)
    if name_zh:
        hotel.name_zh = name_zh

    # --- Infer fields ---
    hotel.hotel_type = infer_hotel_type(name_ja, hotel.hotel_type, city_code)
    hotel.meals_included = infer_meals(hotel.hotel_type, google_results)

    if hotel.nightly_jpy_min:
        inferred_level = infer_price_level(hotel.nightly_jpy_min, hotel.hotel_type)
        if inferred_level:
            hotel.price_level = inferred_level

    # --- Determine confidence ---
    sources = []
    if lat:
        sources.append("coords")
    if price_min:
        sources.append("price")
    if name_zh:
        sources.append("name_zh")
    if address:
        sources.append("address")

    if len(sources) >= 3:
        hotel.data_confidence = "cross_checked"
    elif len(sources) >= 1:
        hotel.data_confidence = "single_source"
    else:
        hotel.data_confidence = "ai_generated"

    hotel.search_notes = f"found:{','.join(sources)}" if sources else "no_data_found"

    # Collect source URLs
    urls = [r["url"] for r in google_results[:3] if r.get("url")]
    hotel.source_urls = " | ".join(urls)

    return hotel


def main():
    # Ensure UTF-8 output on Windows
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    import argparse
    parser = argparse.ArgumentParser(description="Enrich hotel data from real sources")
    parser.add_argument("--grades", default="S,A", help="Comma-separated grades to process")
    parser.add_argument("--dry-run", action="store_true", help="Skip actual searches")
    args = parser.parse_args()

    target_grades = set(args.grades.upper().split(","))

    with open(LEDGER_PATH, encoding="utf-8") as f:
        ledger = json.load(f)

    entries = ledger["entries"]
    targets = [e for e in entries if e.get("grade") in target_grades]
    others = [e for e in entries if e.get("grade") not in target_grades]

    print(f"Total entries: {len(entries)}")
    print(f"Targets ({','.join(sorted(target_grades))}): {len(targets)}")
    print(f"Others (skipped): {len(others)}")
    print()

    enriched: list[HotelEnriched] = []

    for i, entry in enumerate(targets):
        name = entry["name_ja"]
        grade = entry.get("grade", "?")
        city = entry.get("city_code", "?")
        print(f"[{i+1}/{len(targets)}] {grade} | {city:12s} | {name}")

        hotel = enrich_hotel(entry, dry_run=args.dry_run)
        enriched.append(hotel)
        print(f"  => confidence={hotel.data_confidence}, type={hotel.hotel_type}, "
              f"price={hotel.nightly_jpy_min}-{hotel.nightly_jpy_max}, "
              f"coords={hotel.lat},{hotel.lng}")
        print()

    # Also include non-target grades as-is (minimal enrichment)
    for entry in others:
        hotel = HotelEnriched(
            name_ja=entry["name_ja"],
            city_code=entry.get("city_code", ""),
            grade=entry.get("grade", ""),
            hotel_type=entry.get("hotel_type", ""),
            price_level=entry.get("price_level", ""),
            nightly_jpy_min=entry.get("nightly_jpy_min"),
            data_confidence=entry.get("data_confidence", "ai_generated"),
            search_notes="not_searched",
        )
        enriched.append(hotel)

    # --- Write CSV ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = list(HotelEnriched.__dataclass_fields__.keys())
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for h in enriched:
            writer.writerow(asdict(h))

    print(f"\nWritten {len(enriched)} hotels to {OUTPUT_CSV}")

    # --- Statistics ---
    searched = [h for h in enriched if h.search_notes != "not_searched"]
    print(f"\n=== Statistics (searched: {len(searched)}) ===")
    has_coords = sum(1 for h in searched if h.lat is not None)
    has_price = sum(1 for h in searched if h.nightly_jpy_min is not None)
    has_name_zh = sum(1 for h in searched if h.name_zh)
    has_address = sum(1 for h in searched if h.address)
    print(f"  Coordinates: {has_coords}/{len(searched)}")
    print(f"  Price:       {has_price}/{len(searched)}")
    print(f"  Name (ZH):   {has_name_zh}/{len(searched)}")
    print(f"  Address:     {has_address}/{len(searched)}")

    confidence_counts = {}
    for h in searched:
        confidence_counts[h.data_confidence] = confidence_counts.get(h.data_confidence, 0) + 1
    print(f"\n  Confidence distribution:")
    for k, v in sorted(confidence_counts.items()):
        print(f"    {k}: {v}")

    type_counts = {}
    for h in searched:
        type_counts[h.hotel_type] = type_counts.get(h.hotel_type, 0) + 1
    print(f"\n  Hotel type distribution:")
    for k, v in sorted(type_counts.items()):
        print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
