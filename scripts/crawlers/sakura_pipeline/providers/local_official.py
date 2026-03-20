from __future__ import annotations
from pathlib import Path
from bs4 import BeautifulSoup
import yaml
from ..normalize import normalize_stage, stage_to_score
from ..utils import fetch_text, write_text, write_json, now_iso, clean_ws


def load_config(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def parse_one_site(site: dict) -> dict:
    url = site["url"]
    html = fetch_text(url)
    result = {
        "site_id": site["site_id"],
        "url": url,
        "fetched_at": now_iso(),
        "raw_path": None,
        "items": []
    }

    raw_dir = Path("data/local_official/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{site['site_id']}.html"
    write_text(raw_path, html)
    result["raw_path"] = str(raw_path)

    soup = BeautifulSoup(html, "lxml")
    selector = site.get("item_selector")
    if not selector:
        text = clean_ws(soup.get_text(" "))
        stage = normalize_stage(text)
        result["items"].append({
            "spot_name": site.get("spot_name"),
            "city_name": site.get("city_name"),
            "current_stage": stage,
            "stage_score": stage_to_score(stage),
            "best_viewing_start": None,
            "best_viewing_end": None,
            "festival_start": None,
            "festival_end": None,
            "illumination_start": None,
            "illumination_end": None
        })
        return result

    nodes = soup.select(selector)
    for node in nodes:
        txt = clean_ws(node.get_text(" "))
        stage = normalize_stage(txt)
        result["items"].append({
            "spot_name": site.get("spot_name"),
            "city_name": site.get("city_name"),
            "current_stage": stage,
            "stage_score": stage_to_score(stage),
            "raw_text": txt
        })
    return result


def fetch_local_sites(config_path: str, out_dir: str = "data/local_official") -> dict:
    cfg = load_config(config_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    payload = {
        "fetched_at": now_iso(),
        "sites": []
    }

    for site in cfg.get("sites", []):
        payload["sites"].append(parse_one_site(site))

    write_json(out / "local_sites_snapshot.json", payload)
    return payload
