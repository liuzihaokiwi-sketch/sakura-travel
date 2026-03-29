"""
app/core/sentry.py

Sentry 错误监控初始化。
- SENTRY_DSN 为空时自动跳过（开发/测试环境无副作用）
- 捕获未处理异常 + 慢请求性能追踪
- 过滤掉 404 / 429 这类正常业务错误，不作为"异常"上报
- 支持 FastAPI + arq worker 双入口初始化
"""
from __future__ import annotations

import logging
import os

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


def _get_traces_sample_rate(environment: str) -> float:
    """Return traces_sample_rate based on environment."""
    if environment == "production":
        return 0.1
    # development / staging: capture all traces for debugging
    return 1.0


def init_sentry() -> None:
    """
    初始化 Sentry SDK。

    可在 FastAPI lifespan 或 arq worker startup 中调用。
    SENTRY_DSN 为空则静默跳过（graceful no-op）。

    环境变量:
      - SENTRY_DSN: Sentry DSN（为空则不初始化）
      - APP_ENV: 环境标识（default "development"）
      - APP_VERSION: 发布版本号（default "dev"）
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

        environment = settings.app_env or os.getenv("APP_ENV", "development")
        release = os.getenv("APP_VERSION", "dev")
        traces_sample_rate = _get_traces_sample_rate(environment)

        sentry_logging = LoggingIntegration(
            level=_logging.INFO,        # INFO 及以上记录为 breadcrumb
            event_level=_logging.ERROR, # ERROR 及以上作为事件上报
        )

        integrations = [
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            sentry_logging,
        ]

        # arq integration (available in sentry-sdk >= 1.31.0)
        try:
            from sentry_sdk.integrations.arq import ArqIntegration
            integrations.append(ArqIntegration())
            logger.debug("Sentry ArqIntegration 已加载")
        except ImportError:
            logger.debug("sentry_sdk.integrations.arq 不可用，arq 异常将通过手动捕获上报")

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            traces_sample_rate=traces_sample_rate,
            integrations=integrations,
            before_send=_before_send,
            # 不上报 PII 数据
            send_default_pii=False,
        )
        logger.info(
            "Sentry 初始化成功 env=%s release=%s traces_sample_rate=%.1f",
            environment, release, traces_sample_rate,
        )
    except ImportError:
        logger.warning("sentry-sdk 未安装，跳过 Sentry 初始化（pip install sentry-sdk[fastapi]）")
    except Exception as e:
        logger.warning("Sentry 初始化失败（不阻断启动）: %s", e)


def set_sentry_context(
    *,
    trip_id: str | None = None,
    step: str | None = None,
    circle_id: str | None = None,
    plan_id: str | None = None,
    transaction_name: str | None = None,
) -> None:
    """
    为当前 Sentry scope 设置上下文标签。

    在 generate_trip 等关键路径调用，使 Sentry 异常报告包含业务上下文。
    如果 sentry-sdk 未安装则静默跳过。
    """
    try:
        import sentry_sdk
    except ImportError:
        return

    scope = sentry_sdk.get_current_scope()

    if transaction_name:
        scope.set_transaction_name(transaction_name)
    if trip_id:
        scope.set_tag("trip_id", trip_id)
    if step:
        scope.set_tag("step", step)
    if circle_id:
        scope.set_tag("circle_id", circle_id)
    if plan_id:
        scope.set_tag("plan_id", plan_id)


def capture_exception_with_context(
    exc: BaseException,
    *,
    trip_id: str | None = None,
    step: str | None = None,
    circle_id: str | None = None,
) -> None:
    """
    捕获异常并附加业务上下文信息上报到 Sentry。

    如果 sentry-sdk 未安装则静默跳过。
    """
    try:
        import sentry_sdk
    except ImportError:
        return

    with sentry_sdk.push_scope() as scope:
        if trip_id:
            scope.set_tag("trip_id", trip_id)
            scope.set_extra("trip_id", trip_id)
        if step:
            scope.set_tag("step", step)
            scope.set_extra("step", step)
        if circle_id:
            scope.set_tag("circle_id", circle_id)
            scope.set_extra("circle_id", circle_id)
        sentry_sdk.capture_exception(exc)
