"""
日本活动/节庆/季节事件爬虫
============================
数据源:
  1. japan-guide.com/e/events — 最全的英文日本活动日历
  2. rurubu.travel             — 日本本土活动信息（るるぶ）
  3. walkerplus.com/event      — 花火大会/紅葉/桜 季节情报

采集字段:
  name_ja, name_zh, name_en, city_code, start_date, end_date,
  event_type (festival/sakura/koyo/fireworks/illumination/food/market),
  description_zh, venue, lat, lng, image_url, source_url

用法:
  python scripts/event_crawl.py --city tokyo --months 6
  python scripts/event_crawl.py --type sakura          # 只抓樱花信息
  python scripts/event_crawl.py --type fireworks        # 只抓花火大会
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from scripts.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

# ── 城市配置 ─────────────────────────────────────────────────────────────────

CITY_MAP = {
    "tokyo":     {"name_zh": "东京",   "jg_path": "e/tokyo",  "pref_code": "tokyo"},
    "osaka":     {"name_zh": "大阪",   "jg_path": "e/osaka",  "pref_code": "osaka"},
    "kyoto":     {"name_zh": "京都",   "jg_path": "e/kyoto",  "pref_code": "kyoto"},
    "nara":      {"name_zh": "奈良",   "jg_path": "e/nara",   "pref_code": "nara"},
    "hakone":    {"name_zh": "箱根",   "jg_path": "e/hakone", "pref_code": "kanagawa"},
    "sapporo":   {"name_zh": "札幌",   "jg_path": "e/sapporo","pref_code": "hokkaido"},
    "fukuoka":   {"name_zh": "福冈",   "jg_path": "e/fukuoka","pref_code": "fukuoka"},
    "okinawa":   {"name_zh": "冲绳",   "jg_path": "e/okinawa","pref_code": "okinawa"},
    "kamakura":  {"name_zh": "镰仓",   "jg_path": "e/kamakura","pref_code": "kanagawa"},
    "kanazawa":  {"name_zh": "金泽",   "jg_path": "e/kanazawa","pref_code": "ishikawa"},
    "kobe":      {"name_zh": "神户",   "jg_path": "e/kobe",   "pref_code": "hyogo"},
    "nagoya":    {"name_zh": "名古屋", "jg_path": "e/nagoya", "pref_code": "aichi"},
    "yokohama":  {"name_zh": "横滨",   "jg_path": "e/yokohama","pref_code": "kanagawa"},
}

# 月份英文
MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

# 活动类型关键词推断
EVENT_TYPE_KEYWORDS = {
    "sakura":        ["sakura", "cherry blossom", "hanami", "桜", "花見", "樱花"],
    "koyo":          ["autumn leaves", "koyo", "紅葉", "momiji", "红叶"],
    "fireworks":     ["fireworks", "hanabi", "花火", "烟花", "烟火"],
    "illumination":  ["illumination", "light-up", "ライトアップ", "灯光"],
    "festival":      ["matsuri", "festival", "祭", "节", "祭り"],
    "food":          ["food", "gourmet", "ramen", "グルメ", "美食"],
    "market":        ["market", "flea", "マーケット", "市集", "集市"],
    "snow":          ["snow", "ice", "雪", "氷", "冰雪"],
}


def _infer_event_type(name: str, desc: str = "") -> str:
    """从名称和描述推断活动类型"""
    combined = f"{name} {desc}".lower()
    for etype, keywords in EVENT_TYPE_KEYWORDS.items():
        if any(k.lower() in combined for k in keywords):
            return etype
    return "festival"


class EventCrawler(BaseCrawler):
    """
    日本活动/节庆数据爬虫。

    主数据源: japan-guide.com（最全最结构化的日本活动英文网站）
    """

    JG_BASE = "https://www.japan-guide.com"

    def __init__(self, output_dir: str = "data/events_raw", **kwargs):
        kwargs.setdefault("delay_range", (1.5, 3.0))
        kwargs.setdefault("max_concurrent", 2)
        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)

    # ─────────────────────────────────────────────────────────────────────────
    # japan-guide.com 活动日历
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_jg_event_calendar(
        self, year: int = None, month: int = None
    ) -> List[Dict[str, Any]]:
        """采集 japan-guide.com 的节庆活动日历"""
        if not year:
            year = date.today().year
        if not month:
            month = date.today().month

        # 主节庆页 (Matsuri)
        url = f"{self.JG_BASE}/e/e2063.html"
        logger.info(f"📅 japan-guide 节庆日历")

        html = await self.fetch_text(url, referer=self.JG_BASE)
        if not html:
            return []

        return self._parse_jg_festivals(html, year)

    def _parse_jg_festivals(
        self, html: str, year: int
    ) -> List[Dict[str, Any]]:
        """
        解析 japan-guide 节庆页面。
        页面格式: 正文中以 "Month DD" 开头的段落描述各个节日。
        """
        soup = BeautifulSoup(html, "html.parser")
        body_text = soup.get_text()
        results = []

        # 匹配 "Month DD(-DD)" + 后续描述
        month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)'
        # 找所有 "Month DD" 开头的文段
        event_blocks = re.findall(
            rf'({month_pattern}\s+\d{{1,2}}(?:\s*[-–and,]+\s*(?:{month_pattern}\s+)?\d{{1,2}})?)\s*\n+\s*(.+?)(?=\n\s*(?:{month_pattern}\s+\d|\Z))',
            body_text, re.DOTALL
        )

        for match in event_blocks:
            date_str = match[0].strip()
            desc = match[3].strip()[:500] if len(match) > 3 else ""

            # 解析日期
            first_month_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', date_str)
            if not first_month_match:
                continue
            month_num = MONTH_NAMES.get(first_month_match.group(1).lower(), 1)

            # 从描述中提取活动名（通常在描述的前半部分或有链接）
            # 找 bold 文本或者第一句里的专有名词
            name_match = re.search(r'(?:The\s+)?([A-Z][a-zA-Z\s]+(?:Matsuri|Festival|Odori|Nebuta|Gion|Tenjin|Awa|Kanda|Takayama|Chichibu|Sanja|Aoi))', desc)
            if name_match:
                name_en = name_match.group(1).strip()
            else:
                # 取描述前 50 字符作为名称
                first_sentence = desc.split('.')[0][:80]
                name_en = first_sentence

            if len(name_en) < 5:
                continue

            city_code = self._infer_city(desc, name_en)
            event_type = _infer_event_type(name_en, desc)

            start_date, end_date = self._parse_date_range(date_str, year, month_num)

            results.append({
                "name_en": name_en,
                "name_ja": "",
                "name_zh": "",
                "city_code": city_code,
                "event_type": event_type,
                "start_date": start_date,
                "end_date": end_date,
                "date_raw": date_str,
                "venue": "",
                "description_en": desc[:300],
                "description_zh": "",
                "source_url": f"{self.JG_BASE}/e/e2063.html",
                "source": "japan-guide",
                "year": year,
                "crawled_at": datetime.utcnow().isoformat(),
            })
            self.stats.items_scraped += 1

        logger.info(f"  ✅ {len(results)} 个节庆活动")
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # 樱花/红叶 专题
    # ─────────────────────────────────────────────────────────────────────────

    # ── 樱花景点城市页 URL 映射 ──────────────────────────────────────────────
    SAKURA_CITY_PAGES = {
        "tokyo":    "/e/e3050.html",
        "kyoto":    "/e/e3951.html",
        "osaka":    "/e/e7926.html",
        "sapporo":  "/e/e5316.html",
        "hakone":   "/e/e5213.html",
        "kamakura": "/e/e3115.html",
        "nara":     "/e/e4150.html",
        "yokohama": "/e/e3210.html",
        "hiroshima": "/e/e3507.html",
    }

    # 广告域名黑名单 — 过滤掉非景点链接
    _AD_DOMAINS = {"booking.com", "klook.com", "agoda.com", "omakaseje.com",
                   "airbnb.com", "getyourguide.com", "tripadvisor.com"}

    async def crawl_sakura_forecast(self) -> List[Dict[str, Any]]:
        """采集各城市的樱花最佳观赏景点 (japan-guide.com)"""
        logger.info("🌸 开始采集樱花景点 (%d 个城市)", len(self.SAKURA_CITY_PAGES))
        all_spots: List[Dict[str, Any]] = []

        for city_code, page_path in self.SAKURA_CITY_PAGES.items():
            url = f"{self.JG_BASE}{page_path}"
            logger.info("  🌸 %s: %s", city_code, url)
            html = await self.fetch_text(url, referer=self.JG_BASE)
            if not html:
                continue
            await self._random_delay()

            soup = BeautifulSoup(html, "html.parser")
            city_spots = self._parse_sakura_spots(soup, city_code, url)
            all_spots.extend(city_spots)
            logger.info("    ✅ %s: %d 个樱花景点", city_code, len(city_spots))

        # 补充: 采集预报首页的开花状态
        await self._enrich_sakura_status(all_spots)

        logger.info("  🌸 樱花景点采集完成: 共 %d 个", len(all_spots))
        return all_spots

    def _parse_sakura_spots(self, soup: BeautifulSoup, city_code: str,
                            page_url: str) -> List[Dict[str, Any]]:
        """从城市樱花页面解析景点列表 (选择器: .spot_list__spot)"""
        results = []
        now_iso = datetime.utcnow().isoformat()

        for item in soup.select(".spot_list__spot"):
            try:
                # ── 获取链接 ──
                name_el = item.select_one(
                    ".spot_list__spot__desc a, .spot_list__spot__main_info a"
                )
                if not name_el:
                    name_el = item.select_one("a")
                if not name_el:
                    continue

                href = name_el.get("href", "")
                # 过滤广告链接
                if any(ad in href for ad in self._AD_DOMAINS):
                    continue
                # 过滤非 japan-guide 内链
                if href.startswith("http") and "japan-guide.com" not in href:
                    continue

                name_en = name_el.get_text(strip=True)
                # 过滤太短或明显无效的名称
                if len(name_en) < 2 or name_en.lower() in ("sponsored", "see all"):
                    continue
                # 清理名字末尾的 bullet 符号
                name_en = re.sub(r'[•·]+$', '', name_en).strip()

                # 补全链接
                if href and not href.startswith("http"):
                    if not href.startswith("/"):
                        href = "/" + href
                    href = self.JG_BASE + href

                # ── 获取描述 ──
                desc_el = item.select_one(".spot_list__spot__desc")
                desc = ""
                if desc_el:
                    desc = desc_el.get_text(strip=True)
                    # 去掉名字重复
                    if desc.startswith(name_en):
                        desc = desc[len(name_en):].strip()
                desc = desc[:300]

                # ── 获取图片 ──
                img_el = item.select_one("img")
                img_url = ""
                if img_el:
                    img_url = img_el.get("data-src", img_el.get("src", ""))
                    if img_url and not img_url.startswith("http"):
                        img_url = self.JG_BASE + img_url

                results.append({
                    "name_en": name_en,
                    "name_zh": "",
                    "name_ja": "",
                    "city_code": city_code,
                    "event_type": "sakura",
                    "description_en": desc,
                    "image_url": img_url,
                    "source_url": href,
                    "source": "japan-guide",
                    "crawled_at": now_iso,
                    "status": "",
                    "lat": None,
                    "lng": None,
                })
            except Exception:
                continue
        return results

    async def _enrich_sakura_status(self, spots: List[Dict[str, Any]]) -> None:
        """从樱花预报首页获取开花状态 (optional enrichment)"""
        url = f"{self.JG_BASE}/sakura/"
        html = await self.fetch_text(url, referer=self.JG_BASE)
        if not html:
            return
        text_lower = html.lower()
        # 简单全局状态检测
        for keyword, status in [
            ("full bloom", "full_bloom"),
            ("past peak", "past_peak"),
            ("blooming", "blooming"),
            ("opening", "opening"),
            ("approaching", "approaching"),
            ("not yet", "not_yet"),
        ]:
            if keyword in text_lower:
                logger.info("    🌸 检测到全局状态关键词: %s", status)
                break

    async def crawl_koyo_forecast(self) -> List[Dict[str, Any]]:
        """采集红叶前线预测"""
        url = f"{self.JG_BASE}/e/e2015.html"
        logger.info("🍁 采集红叶前线预测")

        html = await self.fetch_text(url, referer=self.JG_BASE)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        results = []

        for row in soup.select("table tr, .spot_list li, [class*='koyo']"):
            try:
                name_el = row.select_one("a")
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                link = name_el.get("href", "")
                if link and not link.startswith("http"):
                    link = self.JG_BASE + link

                text = row.get_text(strip=True)
                city_code = self._infer_city(text, name)

                status = ""
                for keyword in ["peak", "approaching", "past peak", "green"]:
                    if keyword in text.lower():
                        status = keyword
                        break

                results.append({
                    "name_en": name,
                    "name_zh": "",
                    "city_code": city_code,
                    "event_type": "koyo",
                    "status": status,
                    "source_url": link,
                    "source": "japan-guide",
                    "crawled_at": datetime.utcnow().isoformat(),
                })
            except Exception:
                continue

        logger.info(f"  ✅ {len(results)} 个红叶景点")
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # 批量采集
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_all(
        self,
        months_ahead: int = 6,
        include_sakura: bool = True,
        include_koyo: bool = True,
        save_json: bool = True,
    ) -> Dict[str, Any]:
        """全量采集"""
        logger.info(f"📅 开始活动日历采集 (未来 {months_ahead} 个月)")

        all_events = []

        # 月度活动
        today = date.today()
        for m in range(months_ahead):
            target = date(today.year, today.month, 1)
            # 简单月份递增
            month = (today.month + m - 1) % 12 + 1
            year = today.year + (today.month + m - 1) // 12

            events = await self.crawl_jg_event_calendar(year, month)
            all_events.extend(events)

        # 樱花
        if include_sakura:
            sakura = await self.crawl_sakura_forecast()
            all_events.extend(sakura)

        # 红叶
        if include_koyo:
            koyo = await self.crawl_koyo_forecast()
            all_events.extend(koyo)

        # 保存
        if save_json and all_events:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.output_dir / f"events_{ts}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "meta": {
                        "crawled_at": datetime.utcnow().isoformat(),
                        "total_events": len(all_events),
                        "by_type": self._count_by_type(all_events),
                    },
                    "events": all_events,
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 已保存: {filepath}")

        # 摘要
        by_type = self._count_by_type(all_events)
        print(f"\n{'='*50}")
        print(f"📅 活动采集完成 | 共 {len(all_events)} 条")
        print(f"-" * 50)
        for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
            emoji = {"sakura": "🌸", "koyo": "🍁", "fireworks": "🎆",
                     "festival": "⛩️", "illumination": "✨", "food": "🍜",
                     "market": "🛍️", "snow": "❄️"}.get(t, "📌")
            print(f"  {emoji} {t:16s} {c:>4d} 条")
        print(f"{'='*50}")

        return {"events": all_events, "stats": by_type}

    # ─────────────────────────────────────────────────────────────────────────
    # 辅助方法
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_date_range(text: str, year: int, month: int) -> tuple:
        """解析日期文本"""
        if not text:
            return None, None

        # "March 15 - April 5" 格式
        range_match = re.search(
            r'(\w+)\s+(\d{1,2})\s*[-–~to]+\s*(\w+)?\s*(\d{1,2})',
            text, re.IGNORECASE
        )
        if range_match:
            m1_name = range_match.group(1).lower()
            d1 = int(range_match.group(2))
            m2_name = (range_match.group(3) or range_match.group(1)).lower()
            d2 = int(range_match.group(4))

            m1 = MONTH_NAMES.get(m1_name, month)
            m2 = MONTH_NAMES.get(m2_name, m1)

            try:
                start = f"{year}-{m1:02d}-{d1:02d}"
                y2 = year + 1 if m2 < m1 else year
                end = f"{y2}-{m2:02d}-{d2:02d}"
                return start, end
            except Exception:
                pass

        # 单日期 "April 15"
        single_match = re.search(r'(\w+)\s+(\d{1,2})', text, re.IGNORECASE)
        if single_match:
            m_name = single_match.group(1).lower()
            d = int(single_match.group(2))
            m = MONTH_NAMES.get(m_name, month)
            try:
                dt = f"{year}-{m:02d}-{d:02d}"
                return dt, dt
            except Exception:
                pass

        return None, None

    @staticmethod
    def _infer_city(text: str, name: str = "") -> Optional[str]:
        """从文本推断城市"""
        combined = f"{text} {name}".lower()
        city_keywords = {
            "tokyo": ["tokyo", "東京", "asakusa", "shibuya", "shinjuku", "ueno", "ginza", "akihabara"],
            "osaka": ["osaka", "大阪", "dotonbori", "namba", "umeda", "tennoji"],
            "kyoto": ["kyoto", "京都", "gion", "arashiyama", "fushimi", "kiyomizu"],
            "nara": ["nara", "奈良", "todaiji"],
            "hakone": ["hakone", "箱根"],
            "sapporo": ["sapporo", "札幌", "hokkaido", "北海道"],
            "fukuoka": ["fukuoka", "福岡", "hakata"],
            "okinawa": ["okinawa", "沖縄", "naha"],
            "kamakura": ["kamakura", "鎌倉"],
            "kanazawa": ["kanazawa", "金沢"],
            "kobe": ["kobe", "神戸"],
            "nagoya": ["nagoya", "名古屋"],
            "yokohama": ["yokohama", "横浜"],
        }

        for city, keywords in city_keywords.items():
            if any(k in combined for k in keywords):
                return city
        return None

    @staticmethod
    def _count_by_type(events: list) -> dict:
        from collections import Counter
        return dict(Counter(e.get("event_type", "other") for e in events))
