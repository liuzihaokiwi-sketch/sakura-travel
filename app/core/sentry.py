"""
app/core/sentry.py

Sentry 错误监控初始化。
- SENTRY_DSN 为空时自动跳过（开发/测试环境无副作用）
- 捕获未处理异常 + 慢请求性能追踪
- 过滤掉 404 / 429 这类正常业务错误，不作为"异常"上报
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _before_send(event: dict, hint: dict) -> dict | None:
    """
    过滤不需要上报的事件：
      - 404 Not Found（正常的资源未找到）
      - 429 Too Many Requests（限流，预期内）
      - 400 ValidationError（用户输入错误，不是 bug）
    """
    exc_info = hint.get("exc_info")
    if exc_info:
        exc_type, exc_value, _ = exc_info
        # FastAPI/Starlette HTTP 异常
        if hasattr(exc_value, "status_code"):
            if exc_value.status_code in (400, 404, 422, 429):
                return None
    return event


def init_sentry() -> None:
    """
    初始化 Sentry SDK。
    在 main.py lifespan startup 中调用。
    SENTRY_DSN 为空则静默跳过。
    """
    from app.core.config import settings

    dsn = settings.sentry_dsn
    if not dsn:
        logger.debug("SENTRY_DSN 未配置，跳过 Sentry 初始化")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        import logging as _logging

        sentry_logging = LoggingIntegration(
            level=_logging.INFO,        # INFO 及以上记录为 breadcrumb
            event_level=_logging.ERROR, # ERROR 及以上作为事件上报
        )

        sentry_sdk.init(
            dsn=dsn,
            environment=settings.app_env,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                sentry_logging,
            ],
            before_send=_before_send,
            # 不上报 PII 数据
            send_default_pii=False,
        )
        logger.info("Sentry 初始化成功 env=%s", settings.app_env)
    except ImportError:
        logger.warning("sentry-sdk 未安装，跳过 Sentry 初始化（pip install sentry-sdk）")
    except Exception as e:
        logger.warning("Sentry 初始化失败（不阻断启动）: %s", e)
