# 项目全面审计报告

> 2026-03-29 | 审计范围：全代码库 app/ scripts/ tests/ deploy/
> 每个任务标注：模型推荐(Opus/Sonnet)、思考强度(普通/深度思考)

---

## 一、数据可信度体系（新建）

### T0-1. entity_base 增加数据可信度字段 [Sonnet · 普通]
**文件**: `app/db/models/catalog.py`, 新 migration
**问题**: 当前 `data_tier` (S/A/B) 只表示数据来源等级，不表示"这条数据是否可信、是否经过人工验证"。AI 生成的数据和 OSM 爬的混在一起，无法区分。
**方案**:
```
entity_base 新增字段：
  trust_status  VARCHAR(20) DEFAULT 'unverified'
    -- 'verified'    人工已验证
    -- 'unverified'  未验证（真实数据源拉取的）
    -- 'ai_generated' AI 生成，待验证
    -- 'suspicious'  存疑，需人工复核
    -- 'rejected'    已拒绝，不参与推荐
  verified_by   VARCHAR(100) NULL   -- 谁验证的
  verified_at   TIMESTAMPTZ  NULL   -- 何时验证
  trust_note    TEXT         NULL   -- 审核备注
```
- 所有现有 AI 生成数据 UPDATE 为 `ai_generated`
- OSM/Tabelog 爬取的 UPDATE 为 `unverified`
- pipeline.py 写入时根据数据来源自动设置 trust_status
- scorer.py 评分时 `ai_generated` 和 `suspicious` 降权，`rejected` 排除

### T0-2. 管理端数据审核页面 [Sonnet · 普通]
**文件**: `app/api/admin_review.py`（新建）, 前端页面
**方案**:
- GET `/admin/entities/review` — 列出所有 trust_status != 'verified' 的实体，支持按 city_code/entity_type/trust_status 筛选
- PATCH `/admin/entities/{entity_id}/trust` — 更新 trust_status, verified_by, trust_note
- GET `/admin/entities/stats` — 各 trust_status 数量统计
- 管理端页面显示：名称、坐标(地图pin)、来源、trust_status，操作按钮(验证/存疑/拒绝)

### T0-3. pipeline 写入时自动标记 trust_status [Sonnet · 普通]
**文件**: `app/domains/catalog/pipeline.py`, `app/domains/catalog/upsert.py`
**规则**:
- source = osm/tabelog/google/booking/agoda/jnto → `unverified`
- source = ai_generator → `ai_generated`
- 缺坐标或坐标超出城市 bbox → `suspicious`
- 缺名称或名称与已有记录相似度 > 90% → `suspicious`

### T0-4. scorer 根据 trust_status 调整权重 [Sonnet · 普通]
**文件**: `app/domains/ranking/scorer.py`
- `rejected` → 直接排除，不参与评分
- `ai_generated` → 基础分 ×0.6
- `suspicious` → 基础分 ×0.3
- `unverified` → 基础分 ×0.9
- `verified` → 基础分 ×1.0

---

## 二、系统性问题（必须修）

### T1-1. 异常吞掉：全局整改 [Sonnet · 普通]
**影响范围**: 40+ 处 except → pass/logger.debug
**关键文件**:
- `app/workers/jobs/generate_trip.py` — 42+ 处 bare except
- `app/domains/catalog/pipeline.py` — 快照写入、爬虫失败全部静默
- `app/domains/planning/budget_estimator.py` — 酒店价格查询失败静默
- `app/domains/planning/plan_b_builder.py` — 天气/替代方案查询静默
- `app/domains/validation/engine.py:203-216` — 5 处 bare `except: return False`
- `app/domains/rendering/copy_enrichment.py` — AI 丰富失败静默

**修复标准**:
- 不可恢复的错误（DB 连接断开）→ raise，让上层处理
- 可恢复的降级（快照写入）→ logger.warning + metric counter
- 绝不允许 `except: pass` 或 `except Exception: logger.debug(...)`
- 每个 catch 块必须说明：为什么可以降级、降级后的行为是什么

### T1-2. 生产凭证硬编码 [Sonnet · 普通]
**文件**: `app/core/config.py`
- Line 21: `secret_key = "change_me_in_production"` ← 删除默认值，强制从 env 读取
- Line 61: `admin_password = "admin123"` ← 同上
- Line 29: `postgres_password = "japan_ai_dev"` ← 同上
- 新增：`app_env` 为 production 时，如果这些字段是默认值，启动时直接报错退出

### T1-3. Admin 端点无认证 [Sonnet · 普通]
**文件**: `app/main.py` lines 126-204
**问题**: `/admin/sync/{city_code}`, `/admin/sync-all` 等端点没有任何认证
**修复**: 加 `Depends(verify_admin_token)` 中间件，token 从 env 读取

### T1-4. CORS 过于宽松 [Sonnet · 普通]
**文件**: `app/main.py` line 95
**问题**: `allow_methods=["*"], allow_headers=["*"]`
**修复**: 限制为实际使用的 methods 和 headers

### T1-5. 连接池太小 [Sonnet · 普通]
**文件**: `app/db/session.py` lines 11-17
**问题**: `pool_size=5, max_overflow=10`，总共 15 连接
**修复**: `pool_size=20, max_overflow=20`，加 `pool_timeout=30`

---

## 三、偷懒模式修复

### T2-1. "Config 空壳"模式 [Sonnet · 普通]
**受影响文件**:
- `app/domains/planning/budget_estimator.py:32-38` — `_load_budget_config()` 永远返回空 dict
- `app/domains/validation/engine.py:109-110` — rules 文件不存在时返回空规则
- `app/core/config.py:93-94` — `@lru_cache` 无法运行时重载

**修复**:
- budget_config 接入 `data/seed/pace_config.json` 或 config_packs 表
- validation rules 缺失时启动报错，不静默降级
- config 支持 reload（去掉 lru_cache，用 TTL cache）

### T2-2. "Feature flag 永远 on" 模式 [Sonnet · 普通]
**受影响文件**:
- `app/domains/planning/itinerary_builder.py:40` — `CIRCLE_WRITE_MODE = "live"` 硬编码
- `app/workers/jobs/generate_trip.py:27` — `REVIEW_PIPELINE_ENABLED = True` 无法关闭
- `app/workers/jobs/generate_trip.py:885-888` — 非 live 模式直接 return False（死代码）

**修复**:
- 从 config/env 读取 feature flags
- shadow 模式和 disabled 模式要能真正工作，或者删掉

### T2-3. 魔法数字提取为配置 [Sonnet · 普通]
**受影响文件**:
- `itinerary_builder.py:417` — 晚餐60min/午餐45min 写死
- `itinerary_builder.py:67-69` — 用餐时间 08:00/12:00/18:30 写死
- `itinerary_builder.py:45-64` — 每 slot 75 分钟，无文档
- `budget_estimator.py:62-70` — 门票默认值（寺庙500、博物馆1000、主题公园7000）
- `route_skeleton_builder.py:549` — 有司机扣 0.3 容量单位
- `route_skeleton_builder.py:635` — intensity order 硬编码
- `pipeline.py:46-49` — CNY_TO_JPY_RATE = 21 写死

**修复**: 全部提取到 `data/seed/planning_defaults.json`，代码读配置

### T2-4. Copy-paste 三兄弟合并 [Sonnet · 普通]
**文件**: `app/domains/catalog/pipeline.py:73-256`
**问题**: `_write_poi()`, `_write_restaurant()`, `_write_hotel()` 三个函数结构完全一样
**修复**: 合并为 `_write_entity(session, data, entity_type, field_mapping)` 一个泛型函数

### T2-5. Budget 计算竞态 [Sonnet · 普通]
**文件**: `app/domains/planning/budget_estimator.py:100-101`
**问题**: `total_jpy` property 内部修改 `self.misc_jpy`，读属性顺序影响结果
**修复**: misc_jpy 在 __init__ 或专门的 finalize() 中计算，property 只读

### T2-6. 汇率硬编码 [Sonnet · 普通]
**文件**: `app/domains/catalog/pipeline.py:46-49`
**问题**: `CNY_TO_JPY_RATE = 21` 永远不更新
**修复**: 启动时从免费汇率 API（如 exchangerate-api.com）拉取，缓存 24h

---

## 四、数据质量问题

### T3-1. 坐标无边界校验 [Sonnet · 普通]
**文件**: `app/domains/catalog/web_crawler.py`, `app/domains/catalog/pipeline.py`
**问题**:
- OSM 返回坐标不验证是否在城市 bbox 内
- Tabelog 爬虫完全不抓坐标
- lat=0/lng=0 能通过写入
**修复**:
- upsert_entity 增加坐标校验：不在 bbox 内 → trust_status='suspicious'
- Tabelog 无坐标 → 通过 SerpAPI/Google 补坐标

### T3-2. 去重逻辑太弱 [Opus · 深度思考]
**文件**: `app/domains/catalog/upsert.py:152-161`
**问题**: name_zh 完全匹配才去重，"浅草寺" vs "浅草寺 " 会创建两条
**修复**:
- name_zh strip + normalize 后匹配
- 同城市 500m 内同类型实体 → 疑似重复，标记 suspicious
- 加 Levenshtein 距离 < 2 的模糊匹配

### T3-3. _guess_cuisine 默认 "japanese" [Sonnet · 普通]
**文件**: `app/domains/catalog/pipeline.py:259-274`
**问题**: 未匹配菜系全部标为 "japanese"
**修复**: 未匹配时标为 "unknown"，trust_status = 'suspicious'

### T3-4. 爬虫覆盖面不足 [参见第六节爬虫体系]
- CITY_BBOX 只覆盖 11 城市 → 扩展到全部日本城市
- TABELOG_CITY_PREFIX 只覆盖 11 城市 → 扩展
- 中国城市零爬虫覆盖 → 建立携程/大众点评爬虫

---

## 五、架构问题

### T4-1. 缺少 Service 层 [Opus · 深度思考]
**问题**: API endpoint 直接调用 domain 逻辑，无中间抽象
**影响**: `app/api/trips_generate.py` 导入 5+ domain 模块，紧耦合
**修复**:
- 新建 `app/services/` 层
- API → Service → Domain，Service 负责编排和事务管理
- 不急，可以后续重构

### T4-2. Rendering ↔ Planning 循环依赖 [Opus · 普通]
**问题**: rendering 导入 planning，planning 导入 rendering
**修复**: 提取共享数据结构到 `app/domains/shared/schemas.py`

### T4-3. N+1 查询 [Sonnet · 普通]
**文件**: `app/workers/jobs/generate_trip.py:128-129`
**问题**: 循环内逐条 `session.get(EntityBase, item.entity_id)`
**修复**: 批量 `select(EntityBase).where(EntityBase.entity_id.in_(ids))`

### T4-4. 全局可变状态 [Sonnet · 普通]
**文件**:
- `app/api/trips_preview.py` — `global _config_cache`
- `app/core/ai_cache.py` — `global _langfuse`（非线程安全）
- `app/core/queue.py` — `global _redis_pool`
**修复**: 用 `asyncio.Lock` 保护初始化，或用 FastAPI dependency injection

### T4-5. 死表/死代码清理 [Sonnet · 普通]
**DB 死表**: candidate_pool_cache, entity_alternatives, transit_matrix, entity_time_window_scores, user_entity_feedback, city_monthly_context
**Model 死类**: PreviewTriggerScore, SwapCandidateSoftScore, StageWeightPack, ProductConfig, FeatureFlag, UserEvent（均标 DEPRECATED）
**死脚本**: `app/workers/scripts/candidate_pool_precompute.py` 引用不存在的 PlanSlot model
**修复**:
- 死表: 新 migration drop（先确认无数据）
- 死 model: 删除
- 死脚本: 删除

### T4-6. 快照无 TTL 清理 [Sonnet · 普通]
**问题**: source_snapshots 有 expires_at 但无 cleanup job
**修复**: 加 cron job 或 worker task 定期删除过期快照

### T4-7. 硬编码文件路径 [Sonnet · 普通]
**文件**:
- `scripts/export_plan_pdf.py:57-59` — Windows 字体路径
- `scripts/convert_md_to_pdf.py:20-22` — 同上
- `app/domains/rendering/magazine/pdf_renderer.py:148,186-187` — 同上
- `deploy/ai-ops/server.py:20` — `/opt/travel-ai` 硬编码
**修复**: 从 config 读取，按 platform 自动检测

---

## 六、爬虫体系设计（新建）

### T5-1. Google Places API 集成 [Opus · 深度思考]
**新文件**: `app/domains/catalog/crawlers/google_places.py`
**覆盖**: 日本全部城市的酒店、特色店铺、POI
**功能**:
- `fetch_hotels(city_code, limit)` — Nearby Search type=lodging
- `fetch_specialty_shops(city_code, limit)` — Nearby Search type=store, keyword="specialty|craft|souvenir"
- `fetch_pois(city_code, limit)` — Nearby Search type=tourist_attraction
- 返回 google_place_id 用于去重
- 自动标记 trust_status='unverified'
- 每日配额限制（从 config 读取）
**依赖**: Google Places API key（$200/月免费额度）

### T5-2. SerpAPI 集成（Google Places 的备选）[Sonnet · 普通]
**新文件**: `app/domains/catalog/crawlers/serpapi_search.py`
**用途**: 当 Google Places 额度用完或无 key 时的备选
**限制**: 100 次/月免费

### T5-3. 携程酒店爬虫 [Opus · 深度思考]
**新文件**: `app/domains/catalog/crawlers/ctrip_scraper.py`
**覆盖**: 中国城市酒店
**方案**:
- 携程搜索结果页 HTML 解析（不需要登录）
- 提取：酒店名、评分、价格区间、坐标、酒店类型
- User-Agent 轮换 + 请求间隔 3-5s
- 自动标记 trust_status='unverified', data_tier='A'
**反爬处理**: 如遇 Captcha → 记录失败，不重试

### T5-4. 大众点评餐厅/商店爬虫 [Opus · 深度思考]
**新文件**: `app/domains/catalog/crawlers/dianping_scraper.py`
**覆盖**: 中国城市餐厅、特色店铺
**方案**:
- 大众点评搜索页 HTML 解析
- 提取：店名、评分、价格、菜系/品类、坐标
- 特色店铺关键词：手工艺、文创、老字号、非遗
- 自动标记 trust_status='unverified'

### T5-5. 扩展现有爬虫覆盖面 [Sonnet · 普通]
**文件**: `app/domains/catalog/web_crawler.py`
**任务**:
- CITY_BBOX: 从 CITY_MAP 中每个日本城市的坐标自动生成 bbox（中心点 ± 0.1度）
- TABELOG_CITY_PREFIX: 补全缺失城市（查 Tabelog 网站结构）
- 每个新增城市的 bbox 可以通过 Nominatim API 自动获取

### T5-6. Pipeline 集成新爬虫 [Sonnet · 普通]
**文件**: `app/domains/catalog/pipeline.py`
**修改 run_city_pipeline() 的数据源优先级**:
```
日本城市:
  酒店: Google Places → Jalan → AI fallback(标记 ai_generated)
  POI:  OSM → Google Places → AI fallback
  餐厅: Tabelog → Google Places → AI fallback
  特色店: Google Places → AI fallback

中国城市:
  酒店: 携程 → AI fallback
  POI:  高德(未来) → AI fallback
  餐厅: 大众点评 → AI fallback
  特色店: 大众点评 → AI fallback
```
每个环节拿到不够时自动 fallback，但 fallback 数据标记 `trust_status='ai_generated'`

### T5-7. poi_category 扩展 [Sonnet · 普通]
**文件**: `app/domains/catalog/ai_generator.py`
**任务**: `_VALID_POI_CATEGORIES` 增加 `specialty_shop`（特色店铺）
**定义**: 攻略推荐级别的特色小店（手工艺品、本地特产、文创、老字号等），不包括连锁便利店

---

## 七、任务分配总表

### Opus 任务（需要深度思考的复杂设计）
| 编号 | 任务 | 深度思考 | 预估复杂度 |
|------|------|----------|-----------|
| T3-2 | 去重逻辑增强（模糊匹配+距离判断） | 是 | 高 |
| T4-1 | Service 层设计 | 是 | 高（可后续做） |
| T5-1 | Google Places API 集成 | 是 | 高 |
| T5-3 | 携程酒店爬虫 | 是 | 高 |
| T5-4 | 大众点评爬虫 | 是 | 高 |
| T4-2 | 解耦循环依赖 | 否 | 中 |

### Sonnet 任务（明确的修复工作，不需要深度设计）
| 编号 | 任务 | 深度思考 | 预估复杂度 |
|------|------|----------|-----------|
| T0-1 | trust_status 字段 + migration | 否 | 低 |
| T0-2 | 管理端审核 API | 否 | 中 |
| T0-3 | pipeline trust_status 自动标记 | 否 | 低 |
| T0-4 | scorer trust_status 权重 | 否 | 低 |
| T1-1 | 异常吞掉全局整改 | 否 | 中（量大但模式固定） |
| T1-2 | 凭证硬编码修复 | 否 | 低 |
| T1-3 | Admin 认证 | 否 | 低 |
| T1-4 | CORS 收紧 | 否 | 低 |
| T1-5 | 连接池调整 | 否 | 低 |
| T2-1 | Config 空壳修复 | 否 | 低 |
| T2-2 | Feature flag 修复 | 否 | 低 |
| T2-3 | 魔法数字提取 | 否 | 中 |
| T2-4 | Write 函数合并 | 否 | 低 |
| T2-5 | Budget 竞态修复 | 否 | 低 |
| T2-6 | 汇率动态获取 | 否 | 低 |
| T3-1 | 坐标校验 | 否 | 低 |
| T3-3 | 默认菜系修复 | 否 | 低 |
| T4-3 | N+1 查询修复 | 否 | 低 |
| T4-4 | 全局状态修复 | 否 | 低 |
| T4-5 | 死表/死代码清理 | 否 | 中 |
| T4-6 | 快照 TTL 清理 | 否 | 低 |
| T4-7 | 硬编码路径修复 | 否 | 低 |
| T5-2 | SerpAPI 集成 | 否 | 低 |
| T5-5 | 扩展 bbox/prefix | 否 | 中 |
| T5-6 | Pipeline 集成 | 否 | 中 |
| T5-7 | poi_category 扩展 | 否 | 低 |

### 建议执行顺序
**第一批（立即）**: T0-1 → T0-3 → T1-1 → T1-2 → T1-3（数据可信度 + 安全基础）
**第二批（本周）**: T0-2 → T0-4 → T2-3 → T2-5 → T3-1 → T3-3（数据质量 + 偷懒修复）
**第三批（下周）**: T5-1 → T5-3 → T5-4 → T5-5 → T5-6（爬虫体系）
**第四批（后续）**: T4-1 → T4-2 → T2-1 → T4-5（架构重构 + 清理）
