# AI 工作指南（AI Work Guide）

版本：v1.0
日期：2026-03-19
用途：为后续 AI 编码工作提供上下文、约束和优先级指引

---

## 一、项目本质

### 一句话
面向中文用户的日本旅行规划与交付引擎。卖的是决策质量，不是 token 数量。

### 系统最小闭环
```
用户需求 → 标准化画像 → 区域/线路匹配 → 候选召回 → 事实补全
→ 打分与约束过滤 → 行程编排 → 自动校验 → 模板渲染 → 人工审核/发布
```

### 不可违反的 7 条原则
1. 事实与表达分离：LLM 只做标准化和文案，不做事实判断
2. 静态与动态分离：主档 Catalog + 动态 Snapshots + 派生 Derived
3. 规划与渲染分离：编排输出结构化 JSON，渲染独立
4. 排序必须可解释：每个推荐能拆到分项
5. 人工经验做修正，不做真相源：editorial_boost(-8~+8)
6. 工作流思维，非 Agent 思维：确定性状态机 + 队列
7. 卖决策质量，不卖 token 数量

---

## 二、技术栈约束

| 组件 | 选型 | 版本要求 |
|---|---|---|
| API 框架 | FastAPI | ≥0.115 |
| ORM | SQLAlchemy (async) | ≥2.0 |
| 数据库 | PostgreSQL 16 + pgvector | pgvector/pgvector:pg16 |
| 缓存 | Redis 7 | redis:7-alpine |
| 异步任务 | arq | ≥0.26 |
| 配置管理 | pydantic-settings | ≥2.0 |
| PDF 导出 | WeasyPrint | 可选依赖 |
| 容器 | Docker Compose | 本地开发环境 |
| 测试 | pytest + pytest-asyncio | 标准 |

### 代码风格
- Python 3.12+，使用 `from __future__ import annotations`
- 类型注解必须完整（Mapped[], Optional[], list[], dict[]）
- ORM 模型使用 SQLAlchemy 2.0 mapped_column 风格
- 业务逻辑写纯函数（无 I/O），方便测试
- Job 函数签名：`async def job_name(ctx: dict, **kwargs)`

---

## 三、项目结构

```
app/
├── api/                    # HTTP 路由层
│   ├── trips.py           # POST/GET /trips
│   ├── trips_generate.py  # POST /trips/{id}/generate
│   ├── chat.py            # (预留) 对话接口
│   └── ops/               # 运营侧 API
│       └── entities.py    # GET /ops/entities/search
├── core/                   # 基础设施
│   ├── config.py          # pydantic-settings 配置
│   ├── queue.py           # arq Redis pool + enqueue_job
│   └── snapshots.py       # record_snapshot 工具
├── db/
│   ├── session.py         # async session factory
│   ├── models/
│   │   ├── catalog.py     # Layer A: 8 张表
│   │   ├── snapshots.py   # Layer B: 6 张表
│   │   ├── derived.py     # Layer C: 13 张表
│   │   └── business.py    # 业务层: 8 张表
│   └── migrations/        # Alembic
├── domains/                # 业务逻辑层（核心！）
│   ├── catalog/           # 实体主档管理
│   │   ├── upsert.py      # ✅ 幂等写入
│   │   ├── google_places.py # ✅ Google Places 采集
│   │   ├── pipeline.py    # 批量采集管道
│   │   ├── serp_sync.py   # SERP 同步
│   │   ├── web_crawler.py # 网页爬取
│   │   └── ai_generator.py # AI 辅助生成
│   ├── intake/            # 需求采集
│   │   └── intent_parser.py # 意图解析
│   ├── ranking/           # 评分排名
│   │   ├── rules.py       # ✅ 评分规则配置
│   │   └── scorer.py      # ✅ compute_base_score + apply_editorial_boost
│   ├── live_inventory/    # 动态快照
│   │   └── weather.py     # ✅ Open-Meteo 天气
│   ├── trip_core/         # 行程核心
│   │   ├── day_builder.py # ✅ 时间槽编排
│   │   └── planner.py     # ✅ 行程规划（需重构）
│   ├── rendering/         # 渲染导出
│   │   └── renderer.py    # ✅ HTML/PDF 渲染
│   └── review_ops/        # 审核运营（空）
└── workers/
    ├── __main__.py        # WorkerSettings
    └── jobs/
        └── score_entities.py # ✅ 批量评分 job

data/                       # 种子数据
├── 日本_日本区域与线路_SeedData_v1.xlsx  # 12 区域 + 29 线路
└── seed_pois.csv

scripts/                    # 运维脚本
├── seed_catalog.py        # Catalog 初始化
└── crawl.py               # 爬虫脚本

tests/                      # 测试
├── test_scorer.py         # ✅ 23 个评分测试
├── test_catalog_upsert.py # ✅ upsert 测试
├── test_snapshots.py      # ✅ 快照测试
├── test_trip_api.py       # ✅ API 测试
└── test_planner.py        # planner 测试
```

### ✅ = 已实现且有测试  |  无标记 = 骨架存在但逻辑不完整或为空

---

## 四、数据库 Schema（35 张表）

### Layer A: Catalog（8 张表）— 静态事实
- `entity_base`: 实体公共基表（CTI 模式），含 embedding(Vector 1536)
- `pois`: 景点扩展（category, duration, hours, season, rating）
- `hotels`: 酒店扩展（type, star, amenities, price_tier, booking_score）
- `restaurants`: 餐厅扩展（cuisine, michelin, tabelog, reservation）
- `entity_tags`: 标签（namespace: feature/audience/theme/avoid）
- `entity_media`: 媒体资源（图片/视频 URL）
- `entity_editor_notes`: 编辑备注（editorial_boost, avoid_warning, insider_tip）
- `hotel_area_guide`: 酒店周边导览（引流款区域住宿指南用）

### Layer B: Snapshots（6 张表）— 动态快照
- `source_snapshots`: 通用 API 原始响应存档
- `hotel_offer_snapshots` + `hotel_offer_lines`: 酒店报价快照
- `flight_offer_snapshots`: 航班快照
- `poi_opening_snapshots`: 营业时间变更
- `weather_snapshots`: 天气预报快照

### Layer C: Derived（13 张表）— 派生结果
- `entity_scores`: 实体评分（base_score + editorial_boost → final_score）
- `itinerary_scores`: 行程整体评分
- `candidate_sets`: 候选集快照
- `route_matrix_cache`: 两点间交通时间缓存
- `planner_runs`: 规划器运行记录
- `itinerary_plans` / `itinerary_days` / `itinerary_items`: 行程结构
- `route_templates`: 路线模板（引流款用）
- `render_templates`: 渲染模板配置
- `export_jobs` / `export_assets`: 导出任务与产物
- `plan_artifacts`: 全链路追溯

### 业务表（8 张表）
- `users`: 用户
- `product_sku`: 产品 SKU（¥20/¥69/¥128/¥199/¥299+）
- `orders`: 订单
- `trip_requests`: 行程请求
- `trip_profiles`: 用户旅行画像
- `trip_versions`: 行程版本
- `review_jobs` / `review_actions`: 审核

---

## 五、评分引擎详细说明

### 公式（方案设计）
```
candidate_score = 0.60 * system_score + 0.40 * context_score - risk_penalty
final_score = candidate_score + editorial_boost
```

### 当前实现状态
- ✅ system_score: 6 维度加权（platform_rating, review_confidence, 等）
- ✅ risk_penalty: 按 entity_type 的风险规则扣分
- ✅ editorial_boost: -8 ~ +8，叠加到 final_score
- ✅ data_tier 置信度折扣（S=1.0, A=0.9, B=0.75）
- ❌ context_score: **未实现**（需要 trip_profile.theme_weights × entity tags 亲和度）

### context_score 设计思路（待实现）
```python
context_score = Σ (user_theme_weight[i] × entity_theme_affinity[i])
# 其中 theme_affinity 来自 entity_tags 或 AI 预标注
# theme 维度: shopping, food, culture, photo_spots, onsen, comfort, nature, art
```

### 行程整体评分（待实现）
```
itinerary_score = 0.45 * feasibility + 0.30 * context_fit
                + 0.15 * diversity + 0.10 * editorial - risk_penalty
```

---

## 六、种子数据：区域与线路

### 来源文件
`data/日本_日本区域与线路_SeedData_v1.xlsx`

### 12 个区域（Regions）
| ID | 名称 | 核心城市 | 天数 | 优先级 |
|---|---|---|---|---|
| R01 | 东京都市圈 | 东京 | 3-5 | P0 |
| R03 | 富士箱根伊豆圈 | 箱根/河口湖/伊豆 | 2-5 | P0 |
| R05 | 关西经典圈 | 京都/大阪/奈良 | 4-7 | P0 |
| R06 | 北海道圈 | 札幌/小樽/登别/富良野 | 4-7 | P0 |
| R08 | 北陆深度圈 | 金泽/加贺温泉 | 3-5 | P0 |
| R02 | 东京近郊 | 镰仓/横滨 | 1-3 | P1 |
| R04 | 关东山岳 | 日光/轻井泽 | 2-4 | P1 |
| R10 | 濑户内·广岛 | 广岛/宫岛/尾道 | 3-6 | P1 |
| R11 | 九州温泉 | 福冈/由布院/别府 | 4-7 | P1 |
| R07 | 东北季节 | 仙台/青森 | 4-7 | P2 |
| R09 | 阿尔卑斯·飞驒 | 高山/白川乡 | 4-6 | P2 |
| R12 | 冲绳海岛 | 那霸/石垣/宫古 | 4-6 | P2 |

### 29 条线路（Routes）
每条线路属于一个区域，包含：cities_combo, days_min/max, intensity, vacation_mode, suitable_users, first_or_repeat, core_tags, launch_priority

P0 线路（10 条，优先上线）：T01, T02, F01, F02, KS01, KS02, KS03, H01, HK01, HK02

### 枚举值
- **intensity**: RELAX / EASY / BALANCED / CITY_RUSH / SPRINT
- **vacation_mode**: CITY / CLASSIC / SLOW / RESORT / NATURE / ART

### ⚠️ 当前状态：种子数据存在 Excel 中，代码里无 Region/Route 模型

---

## 七、当前已完成的工作流节点

| 工作流节点 | 方案要求 | 代码状态 | 说明 |
|---|---|---|---|
| 1. 提交需求 | POST /trips | ✅ 完成 | 写 trip_requests，返回 202 |
| 2. 标准化画像 | normalize_trip_profile job | ✅ 完成 | 推导 must_have/avoid tags |
| 3. 区域/线路匹配 | 根据画像匹配 Region → Route | ❌ 缺失 | 代码里无此概念 |
| 4. 候选召回 | 按城市+标签+评分召回 | ⚠️ 部分 | planner 有召回，但未用 entity_scores |
| 5. 实时快照 | 抓取酒店报价/天气等 | ⚠️ 部分 | 天气已有，酒店报价未实现 |
| 6. 打分与过滤 | candidate_score 排序 | ⚠️ 部分 | system_score 有，context_score 缺失 |
| 7. 路线矩阵 | Google Routes 缓存 | ❌ 缺失 | route_matrix_cache 表有，逻辑无 |
| 8. 行程编排 | day_builder 装配 | ✅ 完成 | 时间槽编排逻辑完整 |
| 9. 自动校验 | hard_fail/soft_fail 规则 | ❌ 缺失 | review_ops 域为空 |
| 10. 渲染导出 | HTML→PDF | ✅ 完成 | Jinja2 + WeasyPrint |
| 11. 审核发布 | 审核工作台 | ❌ 缺失 | review_jobs/actions 表有，逻辑无 |

---

## 八、优先开发清单（按影响排序）

### 🔴 P0: 必须补齐才能形成完整闭环

#### 8.1 Region/Route 数据模型 + 种子导入
**为什么重要**：没有区域/线路概念，系统无法做"用户→区域→线路→城市"的智能匹配，只能硬编码城市。

需要做的事：
1. 新建 `app/db/models/geography.py`：`regions` 表 + `routes` 表
2. 写导入脚本：把 Excel 种子数据灌进 DB
3. 建立 Route → EntityBase(city_code) 的关联查询

Region 表字段建议：
```
region_id (PK, varchar)    — R01, R02...
region_name_cn (varchar)   — 东京都市圈
region_scope (text)        — 东京23区为主
core_cities (jsonb)        — ["东京"]
min_days / max_days (int)
core_tags (jsonb)          — ["城市","购物","美术馆"]
default_intensity (varchar) — RELAX/EASY/BALANCED/CITY_RUSH/SPRINT
suitable_users (jsonb)     — ["第一次日本","情侣","女生"]
first_trip_friendly (bool)
repeat_trip_friendly (bool)
launch_priority (varchar)  — P0/P1/P2
notes (text)
```

Route 表字段建议：
```
route_id (PK, varchar)     — T01, F01...
region_id (FK → regions)
route_name_cn (varchar)
cities_combo (jsonb)       — ["东京", "箱根"]
days_min / days_max (int)
intensity (varchar)        — RELAX/EASY/BALANCED/CITY_RUSH/SPRINT
vacation_mode (varchar)    — CITY/CLASSIC/SLOW/RESORT/NATURE/ART
suitable_users (jsonb)
first_or_repeat (varchar)  — first/repeat/both
core_features (text)
core_tags (jsonb)
sprint_friendly (bool)
launch_priority (varchar)
```

#### 8.2 context_score 实现
**为什么重要**：方案里候选排序 40% 的权重来自 context_score。没有它，系统无法根据用户偏好做个性化推荐。

需要做的事：
1. 定义 theme 维度枚举和 entity 的 theme_affinity 标注方案
2. 在 scorer.py 中添加 `compute_context_score(signals, profile)` 函数
3. 修改 `compute_base_score` 使其合并 system + context

#### 8.3 trip_profile 增强
**为什么重要**：现有画像字段不够支撑区域匹配和 context_score 计算。

需要新增字段：
- `trip_experience`: first_time / repeat（影响区域推荐）
- `pace`: relax / easy / balanced / city_rush（影响每日安排密度）
- `theme_weights`: `{"shopping": 0.15, "food": 0.25, ...}`（影响 context_score）
- `flight_preferences`: `{"depart_after": "09:00", ...}`（影响首末日安排）

#### 8.4 DB 迁移跑通
需要做的事：Docker 启动后执行 `alembic revision --autogenerate` + `alembic upgrade head`

### 🟡 P1: Phase 1 引流款所需

#### 8.5 route_templates 数据填充
需要做的事：为 P0 线路（10 条）生成 `template_data` JSON，灌入 route_templates 表

#### 8.6 planner 重构：使用 entity_scores
当前 planner 直接 `ORDER BY google_rating DESC`，应改为 `ORDER BY entity_scores.final_score DESC`

#### 8.7 审核规则引擎 v1
实现 `app/domains/review_ops/guardrails.py`：
- hard_fail: 闭馆冲突、路线矩阵缺失、预算超标
- soft_fail: 强度偏高、排队风险

#### 8.8 editorial_boost 录入 API
实现 `POST /ops/entities/{type}/{id}/editorial-score`

### 🟢 P2: Phase 2 利润款所需

- Google Routes API 接入 → route_matrix_cache
- Booking Demand API 接入 → hotel_offer_snapshots
- 区域/线路匹配引擎（用户画像 → 推荐区域 → 推荐线路）
- 个性化行程编排（非模板，动态装配）

---

## 九、需要从 GPT 获取的数据（省 AI token）

### 高优先级

| 序号 | 内容 | 格式 | 用途 |
|---|---|---|---|
| 1 | context_score 主题维度定义 + 权重矩阵 | JSON | 实现 context_score |
| 2 | 12 区域 × 用户画像打分矩阵 | CSV/JSON | 实现区域匹配 |
| 3 | trip_profile 完整 JSON schema | JSON Schema | 增强画像字段 |
| 4 | intensity → 每日约束映射（max_poi/max_walk/max_transit） | JSON | planner 节奏控制 |
| 5 | P0 线路的 template_data 骨架（10 条） | JSON | 引流款模板数据 |

### 中优先级

| 序号 | 内容 | 格式 | 用途 |
|---|---|---|---|
| 6 | 东京 Top 50 POI editorial_boost + editorial_tags 预标注 | CSV | 评分数据 |
| 7 | 大阪/京都 Top 30 POI editorial_boost + editorial_tags | CSV | 评分数据 |
| 8 | 审核规则 hard_fail/soft_fail 完整清单 + 阈值 | Markdown | 实现审核引擎 |
| 9 | 引流款 HTML 模板设计方向（杂志风 CSS 参考） | HTML/CSS | 渲染模板 |

### GPT Prompt 模板

#### 获取 context_score 设计
```
你是旅行 AI 评分系统的设计师。我需要设计一个 context_score，用于衡量"一个旅行实体与特定用户画像的适配度"。

系统已有 system_score（基于平台评分、评论量、数据新鲜度等客观信号），现在需要补充 context_score（基于用户偏好的主观适配度）。

请设计：
1. 主题维度枚举（8-10 个维度，如 shopping, food, culture, onsen...）
2. 每个维度的定义和说明
3. entity 的 theme_affinity 打分方案（0-5 量表）
4. context_score 计算公式：context_score = Σ(user_weight_i × entity_affinity_i) × 归一化系数
5. 示例：东京浅草寺在各维度的 affinity 打分

输出为 JSON 格式，可直接用于 Python 代码。
```

#### 获取区域匹配矩阵
```
我有 12 个日本旅行区域（见下方列表）和 6 种用户类型。
请为每个"用户类型 × 区域"组合打分（0-100），用于区域推荐排序。

区域列表：[贴入 Regions 数据]

用户类型：
- first_time_couple（第一次去日本的情侣）
- first_time_family（第一次去日本的家庭）
- repeat_couple（二刷日本情侣）
- repeat_solo（二刷日本独行侠）
- onsen_focused（温泉主题用户）
- culture_deep（文化深度用户）

输出为 JSON 矩阵格式。
```

#### 获取 P0 线路模板数据
```
你是日本旅行规划师。请为以下 10 条 P0 线路各设计一个"行程骨架"，输出为 JSON。

每条线路需要包含：
- route_id
- 推荐天数
- 每天的结构：{day_number, city_code, area_focus, morning_theme, afternoon_theme, evening_theme, hotel_area}
- 这不是具体的景点推荐，而是"骨架模板"——后续系统会根据这个骨架从 Catalog 召回具体实体

线路列表：[贴入 Routes P0 数据]
```

---

## 十、编码约定

### ORM 模型规范
```python
# 所有模型继承 Base
from app.db.session import Base

# 使用 mapped_column + Mapped 类型注解
class MyModel(Base):
    __tablename__ = "my_table"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

### 领域逻辑规范
```python
# 核心逻辑写纯函数（无 I/O），Job 里做 DB 读写
# 好的：
def compute_base_score(signals: EntitySignals) -> ScoreResult:
    ...  # 纯计算

# 坏的：
async def compute_base_score(session: AsyncSession, entity_id: uuid.UUID) -> float:
    entity = await session.get(...)  # 把 DB 读写混进核心逻辑
```

### Job 规范
```python
# Job 签名统一格式
async def my_job(ctx: dict, param1: str, param2: int = 10) -> dict:
    """Job 文档字符串"""
    # 1. 从 DB 读取数据
    # 2. 调用纯函数处理
    # 3. 写回 DB
    # 4. 返回统计摘要 dict
    return {"processed": n, "errors": 0}

# 注册到 WorkerSettings.functions
```

### 测试规范
```python
# 文件命名：tests/test_<module>.py
# 纯函数测试：直接调用，不需要 DB fixture
# DB 测试：使用 test_db fixture（pytest-asyncio）
# 每个测试函数有中文 docstring 说明覆盖场景
```

---

## 十一、关键文件索引

| 文件 | 说明 | 阅读优先级 |
|---|---|---|
| `日本旅行AI后端完整方案_第一性原理版.md` | 系统设计圣经，1240 行 | 🔴 必读 |
| `PROJECT_PLAN.md` | 项目计划，含阶段/里程碑/API/表索引 | 🔴 必读 |
| `AI_WORK_GUIDE.md` | 本文件，AI 工作指南 | 🔴 必读 |
| `data/日本_日本区域与线路_SeedData_v1.xlsx` | 区域/线路种子数据 | 🟡 重要 |
| `openspec/specs/scoring-engine/spec.md` | 评分引擎详细 Spec | 🟡 按需读 |
| `openspec/specs/*/spec.md` | 其他领域 Spec（8 个） | 🟢 按需读 |
| `openspec/changes/phase0-backend-skeleton/` | Phase 0 变更记录 | 🟢 参考 |

---

## 十二、当前阻塞项

| 阻塞 | 影响 | 解除方式 |
|---|---|---|
| Docker Hub 网络不通 | 无法拉取 pgvector/redis 镜像 | 换网络或用镜像加速器 |
| Alembic 迁移未跑 | 35 张表未真正创建 | Docker 启动后执行迁移 |
| 无 Catalog 实际数据 | 评分/编排无对象可操作 | 运行 seed_catalog.py 或 Google Places 采集 |
| 无 editorial_boost 数据 | 编辑修正层为空 | GPT 预标注 + 人工校准 |
| context_score 未设计 | 个性化推荐缺 40% 权重 | 先从 GPT 获取设计方案 |
