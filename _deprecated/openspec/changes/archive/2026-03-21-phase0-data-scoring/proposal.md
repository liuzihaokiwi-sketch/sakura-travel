## Why

Phase 0 骨架已完成（FastAPI + 35 张表 + Trip API + Worker 框架），但 Catalog 中零数据、评分引擎无法端到端跑通、运营无法干预排序结果。没有实体数据和评分，Phase 1 引流款产品无法启动。本阶段是"数据底座 → 评分可用"的关键衔接，属于 MVP 最高优先级。

**在产品价位梯度中的作用**：所有价位（¥20 引流款 → ¥299 高客单）都依赖 Catalog 数据 + 评分排序。本阶段产出的实体库和评分是整个产品线的基础设施。

**MVP 优先级**：🔴 P0（阻塞所有下游功能）

## What Changes

### 数据灌入（W2）
- 完善 Google Places API 接入：补全 field mask 配置、batch 采集脚本、rate limit 处理
- 批量灌入东京/大阪/京都三城市实体数据（目标 ~800 条）：景点、酒店、餐厅
- 接入 source_snapshots 追溯：每次采集写入 snapshot 记录
- GPT 辅助打标签：为已有实体生成 entity_tags（family_friendly / couple_friendly / luxury / anime 等）
- 补全 entity_media 初始数据（封面图 URL + 图片来源标注）

### 评分引擎对接（W3）
- 将已实现的纯函数 scorer（`scorer.py`）与 arq job（`score_entities.py`）做端到端打通：真实数据 → 真实分数 → 写入 entity_scores 表
- 实现 `editorial_boost` 运营录入 API：`POST /ops/entities/{type}/{id}/editorial-score`
- 实现按 candidate_score 排序的召回接口：`GET /ops/entities/ranked`（带 city_code + entity_type + score_profile 过滤）
- 人工数据分级：批量标记 data_tier（S/A/B），S 级实体优先打 editorial_boost
- 补全 `score_entities` job 在 Worker 中的注册和自动触发（数据采集后自动入队评分）

### 区域匹配落地（W2-W3）
- 将 `data/` 目录下的种子 JSON（region_router、route_binding）加载到 geography 模块
- 实现按区域 + 线路筛选实体的查询能力，为 Phase 1 行程编排做准备

## Capabilities

### New Capabilities
- `catalog-pipeline`: 数据采集调度全流程（Google Places + OSM + Tabelog + AI 生成器 → upsert → snapshots → auto-tag）
- `entity-tagging`: GPT 辅助标签生成 + 批量写入 entity_tags + 标签强度矩阵（theme_affinity）
- `editorial-ops-api`: editorial_boost 录入/查询 API + 按评分排序的实体召回接口

### Modified Capabilities
- `scoring-engine`: 新增端到端 job 触发链路（采集完成 → 自动评分）；新增 ranked 召回接口
- `data-pipeline`: 新增 Google Places field mask 配置 + batch 采集限速 + snapshot 联动
- `geography-routing`: 新增种子数据加载 + 按区域筛选实体的查询能力
- `catalog-entities`: 新增 data_tier 批量标记工具 + entity_media 初始数据灌入

## Impact

**代码变更**：
- `app/domains/catalog/` — pipeline.py 增强、google_places.py 补全、新增 tagger.py
- `app/api/ops/` — 新增 editorial_score.py、ranked_entities.py
- `app/workers/jobs/` — score_entities.py 注册到 WorkerSettings、增加采集后自动入队逻辑
- `app/domains/geography/` — region_router.py 加载种子数据、实现按区域查询
- `scripts/` — 新增 batch 采集脚本、data_tier 标记脚本、tag 生成脚本

**外部依赖**：
- Google Places API Key（已在 .env.example 中声明，需实际配置）
- OpenAI API Key（GPT 辅助打标签 + AI 生成器）
- SerpAPI Key（可选，Tabelog 搜索备用通道）

**数据变更**：
- entity_base / pois / hotels / restaurants：新增 ~800 条记录
- entity_tags：新增标签数据
- entity_scores：首次写入评分结果
- source_snapshots：新增采集快照
- entity_editor_notes：新增 editorial_boost 记录

**无破坏性变更**：所有新增功能不影响已有 Trip API 和 Worker 框架。
