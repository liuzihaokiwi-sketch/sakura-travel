# Pipeline Catalog

## Worker Jobs (arq 异步任务)

| Job 函数 | 文件 | 输入 | 处理 | 输出 |
|---|---|---|---|---|
| `normalize_trip_profile` | `workers/__main__.py` | `trip_request_id` | 解析 raw_input → 结构化画像 | `trip_profiles` 记录 |
| `generate_itinerary_plan` | `workers/jobs/generate_plan.py` | `trip_request_id` | 区域推荐 → 路线匹配 → 行程骨架 | `itinerary_plans` + `itinerary_days` |
| `generate_trip` | `workers/jobs/generate_trip.py` | `trip_request_id` | 加载模板 → 候选填充 → 文案润色 | `itinerary_items` 填充 |
| `render_export` | `workers/jobs/render_export.py` | `plan_id` | Jinja2 渲染 → HTML → PDF/H5 | `export_jobs` + `export_assets` |
| `run_guardrails` | `workers/jobs/run_guardrails.py` | `plan_id` | 质量检查（时间/交通/重复/餐覆盖） | 检查结果 + 状态更新 |
| `score_entities` | `workers/jobs/score_entities.py` | `city_code` | 提取信号 → 评分计算 | `entity_scores` 更新 |
| `scan_flight_prices` | `workers/jobs/scan_flight_prices.py` | — | Amadeus API 查询 | `flight_offer_snapshots` |

## Data Ingestion Pipelines (scripts/)

| 脚本 | 输入 | 处理 | 输出 |
|---|---|---|---|
| `scripts/crawl.py` | 命令行参数 | 调度各爬虫 | 原始 JSON 文件 |
| `scripts/generate_tags.py` | `--city` 参数 | GPT 标签生成 | `entity_tags` 更新 |
| `scripts/mark_data_tier.py` | — | 评分规则 → 分层标记 | `entity_base.data_tier` 更新 |
| `scripts/ingest_all.py` | — | 读取 *_raw/ JSON → 入库 | `entity_base` + 扩展表 |
| `scripts/load_route_templates.py` | — | 读取 route_templates/*.json → 入库 | `route_templates` 表 |
| `scripts/seed_product_skus.py` | — | 创建 SKU 种子数据 | `product_sku` 表 |

## Catalog Pipeline (app/domains/catalog/pipeline.py)

| 函数 | 输入 | 处理 | 输出 |
|---|---|---|---|
| `run_city_pipeline()` | city_code, options | AI 生成 / OSM 爬虫 / SERP → upsert | entity_base + 扩展表 |
| `run_all_cities()` | options | 循环 12 城市调用 run_city_pipeline | 同上 |
| `ingest_hotel_crawl()` | JSON 文件 | 解析酒店数据 → 入库 | hotels |
| `ingest_tabelog_crawl()` | JSON 文件 | 解析 Tabelog 数据 → 入库 | restaurants |
| `ingest_jnto_spots()` | JSON 文件 | 解析 JNTO 景点 → 入库 | pois |
| `ingest_events()` | JSON 文件 | 解析活动数据 → 入库 | entity_base |
| `ingest_experiences()` | JSON 文件 | 解析体验数据 → 入库 | entity_base |

## Crawlers (scripts/crawlers/)

| 爬虫 | 来源 | 数据类型 |
|---|---|---|
| `tabelog.py` | Tabelog | 餐厅评分/价格 |
| `hotels.py` | 多平台 | 酒店信息 |
| `events.py` | 活动平台 | 活动/节日 |
| `experiences.py` | 体验平台 | 体验项目 |
| `jnto.py` | JNTO 官方 | 景点 |
| `google_flights.py` | Google Flights | 航班 |
| `skyscanner.py` | Skyscanner | 航班 |
| `tianxun.py` | 天巡 | 航班 |
| `xiaohongshu.py` | 小红书 | 用户内容 |
| `letsgojp.py` | Letsgojp | 攻略 |
| `matcha.py` | Matcha | 攻略 |