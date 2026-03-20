"""
PlaywrightCrawler — 基于无头浏览器的通用爬虫
=============================================
解决 Skyscanner/Google Flights/Booking 等重 JS 渲染 + 反爬站点。

依赖:
  pip install playwright && python -m playwright install chromium

特性:
  ✅ 真实 Chromium 浏览器环境，绕过 JS 验证/captcha
  ✅ 自动管理 Cookie 和 Session
  ✅ 支持页面截图（调试用）
  ✅ 可复用 browser context（同一爬取任务内共享登录态）
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 有些环境没装 playwright，做软依赖
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


class PlaywrightCrawler:
    """
    Playwright 无头浏览器爬虫基类。

    用法:
        async with PlaywrightCrawler() as crawler:
            page = await crawler.new_page()
            await page.goto("https://example.com")
            content = await page.content()
    """

    def __init__(
        self,
        headless: bool = True,
        locale: str = "zh-CN",
        timezone: str = "Asia/Shanghai",
        delay_range: tuple[float, float] = (1.0, 3.0),
        proxy: Optional[str] = None,
    ) -> None:
        if not HAS_PLAYWRIGHT:
            raise RuntimeError(
                "需要安装 Playwright:\n"
                "  pip install playwright\n"
                "  python -m playwright install chromium"
            )

        self.headless = headless
        self.locale = locale
        self.timezone = timezone
        self.delay_range = delay_range
        self.proxy = proxy

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def __aenter__(self) -> "PlaywrightCrawler":
        await self.open()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def open(self) -> None:
        self._playwright = await async_playwright().start()

        launch_args = {
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        }
        if self.proxy:
            launch_args["proxy"] = {"server": self.proxy}

        self._browser = await self._playwright.chromium.launch(**launch_args)
        self._context = await self._browser.new_context(
            locale=self.locale,
            timezone_id=self.timezone,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
            java_script_enabled=True,
        )

        # 注入反检测脚本
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
        """)

        logger.info("🌐 Playwright 浏览器已启动")

    async def close(self) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("🌐 Playwright 浏览器已关闭")

    async def new_page(self) -> "Page":
        return await self._context.new_page()

    async def random_delay(self) -> None:
        lo, hi = self.delay_range
        await asyncio.sleep(random.uniform(lo, hi))

    async def safe_goto(
        self,
        page: "Page",
        url: str,
        wait_until: str = "networkidle",
        timeout: int = 30000,
    ) -> bool:
        """安全导航，返回是否成功"""
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"⚠️  页面加载失败: {e}")
            return False

    async def extract_text(self, page: "Page", selector: str) -> Optional[str]:
        """安全提取元素文本"""
        try:
            el = await page.query_selector(selector)
            if el:
                return (await el.inner_text()).strip()
        except Exception:
            pass
        return None

    async def extract_all_text(self, page: "Page", selector: str) -> List[str]:
        """提取所有匹配元素的文本"""
        try:
            els = await page.query_selector_all(selector)
            return [((await el.inner_text()).strip()) for el in els]
        except Exception:
            return []
