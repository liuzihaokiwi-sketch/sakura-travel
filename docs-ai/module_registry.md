# Module Registry

| 模块路径 | 职责 | 关键函数/类 |
|---|---|---|
| `app/main.py` | FastAPI 应用入口，路由注册，lifespan | `app`, `lifespan()` |
| `app/core/config.py` | 全局配置（Pydantic Settings） | `Settings`, `settings` |
| `app/core/queue.py` | Redis 连接池管理 | `init_redis_pool()`, `get_redis_pool()` |
| `app/core/snapshots.py` | 快照 TTL 管理 | — |
| `app/db/session.py` | SQLAlchemy async session 工厂 | `AsyncSessionLocal`, `engine`, `Base` |
| `app/db/models/catalog.py` | Catalog 层 ORM（8 表） | `EntityBase`, `Poi`, `Hotel`, `Restaurant`, `EntityTag`, `EntityMedia`, `EntityEditorNote`, `HotelAreaGuide` |
| `app/db/models/business.py` | Business 层 ORM（8 表） | `User`, `ProductSku`, `Order`, `TripRequest`, `TripProfile`, `TripVersion`, `ReviewJob`, `ReviewAction` |
| `app/db/models/derived.py` | Derived 层 ORM（13 表） | `EntityScore`, `ItineraryPlan`, `ItineraryDay`, `ItineraryItem`, `PlannerRun`, `CandidateSet`, `RouteMatrixCache`, `RouteTemplate`, `RenderTemplate`, `ExportJob`, `ExportAsset`, `PlanArtifact`, `ItineraryScore` |
| `app/db/models/snapshots.py` | Snapshots 层 ORM（6 表） | `SourceSnapshot`, `HotelOfferSnapshot`, `HotelOfferLine`, `FlightOfferSnapshot`, `PoiOpeningSnapshot`, `WeatherSnapshot` |
| `app/api/chat.py` | 自然语言对话 API | `chat_start()`, `chat_refine()`, `chat_confirm()` |
| `app/api/orders.py` | 订单 CRUD | `create_order()`, `list_orders()`, `get_order()`, `update_order_status()` |
| `app/api/pois.py` | 景点搜索/详情 | `search_pois()`, `get_poi_detail()`, `list_cities()` |
| `app/api/products.py` | 产品 SKU | `list_products()`, `get_product()`, `calculate_price()` |
| `app/api/quiz.py` | 问卷提交 | `submit_quiz()` |
| `app/api/trips.py` | 行程管理 | `create_trip()`, `get_trip()`, `get_trip_status()` |
| `app/api/trips_generate.py` | 行程生成/导出 | `generate_trip()`, `get_plan()`, `export_plan()`, `get_preview()` |
| `app/api/ops/editorial.py` | 编辑操作 API | — |
| `app/api/ops/entities.py` | 实体管理 API | — |
| `app/api/ops/ranked.py` | 排行查询 API | — |
| `app/domains/intake/intent_parser.py` | NLP 意图解析 | `parse_trip_intent()`, `refine_intent()`, `TripIntentResult` |
| `app/domains/geography/region_router.py` | 区域推荐路由 | `resolve_user_type()`, `rank_regions()`, `recommend_regions_for_profile()`, `load_seed_data()` |
| `app/domains/geography/route_selector.py` | 路线模板匹配 | `select_routes()`, `recommend_routes_for_profile()`, `RouteMatch` |
| `app/domains/catalog/pipeline.py` | 城市数据采集管线 | `run_city_pipeline()`, `run_all_cities()`, `ingest_*()` |
| `app/domains/catalog/tagger.py` | GPT 标签生成 | `generate_tags_for_entities()`, `generate_tags_for_city()`, `get_entity_affinity()` |
| `app/domains/catalog/ai_generator.py` | AI 生成实体数据 | `generate_pois()`, `generate_restaurants()`, `generate_hotels()` |
| `app/domains/catalog/google_places.py` | Google Places 同步 | `search_places()`, `sync_poi_to_db()`, `sync_hotel_to_db()` |
| `app/domains/catalog/serp_sync.py` | SerpAPI 搜索同步 | `search_tabelog_restaurants()`, `search_google_pois()`, `bulk_sync_city()` |
| `app/domains/catalog/web_crawler.py` | OSM/Tabelog 爬虫 | `fetch_osm_pois()`, `fetch_tabelog_restaurants()` |
| `app/domains/catalog/upsert.py` | 实体 upsert 工具 | `upsert_entity()` |
| `app/domains/ranking/scorer.py` | 评分核心逻辑 | `compute_base_score()`, `compute_context_score()`, `apply_editorial_boost()` |
| `app/domains/ranking/affinity.py` | 亲和度查询 | `get_affinity()`, `score_entity_context()` |
| `app/domains/ranking/queries.py` | 排行查询 | `get_ranked_entities()`, `get_entity_score()` |
| `app/domains/ranking/theme_weights.py` | 主题权重计算 | `compute_weights_from_answers()` |
| `app/domains/planning/assembler.py` | 行程装配器 | `assemble_trip()`, `load_template()`, `fetch_slot_candidates()` |
| `app/domains/planning/copywriter.py` | AI 文案润色 | `generate_copy()`, `batch_generate_copy()` |
| `app/domains/planning/route_matrix.py` | 路行矩阵 | `get_travel_time()`, `get_travel_time_matrix()` |
| `app/domains/rendering/renderer.py` | HTML/PDF 渲染 | `render_html()`, `render_pdf()` |
| `app/workers/__main__.py` | Worker 启动 + normalize job | `normalize_trip_profile()`, `WorkerSettings` |
| `app/workers/jobs/generate_plan.py` | 生成行程方案 | `generate_itinerary_plan()` |
| `app/workers/jobs/generate_trip.py` | 填充行程详情 | `generate_trip()` |
| `app/workers/jobs/render_export.py` | 渲染导出 | `render_export()` |
| `app/workers/jobs/run_guardrails.py` | 护栏检查 | `run_guardrails()` |
| `app/workers/jobs/score_entities.py` | 实体评分 | `score_entities()` |
| `app/workers/jobs/scan_flight_prices.py` | 航班价格扫描 | `scan_flight_prices()` |

## 新增模块（2026-03-21 更新）

| 模块路径 | 职责 | 关键函数/类 |
|---|---|---|
| `app/core/logging_config.py` | structlog 日志配置 | `setup_logging()` |
| `app/api/modifications.py` | 用户修改请求 API | `submit_modification()`, `list_modifications()` |
| `app/api/review.py` | 管理员审核 API | `list_pending_reviews()`, `publish_order()`, `reject_order()` |
| `scripts/crawl_orchestrator.py` | 全日本并行爬取调度器 | `CrawlOrchestrator`, `run()` |
| `scripts/crawlers/base.py` | 爬虫基类（自适应限速） | `BaseCrawler`, `adaptive_delay()` |
| `scripts/crawlers/playwright_base.py` | Playwright 爬虫基类 | `PlaywrightCrawler` |
| `scripts/crawlers/sakura_pipeline/cli.py` | 樱花管线 CLI | `fetch()`, `fuse()`, `all()` |
| `scripts/crawlers/sakura_pipeline/fusion.py` | 多源数据融合 | `fuse_all_sources()` |
| `scripts/crawlers/sakura_pipeline/providers/jma.py` | JMA 气象厅数据 | `fetch_jma_bloom()` |
| `scripts/crawlers/sakura_pipeline/providers/weathernews.py` | Weathernews 数据 | `fetch_weathernews()` |
| `scripts/sync_remote_to_local.py` | 远端→本地数据同步 | `sync_table()`, `main()` |
| `scripts/fix_and_init.py` | 数据库修复与初始化 | `normalize_scores()`, `add_area_names()`, `add_tags()` |
| `scripts/smart_commit.py` | 自动语义化 commit | `smart_commit()` |
| `scripts/maintain.py` | 一键维护工具 | `deploy()`, `status()`, `restart()` |
| `web/lib/data.ts` | 樱花数据加载+格式转换 | `getRushScores()`, `getWeathernewsSpots()` |
| `web/app/rush/RushClient.tsx` | 樱花排行榜客户端组件 | `RushClient`, `SpotCard`, `BloomTimeline` |
| `web/app/api/export/plan-image/route.ts` | Playwright 截图导出 API | `POST /api/export/plan-image` |
