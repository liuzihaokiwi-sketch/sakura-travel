from __future__ import annotations
import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Optional
from ..models import CityBloomObservation, SourceMeta
from ..utils import fetch_text, write_text, write_json, now_iso

JMA_BLOOM_URL = "https://www.data.jma.go.jp/sakura/data/sakura_kaika.html"
JMA_FULL_URL = "https://www.data.jma.go.jp/sakura/data/sakura_mankai.html"

# JMA 历史数据 URL (CSV)
JMA_HISTORY_BLOOM_URL = "https://www.data.jma.go.jp/sakura/data/sakura_kaika_v301.csv"
JMA_HISTORY_FULL_URL = "https://www.data.jma.go.jp/sakura/data/sakura_mankai_v301.csv"

# 地区 header 正则: 【沖縄県】 / 【九州地方・山口県】
REGION_RE = re.compile(r"^【(.+?)】$")
# 日期正则: "3月 20日" or "3月20日"
DATE_RE = re.compile(r"(\d{1,2})月\s*(\d{1,2})日")


def _parse_date(text: str, year: int) -> Optional[str]:
    """将 '3月 20日' 转为 '2026-03-20'"""
    m = DATE_RE.search(text)
    if not m:
        return None
    month, day = int(m.group(1)), int(m.group(2))
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_jma_table(html: str, year: int, source_url: str, is_bloom: bool = True) -> List[CityBloomObservation]:
    """
    解析 JMA 的 sakura_kaika.html 或 sakura_mankai.html。
    页面只有一张大表，结构:
      [地区 header行 (1列 colspan)]
      [表头行: 地点名 | 観測日 | 平年差 | 平年日 | 昨年差 | 昨年日 | 品種]
      [数据行: 東京 | 3月 20日 | -4 | 3月24日 | +2 | 3月18日 | (空)]
      ...
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table")
    if not table:
        return []

    results: List[CityBloomObservation] = []
    current_region = None

    for row in table.select("tr"):
        cells = row.select("td, th")
        texts = [c.get_text(strip=True) for c in cells]

        if not texts:
            continue

        # 检查是否是地区 header 行 (只有 1 列)
        if len(texts) == 1:
            m = REGION_RE.match(texts[0])
            if m:
                current_region = m.group(1)
            continue

        # 跳过表头行
        if texts[0] == "地点名":
            continue

        # 数据行：至少需要 2 列 (城市名 + 观测日)
        if len(texts) < 2:
            continue

        city_name = texts[0].strip()
        if not city_name or city_name == "":
            continue

        # 观测日
        observed_date = _parse_date(texts[1], year) if len(texts) > 1 else None
        # 平年日 (历史平均)
        normal_date = _parse_date(texts[3], year) if len(texts) > 3 else None
        # 昨年日
        last_year_date = _parse_date(texts[5], year - 1) if len(texts) > 5 else None
        # 品种 (空 = 染井吉野)
        variety = texts[6].strip() if len(texts) > 6 and texts[6].strip() else "そめいよしの"
        # 平年差
        normal_diff = texts[2].strip() if len(texts) > 2 else None

        # 只有实际有观测日期的才记录
        if not observed_date:
            # 可能还没观测到，记录平年日作为参考
            if normal_date:
                obs = CityBloomObservation(
                    city_name=city_name,
                    prefecture_region=current_region,
                    bloom_date=normal_date if is_bloom else None,
                    full_bloom_date=normal_date if not is_bloom else None,
                    bloom_observed=False,
                    full_bloom_observed=False,
                    variety=variety,
                    source_meta=SourceMeta(
                        source_name=f"jma_{'bloom' if is_bloom else 'full_bloom'}_normal",
                        source_url=source_url,
                        fetched_at=now_iso(),
                    ),
                )
                results.append(obs)
            continue

        obs = CityBloomObservation(
            city_name=city_name,
            prefecture_region=current_region,
            bloom_date=observed_date if is_bloom else None,
            full_bloom_date=observed_date if not is_bloom else None,
            bloom_observed=is_bloom,
            full_bloom_observed=(not is_bloom),
            variety=variety,
            source_meta=SourceMeta(
                source_name=f"jma_{'bloom' if is_bloom else 'full_bloom'}",
                source_url=source_url,
                fetched_at=now_iso(),
            ),
        )
        results.append(obs)

    return results


def fetch_and_parse_jma(year: int = 2026, out_dir: str = "data/sakura/jma") -> dict:
    """采集 JMA 当年开花 + 满开数据"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 开花
    bloom_html = fetch_text(JMA_BLOOM_URL)
    write_text(out / f"jma_bloom_{year}.html", bloom_html)
    bloom_items = parse_jma_table(bloom_html, year, JMA_BLOOM_URL, is_bloom=True)

    # 满开
    full_html = fetch_text(JMA_FULL_URL)
    write_text(out / f"jma_full_{year}.html", full_html)
    full_items = parse_jma_table(full_html, year, JMA_FULL_URL, is_bloom=False)

    payload = {
        "year": year,
        "fetched_at": now_iso(),
        "bloom_count": len(bloom_items),
        "full_bloom_count": len(full_items),
        "bloom": [x.model_dump() for x in bloom_items],
        "full_bloom": [x.model_dump() for x in full_items],
    }
    write_json(out / f"jma_city_truth_{year}.json", payload)
    return payload