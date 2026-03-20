"""
JNTOCrawler — 日本官方旅游数据采集器 (第一层: 官方真相源)
==========================================================
覆盖:
  - JNTO (japan.travel)  : 全国目的地骨架、区域介绍、季节线路
  - GO TOKYO (gotokyo.org): 东京景点、活动日历、季节指南
  - 扩展预留: Kyoto Travel, OSAKA-INFO

数据类型:
  - destinations : 目的地 (region/prefecture/city 三级)
  - spots        : 景点 (名称/地址/营业时间/描述/标签/坐标)
  - events       : 活动 (日期/地点/描述)
  - guides       : 季节/月份指南

用法:
  async with JNTOCrawler() as crawler:
      # 全国目的地骨架
      destinations = await crawler.crawl_jnto_destinations()

      # 东京景点
      spots = await crawler.crawl_gotokyo_spots(limit=50)

      # 东京活动日历
      events = await crawler.crawl_gotokyo_events()

      # 一键全抓
      all_data = await crawler.crawl_all()
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .base import BaseCrawler

logger = logging.getLogger(__name__)


class JNTOCrawler(BaseCrawler):
    """
    日本官方旅游站爬虫。

    采集 JNTO 全国目的地骨架和 GO TOKYO 东京景点/活动数据。
    纯 HTTP 模式（不需要 Playwright），所有页面都是 SSR。
    """

    JNTO_BASE = "https://www.japan.travel"
    GOTOKYO_BASE = "https://www.gotokyo.org"

    # GO TOKYO 已知景点 ID → 名称映射（首批种子）
    _SEED_SPOTS = [
        6, 4, 15, 76, 20, 118, 417,   # Skytree, Tower, Sensoji, Meiji, Hamarikyu, Stadium, Museum
    ]

    # JNTO 区域
    _REGIONS = [
        "hokkaido", "tohoku", "kanto", "hokuriku-shinetsu",
        "tokai", "kansai", "chugoku", "shikoku", "kyushu", "okinawa",
    ]

    def __init__(
        self,
        output_dir: str = "data/raw/official",
        language: str = "en",
        **kwargs,
    ):
        super().__init__(
            delay_range=(1.0, 3.0),
            **kwargs,
        )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.language = language

    # ─────────────────────────────────────────────────────────────────────────
    # JNTO: 全国目的地骨架
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_jnto_destinations(self) -> List[Dict[str, Any]]:
        """
        从 JNTO destinations 页面抓取全国目的地三级结构。

        返回:
            [{
                "region": "kanto",
                "prefecture": "tokyo",
                "city": "ginza-and-nihombashi",
                "name": "Ginza & Nihombashi",
                "url": "/en/destinations/kanto/tokyo/ginza-and-nihombashi/",
                "level": "city",     # region / prefecture / city
                "source": "jnto"
            }, ...]
        """
        logger.info("🏯 JNTO: 抓取全国目的地骨架...")

        url = f"{self.JNTO_BASE}/{self.language}/destinations/"
        html = await self.fetch_text(url)
        if not html:
            logger.warning("❌ 无法获取 JNTO destinations 页面")
            return []

        soup = BeautifulSoup(html, "html.parser")
        # 提取所有 destinations/ 链接
        raw_links = set()
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if "destinations/" in href and href.strip("/") != "destinations":
                # 规范化: 去除域名前缀
                path = href.replace(f"{self.JNTO_BASE}/{self.language}/", "")
                path = path.replace(f"/{self.language}/", "")
                if path.startswith("destinations/"):
                    raw_links.add(path.strip("/"))

        # 解析三级结构
        destinations = []
        for path in sorted(raw_links):
            parts = path.replace("destinations/", "").strip("/").split("/")
            parts = [p for p in parts if p]
            if not parts:
                continue

            region = parts[0] if len(parts) >= 1 else None
            prefecture = parts[1] if len(parts) >= 2 else None
            city = parts[2] if len(parts) >= 3 else None

            # 确定层级
            if city:
                level = "city"
                name = city.replace("-", " ").replace("and", "&").title()
            elif prefecture:
                level = "prefecture"
                name = prefecture.replace("-", " ").title()
            else:
                level = "region"
                name = region.replace("-", " ").title()

            destinations.append({
                "region": region,
                "prefecture": prefecture,
                "city": city,
                "name": name,
                "url": f"/{self.language}/{path}/",
                "level": level,
                "source": "jnto",
                "crawled_at": datetime.utcnow().isoformat(),
            })

        # 统计
        regions = len(set(d["region"] for d in destinations if d["region"]))
        prefs = len([d for d in destinations if d["level"] == "prefecture"])
        cities = len([d for d in destinations if d["level"] == "city"])
        logger.info(f"   ✅ {len(destinations)} 目的地: {regions} 区域, {prefs} 都道府県, {cities} 城市")

        self._save_json("jnto_destinations", destinations)
        return destinations

    async def crawl_jnto_destination_detail(self, path: str) -> Optional[Dict[str, Any]]:
        """抓取单个目的地页面的详细信息。"""
        url = f"{self.JNTO_BASE}/{self.language}/{path.strip('/')}/"
        html = await self.fetch_text(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # 描述
        desc_el = soup.select_one(".mod-keyvisual__description")
        description = desc_el.get_text(strip=True) if desc_el else None

        # 交通信息
        transport_el = soup.select_one(".mod-wysiwyg__howto-get-there-content")
        transport = transport_el.get_text(strip=True) if transport_el else None

        # 主图
        hero_img = soup.select_one(".mod-keyvisual__image-content--pc img")
        image_url = None
        if hero_img:
            image_url = hero_img.get("src") or hero_img.get("data-src")
            if image_url and not image_url.startswith("http"):
                image_url = f"{self.JNTO_BASE}{image_url}"

        return {
            "url": url,
            "description": description,
            "transport": transport,
            "image_url": image_url,
            "source": "jnto",
            "crawled_at": datetime.utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # GO TOKYO: 景点
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_gotokyo_spots(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        从 GO TOKYO 抓取东京景点数据。

        策略: 先从分类页收集景点 URL/ID，再逐个抓取详情页。
        """
        logger.info("🗼 GO TOKYO: 抓取东京景点...")

        # 1. 收集景点 ID
        spot_ids = set(self._SEED_SPOTS)
        category_pages = [
            "/en/see-and-do/attractions/index.html",
            "/en/see-and-do/drinking-and-dining/index.html",
            "/en/see-and-do/culture/index.html",
            "/en/see-and-do/arts-and-design/index.html",
            "/en/see-and-do/shopping/index.html",
            "/en/see-and-do/nature/index.html",
            "/en/see-and-do/nightlife/index.html",
            "/en/see-and-do/onsen-and-bathhouses/index.html",
        ]

        for page_path in category_pages:
            url = f"{self.GOTOKYO_BASE}{page_path}"
            html = await self.fetch_text(url)
            if not html:
                continue

            # 从页面中提取 /spot/数字/ 模式
            ids = re.findall(r"/spot/(\d+)/", html)
            for sid in ids:
                spot_ids.add(int(sid))

            await self._random_delay()

        # 也从 destinations 子页面收集
        dest_pages = [
            "/en/destinations/central-tokyo/index.html",
            "/en/destinations/western-tokyo/index.html",
            "/en/destinations/northern-tokyo/index.html",
            "/en/destinations/waterfront/index.html",
        ]
        for page_path in dest_pages:
            url = f"{self.GOTOKYO_BASE}{page_path}"
            html = await self.fetch_text(url)
            if html:
                ids = re.findall(r"/spot/(\d+)/", html)
                for sid in ids:
                    spot_ids.add(int(sid))
                await self._random_delay()

        logger.info(f"   发现 {len(spot_ids)} 个景点 ID, 抓取前 {limit} 个...")

        # 2. 逐个抓取详情
        spots = []
        for sid in sorted(spot_ids)[:limit]:
            try:
                spot = await self._crawl_gotokyo_spot_detail(sid)
                if spot:
                    spots.append(spot)
                    logger.debug(f"   ✅ [{sid}] {spot.get('name_en', '')[:40]}")
            except Exception as e:
                logger.warning(f"   ⚠️ spot/{sid} 失败: {e}")
            await self._random_delay()

        logger.info(f"   ✅ 共抓取 {len(spots)} 个景点")
        self._save_json("gotokyo_spots", spots)
        return spots

    async def _crawl_gotokyo_spot_detail(self, spot_id: int) -> Optional[Dict[str, Any]]:
        """抓取单个 GO TOKYO 景点详情页。"""
        url = f"{self.GOTOKYO_BASE}/en/spot/{spot_id}/index.html"
        html = await self.fetch_text(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # 名称 (英文 + 日文)
        h1 = soup.select_one("h1")
        full_name = h1.get_text(strip=True) if h1 else ""
        # 拆分英日文: "Tokyo Skytree東京スカイツリー®"
        # 日文通常在最后
        name_en = re.sub(r"[\u3000-\u9fff\uff00-\uffef®]+$", "", full_name).strip()
        name_ja_match = re.search(r"([\u3000-\u9fff\uff00-\uffef®]+)$", full_name)
        name_ja = name_ja_match.group(1) if name_ja_match else None

        if not name_en:
            name_en = full_name

        # 地址
        address = None
        addr_el = soup.select_one('[class*="address"]')
        if addr_el:
            address = addr_el.get_text(strip=True)

        # 营业时间
        hours = None
        hours_el = soup.select_one('[class*="hours"], [class*="time"]')
        if hours_el:
            raw = hours_el.get_text(strip=True)
            # 清理: 去掉重复的星期名
            hours = self._clean_hours(raw)

        # 描述
        description = None
        desc_el = soup.select_one(".mod-keyvisual__description, .spot-description, [class*=description]")
        if not desc_el:
            # 尝试找第一个 <p> 标签
            p_tags = soup.select(".content-main-wrapper p")
            if p_tags:
                desc_el = p_tags[0]
        if desc_el:
            description = desc_el.get_text(strip=True)[:500]

        # 图片
        images = []
        for img in soup.select("img[src*=spot], img[data-src*=spot]"):
            src = img.get("src") or img.get("data-src", "")
            if src and "dummy" not in src:
                if not src.startswith("http"):
                    src = f"{self.GOTOKYO_BASE}{src}"
                images.append(src)

        # 标签
        tags = []
        tag_els = soup.select('[class*="tag"], [class*="category"]')
        for t in tag_els:
            text = t.get_text(strip=True)
            # 拆分 "#tag1#tag2" 格式
            for tag in text.split("#"):
                tag = tag.strip()
                if tag and tag not in tags and len(tag) < 50:
                    tags.append(tag)

        # JSON-LD 结构化数据
        lat, lng = None, None
        ld_scripts = soup.select('script[type="application/ld+json"]')
        for script in ld_scripts:
            try:
                ld = json.loads(script.string)
                if isinstance(ld, dict):
                    geo = ld.get("geo", {})
                    if geo:
                        lat = geo.get("latitude")
                        lng = geo.get("longitude")
                    if not address:
                        addr_obj = ld.get("address", {})
                        if isinstance(addr_obj, dict):
                            address = addr_obj.get("streetAddress")
            except (json.JSONDecodeError, TypeError):
                continue

        # 门票/费用
        fee = None
        fee_el = soup.select_one('[class*="fee"], [class*="price"], [class*="admission"]')
        if fee_el:
            fee = fee_el.get_text(strip=True)[:200]

        return {
            "id": f"gotokyo_{spot_id}",
            "spot_id": spot_id,
            "name_en": name_en,
            "name_ja": name_ja,
            "description": description,
            "address": address,
            "latitude": lat,
            "longitude": lng,
            "hours": hours,
            "fee": fee,
            "tags": tags,
            "images": images[:5],
            "city": "tokyo",
            "url": url,
            "source": "gotokyo",
            "crawled_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _clean_hours(raw: str) -> str:
        """清理营业时间文本 (去重复星期名等)。"""
        # "10:00-22:00MondaysTuesdaysWednesdaysThursdaysFridays9:00-22:00SaturdaysSundaysHolidays"
        # → "Mon-Fri 10:00-22:00, Sat-Sun 9:00-22:00"
        # 简单清理：在时间前加换行
        cleaned = re.sub(r"(\d{1,2}:\d{2}-\d{1,2}:\d{2})", r"\n\1", raw)
        cleaned = re.sub(r"(Mondays?|Tuesdays?|Wednesdays?|Thursdays?|Fridays?|Saturdays?|Sundays?|Holidays?)", r" \1", cleaned)
        return cleaned.strip()[:300]

    # ─────────────────────────────────────────────────────────────────────────
    # GO TOKYO: 活动日历
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_gotokyo_events(self) -> List[Dict[str, Any]]:
        """从 GO TOKYO calendar 页面抓取活动列表。"""
        logger.info("📅 GO TOKYO: 抓取活动日历...")

        url = f"{self.GOTOKYO_BASE}/en/calendar/index.html"
        html = await self.fetch_text(url)
        if not html:
            logger.warning("❌ 无法获取 GO TOKYO calendar 页面")
            return []

        soup = BeautifulSoup(html, "html.parser")
        events = []

        # 查找活动链接
        event_links = soup.select('a[href*="/event/"]')
        seen_urls = set()

        for link in event_links:
            href = link.get("href", "")
            if href in seen_urls:
                continue
            seen_urls.add(href)

            text = link.get_text(strip=True)
            if not text or len(text) < 5:
                continue

            # 解析日期和标题
            # 格式: "May 22, 2025 - Mar 31, 2026Free Cultural Experiences..."
            date_match = re.match(
                r"(\w+ \d{1,2},\s*\d{4})\s*-\s*(\w+ \d{1,2},\s*\d{4})(.*)",
                text,
            )
            if date_match:
                start_date_str = date_match.group(1)
                end_date_str = date_match.group(2)
                title = date_match.group(3).strip()
            else:
                # 尝试单日期
                single_match = re.match(r"(\w+ \d{1,2},\s*\d{4})(.*)", text)
                if single_match:
                    start_date_str = single_match.group(1)
                    end_date_str = None
                    title = single_match.group(2).strip()
                else:
                    title = text
                    start_date_str = None
                    end_date_str = None

            # 规范化 URL
            full_url = href if href.startswith("http") else f"{self.GOTOKYO_BASE}{href}"

            events.append({
                "title": title,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "url": full_url,
                "city": "tokyo",
                "source": "gotokyo",
                "crawled_at": datetime.utcnow().isoformat(),
            })

        logger.info(f"   ✅ {len(events)} 个活动")
        self._save_json("gotokyo_events", events)
        return events

    async def crawl_gotokyo_event_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """抓取单个活动详情页。"""
        html = await self.fetch_text(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        h1 = soup.select_one("h1")
        title = h1.get_text(strip=True) if h1 else None

        desc_el = soup.select_one('[class*="description"], [class*="detail"], .content-main-wrapper p')
        description = desc_el.get_text(strip=True)[:500] if desc_el else None

        venue_el = soup.select_one('[class*="venue"], [class*="place"], [class*="location"]')
        venue = venue_el.get_text(strip=True) if venue_el else None

        return {
            "title": title,
            "description": description,
            "venue": venue,
            "url": url,
            "source": "gotokyo",
            "crawled_at": datetime.utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # GO TOKYO: 季节/月份指南
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_gotokyo_guides(self) -> List[Dict[str, Any]]:
        """抓取 GO TOKYO 的季节和月份指南。"""
        logger.info("🌸 GO TOKYO: 抓取季节指南...")

        guide_paths = [
            # 季节指南
            ("spring", "/en/story/guide/spring/index.html"),
            ("summer", "/en/story/guide/summer/index.html"),
            ("autumn", "/en/story/guide/autumn/index.html"),
            ("winter", "/en/story/guide/winter/index.html"),
            # 月份指南
            ("january", "/en/story/guide/january/index.html"),
            ("february", "/en/story/guide/february/index.html"),
            ("march", "/en/story/guide/march/index.html"),
            ("april", "/en/story/guide/april/index.html"),
            ("june", "/en/story/guide/june/index.html"),
            ("july", "/en/story/guide/july/index.html"),
            ("august", "/en/story/guide/august/index.html"),
            ("september", "/en/story/guide/september/index.html"),
            ("october", "/en/story/guide/october/index.html"),
            ("november", "/en/story/guide/november/index.html"),
            ("december", "/en/story/guide/december/index.html"),
        ]

        guides = []
        for name, path in guide_paths:
            url = f"{self.GOTOKYO_BASE}{path}"
            html = await self.fetch_text(url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            h1 = soup.select_one("h1")
            title = h1.get_text(strip=True) if h1 else name.title()

            # 提取主要文本内容
            content_parts = []
            for p in soup.select(".content-main-wrapper p, .mod-wysiwyg p"):
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    content_parts.append(text)

            # 提取推荐景点 ID
            spot_ids = list(set(int(s) for s in re.findall(r"/spot/(\d+)/", html)))

            # 提取推荐活动链接
            event_links = re.findall(r'href="(/en/event/[^"]+)"', html)

            # 季节判断
            season = None
            if name in ("spring", "march", "april"):
                season = "spring"
            elif name in ("summer", "june", "july", "august"):
                season = "summer"
            elif name in ("autumn", "september", "october", "november"):
                season = "autumn"
            elif name in ("winter", "december", "january", "february"):
                season = "winter"

            guides.append({
                "id": f"gotokyo_guide_{name}",
                "name": name,
                "title": title,
                "season": season,
                "content_summary": "\n".join(content_parts[:5])[:1000],
                "recommended_spot_ids": spot_ids,
                "recommended_events": event_links,
                "city": "tokyo",
                "url": url,
                "source": "gotokyo",
                "crawled_at": datetime.utcnow().isoformat(),
            })

            await self._random_delay()

        logger.info(f"   ✅ {len(guides)} 份指南")
        self._save_json("gotokyo_guides", guides)
        return guides

    # ─────────────────────────────────────────────────────────────────────────
    # 一键全抓
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_all(
        self,
        spots_limit: int = 50,
        include_details: bool = False,
    ) -> Dict[str, Any]:
        """
        一键抓取所有官方数据。

        参数:
            spots_limit: 景点最大数量
            include_details: 是否抓取目的地详情页（慢）
        """
        logger.info("🇯🇵 开始抓取日本官方旅游数据...")
        logger.info("=" * 60)

        results = {}

        # 1. JNTO 全国目的地骨架
        results["destinations"] = await self.crawl_jnto_destinations()

        # 2. GO TOKYO 景点
        results["spots"] = await self.crawl_gotokyo_spots(limit=spots_limit)

        # 3. GO TOKYO 活动
        results["events"] = await self.crawl_gotokyo_events()

        # 4. GO TOKYO 季节指南
        results["guides"] = await self.crawl_gotokyo_guides()

        # 汇总
        logger.info("=" * 60)
        logger.info("📊 官方数据采集汇总:")
        for key, data in results.items():
            logger.info(f"   {key}: {len(data)} 条")

        return results

    # ─────────────────────────────────────────────────────────────────────────
    # 工具方法
    # ─────────────────────────────────────────────────────────────────────────

    def _save_json(self, name: str, data: list) -> None:
        """保存数据到 JSON 文件。"""
        filepath = self.output_dir / f"{name}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"   💾 保存到 {filepath} ({len(data)} 条)")
