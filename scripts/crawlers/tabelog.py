"""
TabelogCrawler — Tabelog 餐厅数据采集器
=========================================
基于 BaseCrawler，实现 Tabelog 列表页 + 详情页的完整采集。

数据源：https://tabelog.com
采集字段：
  列表页 → 名称、评分、价格区间、菜系、区域、评论数、链接
  详情页 → 地址、坐标、营业时间、座位数、是否需要预约、图片URL、电话

策略：
  1. 先访问首页预热 Cookie
  2. 逐页采集列表页
  3. 按需抓取详情页（可配置是否启用）
  4. 请求间随机延迟 2-5 秒（Tabelog 较严格）
  5. 数据落盘到 JSON 文件 + 可选写入 DB

用法：
  # 作为模块
  async with TabelogCrawler() as crawler:
      restaurants = await crawler.crawl_city("tokyo", cuisines=["sushi"])

  # 通过 CLI
  python scripts/tabelog_crawl.py --city tokyo --cuisine sushi --pages 3
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from scripts.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

# ── 城市代码 → Tabelog URL 前缀映射 ──────────────────────────────────────────

TABELOG_AREA_MAP: Dict[str, Dict[str, str]] = {
    # 城市代码 → { prefix: URL路径, name_ja: 日文名 }
    "tokyo":     {"prefix": "tokyo",            "name_ja": "東京"},
    "osaka":     {"prefix": "osaka",            "name_ja": "大阪"},
    "kyoto":     {"prefix": "kyoto",            "name_ja": "京都"},
    "nara":      {"prefix": "nara",             "name_ja": "奈良"},
    "sapporo":   {"prefix": "hokkaido/A0101",   "name_ja": "札幌"},
    "fukuoka":   {"prefix": "fukuoka/A4001",    "name_ja": "福岡"},
    "hiroshima": {"prefix": "hiroshima/A3401",  "name_ja": "広島"},
    "naha":      {"prefix": "okinawa/A4701",    "name_ja": "那覇"},
    "kanazawa":  {"prefix": "ishikawa/A1701",   "name_ja": "金沢"},
    "hakone":    {"prefix": "kanagawa/A1410",   "name_ja": "箱根"},
    "kamakura":  {"prefix": "kanagawa/A1407",   "name_ja": "鎌倉"},
    "kobe":      {"prefix": "hyogo/A2801",      "name_ja": "神戸"},
    "nagoya":    {"prefix": "aichi/A2301",      "name_ja": "名古屋"},
    "yokohama":  {"prefix": "kanagawa/A1401",   "name_ja": "横浜"},
    "sendai":    {"prefix": "miyagi/A0401",     "name_ja": "仙台"},
}

# ── 菜系 → Tabelog 分类代码 ──────────────────────────────────────────────────

TABELOG_CUISINE_MAP: Dict[str, Dict[str, str]] = {
    # cuisine_code → { code: Tabelog分类码, name_ja: 日文名, name_zh: 中文名 }
    "sushi":     {"code": "RC020101", "name_ja": "寿司",        "name_zh": "寿司"},
    "ramen":     {"code": "RC040201", "name_ja": "ラーメン",    "name_zh": "拉面"},
    "kaiseki":   {"code": "RC010101", "name_ja": "懐石・会席",  "name_zh": "怀石料理"},
    "tempura":   {"code": "RC010301", "name_ja": "天ぷら",      "name_zh": "天妇罗"},
    "yakitori":  {"code": "RC010401", "name_ja": "焼鳥",        "name_zh": "烧鸟"},
    "wagyu":     {"code": "RC010601", "name_ja": "焼肉・ステーキ", "name_zh": "和牛/牛排"},
    "izakaya":   {"code": "RC030101", "name_ja": "居酒屋",      "name_zh": "居酒屋"},
    "udon":      {"code": "RC040101", "name_ja": "うどん",      "name_zh": "乌冬面"},
    "soba":      {"code": "RC040102", "name_ja": "そば",        "name_zh": "荞麦面"},
    "seafood":   {"code": "RC020201", "name_ja": "海鮮",        "name_zh": "海鲜"},
    "tonkatsu":  {"code": "RC010501", "name_ja": "とんかつ",    "name_zh": "炸猪排"},
    "curry":     {"code": "RC040301", "name_ja": "カレー",      "name_zh": "咖喱"},
    "unagi":     {"code": "RC020301", "name_ja": "うなぎ",      "name_zh": "鳗鱼"},
    "okonomiyaki": {"code": "RC041101", "name_ja": "お好み焼き", "name_zh": "大阪烧"},
    "cafe":      {"code": "RC050201", "name_ja": "カフェ",      "name_zh": "咖啡馆"},
}

# Tabelog 排序选项
TABELOG_SORT = {
    "score":    "s2",  # 按评分排序（默认推荐）
    "review":   "s1",  # 按评论数排序
    "new":      "s4",  # 按新开业排序
}


class TabelogCrawler(BaseCrawler):
    """
    Tabelog 餐厅爬虫。

    Args:
        fetch_detail:  是否抓取详情页（更完整但更慢）
        sort_by:       排序方式 ("score" / "review" / "new")
        output_dir:    JSON 落盘目录
        **kwargs:      传递给 BaseCrawler 的参数
    """

    BASE_URL = "https://tabelog.com"

    def __init__(
        self,
        fetch_detail: bool = True,
        sort_by: str = "score",
        output_dir: str = "data/tabelog_raw",
        **kwargs: Any,
    ) -> None:
        # Tabelog 反爬较严格，默认延迟 2-5 秒
        kwargs.setdefault("delay_range", (2.0, 5.0))
        kwargs.setdefault("max_retries", 3)
        kwargs.setdefault("max_concurrent", 1)  # 串行！并发会被封

        super().__init__(**kwargs)
        self.fetch_detail = fetch_detail
        self.sort_code = TABELOG_SORT.get(sort_by, "s2")
        self.output_dir = Path(output_dir)

    async def before_crawl(self) -> None:
        """预热：访问 Tabelog 首页获取初始 Cookie"""
        logger.info("🔥 预热：访问 Tabelog 首页获取 Cookie ...")
        resp = await self.fetch(
            self.BASE_URL,
            referer="https://www.google.com/",
        )
        if resp:
            logger.info(f"✅ Cookie 预热成功 (cookies: {len(resp.cookies)})")
        else:
            logger.warning("⚠️  首页访问失败，继续尝试...")

    # ─────────────────────────────────────────────────────────────────────────
    # 列表页
    # ─────────────────────────────────────────────────────────────────────────

    def _build_list_url(
        self,
        city_code: str,
        cuisine: str = "",
        page: int = 1,
    ) -> str:
        """构建列表页 URL"""
        area = TABELOG_AREA_MAP.get(city_code, {})
        prefix = area.get("prefix", city_code)

        cuisine_info = TABELOG_CUISINE_MAP.get(cuisine, {})
        cuisine_code = cuisine_info.get("code", "")

        # URL 格式: /tokyo/rstLst/RC020101/1/?Srt=D&SrtT=rt&sort_mode=1
        parts = [self.BASE_URL, prefix, "rstLst"]
        if cuisine_code:
            parts.append(cuisine_code)
        parts.append(f"{page}/")

        url = "/".join(parts)

        # 按评分排序
        if self.sort_code:
            url += f"?Srt=D&SrtT={self.sort_code}&sort_mode=1"

        return url

    async def crawl_list_page(
        self,
        city_code: str,
        cuisine: str = "",
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        采集单个列表页。

        Returns:
            餐厅基础数据列表（通常 20 条/页）
        """
        url = self._build_list_url(city_code, cuisine, page)
        logger.info(f"📄 列表页: city={city_code} cuisine={cuisine} page={page}")
        logger.debug(f"   URL: {url}")

        html = await self.fetch_text(url, referer=f"{self.BASE_URL}/{TABELOG_AREA_MAP.get(city_code, {}).get('prefix', city_code)}/")
        if not html:
            return []

        return self._parse_list_page(html, city_code, cuisine)

    def _parse_list_page(
        self,
        html: str,
        city_code: str,
        cuisine: str,
    ) -> List[Dict[str, Any]]:
        """解析列表页 HTML，提取餐厅卡片"""
        soup = BeautifulSoup(html, "html.parser")
        results: List[Dict[str, Any]] = []

        # Tabelog 餐厅卡片选择器（多种可能的 class）
        cards = soup.select("div.list-rst") or soup.select("li.list-rst__item")

        if not cards:
            # 备用选择器
            cards = soup.select("[class*='list-rst']")
            logger.debug(f"   使用备用选择器，找到 {len(cards)} 张卡片")

        for card in cards:
            try:
                item = self._parse_list_card(card, city_code, cuisine)
                if item:
                    results.append(item)
            except Exception as e:
                logger.debug(f"   解析卡片失败: {e}")
                continue

        logger.info(f"   ✅ 解析到 {len(results)} 家餐厅")
        return results

    def _parse_list_card(
        self,
        card: Any,
        city_code: str,
        cuisine: str,
    ) -> Optional[Dict[str, Any]]:
        """解析单张餐厅卡片"""

        # ── 餐厅名称 & 链接 ──
        name_el = (
            card.select_one(".list-rst__rst-name-target")
            or card.select_one("a.list-rst__rst-name-target")
            or card.select_one("[class*='rst-name'] a")
        )
        if not name_el:
            return None

        name_ja = name_el.get_text(strip=True)
        if not name_ja:
            return None

        detail_url = name_el.get("href", "")
        if detail_url and not detail_url.startswith("http"):
            detail_url = self.BASE_URL + detail_url

        # ── Tabelog ID ──
        tabelog_id = self._extract_id(detail_url)

        # ── 评分 ──
        score = self._parse_score(card)

        # ── 价格 (午餐/晚餐) ──
        price_lunch, price_dinner = self._parse_budget(card)

        # ── 菜系标签 ──
        cuisine_el = (
            card.select_one(".list-rst__catg")
            or card.select_one("[class*='category']")
        )
        cuisine_raw = cuisine_el.get_text(strip=True) if cuisine_el else ""

        # ── 区域 ──
        area_el = (
            card.select_one(".list-rst__area-genre")
            or card.select_one("[class*='area']")
        )
        area_text = area_el.get_text(strip=True) if area_el else ""
        # 提取区域名（去掉菜系部分）
        district = area_text.split("/")[0].strip() if "/" in area_text else area_text

        # ── 评论数 ──
        review_count = 0
        review_el = card.select_one("[class*='review-count']") or card.select_one("[class*='total-count']")
        if review_el:
            nums = re.findall(r'\d+', review_el.get_text())
            if nums:
                review_count = int(nums[0])

        # ── 图片 ──
        img_el = card.select_one("img.list-rst__photo-img") or card.select_one("[class*='photo'] img")
        image_url = ""
        if img_el:
            image_url = img_el.get("data-original") or img_el.get("src") or ""

        # ── 保存标记 ──
        save_el = card.select_one("[class*='save-count']")
        save_count = 0
        if save_el:
            nums = re.findall(r'\d+', save_el.get_text())
            if nums:
                save_count = int(nums[0])

        self.stats.items_scraped += 1

        return {
            # 基础信息
            "name_ja": name_ja,
            "name_zh": "",
            "name_en": "",
            "city_code": city_code,
            "cuisine_query": cuisine,
            "cuisine_raw": cuisine_raw,
            # Tabelog 特有
            "tabelog_id": tabelog_id,
            "tabelog_url": detail_url,
            "tabelog_score": score,
            "tabelog_review_count": review_count,
            "tabelog_save_count": save_count,
            # 价格
            "price_lunch_jpy": price_lunch,
            "price_dinner_jpy": price_dinner,
            # 区域
            "district": district,
            # 图片
            "image_url": image_url,
            # 元数据
            "source": "tabelog",
            "crawled_at": datetime.utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 详情页
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_detail_page(
        self,
        restaurant: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        抓取餐厅详情页，补充完整信息。

        Args:
            restaurant: 列表页采集的基础数据

        Returns:
            合并后的完整数据
        """
        url = restaurant.get("tabelog_url", "")
        if not url:
            return restaurant

        logger.info(f"   🔍 详情页: {restaurant.get('name_ja', '?')}")

        html = await self.fetch_text(
            url,
            referer=self._build_list_url(restaurant.get("city_code", ""), restaurant.get("cuisine_query", "")),
        )
        if not html:
            return restaurant

        detail = self._parse_detail_page(html)
        # 合并：详情页数据覆盖（补充缺失字段）
        for key, val in detail.items():
            if val is not None and val != "" and val != 0:
                restaurant[key] = val

        return restaurant

    def _parse_detail_page(self, html: str) -> Dict[str, Any]:
        """解析详情页 HTML"""
        soup = BeautifulSoup(html, "html.parser")
        result: Dict[str, Any] = {}

        # ── 地址 ──
        addr_el = (
            soup.select_one(".rstinfo-table__address")
            or soup.select_one("[class*='address'] p")
            or soup.select_one("p.rstinfo-table__address")
        )
        if addr_el:
            result["address_ja"] = addr_el.get_text(strip=True)

        # ── 电话号码 ──
        tel_el = (
            soup.select_one(".rstinfo-table__tel-num-text")
            or soup.select_one("[class*='tel-num']")
        )
        if tel_el:
            result["phone"] = tel_el.get_text(strip=True)

        # ── 营业时间 ──
        hours_data = self._parse_opening_hours(soup)
        if hours_data:
            result["opening_hours_text"] = hours_data.get("text", "")
            result["opening_hours_json"] = hours_data.get("structured")

        # ── 定休日 ──
        holiday_el = soup.select_one("[class*='holiday']") or soup.find(
            "th", string=re.compile(r"定休日")
        )
        if holiday_el:
            td = holiday_el.find_next("td") if holiday_el.name == "th" else holiday_el
            if td:
                result["regular_holiday"] = td.get_text(strip=True)

        # ── 座位数 ──
        seat_el = soup.find("th", string=re.compile(r"席数"))
        if seat_el:
            td = seat_el.find_next("td")
            if td:
                nums = re.findall(r'\d+', td.get_text())
                if nums:
                    result["seating_count"] = int(nums[0])

        # ── 预约情况（详细解析）──
        self._parse_reservation_detail(soup, result)

        # ── 菜系（从详情页 ジャンル 获取更准确的分类）──
        genre_el = soup.find("th", string=re.compile(r"ジャンル"))
        if genre_el:
            td = genre_el.find_next("td")
            if td:
                result["cuisine_detail"] = td.get_text(strip=True)[:100]

        # ── 个室/包间 ──
        private_el = soup.find("th", string=re.compile(r"個室"))
        if private_el:
            td = private_el.find_next("td")
            if td:
                text = td.get_text(strip=True)
                result["has_private_room"] = "有" in text or "あり" in text

        # ── 禁烟 ──
        smoke_el = soup.find("th", string=re.compile(r"禁煙|喫煙"))
        if smoke_el:
            td = smoke_el.find_next("td")
            if td:
                text = td.get_text(strip=True)
                result["smoking_policy"] = text[:50]
                result["is_non_smoking"] = "全席禁煙" in text

        # ── 支付方式 ──
        pay_el = soup.find("th", string=re.compile(r"支払い"))
        if pay_el:
            td = pay_el.find_next("td")
            if td:
                result["payment_methods"] = td.get_text(strip=True)[:100]

        # ── 利用场景 ──
        scene_el = soup.find("th", string=re.compile(r"利用シーン"))
        if scene_el:
            td = scene_el.find_next("td")
            if td:
                result["usage_scene"] = td.get_text(strip=True)[:100]

        # ── 坐标（从 map 链接或 meta 标签提取）──
        lat, lng = self._extract_coordinates(soup)
        if lat and lng:
            result["lat"] = lat
            result["lng"] = lng

        # ── 最近车站 ──
        station_el = (
            soup.select_one(".rdheader-subinfo__item--station")
            or soup.select_one("[class*='station']")
        )
        if station_el:
            result["nearest_station"] = station_el.get_text(strip=True)

        # ── 图片集 ──
        images = self._extract_images(soup)
        if images:
            result["images"] = images

        # ── 米其林/百名店标记 ──
        awards = self._extract_awards(soup)
        if awards:
            result["awards"] = awards

        # ── 英文菜单 ──
        page_text = soup.get_text()
        result["has_english_menu"] = bool(
            re.search(r"英語メニュー|English\s*menu", page_text, re.IGNORECASE)
        )

        return result

    def _parse_reservation_detail(self, soup: BeautifulSoup, result: Dict[str, Any]) -> None:
        """
        详细解析预约信息，输出:
          reservation_info:       原始日文文本
          requires_reservation:   是否必须预约 (bool)
          reservation_difficulty: easy / medium / hard / impossible
          reservation_method:     phone / online / phone_online / referral / walk_in_only
          reservation_phone:      预约电话号码
          reservation_url:        在线预约链接 (如有)
          reservation_note_zh:    中文预约说明
          est_wait_min_peak:      高峰期预估排队(分钟)
          est_wait_min_offpeak:   非高峰预估排队(分钟)
          wait_note_zh:           排队提示
        """
        # ── 提取 予約可否 ──
        reserve_el = soup.find("th", string=re.compile(r"予約可否"))
        rsv_text = ""
        if reserve_el:
            td = reserve_el.find_next("td")
            if td:
                rsv_text = td.get_text(strip=True)
                result["reservation_info"] = rsv_text

        # ── 提取 予約・お問い合わせ (电话) ──
        phone_el = soup.find("th", string=re.compile(r"予約・お問い合わせ"))
        phone = ""
        if phone_el:
            td = phone_el.find_next("td")
            if td:
                phone_match = re.search(r'[\d\-]{8,15}', td.get_text())
                if phone_match:
                    phone = phone_match.group()
                    result["reservation_phone"] = phone

        # ── 检测在线预约按钮 ──
        online_btn = soup.select_one(
            'a[href*="yoyaku"], a[href*="reservation"], '
            'a[href*="ikyu.com"], a[href*="ozmall.co.jp"], '
            '.js-rstpage-rstinfo-online-reservation'
        )
        has_online = online_btn is not None
        if has_online and online_btn:
            href = online_btn.get("href", "")
            if href and href.startswith("http"):
                result["reservation_url"] = href

        # ── 判断预约难度 + 方式 ──
        rsv_lower = rsv_text.lower()
        if "紹介制" in rsv_text:
            result["requires_reservation"] = True
            result["reservation_difficulty"] = "impossible"
            result["reservation_method"] = "referral"
            result["reservation_note_zh"] = "完全预约制+需熟客介绍，普通游客基本无法预约"
        elif "完全予約制" in rsv_text or "要予約" in rsv_text:
            result["requires_reservation"] = True
            result["reservation_difficulty"] = "hard"
            if has_online and phone:
                result["reservation_method"] = "phone_online"
                result["reservation_note_zh"] = "完全预约制，可通过电话或在线平台预约"
            elif has_online:
                result["reservation_method"] = "online"
                result["reservation_note_zh"] = "完全预约制，可在线预约"
            elif phone:
                result["reservation_method"] = "phone"
                result["reservation_note_zh"] = f"完全预约制，需电话预约: {phone}"
            else:
                result["reservation_method"] = "phone"
                result["reservation_note_zh"] = "完全预约制，需提前预约"
        elif "予約不可" in rsv_text:
            result["requires_reservation"] = False
            result["reservation_difficulty"] = "none"
            result["reservation_method"] = "walk_in_only"
            result["reservation_note_zh"] = "不接受预约，只能现场排队"
        elif "予約可" in rsv_text:
            result["requires_reservation"] = False
            result["reservation_difficulty"] = "easy"
            if has_online and phone:
                result["reservation_method"] = "phone_online"
                result["reservation_note_zh"] = "可预约（电话或在线），也可直接到店"
            elif has_online:
                result["reservation_method"] = "online"
                result["reservation_note_zh"] = "可在线预约，也可直接到店"
            elif phone:
                result["reservation_method"] = "phone"
                result["reservation_note_zh"] = f"可电话预约: {phone}，也可直接到店"
            else:
                result["reservation_method"] = "phone"
                result["reservation_note_zh"] = "可预约，也可直接到店"
        else:
            result["requires_reservation"] = False
            result["reservation_difficulty"] = "unknown"
            result["reservation_method"] = "unknown"
            result["reservation_note_zh"] = ""

    @staticmethod
    def estimate_wait_time(
        tabelog_score: float,
        review_count: int,
        requires_reservation: bool,
        reservation_method: str,
        cuisine_type: str = "",
    ) -> Dict[str, Any]:
        """
        基于评分/热度/预约状态估算排队时间。

        返回:
          est_wait_min_peak:    高峰期预估排队(分钟)
          est_wait_min_offpeak: 非高峰预估排队(分钟)
          wait_note_zh:         中文提示
        """
        # 完全预约制 → 有预约就不用等
        if requires_reservation and reservation_method != "walk_in_only":
            return {
                "est_wait_min_peak": 0,
                "est_wait_min_offpeak": 0,
                "wait_note_zh": "预约制，有预约无需等待",
            }

        # 拉面/排队名店特殊处理
        is_ramen = "ramen" in cuisine_type.lower() or "ラーメン" in cuisine_type
        is_queue_type = is_ramen or reservation_method == "walk_in_only"

        # 基础等待时间 (基于评分)
        if tabelog_score >= 4.0:
            base_peak = 60 if is_queue_type else 30
            base_offpeak = 30 if is_queue_type else 10
        elif tabelog_score >= 3.8:
            base_peak = 40 if is_queue_type else 20
            base_offpeak = 15 if is_queue_type else 5
        elif tabelog_score >= 3.7:
            base_peak = 25 if is_queue_type else 15
            base_offpeak = 10 if is_queue_type else 0
        else:
            base_peak = 10
            base_offpeak = 0

        # 热度加成 (评论多 = 更火)
        if review_count > 500:
            base_peak = int(base_peak * 1.3)
            base_offpeak = int(base_offpeak * 1.2)
        elif review_count > 200:
            base_peak = int(base_peak * 1.1)

        # 生成提示
        if base_peak == 0:
            note = "通常无需等待"
        elif is_ramen and tabelog_score >= 4.0:
            note = f"人气拉面店，高峰期可能需排队{base_peak}-{base_peak+30}分钟，建议避开11:30-13:00"
        elif reservation_method == "walk_in_only":
            note = f"不接受预约，高峰期排队约{base_peak}分钟，建议早到或错峰"
        elif base_peak >= 30:
            note = f"人气店铺，高峰期可能等{base_peak}分钟，建议提前预约"
        else:
            note = f"高峰期可能短暂等待约{base_peak}分钟"

        return {
            "est_wait_min_peak": base_peak,
            "est_wait_min_offpeak": base_offpeak,
            "wait_note_zh": note,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 城市级批量采集
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_city(
        self,
        city_code: str,
        cuisines: Optional[List[str]] = None,
        max_pages: int = 3,
        max_items_per_cuisine: int = 60,
        save_json: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        采集指定城市的餐厅数据（主入口）。

        Args:
            city_code:            城市代码
            cuisines:             菜系列表，None=全部
            max_pages:            每种菜系最大翻页数
            max_items_per_cuisine: 每种菜系最大采集数
            save_json:            是否落盘到 JSON 文件

        Returns:
            所有采集到的餐厅数据
        """
        if city_code not in TABELOG_AREA_MAP:
            logger.error(f"❌ 未知城市: {city_code}，支持: {list(TABELOG_AREA_MAP.keys())}")
            return []

        target_cuisines = cuisines or list(TABELOG_CUISINE_MAP.keys())

        logger.info(
            f"🏙️  开始采集 [{city_code}] "
            f"菜系={len(target_cuisines)}种 "
            f"最大页数={max_pages} "
            f"详情页={'✅' if self.fetch_detail else '❌'}"
        )

        await self.before_crawl()

        all_restaurants: List[Dict[str, Any]] = []
        seen_ids: set[str] = set()  # 去重

        for cuisine in target_cuisines:
            cuisine_name = TABELOG_CUISINE_MAP.get(cuisine, {}).get("name_zh", cuisine)
            logger.info(f"\n🍽️  [{city_code}] 采集菜系: {cuisine_name} ({cuisine})")

            cuisine_items: List[Dict[str, Any]] = []

            for page in range(1, max_pages + 1):
                items = await self.crawl_list_page(city_code, cuisine, page)

                if not items:
                    logger.info(f"   📭 第 {page} 页无数据，停止翻页")
                    break

                # 去重
                new_items = []
                for item in items:
                    tid = item.get("tabelog_id") or item.get("name_ja")
                    if tid and tid not in seen_ids:
                        seen_ids.add(tid)
                        new_items.append(item)

                cuisine_items.extend(new_items)

                # 检查是否达到上限
                if len(cuisine_items) >= max_items_per_cuisine:
                    cuisine_items = cuisine_items[:max_items_per_cuisine]
                    logger.info(f"   📊 达到上限 {max_items_per_cuisine}，停止翻页")
                    break

                # 检查是否有下一页
                if len(items) < 20:
                    logger.info(f"   📄 第 {page} 页不足 20 条，可能是最后一页")
                    break

            # 可选：抓取详情页
            if self.fetch_detail and cuisine_items:
                logger.info(f"   🔍 开始抓取 {len(cuisine_items)} 个详情页...")
                enriched = []
                for i, item in enumerate(cuisine_items, 1):
                    logger.debug(f"   详情 [{i}/{len(cuisine_items)}] {item.get('name_ja')}")
                    item = await self.crawl_detail_page(item)
                    enriched.append(item)
                cuisine_items = enriched

            all_restaurants.extend(cuisine_items)
            logger.info(
                f"   ✅ {cuisine_name}: {len(cuisine_items)} 家 "
                f"(累计: {len(all_restaurants)})"
            )

        await self.after_crawl()

        # 落盘
        if save_json and all_restaurants:
            self._save_json(city_code, all_restaurants)

        logger.info(f"\n{self.stats.summary()}")
        logger.info(f"🎉 [{city_code}] 采集完成，共 {len(all_restaurants)} 家餐厅")

        return all_restaurants

    # ─────────────────────────────────────────────────────────────────────────
    # 辅助解析方法
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_id(url: str) -> Optional[str]:
        """从 URL 提取 Tabelog 餐厅 ID"""
        # 格式: https://tabelog.com/tokyo/A1301/A130101/13012345/
        match = re.search(r'/(\d{8})/?', url)
        return match.group(1) if match else None

    @staticmethod
    def _parse_score(card: Any) -> Optional[float]:
        """解析评分"""
        for selector in [
            ".c-rating__val",
            ".list-rst__rating-val",
            "[class*='rating-val']",
            "b.c-rating__val",
        ]:
            el = card.select_one(selector)
            if el:
                try:
                    text = el.get_text(strip=True)
                    score = float(text)
                    if 0 < score <= 5.0:
                        return score
                except (ValueError, TypeError):
                    continue
        return None

    @staticmethod
    def _parse_budget(card: Any) -> tuple[Optional[int], Optional[int]]:
        """解析午餐/晚餐预算"""

        def _extract_price(text: str) -> Optional[int]:
            if not text or text.strip() in ("-", "−", ""):
                return None
            cleaned = text.replace("¥", "").replace("￥", "").replace(",", "").replace("、", "")
            match = re.search(r'(\d+)', cleaned)
            return int(match.group(1)) if match else None

        budget_els = card.select(".c-rating-v3__val") or card.select(".list-rst__budget-val")

        if not budget_els:
            # 备用：查找 budget item
            budget_els = card.select("[class*='budget'] span")

        lunch = None
        dinner = None

        if len(budget_els) >= 2:
            dinner = _extract_price(budget_els[0].get_text(strip=True))
            lunch = _extract_price(budget_els[1].get_text(strip=True))
        elif len(budget_els) == 1:
            dinner = _extract_price(budget_els[0].get_text(strip=True))

        return lunch, dinner

    @staticmethod
    def _parse_opening_hours(soup: Any) -> Optional[Dict[str, Any]]:
        """解析营业时间"""
        hours_el = soup.find("th", string=re.compile(r"営業時間"))
        if not hours_el:
            return None

        td = hours_el.find_next("td")
        if not td:
            return None

        text = td.get_text(strip=True)
        # 尝试结构化
        structured = {}
        # 匹配 "11:00～14:00" 这样的时间段
        time_ranges = re.findall(r'(\d{1,2}:\d{2})\s*[～〜\-–]\s*(\d{1,2}:\d{2})', text)
        if time_ranges:
            if len(time_ranges) >= 2:
                structured["lunch"] = {"open": time_ranges[0][0], "close": time_ranges[0][1]}
                structured["dinner"] = {"open": time_ranges[1][0], "close": time_ranges[1][1]}
            else:
                structured["all_day"] = {"open": time_ranges[0][0], "close": time_ranges[0][1]}

        return {"text": text, "structured": structured or None}

    @staticmethod
    def _extract_coordinates(soup: Any) -> tuple[Optional[float], Optional[float]]:
        """从页面提取坐标"""
        # 方式1: 从 Google Maps 链接
        map_link = soup.find("a", href=re.compile(r"maps\.google\.com"))
        if map_link:
            href = map_link.get("href", "")
            match = re.search(r'q=([\d.]+),([\d.]+)', href)
            if match:
                return float(match.group(1)), float(match.group(2))

        # 方式2: 从 script 标签中的 JSON
        for script in soup.find_all("script"):
            text = script.string or ""
            lat_match = re.search(r'"lat(?:itude)?":\s*([\d.]+)', text)
            lng_match = re.search(r'"lng|lon(?:gitude)?":\s*([\d.]+)', text)
            if lat_match and lng_match:
                return float(lat_match.group(1)), float(lng_match.group(1))

        # 方式3: 从 meta 标签
        for meta in soup.find_all("meta"):
            content = meta.get("content", "")
            if "ICBM" in meta.get("name", ""):
                parts = content.split(",")
                if len(parts) == 2:
                    try:
                        return float(parts[0].strip()), float(parts[1].strip())
                    except ValueError:
                        pass

        return None, None

    @staticmethod
    def _extract_images(soup: Any) -> List[str]:
        """提取餐厅图片 URL（最多 5 张）"""
        images: List[str] = []

        # 详情页的图片容器
        for img in soup.select(".rstdtl-top-photo img, .rstdtl-photo img, .rstdtl-top-postphoto img"):
            src = img.get("data-original") or img.get("src") or ""
            if src and "tabelog" in src and src not in images:
                images.append(src)
                if len(images) >= 5:
                    break

        return images

    @staticmethod
    def _extract_awards(soup: Any) -> List[str]:
        """提取奖项标记（百名店、米其林等）"""
        awards: List[str] = []

        # 百名店
        hyakumeiten = soup.select_one("[class*='hyakumeiten']")
        if hyakumeiten:
            awards.append("百名店")

        # 米其林
        page_text = soup.get_text()
        if "ミシュラン" in page_text:
            star_match = re.search(r'ミシュラン.{0,10}(\d)\s*つ星', page_text)
            if star_match:
                awards.append(f"ミシュラン{star_match.group(1)}つ星")
            else:
                awards.append("ミシュラン掲載")

        # Tabelog Award
        award_el = soup.select_one("[class*='award']")
        if award_el:
            awards.append(award_el.get_text(strip=True)[:50])

        return awards

    # ─────────────────────────────────────────────────────────────────────────
    # 数据导出
    # ─────────────────────────────────────────────────────────────────────────

    def _save_json(self, city_code: str, data: List[Dict[str, Any]]) -> None:
        """保存采集数据到 JSON 文件"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tabelog_{city_code}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "meta": {
                        "city_code": city_code,
                        "crawled_at": datetime.utcnow().isoformat(),
                        "total_count": len(data),
                        "stats": {
                            "requests_total": self.stats.requests_total,
                            "requests_success": self.stats.requests_success,
                            "elapsed_seconds": round(self.stats.elapsed, 1),
                        },
                    },
                    "restaurants": data,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        logger.info(f"💾 数据已保存: {filepath} ({len(data)} 条)")

    @staticmethod
    def save_csv(data: List[Dict[str, Any]], filepath: str) -> None:
        """导出为 CSV（便于 Excel 查看）"""
        import csv

        if not data:
            return

        # 取所有 key 的并集
        fieldnames = list(dict.fromkeys(
            key for item in data for key in item.keys()
            if not isinstance(item.get(key), (list, dict))
        ))

        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"💾 CSV 已保存: {filepath}")
