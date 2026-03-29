"""
ai_client.py -- OpenAI client factory

Provides a lazily-initialized AsyncOpenAI client used by:
  - copy_enrichment (D2)
  - review pipeline
  - any module that needs LLM completions

The client reads credentials from Settings (openai_api_key, ai_base_url).
If openai is not installed or the API key is empty, get_openai_client()
raises ImportError / ValueError so callers can gracefully degrade.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_openai_client() -> Any:
    """
    Return a cached AsyncOpenAI client instance.

    Raises:
        ImportError: if the ``openai`` package is not installed.
        ValueError: if ``openai_api_key`` is not configured.
    """
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        logger.warning("openai package not installed -- AI features disabled")
        raise ImportError("openai package is required for AI features") from exc

    from app.core.config import get_settings

    settings = get_settings()
    api_key = settings.openai_api_key
    if not api_key:
        raise ValueError("openai_api_key is not configured in settings / .env")

    base_url = settings.ai_base_url or settings.openai_base_url or None

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    logger.info("[ai_client] AsyncOpenAI client created (base_url=%s)", base_url)
    return client
