# Do Not Break — 高风险文件清单

> 修改以下文件前务必阅读上下文，理解影响范围，并准备回退方案。

## 🔴 最高风险（修改前必须有测试覆盖）

| 文件 | 职责 | 被谁依赖 | 修改注意 |
|------|------|----------|----------|
| `app/domains/ranking/scorer.py` | 三层评分引擎 | assembler / queries / API | 改评分公式影响所有排序结果 |
| `app/domains/planning/assembler.py` | 行程装配核心 | trips_generate / workers | 改装配逻辑影响所有行程输出 |
| `app/db/models/business.py` | 订单/行程 ORM | 所有 API + workers | 改字段需同步 Alembic 迁移 |
| `app/db/models/catalog.py` | 实体 ORM（35+表） | catalog + ranking + planning | 改字段需同步迁移 + 查询 |
| `app/main.py` | FastAPI 入口 + 路由注册 | 整个后端 | 路由顺序/前缀错误导致 API 不可用 |
| `app/db/session.py` | 数据库连接工厂 | 所有 DB 操作 | 改连接参数影响全局 |

## 🟡 高风险（修改需谨慎）

| 文件 | 职责 | 修改注意 |
|------|------|----------|
| `app/core/config.py` | 全局配置 | 新增字段需同步 .env.example |
| `app/core/ai_cache.py` | AI 缓存中间件 | 改 key 格式会导致缓存失效 |
| `app/domains/catalog/tagger.py` | GPT 标签生成 | 改 prompt 影响标签质量 |
| `app/domains/planning/copywriter.py` | AI 文案润色 | 改 prompt 影响推荐理由文风 |
| `app/domains/ranking/affinity.py` | 种子亲和度数据 | 硬编码的种子数据 |
| `app/api/orders.py` | 订单状态机 | 状态流转逻辑 |
| `web/middleware.ts` | admin 路由保护 | 改错会暴露管理后台 |
| `web/app/page.tsx` | 首页（核心转化页） | 改文案影响转化率 |

## 🟢 数据文件（不可删除）

| 文件 | 说明 |
|------|------|
| `data/seed/entity_affinity_seed_v1.json` | 人工标注的种子亲和度 |
| `data/seed/p0_route_skeleton_templates_v1.json` | 路线骨架模板 |
| `data/seed/japan_region_usertype_matrix_v1.json` | 区域×用户类型矩阵 |
| `data/seed/context_score_design.json` | 评分维度设计 |
| `data/seed/questionnaire_to_theme_weights_rules_v1.json` | 问卷→偏好权重规则 |