# 全局任务进度 + 新增任务对照（更新于 2026-03-21 12:24）

---

## 🟢 已完成（DeepSeek + 本窗口）

### DeepSeek（低级 AI）— Wave 0 DB Schema ✅
- 17 张新表 ORM 模型 → `app/db/models/soft_rules.py`
- Alembic Migration → `app/db/migrations/versions/20260321_120000_soft_rules_system_v1.py`
- 2 张现有表字段扩展（entity_scores + itinerary_items）
- 详见 `parallel-execution-plan-completion-report.md`

### 本窗口（高级 AI）— 核心引擎 ✅
- `app/domains/ranking/soft_rules/dimensions.py` — 12 维度定义 + 校验
- `app/domains/ranking/soft_rules/weight_packs.py` — 7 客群 + 4 阶段权重包 + 聚合
- `app/domains/ranking/soft_rules/estimators/ai_estimator.py` — GPT-4o-mini Prompt 工程
- `app/domains/ranking/soft_rules/estimators/stat_estimator.py` — 统计特征计算
- `app/domains/ranking/soft_rules/estimators/fusion.py` — 三源融合
- `app/domains/ranking/soft_rules/preview_engine.py` — 预览选天引擎
- `app/domains/ranking/soft_rules/swap_engine.py` — 微调候选排序引擎
- `app/domains/ranking/scorer.py` — 三维公式集成
- `app/domains/ranking/rules.py` — 三维权重常量

---

## 🆕 system-closure-v2 新增任务分析

### 与现有任务的重叠/差异

| v2 任务组 | 与已有 change 的关系 | 新增内容（不重叠的） |
|-----------|---------------------|---------------------|
| **1.x 产品真相源** | ≈ closure-v1 T0.2 + strategic T1 | 🆕 1.1 `data/config/product_config.json` 文件方案（比 DB 表方案更轻量） |
| | | 🆕 1.4 重构价格页从配置读取 |
| | | 🆕 1.5 自助/正式修改边界逻辑 |
| | | 🆕 1.6 订单绑定 config_version |
| **2.x 城市上下文** | ≈ closure-v1 T0.1（6 表） | 🆕 2.5-2.8 **具体种子数据**（三城市活动/人流/营业/交通卡） ← 这个很有价值 |
| | | 🆕 2.9 guardrails 接入定休日检查 |
| **3.x 预览引擎** | ≈ closure-v1 T1.x + soft-rule 7.x | 🆕 3.3 预览页**恢复为独立 H5**（之前砍掉了） |
| | | 🆕 3.4 CTA 触发点设计（3-6个位置） |
| | | 🆕 3.5 其他天标题 teaser |
| **4.x 前端增长** | 全新，不在任何已有 change 中 | 🆕🆕 4.1 落地页首屏优化 |
| | | 🆕🆕 4.2 **5 种分享卡** Satori 生成 |
| | | 🆕🆕 4.3 分享回流页 `/s/[card_id]` |
| | | 🆕🆕 4.4 交付页三层阅读结构 |
| | | 🆕🆕 4.5 微信承接系统设计 |
| **5.x 自助微调** | ≈ closure-v1 T2.x + soft-rule 8.x | 🆕 5.3 自动重检（guardrails 联动） |
| | | 🆕 5.4 防改崩三档警告 |
| | | 🆕 5.6 节奏轻重切换 |
| | | 🆕 5.7 "仍不满意→正式精调"入口 |
| **6.x 多模型评审** | ≈ closure-v1 T3.x | 🆕 6.5 Tuning Guard（判断可微调模块） |
| | | 🆕 6.7 review_pipeline_runs 表 |
| | | 🆕 6.8 集成到 generate_trip Job |
| **7.x 后台运营** | ≈ all-remaining 1.x + closure-v1 T5.2 | 🆕 7.3 预览成交表现看板 |
| | | 🆕 7.5 人工介入原因归类 |
| **8.x 埋点学习** | ≈ closure-v1 T4.x + soft-rule 11-12 | 基本重叠 |
| **9.x 离线评测** | ≈ closure-v1 T4.3 | 🆕 9.3 CI/CD 回归检查（质量分下降红灯） |
| **10.x 软规则** | 直接引用 soft-rule-system | 纯引用，无新增 |
| **11.x 前端增长2** | 全新 | 🆕🆕 11.1 旅中模式 MVP |
| | | 🆕🆕 11.2 同行人轻量协作 |
| | | 🆕🆕 11.3 微信承接产品化 |

### 🔑 关键新增（之前完全没有的）

| # | 任务 | 重要性 | AI级 | 建议谁做 |
|---|------|--------|------|---------|
| 4.2 | **5 种分享卡 Satori 生成** | 🔥🔥🔥 增长飞轮核心 | 🟡M | Sonnet |
| 4.3 | **分享回流页 `/s/[card_id]`** | 🔥🔥🔥 传播→获客闭环 | 🟡M | Sonnet |
| 4.4 | **交付页三层阅读结构** | 🔥🔥 用户体验核心 | 🔴H | 本窗口 |
| 3.3 | **预览页恢复 H5 独立成交引擎** | 🔥🔥🔥 转化率核心 | 🔴H | 本窗口 |
| 5.6 | **节奏轻重切换** | 🔥 差异化体验 | 🟡M | Sonnet |
| 9.3 | **CI/CD 质量回归** | 🔥 防止退化 | 🟢L | DeepSeek |
| 11.1 | **旅中模式 MVP** | 🔥 P2 可延后 | 🟡M | 后续 |
| 11.2 | **同行人协作** | 🔥 P2 可延后 | 🟡M | 后续 |
| 1.1 | **product_config.json 文件方案** | 🔥🔥 产品定海神针 | 🟢L | DeepSeek |
| 2.5-2.8 | **三城市种子数据** | 🔥🔥 需要真实数据 | 🔴H | 本窗口 |

---

## 📊 更新后全局统计

| 类别 | 原任务数 | v2 新增 | 重叠 | 实际总数 |
|------|---------|---------|------|---------|
| DB/Schema | 15 | 2 | 1 | 16 |
| Seed 数据 | 10 | 5 | 2 | 13 |
| 后端 Service | 20 | 8 | 4 | 24 |
| API 端点 | 8 | 4 | 2 | 10 |
| 前端页面/组件 | 12 | 10 | 2 | 20 |
| 文档/工具 | 10 | 2 | 0 | 12 |
| 测试/评测 | 5 | 2 | 1 | 6 |
| **总计** | **~80** | **~33** | **~12** | **~101** |

---

## ⚡ 当前并行状态 + 下一步

```
✅ DeepSeek    → Wave 0 DB Schema 完成（已发现并修复 3 处错误，见下方）
✅ 本窗口      → 核心引擎 + 多Agent评审 + Preview 页面 + Preview API 全部完成
⏳ Sonnet 窗口 → 等你开（提示词在 sonnet-prompts.md）
```

### 🔧 DeepSeek 代码修复记录（2026-03-21 12:42）

| # | 文件 | 问题 | 修复 |
|---|------|------|------|
| 1 | `soft_rules.py` L233-236 | `PreviewTriggerScore.itinerary_day_id` 引用了不存在的列 `itinerary_days.itinerary_day_id`（UUID），实际 PK 是 `day_id`（BigInteger） | 改为 `day_id: Mapped[int] = mapped_column(BigInteger, FK("itinerary_days.day_id"))` |
| 2 | migration L102+110 | 同上，migration 中的列名和外键也是错的 | 同步修复 `itinerary_day_id` → `day_id`，类型从 UUID 改为 BigInteger |
| 3 | `derived.py` EntityScore | migration 中 `add_column` 了 6 个新字段，但 ORM 模型没有对应的 `mapped_column` | 补充 `preview_score`/`context_score`/`soft_rule_score`/`soft_rule_breakdown`/`segment_pack_id`/`stage_pack_id` |
| 4 | `derived.py` ItineraryItem | migration 中 `add_column('swap_candidates')` 但 ORM 模型没有 | 补充 `swap_candidates: Mapped[Optional[dict]]` |

### 🆕 本窗口新增完成（2026-03-21）

| 任务 | 文件 | 状态 |
|------|------|------|
| 3.3 预览页恢复 H5 | `web/app/preview/[id]/page.tsx` | ✅ |
| Preview Data API | `app/api/trips_preview.py` | ✅ |
| product_config.json | `data/config/product_config.json` | ✅ |
| API route proxy | `web/app/api/plan/[id]/route.ts` 支持 `?mode=preview` | ✅ |
| 多Agent评审流水线 | `app/domains/review_ops/pipeline.py` | ✅ |
| generate_trip 集成 | `app/workers/jobs/generate_trip.py` | ✅ |
| Seed Data | `data/seed/seasonal_events.json` + `transport_pass_recommendations.json` | ✅ |
| **J1-J8 自助微调 API** | `app/api/trips_tuning.py`（get-candidates / swap / undo） | ✅ |
| **2.5-2.6 区域人流种子** | `data/seed/area_crowd_patterns.json`（17 区域 × 4 时段 × 2 日类型） | ✅ |
| **N1-N2 离线评测框架** | `app/domains/evaluation/offline_eval.py`（6 维评分 + 回归检测） | ✅ |
| **8.1 埋点事件系统** | `app/domains/tracking/events.py`（25 个事件类型 + schema + 写入） | ✅ |
| **DeepSeek 错误修复** | `soft_rules.py` FK / `derived.py` 缺字段 / migration 修复 | ✅ |

### 建议下一步优先级

1. **Sonnet** → 做 `4.2 分享卡 Satori` + `管理后台 C1-C5` + `4.4 交付页三层阅读`
2. **DeepSeek** → 做 Seed 数据（B2-B4）+ 文档体系（D1-D5）
3. **本窗口** → 做 `J1-J9 自助微调引擎`（核心体验）

---

## 📦 待执行：文档体系大任务（代码工作全部完成后启动）

> 以下两个任务由用户于 2026-03-21 12:48 下达，要求在当前所有代码实现工作完成后统一执行。

### DOC-1: 项目文档体系补全方案 v1

**角色**：项目整理官 + 文档架构师 + PMO + AI 文档设计师 + 事实校对员

**目标**：把项目从"很多零散成果"变成两套统一文档体系

**产出物**：《项目文档体系补全方案 v1》

**必须覆盖的 8 大模块**：
| 模块 | 内容 |
|------|------|
| A | 为什么必须同时补全"人类文档"和"AI 文档"——各解决什么问题 |
| B | 当前项目最需要先补的文档缺口（P0/P1/P2 排序） |
| C | **人类文档体系清单**（~10 份）——每份含：名称、读者、作用、必含章节、更新频率、负责人、关联文档 |
| D | **AI 文档体系清单**（~15 份）——每份含：名称、目标 AI/场景、作用、必含字段/章节、推荐格式（md/yaml/json/csv）、更新频率、维护人、被哪些模块引用 |
| E | **单一真相源字段设计**——预览深度、标准版权益、尊享版权益、微调边界、正式修改条件、微信节点、页面职责、城市覆盖、数据可信度、人工介入条件 |
| F | 推荐目录结构（`docs/` vs `docs/ai/` 分层） |
| G | Claude 文档维护机制——读哪些/写哪些/冲突标注/引用规则/何时补全何时不改 |
| H | 2 周内文档补全优先序 |
| I | 总结：这套文档体系如何减少混乱、提高协作效率、提高 AI 输出稳定性 |

**AI 文档至少包含**：
`project_overview.md` / `single_source_of_truth.yaml` / `glossary.md` / `system_map.md` / `workflow_contracts.md` / `hard_rules.md` / `soft_rules_schema.md` / `preview_engine_contract.md` / `self_serve_tuning_contract.md` / `city_context_schema.md` / `multi_agent_review_contract.md` / `evaluation_spec.md` / `event_tracking_schema.md` / `prompt_templates.md` / `example_cases.md`

**关键原则**：
- 先整理事实再判断，先统一口径再优化
- 明确区分：已确定 / 待确认 / 有冲突 / 尚未设计完整
- 人类文档重可读可决策；AI 文档重结构化契约化
- 能归并就归并，建立单一真相源

---

### DOC-2: 项目统一底稿 v1

**角色**：项目整理官 + PMO + 技术文档总编 + 事实校对员 + 任务收口负责人

**目标**：把当前项目从"很多零散成果"整理成"一个可以继续推进的清晰项目状态"

**产出物**：《项目统一底稿 v1》

**必须覆盖的 12 大模块**：
| 模块 | 内容 |
|------|------|
| A | **项目一句话定义**——是什么、卖什么、价值是什么 |
| B | **项目目标优先级**——3-5 个目标，区分商业/产品/系统 |
| C | **已形成共识的系统结构**——9 层（产品/生成/评审/数据/交付/前端/微调/后台/学习），每层：做什么、已明确什么、还缺什么 |
| D | **单一真相源冲突清单**——所有口径不一致处 + 建议统一方案 |
| E | **当前能力地图**——已有/半成型/缺失，影响维度：转付费/用户喜欢度/复购/减少人工/长期壁垒 |
| F | **当前关键缺口**——按影响面分类：转付费/体验/人工效率/数据壁垒 |
| G | **已确定的设计原则**——避免后续重复争论的关键共识 |
| H | **前端与用户体验现状**——首页/预览页/详情页/微调页/分享页/旅中/微信，标注已明确/模糊/优先补 |
| I | **数据与评测现状**——城市上下文/软规则/多模型评审/埋点/离线评测/验收标准，标注想清楚/方向/必须具体化 |
| J | **接下来最值得推进的 10 件事**——按优先级排序，含：做什么/为什么/解决什么/P0-P2/偏哪类 |
| K | **建议继续产出的文档清单**——含先后顺序 |
| L | **总结**——项目处于什么阶段、最该做什么、不该再纠结什么 |

**核心原则**：
- 先整理事实再判断，先统一口径再优化
- 不发散不 brainstorm，只整理/归档/统一/提炼/收口
- 发现冲突必须明确指出，未定论标为"待确认"不假装确定
- 输出必须是团队真正能用的底稿

---

### DOC 任务执行顺序

```
当前状态：⏸️ 等待（所有代码实现完成后启动）

执行顺序：
  Step 1 → DOC-2《项目统一底稿 v1》（先整理事实）
  Step 2 → DOC-1《文档体系补全方案 v1》（基于底稿设计文档架构）
  Step 3 → 逐份产出 P0 文档（single_source_of_truth.yaml → product_config spec → preview_engine_contract 等）
```
