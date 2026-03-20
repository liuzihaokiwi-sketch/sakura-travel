from __future__ import annotations
from pathlib import Path
from bs4 import BeautifulSoup
from ..utils import fetch_text, write_text, write_json, now_iso, clean_ws

JMC_HOME = "https://sakuranavi.n-kishou.co.jp/en/"
JMC_NEWS = "https://n-kishou.com/corp/news-contents/sakura/?lang=en"

def parse_jmc_news_article(html: str, source_url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    text = clean_ws(soup.get_text("\n"))
    return {
        "source": "jmc_news",
        "source_url": source_url,
        "fetched_at": now_iso(),
        "text_excerpt": text[:2000]
    }

def parse_jmc_app_landing(html: str, source_url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    text = clean_ws(soup.get_text(" "))
    return {
        "source": "jmc_app",
        "source_url": source_url,
        "fetched_at": now_iso(),
        "has_flowering_meter": "Flowering Meter" in text,
        "updates_every_thursday": "every Thursday" in text or "updates forecasts for all spots every Thursday" in text,
        "coverage_over_1000_spots": "1,000" in text or "1000" in text
    }

def fetch_jmc(out_dir: str = "data/jmc") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    home_html = fetch_text(JMC_HOME)
    news_html = fetch_text(JMC_NEWS)

    write_text(out / "jmc_home.html", home_html)
    write_text(out / "jmc_news.html", news_html)

    payload = {
        "landing": parse_jmc_app_landing(home_html, JMC_HOME),
        "news": parse_jmc_news_article(news_html, JMC_NEWS)
    }
    write_json(out / "jmc_metadata.json", payload)
    return payload
