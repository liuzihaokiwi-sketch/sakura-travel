"""
AI 调用缓存中间件（ai_cache）

对所有 AI / LLM 调用提供 Redis 缓存层：
  - 缓存 key: ai_cache:{model}:{sha256(prompt)}
  - TTL: 7 天
  - 命中缓存直接返回，不调 AI
  - 未命中则调用 AI API，缓存后返回

Langfuse 追踪（可选）：
  - 通过 LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY 环境变量启用
  - 未配置时自动降级（不影响正常功能）
  - 追踪内容：model / prompt 摘要 / 是否命中缓存 / token 估算
"""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Any, Optional

import redis.asyncio as aioredis
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

# ── Langfuse 可选集成 ─────────────────────────────────────────────────────────

def _get_langfuse_client() -> Any:
    """
    懒加载 Langfuse 客户端。
    如果未安装或未配置环境变量则返回 None（降级模式）。
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        return None

    try:
        from langfuse import Langfuse
        return Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
    except ImportError:
        logger.debug("langfuse 未安装，AI 追踪已跳过")
        return None
    except Exception as e:
        logger.warning("Langfuse 初始化失败（追踪已跳过）: %s", e)
        return None


# 模块级别懒加载（首次使用时初始化，Lock 保护并发初始化）
import threading as _threading
_langfuse: Any = None
_langfuse_lock = _threading.Lock()


def _lf() -> Any:
    """获取全局 Langfuse 实例（None = 追踪禁用）。线程安全的懒加载。"""
    global _langfuse
    if _langfuse is None:
        with _langfuse_lock:
            if _langfuse is None:
                _langfuse = _get_langfuse_client()
    return _langfuse

_CACHE_TTL = 7 * 24 * 3600  # 7 天（秒）
_CACHE_PREFIX = "ai_cache"


def _make_cache_key(model: str, prompt: str) -> str:
    """生成缓存 key: ai_cache:{model}:{sha256(prompt)}"""
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return f"{_CACHE_PREFIX}:{model}:{prompt_hash}"


def _get_redis_client() -> Optional[aioredis.Redis]:
    """获取全局 Redis 连接池"""
    try:
        from app.core.queue import get_redis_pool
        pool = get_redis_pool()
        return pool
    except Exception:
        return None


async def cached_ai_call(
    prompt: str,
    model: str,
    *,
    system_prompt: str = "",
    temperature: float = 0.1,
    max_tokens: int = 2000,
    response_format: Optional[dict] = None,
    redis_client: Optional[aioredis.Redis] = None,
    ttl: int = _CACHE_TTL,
    **kwargs: Any,
) -> str:
    """
    带 Redis 缓存的 AI 调用。

    Args:
        prompt:          用户 prompt
        model:           模型名称（如 gpt-4o-mini / gpt-4o / claude-sonnet）
        system_prompt:   系统提示词
        temperature:     温度
        max_tokens:      最大 token 数
        response_format: 响应格式（如 {"type": "json_object"}）
        redis_client:    外部 Redis 连接（None 时使用全局连接池）
        ttl:             缓存 TTL 秒数（默认 7 天）
        **kwargs:        其他传给 AI API 的参数

    Returns:
        AI 响应文本
    """
    # 构建完整 prompt 用于缓存 key（包含 system_prompt 以区分不同上下文）
    full_prompt = f"{system_prompt}|||{prompt}" if system_prompt else prompt
    cache_key = _make_cache_key(model, full_prompt)

    # 获取 Redis 客户端
    client = redis_client or _get_redis_client()

    # ── Langfuse 追踪：开始一次 generation ───────────────────────────────────
    lf = _lf()
    lf_generation = None
    if lf is not None:
        try:
            # prompt 摘要（前 200 字，避免暴露过多数据）
            prompt_preview = (full_prompt[:200] + "…") if len(full_prompt) > 200 else full_prompt
            lf_generation = lf.generation(
                name="cached_ai_call",
                model=model,
                input={"system": system_prompt[:100] if system_prompt else "", "user": prompt_preview},
                metadata={"cache_key": cache_key[:60], "temperature": temperature, "max_tokens": max_tokens},
            )
        except Exception:
            lf_generation = None  # 追踪失败不影响主流程

    # 1. 尝试读取缓存
    if client is not None:
        try:
            cached = await client.get(cache_key)
            if cached is not None:
                cached_str = cached.decode("utf-8") if isinstance(cached, bytes) else cached
                logger.debug("AI cache HIT: %s (model=%s)", cache_key[:60], model)
                # Langfuse：标记为缓存命中
                if lf_generation is not None:
                    try:
                        lf_generation.end(
                            output=cached_str[:200],
                            metadata={"cache_hit": True},
                        )
                    except Exception:
                        pass
                return cached_str
        except Exception as e:
            logger.warning("AI cache read failed: %s", e)

    # 2. 缓存未命中，限速后调用 AI
    logger.debug("AI cache MISS: %s (model=%s)", cache_key[:60], model)
    try:
        from app.core.rate_limiter import ai_rate_limiter
        await ai_rate_limiter.wait()
    except Exception:
        pass  # 限速器异常不阻塞主流程
    result = await _call_ai(
        prompt=prompt,
        model=model,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        **kwargs,
    )

    # Langfuse：记录实际 AI 调用结果
    if lf_generation is not None:
        try:
            lf_generation.end(
                output=result[:200] if result else "",
                metadata={"cache_hit": False},
            )
        except Exception:
            pass

    # 3. 写入缓存
    if client is not None and result:
        try:
            await client.set(cache_key, result, ex=ttl)
            logger.debug("AI cache SET: %s (ttl=%ds)", cache_key[:60], ttl)
        except Exception as e:
            logger.warning("AI cache write failed (non-blocking): %s", e)

    return result


async def _call_ai(
    prompt: str,
    model: str,
    system_prompt: str = "",
    temperature: float = 0.1,
    max_tokens: int = 2000,
    response_format: Optional[dict] = None,
    **kwargs: Any,
) -> str:
    """
    统一 AI 调用入口，根据 model 名称路由到 OpenAI 或 Anthropic。
    """
    from app.core.config import settings

    # 中转站统一走 OpenAI 兼容接口（支持 claude/gpt 等所有模型）
    # 仅在配置了 ANTHROPIC_API_KEY 且未配置 AI_BASE_URL 时才走官方 Anthropic API
    use_native_anthropic = (
        ("claude" in model.lower() or "anthropic" in model.lower())
        and getattr(settings, "anthropic_api_key", None)
        and not getattr(settings, "ai_base_url", None)
    )

    if use_native_anthropic:
        return await _call_anthropic(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
    else:
        return await _call_openai(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            **kwargs,
        )


@retry(
    retry=retry_if_exception_type((Exception,)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _call_openai(
    prompt: str,
    model: str,
    system_prompt: str = "",
    temperature: float = 0.1,
    max_tokens: int = 2000,
    response_format: Optional[dict] = None,
    **kwargs: Any,
) -> str:
    """调用 OpenAI 兼容 API（含 tenacity 自动重试，最多 3 次，指数退避）"""
    from openai import AsyncOpenAI
    from app.core.config import settings

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.ai_base_url if settings.ai_base_url else None,
    )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    create_kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        create_kwargs["response_format"] = response_format

    response = await client.chat.completions.create(**create_kwargs)
    return response.choices[0].message.content or ""


@retry(
    retry=retry_if_exception_type((Exception,)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _call_anthropic(
    prompt: str,
    model: str,
    system_prompt: str = "",
    temperature: float = 0.1,
    max_tokens: int = 2000,
    **kwargs: Any,
) -> str:
    """调用 Anthropic Claude API（含 tenacity 自动重试，最多 3 次，指数退避）"""
    import httpx
    from app.core.config import settings

    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    body: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        body["system"] = system_prompt

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        # Anthropic 返回格式: {"content": [{"type": "text", "text": "..."}]}
        content_blocks = data.get("content", [])
        return "".join(
            block.get("text", "") for block in content_blocks if block.get("type") == "text"
        )


async def invalidate_cache(model: str, prompt: str, system_prompt: str = "") -> bool:
    """手动清除指定 prompt 的缓存"""
    full_prompt = f"{system_prompt}|||{prompt}" if system_prompt else prompt
    cache_key = _make_cache_key(model, full_prompt)
    client = _get_redis_client()
    if client:
        try:
            deleted = await client.delete(cache_key)
            return deleted > 0
        except Exception as e:
            logger.warning("AI cache invalidate failed: %s", e)
    return False
