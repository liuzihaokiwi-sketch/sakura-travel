# 剩余全部任务 — 5 轮并行执行计划

> 来源：product-conversion-redesign / phase0-data-scoring / phase1-trip-engine / nextjs-sakura-redesign / repo-restructure / tools-audit
> 总计：~35 个独立任务

---

## 并行依赖图

```
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  第1轮    │  │  第2轮    │  │  第4轮    │   ← 三轮可同时开始
        │ 管理后台  │  │ 数据+工具 │  │ 文档+前端 │
        └────┬─────┘  └────┬─────┘  └──────────┘
             │             │
             ▼             ▼
        ┌──────────────────────────┐
        │        第3轮              │   ← 等第1+2轮完成
        │  导出 + 端到端验证        │
        └────────────┬─────────────┘
                     │
                     ▼
        ┌──────────────────────────┐
        │        第5轮              │   ← 等全部完成
        │  视觉走查 + 收尾归档      │
        └──────────────────────────┘
```

**可并行的轮次**：第1轮 + 第2轮 + 第4轮 → 同时开 3 个 AI 窗口
**必须串行的轮次**：第3轮（依赖1+2）→ 第5轮（依赖全部）

---

## 🟦 第 1 轮：管理后台 + 审核 API（AI 窗口 A）

> ⚠️ 此轮写**前端（Next.js）+ 后端（FastAPI）**，需要两边都改

| # | 任务 | 来源 |
|---|---|---|
| 1.1 | D3. 实现密码保护中间件 | product-conversion |
| 1.2 | D1. 实现订单看板 `/admin` | product-conversion |
| 1.3 | D2. 实现单订单审核页 `/admin/order/[id]` | product-conversion |
| 1.4 | E3. 修改请求 API | product-conversion |
| 1.5 | E4. 审核操作 API | product-conversion |
| 1.6 | Git commit + push | — |

---

## 🟩 第 2 轮：数据补全 + 翻译 + 工具升级（AI 窗口 B）

> ⚠️ 此轮主要写**Python 脚本和配置**，不碰前端

| # | 任务 | 来源 |
|---|---|---|
| 2.1 | GPT 标签生成（全量） | phase0-data-scoring |
| 2.2 | 创建 `scripts/batch_translate.py` | tools-audit |
| 2.3 | AI 模型分层配置 | tools-audit |
| 2.4 | AI 调用缓存中间件 | tools-audit |
| 2.5 | R6 安全扫尾 | repo-restructure |
| 2.6 | data/ 目录重组 | repo-restructure |
| 2.7 | README + CONTRIBUTING + CODEOWNERS | repo-restructure |
| 2.8 | Git commit + push | — |

---

## 🟧 第 4 轮：双文档体系填充 + 前端补遗（AI 窗口 C）

> ⚠️ 此轮主要**写文档**，不碰代码逻辑（BloomTimeline 除外）

| # | 任务 | 来源 |
|---|---|---|
| 4.1 | docs-human/ 10 份文档填充 | repo-restructure |
| 4.2 | docs-ai/ 10 份文档填充 | repo-restructure |
| 4.3 | 创建 `BloomTimeline.tsx` | nextjs-sakura-redesign |
| 4.4 | 全站文案审查 | product-conversion |
| 4.5 | Git commit + push | — |

---

## 🟨 第 3 轮：导出功能 + 端到端验证（等第1+2轮完成后）

| # | 任务 | 来源 |
|---|---|---|
| 3.1 | C4. 交付页导出为图片 | product-conversion |
| 3.2 | PDF 验证 | phase1-trip-engine |
| 3.3 | 多场景攻略生成 | phase1-trip-engine |
| 3.4 | F1. 端到端全漏斗 | product-conversion |
| 3.5 | F3. 移动端适配 | product-conversion |
| 3.6 | F4. 社交分享验证 | product-conversion |
| 3.7 | Git commit + push | — |

---

## � 第 5 轮：视觉走查 + 自动化 + 收尾（最后执行）

| # | 任务 | 来源 |
|---|---|---|
| 5.1 | 全页面视觉走查 | nextjs-sakura-redesign |
| 5.2 | `?export=true` 验证 | nextjs-sakura-redesign |
| 5.3 | 小红书图 + 朋友圈图导出 | nextjs-sakura-redesign |
| 5.4 | Satori 批量导出 | nextjs-sakura-redesign |
| 5.5 | structlog 集成 | tools-audit |
| 5.6 | tenacity 重试 | tools-audit |
| 5.7 | OpenSpec 归档 | openspec |
| 5.8 | tag v1.0.0-beta + push | — |

---

## 📋 提示词（复制粘贴即可）

### AI 窗口 A — 第 1 轮提示词

```
你是一个全栈工程师，负责在一个日本旅行定制服务项目中实现**内部管理后台**和**审核 API**。

## 项目技术栈
- **前端**：Next.js 14 (App Router) + TypeScript + Tailwind CSS 4 + Framer Motion，项目在 `web/` 目录
- **后端**：FastAPI + SQLAlchemy 2 (async) + PostgreSQL + arq (Redis)，项目在 `app/` 目录
- **样式**：后台用**简洁工具风格**（不用杂志风），颜色用 slate/zinc 中性色系

## 已有代码（你要读取理解后再写）
- `app/api/orders.py` — 订单 CRUD + 状态机（quiz_submitted → preview_sent → paid → generating → review → delivered）
- `app/db/models/business.py` — Order / TripRequest / TripProfile 等 ORM 模型
- `app/main.py` — FastAPI 应用入口，路由注册在这里
- `web/app/plan/[id]/page.tsx` — 用户端交付页（审核页左侧预览要复用这个的渲染风格）

## 需要完成的 5 个任务（按顺序做）

### 任务 1: 密码保护中间件（D3）
在 Next.js 端实现 `/admin` 路由的简单密码保护：
- 使用 Next.js middleware.ts，检测 `/admin*` 路由
- 密码存在环境变量 `ADMIN_PASSWORD` 中
- 未登录 → 跳转到 `/admin/login` 登录页
- 登录后在 cookie 中存 token（简单实现即可，不用 JWT）
- 创建 `web/app/admin/login/page.tsx` 登录页（密码输入框 + 登录按钮）

### 任务 2: 订单看板页（D1）
创建 `web/app/admin/page.tsx`，实现三列看板：
- 三列：待审核 📋 | 进行中 🔄 | 已交付 ✅
- 每个订单卡片显示：订单号（前8位）、城市+天数+同行人、套餐类型、旅行日期、创建时间/等待时长、状态标签
- 数据从后端 `GET /orders?status=xxx` 获取
- 支持点击卡片跳转到 `/admin/order/[id]`
- 自动刷新（每 30 秒 polling）
- 工具风格：紧凑布局、slate 色系、无动画

### 任务 3: 单订单审核页（D2）
创建 `web/app/admin/order/[id]/page.tsx`：
- **左右分栏**：左 60% 方案预览（只读，复用交付页组件）、右 40% 编辑面板
- **右侧三个 Tab**：
  - Tab 1 结构化修改：选天数 → 替换景点/餐厅（下拉备选5个）→ 调时间
  - Tab 2 提示词补充：textarea 输入框 + [重新生成此天] [重新生成全部] 按钮
  - Tab 3 历史版本：版本号/时间/变更摘要，可回退
- **底部按钮**：[保存草稿] [预览效果] [发布给用户 ✓]
- 系统自动标注可能有问题的内容（黄色高亮）
- 快捷键：Cmd+S 保存，Cmd+Enter 发布

### 任务 4: 修改请求 API（E3）
在 `app/api/` 新建 `modifications.py`：
- `POST /orders/{order_id}/modify` — 接收结构化修改请求
  - body: `{ day: int, changes: [{ type: "replace_spot"|"replace_restaurant"|"adjust_pace"|"remove_spot", target_entity_id: str, replacement_entity_id?: str }] }`
  - 校验精调次数（248包1次，888包3次）
  - 扣减精调次数
  - 入队 `generate_trip` 重新生成受影响的天
  - 返回 202
- `GET /orders/{order_id}/modifications` — 查看修改历史

### 任务 5: 审核操作 API（E4）
在 `app/api/` 新建 `review.py`：
- `GET /admin/reviews/pending` — 待审核列表（status=review 的订单）
- `PATCH /admin/reviews/{order_id}` — 更新方案内容（body 包含修改后的 itinerary JSON）
- `POST /admin/reviews/{order_id}/publish` — 发布给用户（状态 review → delivered）
- `POST /admin/reviews/{order_id}/reject` — 打回重做（状态 review → generating）
- 在 `app/main.py` 中注册新路由

## 注意事项
- 所有前端页面在 `web/app/admin/` 下
- 后台 API 路由前缀用 `/admin/` 和 `/orders/`
- 不要修改已有的用户端页面（`/plan`、`/quiz` 等）
- 每完成一个任务做一次 git commit
- 最后 git push
```

---

### AI 窗口 B — 第 2 轮提示词

```
你是一个 Python 后端工程师，负责在一个日本旅行定制服务项目中完成**数据补全、翻译脚本、AI 模型分层、仓库治理**等工作。

## 项目技术栈
- **后端**：FastAPI + SQLAlchemy 2 (async) + PostgreSQL + arq + Redis
- **Python 版本**：3.11+
- **包管理**：pyproject.toml (hatch)
- **已有脚本**：`scripts/crawl.py`、`scripts/generate_tags.py`、`scripts/mark_data_tier.py`

## 已有代码（你要读取理解后再写）
- `app/domains/catalog/tagger.py` — GPT 标签生成模块（generate_tags_for_city 函数）
- `app/core/config.py` — 全局配置（Settings + Pydantic）
- `scripts/generate_tags.py` — 标签生成脚本（支持 --city 和 --seed-only）
- `data/` 目录 — 种子数据 JSON + 爬取数据
- `.env.example` — 环境变量示例
- `.gitignore` — 当前 gitignore 规则
- `README.md` — 项目说明

## 需要完成的 7 个任务（按顺序做）

### 任务 1: GPT 标签生成（2.1）
运行已有的标签生成脚本为三个城市的所有实体生成 9 维主题亲和度标签：
```bash
cd /Users/yanghailin/projects/travel-ai
python scripts/generate_tags.py --city tokyo
python scripts/generate_tags.py --city osaka
python scripts/generate_tags.py --city kyoto
```
- 需要先确认数据库连接和 OpenAI API key 配置正确
- 检查 `.env` 中有 `OPENAI_API_KEY`
- 如果运行报错，修复问题后重试
- 记录生成了多少条标签

### 任务 2: 批量翻译脚本（2.2）
创建 `scripts/batch_translate.py`：
- 使用 DeepL 免费 API（https://api-free.deepl.com/v2/translate）
- 从数据库读取所有 entity_base 中 name_local（日文名）
- 翻译为中文，写入 name_zh 字段（如果 entity_base 没有此字段，先用 Alembic 加）
- Redis 缓存翻译结果（key: `translate:ja:zh:{text}`，永不过期）
- 支持 `--city tokyo` 过滤和 `--dry-run` 预览
- 需要环境变量 `DEEPL_API_KEY`
- 在 `.env.example` 中添加 `DEEPL_API_KEY=`

### 任务 3: AI 模型分层配置（2.3）
在 `app/core/config.py` 的 Settings 类中添加三级 AI 模型配置：
```python
ai_model_light: str = "gpt-4o-mini"      # Tier 1: 标签/分类/翻译
ai_model_standard: str = "gpt-4o"         # Tier 2: 推荐理由/润色
ai_model_strong: str = "claude-sonnet"    # Tier 3: 完整行程编排
```
- 更新 `app/domains/catalog/tagger.py` 使用 `settings.ai_model_light`
- 更新 `app/domains/planning/copywriter.py` 使用 `settings.ai_model_standard`
- 更新 `.env.example` 添加对应环境变量

### 任务 4: AI 调用缓存中间件（2.4）
创建 `app/core/ai_cache.py`：
- 实现 `async def cached_ai_call(prompt, model, **kwargs) -> str`
- Redis 缓存 key: `ai_cache:{model}:{sha256(prompt)}`
- TTL: 7 天
- 命中缓存时直接返回，不调用 AI
- 未命中时调用对应 AI API，缓存后返回
- 在 tagger.py 和 copywriter.py 中集成使用

### 任务 5: 安全扫尾（2.5）
- 检查 `.env` 是否曾被 git 提交：`git log --all --diff-filter=A -- .env`
- 如果存在，用 `git filter-repo` 或 BFG 清理
- 补全 `.env.example`（确保包含所有环境变量：DATABASE_URL, REDIS_URL, OPENAI_API_KEY, DEEPL_API_KEY, ANTHROPIC_API_KEY, SERPAPI_KEY, GOOGLE_PLACES_API_KEY, ADMIN_PASSWORD）
- 添加 pre-commit hook 防止提交 .env 文件

### 任务 6: data/ 目录重组（2.6）
将 data/ 目录重组为：
```
data/
  seed/          ← 永久配置（route templates, region matrix, entity affinity seed）
  crawled/       ← 临时爬取数据（gitignore 排除）
  city_defaults/ ← 城市默认图片
```
- 移动现有 JSON 种子文件到 `data/seed/`
- 确保所有 `open("data/xxx.json")` 的代码路径不被打断（用软链接兼容）
- 更新 `.gitignore` 排除 `data/crawled/`

### 任务 7: README + CONTRIBUTING + CODEOWNERS（2.7）
更新 `README.md`：
- 项目简介（日本旅行 AI 定制服务）
- 技术栈清单
- 本地开发环境搭建步骤（Python + Node + DB + Redis）
- 常用命令（启动后端/前端/运行脚本）
- 目录结构说明
- API 端点概览

创建 `CONTRIBUTING.md`：
- Git 工作流（分支命名/commit 规范）
- 代码风格（Ruff / ESLint）
- PR 流程

创建 `CODEOWNERS`：
- `app/` → 后端负责人
- `web/` → 前端负责人
- `openspec/` → 产品负责人

## 注意事项
- 不要修改前端代码（web/ 目录）
- 每完成一个任务做一次 git commit
- 最后 git push
```

---

### AI 窗口 C — 第 4 轮提示词

```
你是一个技术文档工程师 + 前端工程师，负责在一个日本旅行定制服务项目中完成**双文档体系填充**和**一个前端组件**。

## 项目背景
这是一个日本旅行 AI 定制服务（Travel AI），技术栈：
- 后端：FastAPI + SQLAlchemy 2 + PostgreSQL + arq + Redis
- 前端：Next.js 14 + TypeScript + Tailwind CSS 4 + Framer Motion
- 渲染：Jinja2 模板 + WeasyPrint PDF
- 数据：爬虫 + GPT 标签 + 评分引擎 + 行程装配器

项目目录结构：
- `app/` — Python 后端（domains/catalog, domains/planning, domains/ranking, domains/rendering, api/, workers/, db/）
- `web/` — Next.js 前端（app/page.tsx 首页, app/quiz 问卷, app/plan/[id] 交付页, app/pricing 价格页）
- `templates/magazine/` — Jinja2 杂志风模板
- `data/` — 种子数据 + 爬取数据
- `scripts/` — 采集/标签/翻译脚本
- `openspec/` — 需求文档和变更管理

## 需要完成的 4 个任务

### 任务 1: docs-human/ 文档填充（4.1）
读取项目所有代码后，为以下 10 个文档写入**完整内容**（面向人类开发者/产品经理/新人 onboarding）：

| 文件 | 内容 |
|---|---|
| `docs-human/00-overview.md` | 项目全局概览：是什么、解决什么问题、目标用户、商业模式 |
| `docs-human/01-product-scope.md` | 产品范围：三档定价（免费/248/888）、用户流程、交付物 |
| `docs-human/02-system-architecture.md` | 系统架构图（文字版）：前端→API→Worker→DB 的数据流 |
| `docs-human/03-data-system.md` | 数据体系：实体类型、采集来源、GPT标签、评分引擎、数据新鲜度 |
| `docs-human/04-generation-workflow.md` | 攻略生成流程：模板选择→装配→文案润色→护栏检查→渲染→导出 |
| `docs-human/05-delivery-workflow.md` | 交付流程：问卷→微信→审核→发布→修改→升级 |
| `docs-human/06-ops-and-customer-service.md` | 运营与客服：话术规范、分流策略、FAQ |
| `docs-human/07-content-engine.md` | 内容引擎：小红书内容支柱、排期、素材来源 |
| `docs-human/08-deployment-and-env.md` | 部署与环境：Docker/环境变量/数据库迁移/Redis |
| `docs-human/09-risk-and-known-issues.md` | 风险与已知问题：数据缺口、图片治理、翻译覆盖 |

每篇文档 200-400 字，清晰实用，不要空话。

### 任务 2: docs-ai/ 文档填充（4.2）
为以下 10 个文档写入**结构化内容**（面向 AI 编码助手，帮助 AI 快速理解项目结构）：

| 文件 | 内容 |
|---|---|
| `docs-ai/repo_index.md` | 目录结构树 + 每个目录的一句话说明 |
| `docs-ai/module_registry.md` | 所有 Python 模块清单（路径 + 职责 + 关键函数） |
| `docs-ai/dependency_map.md` | 模块间依赖关系（谁 import 谁） |
| `docs-ai/data_models.md` | 所有 SQLAlchemy 模型清单（表名 + 字段 + 关系） |
| `docs-ai/pipeline_catalog.md` | 所有数据管线/Worker job 清单（输入→处理→输出） |
| `docs-ai/prompt_catalog.md` | 所有 GPT/Claude prompt 模板清单（位置 + 用途 + 模型） |
| `docs-ai/config_inventory.md` | 所有环境变量/配置项清单 |
| `docs-ai/runtime_entrypoints.md` | 启动入口清单（FastAPI/Worker/脚本） |
| `docs-ai/naming_conventions.md` | 命名规范（文件/类/函数/变量/路由） |
| `docs-ai/do_not_break.md` | 高风险文件清单（修改这些文件前必须格外小心） |

格式要求：用表格或代码块，便于 AI 解析。不要叙述，只要结构化数据。

### 任务 3: BloomTimeline 组件（4.3）
创建 `web/components/rush/BloomTimeline.tsx`：
- 水平花期时间轴组件
- 显示 3月上旬 → 4月下旬 的时间范围
- 每个半月一个节点，显示花期状态（未开/3分咲/5分咲/满开/樱吹雪）
- 当前周用高亮指示器标注
- 使用 Tailwind CSS + Framer Motion 动画
- 颜色用 sakura 色系（pink-200 到 pink-500）
- 移动端可横向滚动

### 任务 4: 全站文案审查（4.4）
扫描以下文件中的所有用户可见文案，检查是否符合品牌规范：
- `web/app/page.tsx`（首页）
- `web/app/quiz/page.tsx`（问卷）
- `web/app/pricing/page.tsx`（价格页）
- `web/app/plan/[id]/page.tsx`（交付页）
- `web/app/submitted/page.tsx`（提交成功页）

检查规则：
1. 不能出现"AI生成"、"自动生成"等字眼 → 应改为"规划师"、"专业团队"
2. 不能讲功能 → 要讲"用户痛点 → 你获得的结果"
3. 不能有"限制"、"上限"、"不能" → 用正向表达
4. CTA 要有行动感，不要"了解更多"这种弱CTA

输出一份审查报告（markdown），列出：文件/行号/当前文案/问题/建议修改。

## 注意事项
- 先通读整个项目代码再写文档（确保内容准确）
- 不要修改后端 Python 代码
- 每完成一个任务做一次 git commit
- 最后 git push
```

---

## 第 3 轮和第 5 轮提示词（等前面完成后再用）

### 第 3 轮提示词

```
做第3轮：导出功能和端到端验证。

具体任务：
1. C4 交付页导出为图片（Playwright截图→朋友圈分享图1080x1080）
2. 验证 PDF 可正常打开，中文显示正常
3. 生成 2 条不同场景攻略（tokyo_classic_5d/couple + kansai_classic_6d/family），人工检查质量
4. 端到端走通全漏斗（首页→问卷→提交→微信→生成→审核→交付→修改）
5. 移动端适配验证（Landing/Quiz/Pricing/Plan 四大页面）
6. 社交分享验证（OG图/微信卡片）
7. Git commit + push

参考 openspec/changes/all-remaining-tasks.md 中第3轮的详细说明。
```

### 第 5 轮提示词

```
做第5轮：内容引擎和收尾归档。

具体任务：
1. 全页面视觉走查（首页/排行榜/定制/导出）
2. 验证 ?export=true 模式下 Navbar/FloatingCTA 隐藏
3. Playwright 导出小红书图 + 朋友圈图质量检查
4. Satori 批量导出 5 城市封面卡片
5. structlog 结构化日志集成
6. tenacity 重试策略替换手写 retry
7. 归档所有已完成的 OpenSpec changes
8. 最终 Git 清理 + tag v1.0.0-beta + push

参考 openspec/changes/all-remaining-tasks.md 中第5轮的详细说明。
```