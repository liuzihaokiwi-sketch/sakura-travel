
# 当前状态与剩余工作

> 最后更新: 2026-03-29

---

## 系统成熟度

| 模块 | 状态 | 说明 |
|------|------|------|
| 表单采集 (Intake) | **可用** | DetailForm + submissions 完整 |
| 归一化 (Normalize) | **可用** | layer2_contract + profile tags |
| 城市圈决策链 | **可用** | 完整10步管线，Kansai 圈数据最全 |
| 页面生成 | **可用** | planning_output 直通，17种页型 |
| PDF 渲染 | **可用** | WeasyPrint + 水印 |
| 质量门控 | **可用** | 规则引擎 + 离线评测 + 多模型评审 |
| 管理后台 | **基本可用** | 订单/实体CRUD/配置/trace/review |
| 用户前端 | **暂停** | 骨架在，前期不上线，抖音表单为主入口 |

---

## MVP 定义

目标：Kansai 关西经典圈，端到端跑通一个完整订单。

**MVP = 一个真实用户付298块，收到手账本，觉得值。**

启动条件：
- Kansai 圈核心实体数据深度够用（S级实体全部加厚）
- 端到端 form → PDF 可跑通
- 自动发布率 >80%
- PDF 有真实图片（非 placeholder）
- 出发准备内容为关西实际内容（非通用占位）

明确推迟：其余5个城市圈、H5渠道、抖音入口对接、V3多步表单、运营后台城市圈结构管理

---

## 已完成总览

> 第一波（代码基础设施 A1-A6）+ 第二波（数据生成 C1-C3 + 功能代码 D1-D8）+ 架构重构 — **全部完成**。
> 详细清单见 git log。

**代码侧**：flights 删除、定价迁移、schema 升级、预约提醒 cron、API 限流、推荐轮转、知识包接入、文案 prompt、Plan B、预约指南、预算估算、DIY 渲染、企微通知、Sentry、全链路集成测试（291 passed）

**数据侧**：关西深度数据（20景点+30餐厅+10住宿区域）已生成，**待审核后导入 DB**

**架构侧**：Report-First 胶水层删除（~1900行）、planning_output 直出、copy_enrichment 独立、旧 assembler/renderer 删除、文档精简

---

## 数据第一性原理

详见 [DATA_FIRST_PRINCIPLES.md](DATA_FIRST_PRINCIPLES.md)：从用户拿到手账的体验倒推数据需求，统一了 quality_tier/budget_tier/arrival_friendly 等矛盾口径，定义了 6 层数据结构和 3 层字段重要性分级。

---

## 质量差距（架构OK，数据和视觉是短板）

| 维度 | 状态 |
|------|------|
| 实体数据深度 | 20景+30餐+10区已生成，**待审核导入** |
| 出行实用信息 | ✅ 关西知识包8 section 已接入 |
| 文案质量 | ✅ "去过20次旅行者"语感 prompt 已替换 |
| Plan B | ✅ 三类替代逻辑已接入 |
| 预算透明 | ✅ 每日预算写入 plan_metadata |
| 视觉 | ⏳ placeholder 图片，等提供实拍（1.7） |

---

## 剩余工作（等你参与）

| # | 任务 | 执行方 | 依赖 | 状态 |
|---|------|--------|------|------|
| C1-C3 | 审核关西深度数据（20景+30餐+10区） | 👤 你审核 | 数据已生成 | ⏳ 等你（~3h） |
| E1 | 审核通过后导入 DB | 🤖 Sonnet | C1-C3 审核✅ | 脚本已写好 |
| 1.7 | 图片素材收集 | 👤 你 | 无 | ⏳ 随时可做 |
| E2 | 素材包接入 | 🤖 Sonnet | 1.7✅ | 等图片 |
| E4 | 10单冒烟测试 | 🤖+👤 | E1✅ | 待启动 |
| E5 | 10份样本审读 | 👤 你 | E4✅ | 待启动 |
| 3.1 | 确定前期入口（抖音/客服/H5） | 👤 决策 | 随时 | ⏳ |
| 3.5 | 交付方式确定 | 👤 决策 | 随时 | ⏳ |

**关键路径**：C1-C3 审核 → E1 导入 → E4 冒烟 → E5 审读 → **可以接第一单**

---

## 六城市圈覆盖度

| 城市圈 | 实体数据 | 策略包 | 知识包 | 状态 |
|--------|---------|--------|--------|------|
| 关西经典 (Kansai) | ~224骨架 + 20景点/30餐厅/10区域深度数据（**待审核导入**） | 有 | ✅ 完整8 section | **MVP 目标，数据待审核** |
| 关东 (Kanto) | 少量 | 骨架 | 占位 | 待 MVP 后 |
| 北海道 (Hokkaido) | 少量 | 骨架 | 占位 | 待 MVP 后 |
| 广府 (Guangfu) | 无 | 无 | 无 | 待启动 |
| 北疆 (Xinjiang) | 无 | 无 | 无 | 待启动 |
| 广东 (Guangdong) | 无 | 无 | 无 | 待启动 |

---

## 本轮收口更新（2026-03-29，Codex）

已完成：
- `activity_clusters` 核心字段全量回填完成：`city_code / experience_family / rhythm_role / energy_level` 现已全部补齐。
- 关西圈 `anchor_entities` 补齐完成：`kansai_classic_circle` 的 weak anchor 已从 30 降到 0。
- 全圈 `circle_entity_roles` 已完成一轮自动绑定，新增 424 条 role 记录。
- 绑定脚本已修复两处问题：
  - 已存在判断改为按 `(circle_id, cluster_id, entity_id, role)` 检查
  - 单次执行内增加 planned-key 去重，避免唯一约束冲突

当前数据库结果：
- 所有城市圈 `missing_city_code = 0`
- 所有城市圈 `missing_experience_family = 0`
- 所有城市圈 `missing_rhythm_role = 0`
- 所有城市圈 `missing_energy_level = 0`
- 所有城市圈 `weak_anchor = 0`

当前 role 绑定覆盖：
- `kansai_classic_circle`: S/A `41/45`，`role_rows = 339`
- `tokyo_metropolitan_circle`: S/A `37/43`，`role_rows = 142`
- `hokkaido_nature_circle`: S/A `25/35`，`role_rows = 68`
- `hokkaido_city_circle`: S/A `2/2`，`role_rows = 7`
- `kanto_city_circle`: S/A `2/2`，`role_rows = 12`
- `osaka_day_base_circle`: S/A `4/4`，`role_rows = 17`

仍未收口的真实缺口：
- `anchor_entities -> entity_base` 的实体匹配率目前约 `26%`（`501 / 1909`）
- 仍有 `1408` 个实体需求未匹配到 `entity_base`
- 最新分析报告：`data/seed/cluster_entity_pipeline/gaps_report_20260329_043538.json`

缺口优先级判断：
- 当前不再是“簇字段不完整”问题
- 当前主要是“实体库未覆盖 / 名称匹配不足”问题
- 下一步应优先处理 `not_found` 报表，按圈补实体后再重跑绑定

完成人：
- `Codex`
