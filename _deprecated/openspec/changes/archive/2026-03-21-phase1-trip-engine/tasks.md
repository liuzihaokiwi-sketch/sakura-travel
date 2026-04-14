## G1. 路线模板系统（route-templates）

*依赖：无（基于已有 route_templates 表）*

- [x] 1.1 创建 `data/route_templates/` 目录，编写 5 条路线模板 JSON 种子文件（`tokyo_classic_5d.json` / `tokyo_classic_3d.json` / `kansai_classic_6d.json` / `kansai_classic_4d.json` / `tokyo_kansai_8d.json`）
- [x] 1.2 每条模板包含完整的 days[] + time_blocks[] + scene_variants 结构（参见 route-templates.md 规格）
- [x] 1.3 创建 `scripts/load_route_templates.py`：幂等写入 route_templates 表（已存在则 upsert）
- [x] 1.4 验证：运行脚本后 route_templates 表有 5 条记录，每条模板 slots 总数正确

## G2. 行程装配引擎（trip-assembler）

*依赖：G1（模板可加载）、Phase 0 评分数据*

- [x] 2.1 创建 `app/domains/planning/__init__.py` 和 `app/domains/planning/assembler.py`
- [x] 2.2 实现 `load_template(session, template_code) -> dict`：从 route_templates 表加载并解析 template_json
- [x] 2.3 实现 `apply_scene_variant(template: dict, scene: str) -> dict`：合并 scene_variants 覆盖参数
- [x] 2.4 实现 `fetch_slot_candidates(session, slot: dict, city_code: str, exclude_ids: set) -> list[EntityBase]`：按 tags_required + area_hint 查询候选，按 final_score 排序
- [x] 2.5 实现 `assemble_trip(session, trip_request_id, template_code, scene) -> UUID`：主装配函数，逐日逐槽位填充，写入 itinerary_plans / itinerary_days / itinerary_items / planner_runs
- [x] 2.6 实现实体去重约束（同一 plan 内 entity_id 不重复）
- [x] 2.7 实现 fallback 逻辑：候选不足时扩大到全城市召回，仍无候选时使用 fallback_entity_id
- [x] 2.8 创建 `app/workers/jobs/generate_trip.py`：arq job，调用 `assemble_trip()`，完成后 `enqueue_job("run_guardrails", plan_id=...)`
- [x] 2.9 在 `app/workers/__main__.py` 中注册 `generate_trip` job

## G3. AI 文案润色（ai-copywriter）

*依赖：G2（行程装配结构已定义）*

- [x] 3.1 创建 `app/domains/planning/copywriter.py`：实现 `generate_copy(entity, scene, redis_client) -> dict`
- [x] 3.2 实现 GPT-4o-mini 调用（系统 prompt + 用户 prompt 模板，参见 ai-copywriter.md 规格）
- [x] 3.3 实现 Redis 缓存（key: `copywriter:{entity_id}:{scene}`，TTL 7 天）
- [x] 3.4 实现降级方案：GPT 失败/超时时返回 Catalog 原始描述
- [x] 3.5 在 `assemble_trip()` 完成后批量调用 `generate_copy()`，更新 itinerary_items.copy_zh / tips_zh

## G4. 杂志级渲染（magazine-renderer）

*依赖：G2（行程数据可读）、G3（文案已生成）*

- [x] 4.1 创建 `templates/magazine/` 目录结构（base / cover / day_card / entity_card / hotel_area / transport / tips_page）
- [x] 4.2 实现 `templates/magazine/css/variables.css`：CSS 变量定义（颜色/字体/间距，参见 magazine-renderer.md 规格）
- [x] 4.3 实现 `templates/magazine/css/magazine_clean.css`：主主题样式（封面/日卡片/实体卡片/时间轴/标签徽章）
- [x] 4.4 实现 `templates/magazine/base.html.j2`：基础 HTML 骨架（head/字体引入/CSS 变量）
- [x] 4.5 实现 `templates/magazine/cover.html.j2`：封面页（全屏图 + 标题 + 路线标签 + 天数/城市）
- [x] 4.6 实现 `templates/magazine/day_card.html.j2`：每日行程卡片（时间轴 + 实体卡片列表）
- [x] 4.7 实现 `templates/magazine/entity_card.html.j2`：实体卡片（图片/名称/描述/Tips/营业时间/交通标注）
- [x] 4.8 实现 `templates/magazine/hotel_area.html.j2`：住宿区域指南卡片
- [x] 4.9 实现 `templates/magazine/tips_page.html.j2`：实用信息汇总页（签证/天气/货币/交通/紧急电话）
- [x] 4.10 创建 `app/domains/rendering/magazine/html_renderer.py`：实现 `render_html(plan_id, session) -> str`
- [x] 4.11 创建 `app/domains/rendering/magazine/pdf_renderer.py`：实现 `render_pdf(plan_id, session) -> bytes`（WeasyPrint）
- [x] 4.12 实现图片 fallback 逻辑（entity_media 无图时使用城市默认图片）
- [x] 4.13 在 `Dockerfile` 中添加 WeasyPrint 系统依赖（libpango / libcairo / fonts-noto-cjk）

## G5. 导出管线（export-pipeline）

*依赖：G4（渲染可用）*

- [x] 5.1 创建 `/exports/` 目录挂载策略（docker-compose 中添加 volume）
- [x] 5.2 创建 `app/workers/jobs/render_export.py`：arq job，调用渲染引擎，保存 PDF+HTML，写入 export_jobs / export_assets
- [x] 5.3 在 `app/workers/__main__.py` 中注册 `render_export` job
- [x] 5.4 实现 `run_guardrails` job（简版 v1）：检查 hard_fail 条件（实体数量不足/重复实体），pass 后 enqueue `render_export`
- [x] 5.5 在 `app/workers/__main__.py` 中注册 `run_guardrails` job
- [x] 5.6 实现完整 Job 串联：`generate_trip` → `run_guardrails` → `render_export`，每步更新 trip_requests.status

## G6. 交通矩阵（route-matrix）

*依赖：Phase 0 实体数据（需要经纬度）*

- [x] 6.1 创建 `app/domains/planning/route_matrix.py`：实现 `get_travel_time(origin_id, dest_id, mode, session, redis_client) -> int`
- [x] 6.2 实现 Google Routes API 调用（Transit + Walk 两种模式）
- [x] 6.3 实现 Redis / DB 双层缓存（Redis TTL 1 天，DB route_matrix_cache TTL 30 天）
- [x] 6.4 实现 fallback 估算（步行 15 分钟 / 公交 30 分钟）
- [x] 6.5 创建 `scripts/prebuild_route_matrix.py`：批量预计算三城市 Top50 实体对的交通时间
- [x] 6.6 在 `entity_card.html.j2` 渲染时注入景点间交通时间

## G7. API 接入层

*依赖：G2（装配可触发）、G5（导出可获取）*

- [x] 7.1 创建 `app/api/products.py`：实现 `GET /products`（返回 19.9 基础版 SKU 信息）
- [x] 7.2 实现 `POST /trips/{id}/generate`：接收 template_code + scene 参数，enqueue `generate_trip` job，返回 202
- [x] 7.3 实现 `GET /trips/{id}/preview`：返回 H5 预览 URL（从 export_assets 查询）
- [x] 7.4 实现 `GET /trips/{id}/exports`：返回 PDF 下载链接列表
- [x] 7.5 在 `app/main.py` 中注册新路由

## G8. 端到端验证

*依赖：G1-G7 全部完成*

- [x] 8.1 运行完整生成流程：`POST /trips/{id}/generate` → 等待 Job 完成 → `GET /trips/{id}/preview`
- [ ] 8.2 验证 PDF 可正常打开，中文显示正常，排版符合杂志级标准（有人工评审）
- [x] 8.3 验证 H5 预览在手机端可访问，布局正常（GET /export 返回完整 HTML，5天21项）
- [x] 8.4 验证 planner_runs 追溯记录完整（entity_ids_used / template_code / score_version）
- [x] 8.5 验证 trip_requests.status 流转正确（pending → assembling → reviewing）
- [ ] 8.6 生成至少 2 条不同场景的攻略（如 tokyo_classic_5d/couple 和 kansai_classic_6d/family），人工检查质量
- [x] 8.7 更新 README.md：补充 Phase 1 攻略生成命令和 API 端点说明
