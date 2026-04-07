"""
Scrape enrichment data from japan-guide.com for spots in the candidate pool.

Extracts: lat, lng, cost_jpy, visit_minutes, best_season, name_zh
Outputs to data/kansai_spots/discovery_pool/spots_enriched.csv

Usage:
    .venv/Scripts/python.exe scripts/scrape_spots_japanguide.py
    .venv/Scripts/python.exe scripts/scrape_spots_japanguide.py --start 0 --end 20  # partial
"""

from __future__ import annotations

import argparse
import copy
import csv
import logging
import re
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "data/kansai_spots/discovery_pool/spots_candidate_pool.csv"
OUTPUT_CSV = PROJECT_ROOT / "data/kansai_spots/discovery_pool/spots_enriched.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Common Japanese → Chinese name suffix mappings
JA_ZH_SUFFIX_MAP = {
    "寺": "寺",
    "神社": "神社",
    "城": "城",
    "大社": "大社",
    "院": "院",
    "宮": "宫",
    "殿": "殿",
    "塔": "塔",
    "橋": "桥",
    "滝": "瀑布",
    "山": "山",
    "川": "川",
    "湖": "湖",
    "島": "岛",
    "市場": "市场",
    "通": "通",
    "園": "园",
    "公園": "公园",
    "博物館": "博物馆",
    "美術館": "美术馆",
    "水族館": "水族馆",
    "動物園": "动物园",
    "タワー": "塔",
    "ミュージアム": "博物馆",
}

# Full name_ja → name_zh lookup for known spots
# (populated from name_ja column; common Kansai spots)
JA_ZH_FULL_MAP: dict[str, str] = {
    "二条城": "二条城",
    "錦市場": "锦市场",
    "京都御所": "京都御所",
    "先斗町": "先斗町",
    "本願寺": "本愿寺",
    "京都タワー": "京都塔",
    "清水寺": "清水寺",
    "銀閣寺": "银阁寺",
    "南禅寺": "南禅寺",
    "京都国立博物館": "京都国立博物馆",
    "建仁寺": "建仁寺",
    "哲学の道": "哲学之道",
    "高台寺": "高台寺",
    "青蓮院": "青莲院",
    "八坂神社": "八坂神社",
    "知恩院": "知恩院",
    "三十三間堂": "三十三间堂",
    "金閣寺": "金阁寺",
    "龍安寺": "龙安寺",
    "仁和寺": "仁和寺",
    "北野天満宮": "北野天满宫",
    "大徳寺": "大德寺",
    "下鴨神社": "下鸭神社",
    "上賀茂神社": "上贺茂神社",
    "嵐山": "岚山",
    "天龍寺": "天龙寺",
    "竹林の小径": "竹林小径",
    "渡月橋": "渡月桥",
    "鈴虫寺": "铃虫寺",
    "苔寺": "苔寺",
    "桂離宮": "桂离宫",
    "伏見稲荷大社": "伏见稻荷大社",
    "醍醐寺": "醍醐寺",
    "東福寺": "东福寺",
    "泉涌寺": "泉涌寺",
    "平等院": "平等院",
    "三室戸寺": "三室户寺",
    "貴船神社": "贵船神社",
    "鞍馬寺": "鞍马寺",
    "大阪城": "大阪城",
    "道頓堀": "道顿堀",
    "心斎橋": "心斋桥",
    "通天閣": "通天阁",
    "新世界": "新世界",
    "梅田スカイビル": "梅田蓝天大厦",
    "大阪天満宮": "大阪天满宫",
    "万博記念公園": "万博纪念公园",
    "四天王寺": "四天王寺",
    "住吉大社": "住吉大社",
    "黒門市場": "黑门市场",
    "なんばグランド花月": "难波花月剧场",
    "海遊館": "海游馆",
    "天保山": "天保山",
    "カップヌードルミュージアム": "杯面博物馆",
    "姫路城": "姬路城",
    "有馬温泉": "有马温泉",
    "神戸ハーバーランド": "神户港乐园",
    "北野異人館": "北野异人馆",
    "南京町": "南京町",
    "六甲山": "六甲山",
    "布引の滝": "布引瀑布",
    "奈良公園": "奈良公园",
    "東大寺": "东大寺",
    "春日大社": "春日大社",
    "興福寺": "兴福寺",
    "法隆寺": "法隆寺",
    "吉野山": "吉野山",
    "高野山": "高野山",
    "熊野古道": "熊野古道",
    "白浜": "白滨",
    "那智の滝": "那智瀑布",
    "熊野那智大社": "熊野那智大社",
    "熊野速玉大社": "熊野速玉大社",
    "琵琶湖": "琵琶湖",
    "比叡山延暦寺": "比叡山延历寺",
    "彦根城": "彦根城",
    "近江八幡": "近江八幡",
    "長浜": "长滨",
    "伊勢神宮": "伊势神宫",
    "鳥取砂丘": "鸟取砂丘",
    "天橋立": "天桥立",
    "竹田城跡": "竹田城迹",
    "永観堂": "永观堂",
    "祇園": "祇园",
    "京都国際マンガミュージアム": "京都国际漫画博物馆",
    "京都水族館": "京都水族馆",
    "京都鉄道博物館": "京都铁道博物馆",
    "妙心寺": "妙心寺",
    "東寺": "东寺",
    "西本願寺": "西本愿寺",
    "東本願寺": "东本愿寺",
    "元離宮二条城": "元离宫二条城",
}


def extract_coordinates(html: str) -> tuple[float | None, float | None]:
    """Extract lat/lng from Google Maps embed URL in the page."""
    # Pattern: center=LAT,LNG in maps embed
    m = re.search(
        r"google\.com/maps/embed[^\"]*center=([\d.]+)%2C([\d.]+)", html
    )
    if m:
        lat, lng = float(m.group(1)), float(m.group(2))
        # Sanity check for Kansai region (roughly 33.5-36, 134-137)
        if 33.0 <= lat <= 37.0 and 133.0 <= lng <= 137.0:
            return round(lat, 7), round(lng, 7)
    # Fallback: look for raw coordinate patterns
    m = re.search(r"center=(3[3-7]\.\d+),(13[3-7]\.\d+)", html)
    if m:
        return round(float(m.group(1)), 7), round(float(m.group(2)), 7)
    return None, None


def extract_admission(soup: BeautifulSoup) -> int | None:
    """Extract admission fee in JPY from the Hours and Fees section."""
    section = soup.find("section", class_="page_section--admission")
    if not section:
        return None

    text = section.get_text(separator="\n", strip=True)

    # Check for free admission
    if re.search(r"\bfree\b", text, re.I):
        return 0

    # Find "Admission" line and extract yen amount
    lines = text.split("\n")
    in_admission = False
    for line in lines:
        if re.search(r"^admission", line, re.I):
            in_admission = True
        if in_admission:
            # Extract first yen amount
            m = re.search(r"(\d[\d,]*)\s*yen", line, re.I)
            if m:
                return int(m.group(1).replace(",", ""))
        # Also check for "yen" on any line in the section
    # Fallback: just find first yen amount in the section
    m = re.search(r"(\d[\d,]*)\s*yen", text, re.I)
    if m:
        return int(m.group(1).replace(",", ""))
    return None


def _get_main_content_text(soup: BeautifulSoup) -> str:
    """Extract text from the main article content section only."""
    # japan-guide uses section.page_section--main_content for the article body
    main = soup.find("section", class_="page_section--main_content")
    if main:
        return main.get_text(separator=" ", strip=True).lower()
    # Fallback: try <main> tag but strip obvious nav/footer
    main_tag = soup.find("main")
    if main_tag:
        s = copy.deepcopy(main_tag)
        for sel in ["nav", "footer", "header", ".sidebar", ".seasonal_alert"]:
            for el in s.select(sel):
                el.decompose()
        return s.get_text(separator=" ", strip=True).lower()
    return ""


def extract_best_season(soup: BeautifulSoup) -> str:
    """Extract best season from the main article content."""
    text = _get_main_content_text(soup)

    seasons = set()
    # Only match patterns that indicate THIS spot is seasonal
    if re.search(r"cherry blossom|hanami spot|sakura season", text):
        seasons.add("spring")
    if re.search(r"autumn lea|fall foliage|koyo spot|momiji|autumn color", text):
        seasons.add("autumn")
    if re.search(r"snow festival|winter illuminat|snow scenery", text):
        seasons.add("winter")
    if re.search(r"hydrangea|iris garden|summer festival|firefl", text):
        seasons.add("summer")

    if not seasons:
        return "all_year"
    if len(seasons) >= 3:
        return "all_year"
    return ",".join(sorted(seasons))


def estimate_visit_minutes(
    soup: BeautifulSoup, main_type: str, sub_type: str
) -> int | None:
    """Try to extract visit duration from page, or estimate based on type."""
    # Look in the admission/hours section first for structured duration info
    section = soup.find("section", class_="page_section--admission")
    text = section.get_text(separator=" ", strip=True) if section else ""

    # Also check the main intro paragraphs
    intro = ""
    for p in soup.find_all("p"):
        intro += " " + p.get_text(separator=" ", strip=True)
    full_text = text + " " + intro

    # Look for explicit "X to Y minutes" visit duration patterns
    m = re.search(
        r"(?:visit|tour|walk|spend|allow|takes?|requires?)\s+(?:about\s+)?(\d+)\s*(?:to|-)\s*(\d+)\s*minutes",
        full_text,
        re.I,
    )
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        avg = (lo + hi) // 2
        if 20 <= avg <= 480:
            return avg

    m = re.search(
        r"(?:visit|tour|walk|spend|allow|takes?|requires?)\s+(?:about\s+)?(\d+)\s+minutes",
        full_text,
        re.I,
    )
    if m:
        val = int(m.group(1))
        if 20 <= val <= 480:
            return val

    # Estimate by type (fallback)
    estimates: dict[str, int] = {
        "history_religion": 45,
        "culture_art": 75,
        "nature_scenery": 60,
        "animal_science": 90,
        "landmark_view": 30,
        "shopping_district": 90,
        "historic_district": 120,
        "food_street": 60,
        "amusement_park": 180,
        "hot_spring": 120,
        "garden": 45,
    }
    if main_type == "area_dest":
        return estimates.get(sub_type, 120)
    return estimates.get(sub_type)


def translate_name(name_ja: str, name_en: str) -> str | None:
    """Translate Japanese name to Chinese using lookup table."""
    if not name_ja:
        return None
    # Direct lookup
    if name_ja in JA_ZH_FULL_MAP:
        return JA_ZH_FULL_MAP[name_ja]
    return None


def fetch_and_parse(
    url: str, main_type: str, sub_type: str, client: httpx.Client
) -> dict[str, str | float | int | None]:
    """Fetch a japan-guide page and extract enrichment fields."""
    result: dict[str, str | float | int | None] = {
        "lat": None,
        "lng": None,
        "cost_jpy": None,
        "visit_minutes": None,
        "best_season": None,
    }
    try:
        resp = client.get(url, follow_redirects=True, timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("Failed to fetch %s: %s", url, exc)
        return result

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    lat, lng = extract_coordinates(html)
    result["lat"] = lat
    result["lng"] = lng
    result["cost_jpy"] = extract_admission(soup)
    result["best_season"] = extract_best_season(soup)
    result["visit_minutes"] = estimate_visit_minutes(soup, main_type, sub_type)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape japan-guide.com for spot enrichment data"
    )
    parser.add_argument("--start", type=int, default=0, help="Start row index")
    parser.add_argument(
        "--end", type=int, default=None, help="End row index (exclusive)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=10, help="URLs per batch"
    )
    parser.add_argument(
        "--delay", type=float, default=2.0, help="Seconds between batches"
    )
    args = parser.parse_args()

    # Read input CSV
    with open(INPUT_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    end = args.end or len(rows)
    subset = rows[args.start : end]
    log.info(
        "Processing rows %d-%d of %d total", args.start, end - 1, len(rows)
    )

    enriched_fields = ["lat", "lng", "cost_jpy", "visit_minutes", "best_season", "name_zh"]
    output_fields = list(rows[0].keys()) + enriched_fields

    client = httpx.Client(headers=HEADERS)
    results: list[dict] = []

    for batch_start in range(0, len(subset), args.batch_size):
        batch = subset[batch_start : batch_start + args.batch_size]
        for row in batch:
            url = row.get("japan_guide_url", "")
            name_en = row.get("name_en", "")
            name_ja = row.get("name_ja", "")
            main_type = row.get("main_type", "")
            sub_type = row.get("sub_type", "")

            log.info("Fetching: %s (%s)", name_en, url)

            if not url or not url.startswith("http"):
                log.warning("Skipping %s: no valid URL", name_en)
                enriched = {k: None for k in enriched_fields}
            else:
                enriched = fetch_and_parse(url, main_type, sub_type, client)
                # For area destinations, high costs are likely sub-attraction fees
                if main_type == "area_dest" and enriched.get("cost_jpy"):
                    if enriched["cost_jpy"] > 2000:
                        log.info(
                            "  %s: cost %d looks like sub-attraction fee for area_dest, setting to null",
                            name_en, enriched["cost_jpy"],
                        )
                        enriched["cost_jpy"] = None

            enriched["name_zh"] = translate_name(name_ja, name_en)

            merged = {**row, **enriched}
            results.append(merged)

        if batch_start + args.batch_size < len(subset):
            log.info("Batch done, waiting %.1fs...", args.delay)
            time.sleep(args.delay)

    client.close()

    # Write output: merge with rows not in subset
    all_results = []
    for i, row in enumerate(rows):
        if args.start <= i < end:
            all_results.append(results[i - args.start])
        else:
            # Fill enriched fields with None for non-processed rows
            padded = {**row}
            for k in enriched_fields:
                padded.setdefault(k, None)
            all_results.append(padded)

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(all_results)

    # Stats
    has_coords = sum(1 for r in results if r.get("lat"))
    has_cost = sum(1 for r in results if r.get("cost_jpy") is not None)
    has_season = sum(
        1 for r in results if r.get("best_season") and r["best_season"] != "all_year"
    )
    has_zh = sum(1 for r in results if r.get("name_zh"))

    log.info("=== Results ===")
    log.info("Processed: %d spots", len(results))
    log.info("Coordinates: %d/%d", has_coords, len(results))
    log.info("Cost: %d/%d", has_cost, len(results))
    log.info("Seasonal: %d/%d", has_season, len(results))
    log.info("Chinese name: %d/%d", has_zh, len(results))
    log.info("Output: %s", OUTPUT_CSV)


if __name__ == "__main__":
    main()
