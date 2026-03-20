# Config Inventory

## 环境变量（app/core/config.py → Settings 类）

| 变量名 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `APP_ENV` | `Literal["development","staging","production"]` | `"development"` | 应用环境 |
| `APP_DEBUG` | `bool` | `False` | 调试模式 |
| `SECRET_KEY` | `str` | `"change_me_in_production"` | 应用密钥 |
| `ALLOWED_ORIGINS` | `List[str]` | `["http://localhost:3000","http://localhost:8000"]` | CORS 允许来源 |
| `DATABASE_URL` | `str` | `"sqlite+aiosqlite:///./japan_ai.db"` | 数据库连接串 |
| `POSTGRES_USER` | `str` | `"japan_ai"` | PostgreSQL 用户名 |
| `POSTGRES_PASSWORD` | `str` | `"japan_ai_dev"` | PostgreSQL 密码 |
| `POSTGRES_DB` | `str` | `"japan_ai"` | PostgreSQL 数据库名 |
| `REDIS_URL` | `str` | `"redis://localhost:6379/0"` | Redis 连接串 |
| `GOOGLE_PLACES_API_KEY` | `str` | `""` | Google Places API Key |
| `OPENAI_API_KEY` | `str` | `""` | OpenAI API Key |
| `OPENAI_BASE_URL` | `str` | `"https://api.openai.com/v1"` | OpenAI API 基础 URL |
| `AI_BASE_URL` | `str` | `"https://api.openai.com/v1"` | AI 中转站地址 |
| `AI_MODEL` | `str` | `"claude-opus-4-6"` | 默认 AI 模型 |
| `AI_MODEL_STRONG` | `str` | `"claude-opus-4-6"` | 强力 AI 模型 |
| `SERPAPI_KEY` | `str` | `""` | SerpAPI Key |
| `AMADEUS_CLIENT_ID` | `str` | `""` | Amadeus 客户端 ID |
| `AMADEUS_CLIENT_SECRET` | `str` | `""` | Amadeus 客户端密钥 |
| `WECOM_WEBHOOK_URL` | `str` | `""` | 企业微信机器人 Webhook |
| `SMTP_HOST` | `str` | `""` | SMTP 邮件主机 |
| `SMTP_USER` | `str` | `""` | SMTP 用户名 |
| `SMTP_PASSWORD` | `str` | `""` | SMTP 密码 |
| `ALERT_EMAIL` | `str` | `""` | 告警邮件地址 |
| `SNAPSHOT_TTL_HOTEL_OFFER` | `int` | `1` | 酒店报价快照 TTL（天） |
| `SNAPSHOT_TTL_FLIGHT_OFFER` | `int` | `1` | 航班报价快照 TTL（天） |
| `SNAPSHOT_TTL_POI_OPENING` | `int` | `7` | 景点开放快照 TTL（天） |
| `SNAPSHOT_TTL_WEATHER` | `int` | `1` | 天气快照 TTL（天） |
| `WORKER_MAX_JOBS` | `int` | `10` | Worker 最大并发任务数 |
| `JOB_RETRY_MAX` | `int` | `3` | 任务最大重试次数 |
| `JOB_RETRY_DELAY_SECS` | `int` | `10` | 任务重试延迟（秒） |

## 前端环境变量

| 变量名 | 使用位置 | 说明 |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `web/app/quiz/page.tsx` | 后端 API 地址（默认 `http://localhost:8000`） |

## 硬编码常量

| 位置 | 常量 | 值 |
|---|---|---|
| `web/lib/constants.ts` | `WECHAT_ID` | 规划师微信号 |
| `web/app/submitted/page.tsx` | `PLANNER_WECHAT` | `"sakura_plan"` |
| `app/domains/planning/copywriter.py` | `_REDIS_TTL` | `604800`（7天秒数） |
| `app/domains/planning/copywriter.py` | `_GPT_TIMEOUT` | `3.0`（秒） |