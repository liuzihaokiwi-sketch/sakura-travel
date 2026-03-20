from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Any
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SakuraPipeline/1.0; +https://example.com/bot)"
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_text(url: str, timeout: int = 30, headers: Optional[dict] = None) -> str:
    h = DEFAULT_HEADERS.copy()
    if headers:
        h.update(headers)
    r = requests.get(url, timeout=timeout, headers=h)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or r.encoding
    return r.text


def write_text(path: str | Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def write_json(path: str | Path, payload: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def clean_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def ym_to_iso(year: int, month_text: str, day_text: str) -> str:
    month = int(month_text)
    day = int(day_text)
    return f"{year:04d}-{month:02d}-{day:02d}"
