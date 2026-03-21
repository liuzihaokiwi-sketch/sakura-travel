# Travel AI — 文档索引

> 最后更新：2026-03-22

## 📂 文档结构

```
docs-human/                          # 人工编写的核心需求文档（权威源）
  travel_ai_unified_system_doc.md    # 统一系统文档（25 章，唯一需求源）
  copywriting-audit-report.md        # 全站文案审查报告

docs/                                # AI 生成/维护的工作文档
  README.md                          # ← 你正在看的文档索引
  unified-system-gap-tasks.md        # 主任务清单（差距分析 + 全部任务状态）
  product-refactor-tasks.md          # 产品重构任务（表单字段 + 校验规则 + 状态流定义）
  eval_flywheel_and_case_system.md   # 评测飞轮设计（4 层评测 + 20 用例 + grader 规格）
  01-08_*.md                         # 产品定位/结构/增长等战略文档

docs/ops/                            # 运营相关文档
  09_post_trip_followup_and_feedback.md
  10_xiaohongshu_growth_engine.md
```

## 📋 哪个文档看什么

| 你想了解... | 看这个 |
|---|---|
| **需求全貌**（25 章完整系统定义） | `docs-human/travel_ai_unified_system_doc.md` |
| **当前进度**（什么做了、什么没做、谁做） | `docs/unified-system-gap-tasks.md` |
| **表单字段 + 校验规则 + 客服流程** | `docs/product-refactor-tasks.md` |
| **评测体系**（用例、grader、飞轮） | `docs/eval_flywheel_and_case_system.md` |
| **产品定位 & 定价** | `docs/01_positioning_and_value.md` + `02_product_structure_and_pricing.md` |
| **增长漏斗 & 前端** | `docs/06_growth_funnel_and_frontend.md` |

## 🗑️ 已清理的废弃文档

以下文档已在 2026-03-22 删除（内容已被 `travel_ai_unified_system_doc.md` 或其他文档取代）：

- `docs-human/00-overview.md` ~ `09-risk-and-known-issues.md`（10 篇，被统一文档取代）
- `docs-human/test.md`（被 `eval_flywheel_and_case_system.md` 取代）
- `docs-human/buchong.md`（空文件）
- `docs-human/crawlers-guide.md`（空 TODO）
- `docs/ALL_DOCS_COMBINED.md`（01-08 的合并副本，冗余）
- `docs/admin_generation_observability_spec.md`（设计方案，已被 H15a/H15b 实现取代）

## ⚡ 11 状态机（唯一定义）

```
new → sample_viewed → paid → detail_filling → detail_submitted
→ validating → needs_fix → validated → generating → done → delivered
终态：cancelled / refunded
```

所有后端 API、前端 UI、文档均已统一到此定义。