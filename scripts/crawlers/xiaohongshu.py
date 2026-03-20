"""
小红书日本旅游攻略爬虫 (Playwright)
====================================
采集小红书上的日本旅游 UGC 内容，用于丰富旅行方案的文案和推荐理由。

采集字段:
  title, content_snippet, likes, collects, comments,
  tags, city_code, images, author, source_url

反爬说明:
  小红书反爬极强，必须用 Playwright + 随机行为模拟。
  本爬虫只采集公开搜索结果页，不登录不侵入。

用法:
  python scripts/xhs_crawl.py --keyword "东京攻略" --pages 2
  python scripts/xhs_crawl.py --keyword "京都美食" --keyword "大阪购物"
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncio

from scripts.crawlers.playwright_base import PlaywrightCrawler

logger = logging.getLogger(__name__)

# ── 预设搜索关键词（覆盖核心旅行场景）──────────────────────────────────────────

DEFAULT_KEYWORDS = {
    "tokyo":    ["东京攻略", "东京必去", "东京美食推荐", "东京购物"],
    "osaka":    ["大阪攻略", "大阪美食", "大阪购物"],
    "kyoto":    ["京都攻略", "京都和服", "京都寺庙"],
    "nara":     ["奈良攻略", "奈良小鹿"],
    "hakone":   ["箱根温泉", "箱根攻略"],
    "sapporo":  ["北海道攻略", "札幌美食"],
    "okinawa":  ["冲绳攻略", "冲绳海滩"],
    "general":  ["日本自由行攻略", "日本交通攻略", "JR Pass攻略", "日本签证", "日本特价机票"],
}

CITY_KEYWORD_MAP = {
    "东京": "tokyo", "大阪": "osaka", "京都": "kyoto", "奈良": "nara",
    "箱根": "hakone", "札幌": "sapporo", "北海道": "sapporo",
    "冲绳": "okinawa", "福冈": "fukuoka", "镰仓": "kamakura",
    "金泽": "kanazawa", "神户": "kobe", "名古屋": "nagoya",
    "横滨": "yokohama", "日本": None,
}


class XiaohongshuCrawler(PlaywrightCrawler):
    """
    小红书搜索结果爬虫（Playwright）。

    只采集公开搜索结果页的笔记标题、互动数据、标签等。
    不获取完整正文（需要登录），只用摘要。
    """

    BASE = "https://www.xiaohongshu.com"

    def __init__(
        self,
        output_dir: str = "data/xhs_raw",
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("delay_range", (3.0, 6.0))  # 小红书反爬强，延迟大
        kwargs.setdefault("locale", "zh-CN")
        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)

    async def search_notes(
        self,
        keyword: str,
        max_pages: int = 2,
        sort_by: str = "general",  # general / time_descending / popularity_descending
    ) -> List[Dict[str, Any]]:
        """
        搜索小红书笔记。

        Args:
            keyword:   搜索关键词
            max_pages: 最大翻页数（每页约 20 条）
            sort_by:   排序方式

        Returns:
            笔记列表
        """
        logger.info(f"📕 小红书搜索: '{keyword}'")

        page = await self.new_page()
        results = []

        try:
            # 先访问首页获取 cookie
            await self.safe_goto(page, self.BASE, timeout=15000)
            await self.random_delay()

            # 搜索
            search_url = f"{self.BASE}/search_result?keyword={keyword}&source=web_search_result_notes"
            if sort_by == "popularity_descending":
                search_url += "&sort=popularity_descending"
            elif sort_by == "time_descending":
                search_url += "&sort=time_descending"

            # 小红书笔记卡片备用选择器（按优先级排列）
            _NOTE_SELECTORS = [
                "section.note-item",
                "[class*='note-item']",
                "[class*='NoteItem']",
                "[class*='search-result-item']",
                ".feeds-page [class*='item']",
                "[class*='noteItem']",
            ]

            for pg in range(max_pages):
                if pg == 0:
                    # 先用 domcontentloaded，避免 networkidle 超时
                    ok = await self.safe_goto(
                        page, search_url,
                        wait_until="domcontentloaded",
                        timeout=25000,
                    )
                    if not ok:
                        break
                    # 等待 JS 渲染完成
                    await asyncio.sleep(2.5)
                    await self.random_delay()
                else:
                    # 双滚动确保懒加载内容出现
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.7)")
                    await asyncio.sleep(1.0)
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await self.random_delay()

                # 等待笔记卡片（依次尝试备用选择器）
                loaded = False
                for sel in _NOTE_SELECTORS:
                    try:
                        await page.wait_for_selector(sel, timeout=8000)
                        loaded = True
                        break
                    except Exception:
                        continue

                if not loaded:
                    logger.warning(f"  ⚠️  第 {pg+1} 页：笔记元素未找到，尝试提取可见内容")

                await self.random_delay()

                # 提取笔记数据
                page_notes = await self._extract_notes(page, keyword)
                new_count = 0
                existing_titles = {r["title"] for r in results}
                for note in page_notes:
                    if note["title"] not in existing_titles:
                        results.append(note)
                        new_count += 1

                logger.info(f"  📄 第 {pg+1} 页: {new_count} 条新笔记 (loaded={loaded})")

                if new_count == 0 and pg > 0:
                    break  # 首页无数据可能是加载慢，不提前退出

        except Exception as e:
            logger.error(f"  ❌ 搜索异常: {e}")
        finally:
            await page.close()

        logger.info(f"  ✅ '{keyword}': {len(results)} 条笔记")
        return results

    async def _extract_notes(
        self, page: Any, keyword: str
    ) -> List[Dict[str, Any]]:
        """从搜索结果页提取笔记数据"""
        results = []

        # 方式1: 从 JS 全局数据提取
        try:
            js_data = await page.evaluate("""
                () => {
                    if (window.__INITIAL_STATE__) return JSON.stringify(window.__INITIAL_STATE__);
                    if (window.__NEXT_DATA__) return JSON.stringify(window.__NEXT_DATA__);
                    return null;
                }
            """)
            if js_data:
                parsed = json.loads(js_data)
                js_notes = self._parse_xhs_json(parsed, keyword)
                if js_notes:
                    return js_notes
        except Exception as e:
            logger.debug(f"  JS 提取失败: {e}")

        # 方式2: DOM 提取
        cards = await page.query_selector_all(
            "section.note-item, [class*='note-item'], [class*='NoteItem']"
        )

        for card in cards:
            try:
                text = await card.inner_text()

                # 标题
                title_el = (
                    await card.query_selector("[class*='title'], a[class*='title']")
                    or await card.query_selector("a")
                )
                title = (await title_el.inner_text()).strip() if title_el else ""
                if not title:
                    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 5]
                    title = lines[0] if lines else ""
                if not title:
                    continue

                # 链接
                link = ""
                link_el = await card.query_selector("a[href*='/explore/'], a[href*='/search_result/']")
                if link_el:
                    link = await link_el.get_attribute("href") or ""
                    if link and not link.startswith("http"):
                        link = self.BASE + link

                # 互动数据
                likes = self._extract_number(text, r'(\d+(?:\.\d+)?[万w]?)\s*(?:赞|❤|♥|like)', 0)
                collects = self._extract_number(text, r'(\d+(?:\.\d+)?[万w]?)\s*(?:收藏|⭐|★)', 0)

                # 作者
                author_el = await card.query_selector("[class*='author'], [class*='nickname']")
                author = (await author_el.inner_text()).strip() if author_el else ""

                # 图片
                img_el = await card.query_selector("img")
                img = await img_el.get_attribute("src") if img_el else ""

                # 城市推断
                city_code = None
                for city_zh, code in CITY_KEYWORD_MAP.items():
                    if city_zh in title or city_zh in keyword:
                        city_code = code
                        break

                # 标签提取
                tags = re.findall(r'#([^\s#]+)', text)

                results.append({
                    "title": title,
                    "keyword": keyword,
                    "city_code": city_code,
                    "likes": likes,
                    "collects": collects,
                    "author": author,
                    "tags": tags[:10],
                    "image_url": img,
                    "source_url": link,
                    "source": "xiaohongshu",
                    "crawled_at": datetime.utcnow().isoformat(),
                })

            except Exception as e:
                logger.debug(f"  解析笔记失败: {e}")

        return results

    def _parse_xhs_json(
        self, data: dict, keyword: str
    ) -> List[Dict[str, Any]]:
        """从小红书 SSR JSON 中提取笔记"""
        results = []

        # 尝试多种数据路径
        notes = (
            data.get("search", {}).get("feeds", [])
            or data.get("note", {}).get("noteDetailMap", {})
            or data.get("props", {}).get("pageProps", {}).get("notes", [])
        )

        if isinstance(notes, dict):
            notes = list(notes.values())

        for note in notes:
            if isinstance(note, dict):
                n = note.get("note") or note
                title = n.get("title", "") or n.get("displayTitle", "")
                if not title:
                    continue

                likes = n.get("interactInfo", {}).get("likedCount", 0) or n.get("likes", 0)
                collects = n.get("interactInfo", {}).get("collectedCount", 0) or n.get("collects", 0)
                note_id = n.get("noteId") or n.get("id", "")

                city_code = None
                for city_zh, code in CITY_KEYWORD_MAP.items():
                    if city_zh in title:
                        city_code = code
                        break

                tags = [t.get("name", "") for t in n.get("tagList", []) if t.get("name")]

                img = ""
                images = n.get("imageList", [])
                if images and isinstance(images[0], dict):
                    img = images[0].get("urlDefault", "") or images[0].get("url", "")

                results.append({
                    "title": title,
                    "keyword": keyword,
                    "city_code": city_code,
                    "likes": likes,
                    "collects": collects,
                    "author": n.get("user", {}).get("nickname", ""),
                    "tags": tags[:10],
                    "image_url": img,
                    "source_url": f"{self.BASE}/explore/{note_id}" if note_id else "",
                    "source": "xiaohongshu",
                    "crawled_at": datetime.utcnow().isoformat(),
                })

        return results

    @staticmethod
    def _extract_number(text: str, pattern: str, default: int = 0) -> int:
        """从文本提取数字（支持 '1.2万' 格式）"""
        match = re.search(pattern, text)
        if not match:
            return default
        num_str = match.group(1)
        if '万' in num_str or 'w' in num_str.lower():
            return int(float(num_str.replace('万', '').replace('w', '').replace('W', '')) * 10000)
        return int(float(num_str))

    async def crawl_by_city(
        self,
        city_code: str = "general",
        max_pages: int = 2,
        save_json: bool = True,
    ) -> List[Dict[str, Any]]:
        """按城市采集攻略"""
        keywords = DEFAULT_KEYWORDS.get(city_code, DEFAULT_KEYWORDS["general"])
        all_notes = []

        for kw in keywords:
            notes = await self.search_notes(kw, max_pages=max_pages)
            all_notes.extend(notes)

        # 去重
        seen = set()
        unique = []
        for n in all_notes:
            if n["title"] not in seen:
                seen.add(n["title"])
                unique.append(n)

        if save_json and unique:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = self.output_dir / f"xhs_{city_code}_{ts}.json"
            with open(fp, "w", encoding="utf-8") as f:
                json.dump({"meta": {"city": city_code, "total": len(unique)}, "notes": unique},
                          f, ensure_ascii=False, indent=2)
            logger.info(f"💾 已保存: {fp}")

        print(f"\n📕 小红书 [{city_code}]: {len(unique)} 条攻略")
        # Top 5
        for n in sorted(unique, key=lambda x: x.get("likes", 0), reverse=True)[:5]:
            print(f"  ❤️{n['likes']:>5d}  {n['title'][:40]}")

        return unique
