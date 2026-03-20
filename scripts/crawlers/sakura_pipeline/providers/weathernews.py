from __future__ import annotations
from pathlib import Path
from bs4 import BeautifulSoup
from ..utils import fetch_text, write_text, write_json, now_iso, clean_ws

WEATHERNEWS_HOME = "https://weathernews.jp/sakura/"
WEATHERNEWS_NEWS = "https://weathernews.jp/news/202603/180076/"

def parse_weathernews_news(html: str, source_url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    text = clean_ws(soup.get_text(" "))
    return {
        "source": "weathernews_news",
        "source_url": source_url,
        "fetched_at": now_iso(),
        "uses_200m_reports": "200万" in text or "200万通以上" in text,
        "mentions_local_reporting": "独自取材" in text,
        "text_excerpt": text[:2400]
    }

def parse_weathernews_home(html: str, source_url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    text = clean_ws(soup.get_text(" "))
    return {
        "source": "weathernews_home",
        "source_url": source_url,
        "fetched_at": now_iso(),
        "contains_sakura_index": "さくら" in text and "名所" in text,
        "text_excerpt": text[:2000]
    }

def fetch_weathernews(out_dir: str = "data/weathernews") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    home_html = fetch_text(WEATHERNEWS_HOME)
    news_html = fetch_text(WEATHERNEWS_NEWS)

    write_text(out / "weathernews_home.html", home_html)
    write_text(out / "weathernews_news.html", news_html)

    payload = {
        "home": parse_weathernews_home(home_html, WEATHERNEWS_HOME),
        "news": parse_weathernews_news(news_html, WEATHERNEWS_NEWS)
    }
    write_json(out / "weathernews_metadata.json", payload)
    return payload
