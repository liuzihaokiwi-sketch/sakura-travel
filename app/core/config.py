from __future__ import annotations

from functools import lru_cache
from typing import List, Literal, Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    secret_key: str = "change_me_in_production"
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ── Database ──────────────────────────────────────────────
    # SQLite 示例: sqlite+aiosqlite:///./japan_ai.db
    # PostgreSQL 示例: postgresql+asyncpg://user:pass@localhost:5432/japan_ai
    database_url: str = "sqlite+aiosqlite:///./japan_ai.db"
    postgres_user: str = "japan_ai"
    postgres_password: str = "japan_ai_dev"
    postgres_db: str = "japan_ai"

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── External APIs ─────────────────────────────────────────
    google_places_api_key: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    ai_base_url: str = "https://api.openai.com/v1"   # 中转站地址

    # 通知渠道
    wecom_webhook_url: str = ""      # 企业微信机器人（旧版 wecom_notify）
    wechat_work_webhook_url: str = ""  # 企业微信群机器人 webhook（新版 wechat_notify）
    enable_wechat_notify: bool = False  # 企微通知开关（默认关闭）
    smtp_host: str = ""
    smtp_user: str = ""
    smtp_password: str = ""
    alert_email: str = ""
    ai_model: str = "gpt-4o"
    # ── AI 模型分层（Tiered Model Selection）──────────────
    # Tier 1 (Light):    标签/分类/翻译 — 高吞吐低成本
    # Tier 2 (Standard): 文案生成/文本解析 — 中等能力日常主力
    # Tier 3 (Strong):   质量评审/复杂推理/多维评估 — 最强模型少量调用
    ai_model_light: str = "gpt-4o-mini"
    ai_model_standard: str = "gpt-4o"
    ai_model_strong: str = "claude-sonnet"

    serpapi_key: str = ""
    anthropic_api_key: str = ""
    deepl_api_key: str = ""
    admin_password: str = "admin123"

    # ── Sentry ────────────────────────────────────────────────
    sentry_dsn: str = ""              # 空字符串=禁用
    sentry_traces_sample_rate: float = 0.1   # 生产环境 10% 采样

    # ── Snapshot TTL (days) ───────────────────────────────────
    snapshot_ttl_hotel_offer: int = 1
    snapshot_ttl_poi_opening: int = 7
    snapshot_ttl_weather: int = 1

    # ── Worker ────────────────────────────────────────────────
    worker_max_jobs: int = 10
    job_retry_max: int = 3
    job_retry_delay_secs: int = 10

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: Union[str, list]) -> List[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
