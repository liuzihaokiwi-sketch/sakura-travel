# 日本旅行 AI 产品 — 完整项目计划（第一性原理版）

版本：v2.0
日期：2026-03-18
基于：`日本旅行AI后端完整方案_第一性原理版.md`

---

## 一、项目定位

### 一句话
面向中文用户的日本旅行规划与交付引擎。不是聊天机器人，不是 OTA，不是 CMS。

### 系统目标函数
```
Utility = 可执行性 × 适配度 × 解释性 × 交付速度 × 复用能力
```

### 架构形态
**模块化单体（Modular Monolith）**：复杂度来自业务编排不来自吞吐量。

### 技术栈
| 层 | 选型 |
|---|---|
| API 框架 | FastAPI |
| 数据库 | PostgreSQL |
| 向量检索 | pgvector |
| 缓存/锁 | Redis |
| 异步任务 | Queue Worker |
| 对象存储 | S3 compatible |
| PDF 导出 | WeasyPrint |
| POI/路线 | Google Places + Routes API |
| 酒店库存 | Booking Demand API (Phase 2+) |
| 官方信息 | JNTO + JMA + MOFA |

---

## 二、产品价位体系

| 层级 | 价格 | 定位 | 核心差异 |
|---|---|---|---|
| 引流款 | ¥19.9~29.9 | 秀肌肉（杂志级渲染是肌肉本体） | 模板化、无餐厅、酒店只推区域、不支持输入 |
| 利润款 | ¥69 | 主题攻略 | 半模板+基础个性化+餐厅+酒店 |
| 利润款 | ¥128 | 个性化定制 | 全个性化+精选餐厅酒店+避坑指南 |
| 利润款 | ¥199 | 深度定制 | 全个性化+深度点评+全格式 |
| 高客单 | ¥299+ | **地区深度×主题深度** | 小众地区+高度主题化（茶道/动漫/温泉/滑雪…） |

**关键原则**：
- 渲染质量是基础线，所有价位都是杂志级
- 引流款和利润款差异在内容（餐厅/酒店/避坑/个性化）
- 利润款和高客单差异在地区覆盖和主题深度

详见 → `openspec/specs/product-tiers/spec.md`

---

## 三、7 条系统结论（第一性原理）

1. **事实与表达分离**：LLM 只做标准化和文案，不做事实判断
2. **静态与动态分离**：主档 Catalog + 动态 Snapshots + 派生 Derived 三层
3. **规划与渲染分离**：编排输出 JSON，渲染独立处理
4. **排序必须可解释**：每个推荐能拆到分项
5. **人工经验做修正，不做真相源**：editorial_boost(-8~+8) + force_include/exclude
6. **工作流思维，非 Agent 思维**：确定性状态机+队列，不是 Agent 互相调用
7. **卖决策质量，不卖 token 数量**

---

## 四、六大领域划分

| 领域 | 职责 |
|---|---|
| **Trip Core** | 用户需求/订单/行程版本/交付状态 |
| **Catalog** | 景点/酒店/餐厅 主档 + 标签 + 媒体 + 编辑备注 |
| **Live Inventory** | 酒店报价/营业时间/天气/签证 快照 |
| **Ranking & Planning** | 候选召回/评分/路线矩阵/行程编排/备用方案 |
| **Rendering** | HTML/PDF/H5/长图/微信摘要 |
| **Review & Ops** | 审核规则/抽检/发布/editorial_boost 后台/版本追溯 |

---

## 五、三层数据架构

```
Layer A：Catalog（主档事实）
  entity_base / pois / hotels / restaurants
  entity_tags / entity_media / entity_editor_notes
  hotel_area_guide

Layer B：Live Snapshots（动态快照）
  source_snapshots（通用快照）
  hotel_offer_snapshots + hotel_offer_lines
  flight_offer_snapshots
  poi_opening_snapshots
  weather_snapshots

Layer C：Derived（派生结果）
  entity_scores / itinerary_scores
  candidate_sets / route_matrix_cache
  itinerary_plans / itinerary_days / itinerary_items
  planner_runs
  export_jobs / export_assets / plan_artifacts
```

---

## 六、Spec 文件索引

| Spec | 路径 | 说明 |
|---|---|---|
| 产品价位体系 | `specs/product-tiers/spec.md` | 价位矩阵、价位→工作流映射、SKU/订单/用户表 |
| Catalog 实体主档 | `specs/catalog-entities/spec.md` | entity_base + POI/Hotel/Restaurant 扩展表 + 标签 + 媒体 |
| **区域与线路匹配** | `specs/geography-routing/spec.md` | **12 区域 + 29 线路、匹配逻辑、intensity 枚举、种子数据** |
| 评分引擎 | `specs/scoring-engine/spec.md` | 两阶段评分（候选排序+编辑修正）、全部分项、实现状态 |
| 需求采集与画像 | `specs/user-intake/spec.md` | 采集字段（含 theme_weights/pace/trip_experience）、画像结构、转换规则 |
| 行程串联 | `specs/itinerary-planner/spec.md` | 编排流程、装配约束、intensity 约束映射、模板结构 |
| 模板渲染 | `specs/template-renderer/spec.md` | 三层模板架构、组件矩阵、导出追溯 |
| 审核闸门 | `specs/review-gate/spec.md` | hard_fail/soft_fail 规则、抽检策略、guardrails.py 实现规格 |
| 数据管道+快照 | `specs/data-pipeline/spec.md` | 数据源、快照表、采集流程、缓存策略 |

---

## 七、数据库全表索引

### Layer A：Catalog
| 表名 | 说明 |
|---|---|
| entity_base | 实体公共基表 |
| pois | 景点扩展表 |
| hotels | 酒店扩展表 |
| restaurants | 餐饮扩展表 |
| entity_tags | 统一标签表 |
| entity_media | 媒体资源表 |
| entity_editor_notes | 编辑修正表 |
| hotel_area_guide | 区域住宿指南（引流款用） |

### Layer B：Live Snapshots
| 表名 | 说明 |
|---|---|
| source_snapshots | 通用快照表 |
| hotel_offer_snapshots | 酒店报价快照头表 |
| hotel_offer_lines | 酒店报价快照行表 |
| flight_offer_snapshots | 航班快照 |
| poi_opening_snapshots | 营业时间变更快照 |
| weather_snapshots | 天气快照 |

### Layer C：Derived
| 表名 | 说明 |
|---|---|
| entity_scores | 候选评分记录 |
| itinerary_scores | 行程评分记录 |
| candidate_sets | 候选集快照 |
| route_matrix_cache | 路线矩阵缓存 |
| planner_runs | 编排运行记录 |
| itinerary_plans | 行程计划 |
| itinerary_days | 每日行程 |
| itinerary_items | 行程项 |
| route_templates | 路线模板（引流款用） |
| render_templates | 渲染模板配置 |
| export_jobs | 导出任务 |
| export_assets | 导出产物 |
| plan_artifacts | 全链路追溯 |

### 业务表
| 表名 | 说明 |
|---|---|
| users | 用户 |
| orders | 订单 |
| product_sku | 产品 SKU |
| trip_requests | 行程请求 |
| trip_profiles | 用户旅行画像 |
| trip_versions | 行程版本 |
| review_jobs | 审核任务 |
| review_actions | 审核动作 |

---

## 八、API 设计

### 用户侧
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /trips | 提交需求 |
| GET | /trips/{id} | 查询行程 |
| GET | /trips/{id}/status | 查询状态 |
| GET | /trips/{id}/preview | 查看预览 |
| POST | /trips/{id}/regenerate | 重新生成 |
| GET | /trips/{id}/exports | 获取导出物 |
| GET | /products | 产品列表 |
| POST | /orders | 创建订单 |

### 运营侧
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /ops/entities/search | 搜索实体 |
| POST | /ops/entities/{type}/{id}/editorial-score | 编辑修正 |
| POST | /ops/trips/{id}/review | 审核 |
| POST | /ops/trips/{id}/publish | 发布 |
| POST | /ops/trips/{id}/rebuild | 重跑 |
| GET | /ops/source-snapshots/{id} | 查看快照 |

### 内部工作流 Queue Jobs
```
normalize_trip_profile → retrieve_candidates → fetch_live_snapshots
→ score_candidates → build_route_matrix → plan_trip
→ run_guardrails → render_exports
```

---

## 九、开发阶段计划

### Phase 0：骨架与数据底座（Week 1-3）

**目标**：FastAPI 跑起来，数据库建好，Catalog 有数据，能出评分。

| 周 | 任务 | 产出 |
|---|---|---|
| W1 | FastAPI skeleton + PostgreSQL schema 全量建表 | 项目骨架+DDL |
| W1 | Trip 提交/状态查询 API | 基础 API |
| W1 | trip_profile 标准化逻辑 | 画像生成 |
| W2 | Google Places API 接入（field mask） | 采集脚本 |
| W2 | entity_base + pois/hotels/restaurants 批量写入（东京/大阪/京都） | ~800 实体 |
| W2 | source_snapshots 机制实现 | 快照可追溯 |
| W2 | entity_tags GPT 辅助打标签 | 标签数据 |
| W3 | scoring engine v1（system_score + context_score + risk_penalty） | 候选排序可用 |
| W3 | editorial_boost 录入接口 | 编辑修正可用 |
| W3 | 人工数据分级（S/A/B tier 标记） | data_tier 完成 |
| W3 | 你开始打 editorial_boost + editorial_label | 核心实体修正 |

**里程碑**：能按城市+区域召回实体，按 candidate_score 排序，editorial_boost 能干预结果。

### Phase 1：引流款产品（Week 4-7）

**目标**：产出第一批 ¥20 杂志级模板攻略，可售卖。

| 周 | 任务 | 产出 |
|---|---|---|
| W4 | hotel_area_guide 编写 | 区域住宿指南 |
| W4 | route_template 设计（3-5 条经典路线） | 模板结构 |
| W4 | 行程编排 v1（基于模板装配） | itinerary 生成 |
| W5 | route_matrix_cache v1（Google Routes） | 交通时间 |
| W5 | 自动审核规则 v1（hard_fail + soft_fail） | 闸门可用 |
| W5 | AI 文案润色（LLM 只做表达层） | 文案生成 |
| W6 | 杂志级 HTML/CSS 模板设计 | 排版完成 |
| W6 | WeasyPrint PDF 渲染 | PDF 可导出 |
| W6 | H5 预览页面 | 在线可看 |
| W7 | 第一批引流款攻略生成（3-5 条） | 成品攻略 |
| W7 | plan_artifacts 追溯链路 | 版本可追溯 |
| W7 | 基础支付接入 | 能收钱 |

**里程碑**：3-5 条 ¥20 杂志级攻略上线，H5+PDF 双格式，有升级引导。

**验收标准**：
- 排版达到杂志级（用户看到觉得"20 块太值了"）
- 无 hard_fail 审核问题
- 有自然的升级引导入口
- plan_artifacts 能追溯到快照版本+模板版本

### Phase 2：利润款产品（Week 8-13）

**目标**：上线 ¥69/128/199 个性化定制。

| 周 | 任务 | 产出 |
|---|---|---|
| W8 | 需求采集表单（前端） | 用户输入 |
| W8 | trip_profile 画像 → 候选召回联动 | 个性化召回 |
| W9 | context_score 实时计算 | 场景适配评分 |
| W9 | 个性化行程编排（非模板，动态装配） | 自动编排 |
| W10 | 餐厅推荐集成（附近召回+时段匹配） | 餐饮模块 |
| W10 | 酒店精选推荐（具体酒店+推荐理由） | 酒店卡片 |
| W11 | 避坑指南渲染（editorial_reason + pitfall_notes） | 避坑内容 |
| W11 | Google Routes 精确路线矩阵 | 交通优化 |
| W11 | 预算汇总模块 | 费用明细 |
| W12 | editorial_boost 后台（搜索/打标/上下调/标记不推荐） | 运营工具 |
| W12 | 审核工作台（画像/候选 Top10/日负载/快照时间/模板预览） | 审核界面 |
| W13 | ¥69/128/199 SKU + workflow_config 差异化 | 多档位上线 |
| W13 | 全流程联调（表单→生成→审核→交付） | 端到端 |

**里程碑**：用户填表单 → 系统个性化生成 → 审核 → 交付 PDF/H5。

### Phase 3：高客单+扩展（Week 14+）

| 任务 | 说明 |
|---|---|
| 小众地区数据覆盖 | 四国/东北/九州深度/濑户内海/北海道深度 |
| 主题维度深度标签 | tea_ceremony / anime_pilgrimage / onsen_deep / ski |
| theme_affinity 评分 | 高客单用主题亲和度加权 |
| 主题深度板块渲染 | 茶道/温泉/动漫等专属内容组件 |
| Booking Demand API 接入 | 酒店动态报价 |
| 会员订阅 | 月度更新/季节推送 |
| 多国家复制 | 韩国/东南亚 |
| regenerate 流程 | 重新生成+版本对比 |
| 社交分享长图 | 小红书/微信长图 |

---

## 十、关键风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| Google Places API 成本 | 批量采集成本高 | field mask + 缓存 + 分级刷新 |
| Booking API 审批延迟 | 酒店动态报价无法接入 | Phase 2+ 再接入，Phase 1 用静态价格带 |
| editorial_boost 覆盖不足 | 核心实体没有修正 | GPT 辅助预标注，你校准 S 级 |
| 杂志级渲染开发周期 | CSS 调排版耗时 | 先做一套 magazine_clean 主题，后续迭代变体 |
| 自动编排质量 | 路线不合理 | Phase 1 用模板装配，Phase 2 再做动态编排 |
| 合规风险 | 被认定为旅行社 | 定位为信息服务+免责声明 |

---

## 十一、可观测性要求

每次生成必须记录：
- `profile_version`
- `catalog_version`
- `snapshot_version_set`
- `score_version`
- `planner_version`
- `template_version`

每次生成必须记录日志：
- 需求标准化结果
- 召回对象数 / shortlist 对象数
- route_matrix 命中率
- 审核规则命中项
- 导出耗时
- 使用了哪些快照源

---

## 十二、编辑修正表模板（供 GPT 辅助标注）

> 导出为 CSV，批量给 GPT 预标注，你做最终校准。

### 实体编辑修正表
| entity_id | entity_type | name_zh | city | area | editorial_boost (-8~+8) | editorial_label | editorial_reason | editorial_tags | theme_affinity |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |

### 标签强度表
| entity_id | entity_type | name_zh | family_friendly (0-5) | couple_friendly (0-5) | luxury (0-5) | budget_friendly (0-5) | anime (0-5) | onsen (0-5) | photo_spot (0-5) | transport_convenient (0-5) | rainy_day_friendly (0-5) | tea_ceremony (0-5) | skiing (0-5) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | | | |

---

## 十三、合规与安全

- 产品定位：攻略内容服务 / 行程建议服务 / 决策辅助服务
- 不做：机酒代订 / 包价旅游 / 旅行社业务
- 不采集：护照影像 / 身份证件 / 精确实时轨迹 / 未成年人敏感信息
- 页面声明：动态信息请出发前复核 / 以官方实时通告为准

---

## 十四、参考资料

详见 `日本旅行AI后端完整方案_第一性原理版.md` 第 26 章完整参考资料清单。