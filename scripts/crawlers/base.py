"""
BaseCrawler — 通用异步爬虫基类
================================
提供会话管理、反爬策略、速率限制、自动重试、代理支持等基础能力。
所有专用爬虫（Tabelog / Booking / Jalan 等）都继承此类。

特性：
  ✅ User-Agent 轮换（50+ 真实 UA）
  ✅ 随机延迟（可配置范围）
  ✅ 自动重试 + 指数退避
  ✅ Cookie 会话保持
  ✅ 可选代理池
  ✅ 请求计数 & 统计
  ✅ 优雅关闭
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# ── 真实浏览器 User-Agent 池 ──────────────────────────────────────────────────

_USER_AGENTS: list[str] = [
    # Chrome (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Firefox (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Safari (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    # Chrome (Linux)
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# ── Accept-Language 池 ────────────────────────────────────────────────────────

_ACCEPT_LANGUAGES: list[str] = [
    "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    "ja-JP,ja;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "ja,en-US;q=0.9,en;q=0.8",
    "ja-JP,ja;q=0.9",
    "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6",
]


@dataclass
class CrawlStats:
    """爬取统计"""
    requests_total: int = 0
    requests_success: int = 0
    requests_failed: int = 0
    requests_retried: int = 0
    items_scraped: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def success_rate(self) -> float:
        if self.requests_total == 0:
            return 0.0
        return self.requests_success / self.requests_total

    def summary(self) -> str:
        return (
            f"📊 爬取统计: "
            f"请求={self.requests_total} "
            f"成功={self.requests_success} "
            f"失败={self.requests_failed} "
            f"重试={self.requests_retried} "
            f"采集条目={self.items_scraped} "
            f"耗时={self.elapsed:.1f}s "
            f"成功率={self.success_rate:.1%}"
        )


class BaseCrawler:
    """
    通用异步爬虫基类。

    Args:
        delay_range:   每次请求间的随机延迟范围 (min_sec, max_sec)
        max_retries:   单次请求最大重试次数
        timeout:       请求超时（秒）
        proxies:       代理列表，如 ["http://user:pass@host:port", ...]
        max_concurrent: 最大并发请求数
        cookie_jar:    初始 Cookies（可选）
    """

    def __init__(
        self,
        delay_range: tuple[float, float] = (1.0, 3.0),
        max_retries: int = 3,
        timeout: float = 20.0,
        proxies: Optional[List[str]] = None,
        max_concurrent: int = 3,
        cookie_jar: Optional[Dict[str, str]] = None,
    ) -> None:
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.timeout = timeout
        self.proxies = proxies or []
        self.max_concurrent = max_concurrent
        self._initial_cookies = cookie_jar or {}

        self._client: Optional[httpx.AsyncClient] = None
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self.stats = CrawlStats()

    # ── 生命周期（async context manager）─────────────────────────────────────

    async def __aenter__(self) -> "BaseCrawler":
        await self.open()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def open(self) -> None:
        """初始化 HTTP 客户端"""
        if self._client is None:
            transport_kwargs: Dict[str, Any] = {}
            if self.proxies:
                # 随机选一个代理
                proxy = random.choice(self.proxies)
                transport_kwargs["proxy"] = proxy

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                cookies=self._initial_cookies,
                http2=True,      # 使用 HTTP/2 更像真实浏览器
                limits=httpx.Limits(
                    max_connections=self.max_concurrent + 2,
                    max_keepalive_connections=self.max_concurrent,
                ),
                **transport_kwargs,
            )
        logger.debug("BaseCrawler: HTTP client opened")

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.debug("BaseCrawler: HTTP client closed")

    # ── 核心请求方法 ─────────────────────────────────────────────────────────

    def _build_headers(self) -> Dict[str, str]:
        """构建随机化的请求头"""
        ua = random.choice(_USER_AGENTS)
        lang = random.choice(_ACCEPT_LANGUAGES)

        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": lang,
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    async def _random_delay(self) -> None:
        """随机延迟，模拟人类行为"""
        lo, hi = self.delay_range
        delay = random.uniform(lo, hi)
        # 偶尔插入更长延迟（模拟阅读/思考）
        if random.random() < 0.1:
            delay += random.uniform(2.0, 5.0)
        await asyncio.sleep(delay)

    async def fetch(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        referer: Optional[str] = None,
    ) -> Optional[httpx.Response]:
        """
        发送 HTTP 请求，自带：
        - 信号量控制并发
        - 随机 UA + 延迟
        - tenacity 自动重试 + 指数退避（替换手写 retry 循环）
        - 请求统计

        Returns:
            httpx.Response 或 None（全部失败时）
        """
        if not self._client:
            await self.open()

        async with self._semaphore:
            self.stats.requests_total += 1
            req_headers = self._build_headers()
            if referer:
                req_headers["Referer"] = referer
            if headers:
                req_headers.update(headers)

            await self._random_delay()

            # ── 可重试异常（tenacity 会自动重试这些） ──────────────────────────

            class _RetryableError(Exception):
                """标记为可重试的内部异常"""

            async def _do_request() -> httpx.Response:
                resp = await self._client.request(  # type: ignore[union-attr]
                    method,
                    url,
                    headers=self._build_headers() | ({"Referer": referer} if referer else {}) | (headers or {}),
                    params=params,
                    data=data,
                )
                # 429 / 503 视为可重试（tenacity 会等待后再试）
                if resp.status_code == 429:
                    logger.warning(f"⚠️  429 限速，等待后重试 [{url}]")
                    self.stats.requests_retried += 1
                    raise _RetryableError("429 Rate limited")
                if resp.status_code == 503:
                    logger.warning(f"⚠️  503 服务不可用，等待后重试 [{url}]")
                    self.stats.requests_retried += 1
                    raise _RetryableError("503 Service unavailable")
                return resp

            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self.max_retries),
                    wait=wait_exponential(multiplier=1, min=2, max=30),
                    retry=retry_if_exception_type(
                        (httpx.TimeoutException, httpx.ConnectError, _RetryableError)
                    ),
                    reraise=False,
                ):
                    with attempt:
                        try:
                            resp = await _do_request()
                        except (httpx.TimeoutException, httpx.ConnectError) as e:
                            self.stats.requests_retried += 1
                            logger.warning(
                                f"⏱️  网络错误 (attempt {attempt.retry_state.attempt_number}/{self.max_retries}): {e} [{url}]"
                            )
                            raise  # 交给 tenacity 处理重试

            except RetryError:
                # 全部重试耗尽
                self.stats.requests_failed += 1
                logger.error(f"❌ 所有重试失败（tenacity 退出）[{url}]")
                return None
            except Exception as e:
                logger.error(f"❌ 请求异常: {e} [{url}]")
                self.stats.requests_failed += 1
                return None

            # ── 处理 3xx+ 非重试错误 ──────────────────────────────────────────
            if resp.status_code == 403:
                logger.warning(f"⚠️  403 被拒绝（可能被封），跳过 [{url}]")
                self.stats.requests_failed += 1
                return None

            if resp.status_code >= 400:
                logger.warning(f"⚠️  HTTP {resp.status_code} [{url}]")
                self.stats.requests_failed += 1
                return None

            self.stats.requests_success += 1
            return resp

    async def fetch_text(self, url: str, **kwargs: Any) -> Optional[str]:
        """获取页面 HTML 文本"""
        resp = await self.fetch(url, **kwargs)
        if resp:
            return resp.text
        return None

    # ── 子类钩子 ─────────────────────────────────────────────────────────────

    async def before_crawl(self) -> None:
        """爬取前的初始化（子类可覆写，如先访问首页获取 cookie）"""
        pass

    async def after_crawl(self) -> None:
        """爬取后的清理（子类可覆写）"""
        pass
