from __future__ import annotations
from typing import List, Dict, Optional, Any
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from dateutil.parser import parse as dt_parse
from .utils import read_json, write_json, now_iso


def _date_to_ordinal(d: Optional[str]) -> Optional[int]:
    if not d:
        return None
    return dt_parse(d).date().toordinal()


def _ordinal_to_iso(o: Optional[int]) -> Optional[str]:
    if o is None:
        return None
    return datetime.fromordinal(o).date().isoformat()


def weighted_median(values: List[tuple[int, float]]) -> Optional[int]:
    if not values:
        return None
    items = sorted(values, key=lambda x: x[0])
    total = sum(w for _, w in items)
    c = 0.0
    for v, w in items:
        c += w
        if c >= total / 2:
            return v
    return items[-1][0]


def fuse_city_truth(year: int, jma_path: str) -> dict:
    data = read_json(jma_path)
    out = {"year": year, "cities": []}
    full_map = {x["city_name"]: x["full_bloom_date"] for x in data.get("full_bloom", [])}
    for item in data.get("bloom", []):
        city = item["city_name"]
        out["cities"].append({
            "city_name": city,
            "year": year,
            "bloom_date": item.get("bloom_date"),
            "full_bloom_date": full_map.get(city),
            "truth_source": "jma",
            "confidence": 100,
            "source_refs": [item["source_meta"]["source_url"]]
        })
    return out


def fuse_spot_truth(
    jmc_forecasts: List[dict] | None = None,
    weathernews_forecasts: List[dict] | None = None,
    local_official_items: List[dict] | None = None
) -> dict:
    jmc_forecasts = jmc_forecasts or []
    weathernews_forecasts = weathernews_forecasts or []
    local_official_items = local_official_items or []

    grouped: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "jmc": None,
        "weathernews": None,
        "local": None
    })

    for x in jmc_forecasts:
        grouped[x["spot_name"]]["jmc"] = x
    for x in weathernews_forecasts:
        grouped[x["spot_name"]]["weathernews"] = x
    for x in local_official_items:
        grouped[x["spot_name"]]["local"] = x

    out = {"fused_at": now_iso(), "spots": []}
    for spot_name, bucket in grouped.items():
        jmc = bucket["jmc"]
        wn = bucket["weathernews"]
        local = bucket["local"]

        bloom_values = []
        full_values = []
        refs = []

        if jmc and jmc.get("forecast_bloom_date"):
            bloom_values.append((_date_to_ordinal(jmc["forecast_bloom_date"]), 0.45))
            refs.append(jmc.get("source_url", "jmc"))
        if wn and wn.get("forecast_bloom_date"):
            bloom_values.append((_date_to_ordinal(wn["forecast_bloom_date"]), 0.35))
            refs.append(wn.get("source_url", "weathernews"))
        if local and local.get("forecast_bloom_date"):
            bloom_values.append((_date_to_ordinal(local["forecast_bloom_date"]), 0.20))
            refs.append(local.get("source_url", "local"))

        if jmc and jmc.get("forecast_full_bloom_date"):
            full_values.append((_date_to_ordinal(jmc["forecast_full_bloom_date"]), 0.45))
        if wn and wn.get("forecast_full_bloom_date"):
            full_values.append((_date_to_ordinal(wn["forecast_full_bloom_date"]), 0.35))
        if local and local.get("forecast_full_bloom_date"):
            full_values.append((_date_to_ordinal(local["forecast_full_bloom_date"]), 0.20))

        fused_bloom = _ordinal_to_iso(weighted_median([(v, w) for v, w in bloom_values if v is not None]))
        fused_full = _ordinal_to_iso(weighted_median([(v, w) for v, w in full_values if v is not None]))

        current_stage = None
        if local and local.get("current_stage"):
            current_stage = local["current_stage"]
            confidence = 90
        elif wn and wn.get("current_stage"):
            current_stage = wn["current_stage"]
            confidence = 80
        elif jmc and jmc.get("current_stage"):
            current_stage = jmc["current_stage"]
            confidence = 75
        elif fused_bloom or fused_full:
            confidence = 55
        else:
            confidence = 35

        out["spots"].append({
            "spot_name": spot_name,
            "city_name": (local or wn or jmc or {}).get("city_name"),
            "forecast_bloom_date": fused_bloom,
            "forecast_full_bloom_date": fused_full,
            "current_stage": current_stage,
            "confidence": confidence,
            "source_refs": refs
        })

    return out


def build_all(year: int, data_dir: str = "data") -> dict:
    data_path = Path(data_dir)
    city_truth = fuse_city_truth(year, data_path / "jma" / f"jma_city_truth_{year}.json")

    local_snapshot_path = data_path / "local_official" / "local_sites_snapshot.json"
    local_items = []
    if local_snapshot_path.exists():
        local_payload = read_json(local_snapshot_path)
        for site in local_payload.get("sites", []):
            for item in site.get("items", []):
                item["source_url"] = site.get("url")
                local_items.append(item)

    spot_truth = fuse_spot_truth(local_official_items=local_items)

    payload = {
        "year": year,
        "city_truth": city_truth,
        "spot_truth": spot_truth
    }
    write_json(data_path / f"fused_sakura_truth_{year}.json", payload)
    return payload
