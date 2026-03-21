"""
structlog 结构化日志配置

开发环境：彩色终端友好格式
生产环境：JSON 格式（便于日志收集）

使用方式（替代 logging.getLogger）：
    import structlog
    logger = structlog.get_logger()
    logger.info("event_name", key="value")
"""
from __future__ import annotations

import logging
import sys

import structlog


def setup_logging(*, json_output: bool = False, log_level: str = "INFO") -> None:
    """
    初始化 structlog + 标准 logging 的双通道配置。

    - 所有 structlog logger 和标准 logging logger 都走统一的处理链
    - json_output=True 时输出 JSON（生产用），否则输出彩色 console（开发用）

    Args:
        json_output: 是否输出 JSON 格式
        log_level: 日志级别（DEBUG / INFO / WARNING / ERROR）
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # ── 共享处理器 ─────────────────────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        # 生产环境：JSON 输出
        renderer = structlog.processors.JSONRenderer(ensure_ascii=False)
    else:
        # 开发环境：彩色终端
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    # ── 配置 structlog ────────────────────────────────────────
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ── 配置标准 logging（让第三方库日志也走 structlog 格式）───
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # 降低第三方库的日志级别
    for noisy_logger in ("httpx", "httpcore", "asyncio", "multipart", "urllib3"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
