# 剩余全部任务 — 5 轮均分执行计划

> 来源：product-conversion-redesign / phase0-data-scoring / phase1-trip-engine / nextjs-sakura-redesign / repo-restructure / tools-audit
> 原则：按依赖关系排序，每轮 AI 执行时间大致相当（约 30-45 分钟）
> 总计：~35 个独立任务

---

## 🟦 第 1 轮：管理后台 + 审核 API（后台核心闭环）

> 目标：让"接单→审核→发布"全流程跑通

| # | 任务 | 来源 |
|---|---|---|
| 1.1 | D3. 实现密码保护中间件（简单 Basic Auth） | product-conversion |
| 1.2 | D1. 实现订单看板 `/admin`（三列看板：待处理/审核中/已发布） | product-conversion |
| 1.3 | D2. 实现单订单审核页 `/admin/order/[id]`（左侧预览+右侧编辑+状态切换） | product-conversion |
| 1.4 | E3. 修改请求 API（POST /orders/{id}/modify → 结构化修改 → 重新生成 → 审核队列） | product-conversion |
| 1.5 | E4. 审核操作 API（GET 待审核列表 / PATCH 更新内容 / POST 发布） | product-conversion |
| 1.6 | Git commit + push | — |

**交付物**：`/admin` 看板可用，修改+审核 API 可调用

---

## 🟩 第 2 轮：数据补全 + 翻译 + 工具升级

> 目标：数据质量提升，填补评分/翻译/AI 分层空白

| # | 任务 | 来源 |
|---|---|---|
| 2.1 | 7.5 运行 GPT 标签生成（tokyo + osaka + kyoto 全量实体） | phase0-data-scoring |
| 2.2 | P0 — 创建 `scripts/batch_translate.py`（DeepL 免费 API + Redis 缓存批量翻译景点/餐厅名） | tools-audit |
| 2.3 | P0 — AI 模型分层配置（config.py 加 ai_model_light/standard/strong 三级） | tools-audit |
| 2.4 | P1 — AI 调用缓存中间件（Redis 缓存 AI 响应，key=hash(prompt+model)） | tools-audit |
| 2.5 | R6 安全扫尾：确认 .env 不在 git 历史 + 补全 .env.example + pre-commit hook | repo-restructure |
| 2.6 | R7 Commit 5：data/ 目录重组（seed/ + crawled/ + 软链接兼容） | repo-restructure |
| 2.7 | R7 Commit 7：更新 README.md + 新增 CONTRIBUTING.md + CODEOWNERS | repo-restructure |
| 2.8 | Git commit + push | — |

**交付物**：全量 GPT 标签、翻译脚本、AI 分层配置、仓库治理完成

---

## 🟨 第 3 轮：导出功能 + 交付验证

> 目标：导出图片/PDF 可用，端到端交付流程验证

| # | 任务 | 来源 |
|---|---|---|
| 3.1 | C4. 交付页"导出为图片"功能（Playwright 截图 → 朋友圈分享图） | product-conversion |
| 3.2 | 8.2 验证 PDF 可正常打开，中文显示正常，排版符合杂志级标准 | phase1-trip-engine |
| 3.3 | 8.6 生成 2 条不同场景攻略（tokyo_classic_5d/couple + kansai_classic_6d/family）并人工检查 | phase1-trip-engine |
| 3.4 | F1. 端到端走通全漏斗（首页→问卷→提交→微信→生成→审核→交付→修改） | product-conversion |
| 3.5 | F3. 移动端适配验证（Landing/Quiz/Pricing/Plan 四大页面） | product-conversion |
| 3.6 | F4. 社交分享验证（OG 图/微信卡片/小红书分享） | product-conversion |
| 3.7 | Git commit + push | — |

**交付物**：分享图可导出，全漏斗端到端通过，移动端适配 OK

---

## 🟧 第 4 轮：双文档体系填充 + 前端补遗

> 目标：文档从骨架变成可用参考，前端遗留组件补完

| # | 任务 | 来源 |
|---|---|---|
| 4.1 | docs-human/ 10 个文档填充内容（overview → product-scope → architecture → data → generation → delivery → ops → content → deployment → risk） | repo-restructure |
| 4.2 | docs-ai/ 10 个文档填充内容（repo_index → module_registry → dependency_map → data_models → pipeline_catalog → prompt_catalog → config_inventory → runtime_entrypoints → naming_conventions → do_not_break） | repo-restructure |
| 4.3 | 4.3 创建 `BloomTimeline.tsx`（水平花期时间轴 + 当前周高亮） | nextjs-sakura-redesign |
| 4.4 | F2. 全站文案审查（品牌语气规范合规性 — "痛点→结果"原则检查） | product-conversion |
| 4.5 | Git commit + push | — |

**交付物**：完整双文档体系、BloomTimeline 组件、文案审查报告

---

## 🟥 第 5 轮：内容引擎 + 长期自动化 + 收尾

> 目标：内容生产自动化基础设施，收尾全部 spec 检查项

| # | 任务 | 来源 |
|---|---|---|
| 5.1 | 8.1 全页面视觉走查（首页/排行榜/定制/导出） | nextjs-sakura-redesign |
| 5.2 | 8.2 验证 `?export=true` 模式下 Navbar/FloatingCTA 隐藏 | nextjs-sakura-redesign |
| 5.3 | 8.3 Playwright 导出小红书图 + 朋友圈图质量检查 | nextjs-sakura-redesign |
| 5.4 | 8.4 Satori 批量导出 5 城市封面卡片 | nextjs-sakura-redesign |
| 5.5 | P1 — 结构化日志 structlog 集成 | tools-audit |
| 5.6 | P2 — tenacity 重试策略替换手写 retry | tools-audit |
| 5.7 | 归档已完成的 OpenSpec changes（nextjs-sakura-redesign / phase0-data-scoring / phase1-trip-engine / product-conversion-redesign / repo-restructure） | openspec 治理 |
| 5.8 | 最终 Git 清理 + tag v1.0.0-beta + push | — |

**交付物**：视觉走查通过、内容导出可用、日志/重试升级、OpenSpec 归档完成、发布 beta 标签

---

## 提示词速查

| 轮次 | 提示词 |
|---|---|
| 第 1 轮 | `做第1轮：管理后台和审核API` |
| 第 2 轮 | `做第2轮：数据补全和工具升级` |
| 第 3 轮 | `做第3轮：导出功能和端到端验证` |
| 第 4 轮 | `做第4轮：文档填充和前端补遗` |
| 第 5 轮 | `做第5轮：内容引擎和收尾归档` |
