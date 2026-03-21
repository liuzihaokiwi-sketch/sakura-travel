# Config Inventory（AI 版）

## 原则
只记录对当前主链路重要的配置，不重复罗列所有低优先级变量。

## 核心后端配置
- `APP_ENV`
- `APP_DEBUG`
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `AI_BASE_URL`
- `AI_MODEL`
- `AI_MODEL_STRONG`
- `OPENAI_API_KEY`
- `GOOGLE_PLACES_API_KEY`

## 运维/告警配置
- `WECOM_WEBHOOK_URL`
- `SMTP_HOST`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `ALERT_EMAIL`

## Worker/TTL 配置
- `SNAPSHOT_TTL_HOTEL_OFFER`
- `SNAPSHOT_TTL_FLIGHT_OFFER`
- `SNAPSHOT_TTL_POI_OPENING`
- `SNAPSHOT_TTL_WEATHER`
- `WORKER_MAX_JOBS`
- `JOB_RETRY_MAX`
- `JOB_RETRY_DELAY_SECS`

## 前端关键配置
- `NEXT_PUBLIC_API_URL`

## 当前配置问题
1. 微信号存在前端硬编码
2. 一些价格和产品逻辑不应该继续分散在配置/种子/文案里
3. 当前项目缺少独立的 single source of truth 配置文件

## 建议
后续新增：
- `single_source_of_truth.yaml`
用于统一：
- 价格参考价
- 免费体验边界
- 自助微调规则
- 正式修改次数
- 页面职责
