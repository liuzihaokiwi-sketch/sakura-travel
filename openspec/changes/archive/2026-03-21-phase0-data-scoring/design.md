## Context

Phase 0 骨架已就位：FastAPI 应用 + 35 张 PostgreSQL 表 + Trip 提交 API + arq Worker 框架 + source_snapshots 机制。

当前状态：
- `app/domains/catalog/` 已有完整的采集管道代码（pipeline.py、google_places.py、ai_generator.py、web_crawler.py、serp_sync.py、upsert.py），但 **数据库中零数据**
- `app/domains/ranking/scorer.py` 已实现完整的纯函数评分引擎（system_score + context_score + risk_penalty + editorial_boost），有单元测试
- `app/workers/jobs/score_entities.py` 已实现批量评分 job，但 **未注册到 WorkerSettings**
- `app/api/ops/entities.py` 只有基础搜索，**无 editorial_boost 录入接口、无按评分排序召回**
- `app/domains/geography/` 有 region_router.py 和 route_selector.py 框架，`data/` 目录有种子 JSON，**未联通**
- `data/entity_affinity_seed_v1.json` 已有标签亲和度种子数据

约束：
- 使用 arq（非 Celery）作为任务队列
- 数据库为 PostgreSQL + pgvector（已建好）
- 所有采集必须写 source_snapshots 追溯
- 评分纯函数（无 I/O），DB 写入由 job 层负责

## Goals / Non-Goals

**Goals:**
1. 东京/大阪/京都三城市灌入 ~800 条实体（POI + 酒店 + 餐厅），数据可查可用
2. 每条实体自动生成 entity_tags（主题亲和度标签），支持后续 context_score 计算
3. 评分 job 端到端跑通：采集 → 自动触发评分 → entity_scores 表有真实分数
4. 运营可通过 API 录入 editorial_boost、查看按分排序的实体列表
5. 批量标记 data_tier（S/A/B），S 级优先人工校准
6. 区域种子数据加载到内存/缓存，实体可按区域筛选

**Non-Goals:**
- 不做前端 UI（运营端用 API + curl/Postman）
- 不做酒店动态报价接入（Phase 2+）
- 不做行程编排（Phase 1）
- 不做 entity_media 的图片下载/CDN 上传（只记录 URL）
- 不做 pgvector 向量搜索（本阶段用标签 + 评分排序）

## Decisions

### D1：采集策略 — 混合模式优先

**选择**：保持现有 pipeline.py 的混合模式（OSM/Tabelog 真实爬虫 + AI 生成器兜底），Google Places 作为补充通道。

**理由**：
- 已有代码支持自动检测网络连通性并选择数据源
- AI 生成器能立即出数据（不依赖外部 API 配额），适合快速填充基础数据
- Google Places 用于后续增量更新和字段补全（rating、review_count 等）
- 替代方案（纯 Google Places）：成本高、有 API 配额限制、无法覆盖 Tabelog 评分

### D2：标签生成 — GPT 批量生成 + 种子数据校准

**选择**：用 OpenAI GPT-4o-mini 批量为实体生成 theme_affinity 标签（9 个维度，0-5 强度），然后用 `entity_affinity_seed_v1.json` 中的人工种子数据覆盖校准。

**理由**：
- GPT 成本低（mini 模型），800 条实体约 $0.5
- 种子数据已有典型实体的标签模板，可直接覆盖
- 替代方案（纯人工打标）：800 条人工打标耗时数天，GPT 预标注 + 人工校准 S 级更高效

### D3：评分触发 — 采集完成后自动入队

**选择**：在 pipeline.py 的 `run_city_pipeline()` 末尾自动调用 `enqueue_job("score_entities", city_code=xxx)`。

**理由**：
- 保证数据一灌入就有分数，不需要人工记得手动跑
- score_entities job 已实现幂等性（UPSERT），重复触发无副作用
- 替代方案（手动触发 / cron 定时）：容易遗忘，数据和分数不同步

### D4：editorial_boost 录入 — 直接写 entity_editor_notes 表

**选择**：`POST /ops/entities/{entity_type}/{entity_id}/editorial-score` 直接写 `entity_editor_notes` 表，note_type="editorial_boost"。

**理由**：
- 表已建好，score_entities job 已能从 editor_notes 中提取 boost 值
- 支持有效期（valid_until），过期自动失效
- 写入后自动触发该实体的重新评分
- 替代方案（单独建 editorial_boost 表）：多余，editor_notes 已覆盖

### D5：区域数据加载 — 启动时加载到内存字典

**选择**：在 FastAPI startup 事件中加载 `data/*.json` 种子文件到全局字典，`region_router.py` 查询时直接从内存读取。

**理由**：
- 种子数据量小（12 区域 + 29 线路），无需数据库查询
- 查询频率高（每次行程规划都要用），内存访问零延迟
- 替代方案（写入 DB 查询）：增加复杂度，种子数据变更频率极低

### D6：data_tier 批量标记 — 脚本 + API 双通道

**选择**：提供 `scripts/mark_data_tier.py` 批量脚本（按规则自动标记）+ `PATCH /ops/entities/{id}/data-tier` API（人工单条调整）。

**理由**：
- 自动规则：有 Google Place ID → A，有 OSM 来源 → A，纯 AI 生成 → B，人工确认 → S
- API 用于后续人工逐条提升到 S 级
- 替代方案（纯手动）：初始 800 条无法逐条标记

## Risks / Trade-offs

| 风险 | 缓解 |
|---|---|
| AI 生成数据质量不稳定（幻觉地址、虚假评分） | GPT prompt 要求只输出真实存在的地点 + 后续 Google Places 交叉验证补全 |
| Google Places API 配额不足 | 初始灌入优先用 AI + OSM，Google Places 只做增量补全 |
| 标签生成偏差（GPT 对日本文化理解不够） | 种子数据覆盖核心实体 + S 级实体人工复核 |
| score_entities job 大批量耗时长 | 已实现分批处理（BATCH_SIZE=100），支持按城市/类型过滤 |
| region_router 内存加载在多 worker 进程下重复 | 数据量极小（<1MB），多进程复制无性能问题 |
