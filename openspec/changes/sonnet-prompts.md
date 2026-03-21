# Sonnet 中级 AI 窗口提示词

> 复制粘贴到 CodeMaker 新窗口使用

---

## 窗口 1：管理后台 + 审核 API

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

### 任务 1: 密码保护中间件
在 Next.js 端实现 `/admin` 路由的简单密码保护：
- 使用 Next.js middleware.ts，检测 `/admin*` 路由
- 密码存在环境变量 `ADMIN_PASSWORD` 中
- 未登录 → 跳转到 `/admin/login` 登录页
- 登录后在 cookie 中存 token（简单实现即可，不用 JWT）
- 创建 `web/app/admin/login/page.tsx` 登录页（密码输入框 + 登录按钮）

### 任务 2: 订单看板页
创建 `web/app/admin/page.tsx`，实现三列看板：
- 三列：待审核 📋 | 进行中 🔄 | 已交付 ✅
- 每个订单卡片显示：订单号（前8位）、城市+天数+同行人、套餐类型、旅行日期、创建时间/等待时长、状态标签
- 数据从后端 `GET /orders?status=xxx` 获取
- 支持点击卡片跳转到 `/admin/order/[id]`
- 自动刷新（每 30 秒 polling）
- 工具风格：紧凑布局、slate 色系、无动画

### 任务 3: 单订单审核页
创建 `web/app/admin/order/[id]/page.tsx`：
- **左右分栏**：左 60% 方案预览（只读，复用交付页组件）、右 40% 编辑面板
- **右侧三个 Tab**：
  - Tab 1 结构化修改：选天数 → 替换景点/餐厅（下拉备选5个）→ 调时间
  - Tab 2 提示词补充：textarea 输入框 + [重新生成此天] [重新生成全部] 按钮
  - Tab 3 历史版本：版本号/时间/变更摘要，可回退
- **底部按钮**：[保存草稿] [预览效果] [发布给用户 ✓]
- 系统自动标注可能有问题的内容（黄色高亮）

### 任务 4: 修改请求 API
在 `app/api/` 新建 `modifications.py`：
- `POST /orders/{order_id}/modify` — 接收结构化修改请求
  - body: `{ day: int, changes: [{ type: "replace_spot"|"replace_restaurant"|"adjust_pace"|"remove_spot", target_entity_id: str, replacement_entity_id?: str }] }`
  - 校验精调次数（248包1次，888包3次）
  - 扣减精调次数
  - 入队 `generate_trip` 重新生成受影响的天
  - 返回 202
- `GET /orders/{order_id}/modifications` — 查看修改历史

### 任务 5: 审核操作 API
在 `app/api/` 新建 `review.py`：
- `GET /admin/reviews/pending` — 待审核列表
- `PATCH /admin/reviews/{order_id}` — 更新方案内容
- `POST /admin/reviews/{order_id}/publish` — 发布（review → delivered）
- `POST /admin/reviews/{order_id}/reject` — 打回（review → generating）
- 在 `app/main.py` 中注册新路由

## 注意事项
- 所有前端页面在 `web/app/admin/` 下
- 不要修改已有的用户端页面
- 先读懂已有代码的风格和模式再动手
```

---

## 窗口 2：数据工具 + AI 缓存 + 仓库治理

```
你是一个 Python 后端工程师，负责在一个日本旅行定制服务项目中完成**翻译脚本、AI 模型分层、AI 缓存、仓库治理**。

## 项目技术栈
- FastAPI + SQLAlchemy 2 (async) + PostgreSQL + arq + Redis
- Python 3.11+，包管理用 pyproject.toml (hatch)

## 已有代码（先读再写）
- `app/core/config.py` — 全局配置 Settings
- `app/domains/catalog/tagger.py` — GPT 标签生成（调 OpenAI API）
- `app/domains/planning/copywriter.py` — AI 文案润色
- `scripts/` — 各种数据脚本
- `.env.example` / `.gitignore` / `README.md`

## 需要完成的 6 个任务

### 任务 1: 批量翻译脚本
创建 `scripts/batch_translate.py`：
- 用 DeepL 免费 API（https://api-free.deepl.com/v2/translate）
- 从 DB 读 entity_base 的 name_local（日文名）→ 翻译为中文 → 写入 name_zh
- Redis 缓存（key: `translate:ja:zh:{text}`，永不过期）
- 支持 `--city tokyo` 过滤 + `--dry-run` 预览
- 环境变量 `DEEPL_API_KEY`

### 任务 2: AI 模型分层配置
在 `app/core/config.py` Settings 中添加：
```python
ai_model_light: str = "gpt-4o-mini"      # 标签/分类
ai_model_standard: str = "gpt-4o"         # 推荐理由/润色
ai_model_strong: str = "claude-sonnet"    # 完整行程编排
```
- 更新 tagger.py 用 settings.ai_model_light
- 更新 copywriter.py 用 settings.ai_model_standard
- 更新 .env.example

### 任务 3: AI 调用缓存中间件
创建 `app/core/ai_cache.py`：
- `async def cached_ai_call(prompt, model, **kwargs) -> str`
- Redis key: `ai_cache:{model}:{sha256(prompt)}`，TTL 7天
- 命中 → 直接返回；未命中 → 调 AI → 缓存 → 返回
- 在 tagger.py 和 copywriter.py 中集成

### 任务 4: 安全扫尾
- `git log --all --diff-filter=A -- .env` 检查敏感文件
- 补全 .env.example（DATABASE_URL, REDIS_URL, OPENAI_API_KEY, DEEPL_API_KEY, ANTHROPIC_API_KEY, ADMIN_PASSWORD 等）
- 添加 pre-commit hook 防止提交 .env

### 任务 5: data/ 目录重组
```
data/
  seed/          ← 永久配置
  crawled/       ← 临时爬取（gitignore）
  city_defaults/ ← 城市默认图片
```
- 移动文件 + 更新代码路径引用 + 更新 .gitignore

### 任务 6: README + CONTRIBUTING + CODEOWNERS
更新 README.md（项目简介/技术栈/本地开发/常用命令/目录结构/API 端点）
创建 CONTRIBUTING.md（Git 工作流/代码风格/PR 流程）
创建 CODEOWNERS

## 注意事项
- 不碰前端代码
- 先读现有代码风格再写
```

---

## 窗口 3：前端组件 + 文档体系

```
你是一个前端工程师 + 技术文档工程师，负责**文档体系填充**和**前端组件开发**。

## 项目背景
日本旅行 AI 定制服务，技术栈：
- 后端：FastAPI + SQLAlchemy 2 + PostgreSQL + arq + Redis
- 前端：Next.js 14 + TypeScript + Tailwind CSS 4 + Framer Motion
- 渲染：Jinja2 + WeasyPrint PDF

## 需要完成的 4 个任务

### 任务 1: docs-human/ 文档填充
读取项目所有代码后，为 10 个文档写完整内容（面向人类开发者）：
- `docs-human/00-overview.md` — 项目全局概览
- `docs-human/01-product-scope.md` — 产品范围（定价/流程/交付物）
- `docs-human/02-system-architecture.md` — 系统架构图（文字版）
- `docs-human/03-data-system.md` — 数据体系
- `docs-human/04-generation-workflow.md` — 攻略生成流程
- `docs-human/05-delivery-workflow.md` — 交付流程
- `docs-human/06-ops-and-customer-service.md` — 运营与客服
- `docs-human/07-content-engine.md` — 内容引擎
- `docs-human/08-deployment-and-env.md` — 部署与环境
- `docs-human/09-risk-and-known-issues.md` — 风险与已知问题

每篇 200-400 字，清晰实用。

### 任务 2: docs-ai/ 文档填充
10 个结构化文档（面向 AI 编码助手）：
- `docs-ai/repo_index.md` — 目录结构树
- `docs-ai/module_registry.md` — Python 模块清单
- `docs-ai/dependency_map.md` — 模块间依赖
- `docs-ai/data_models.md` — 所有 ORM 模型
- `docs-ai/pipeline_catalog.md` — Worker job 清单
- `docs-ai/prompt_catalog.md` — GPT/Claude prompt 清单
- `docs-ai/config_inventory.md` — 环境变量清单
- `docs-ai/runtime_entrypoints.md` — 启动入口
- `docs-ai/naming_conventions.md` — 命名规范
- `docs-ai/do_not_break.md` — 高风险文件

格式用表格/代码块，便于 AI 解析。

### 任务 3: BloomTimeline 组件
创建 `web/components/rush/BloomTimeline.tsx`：
- 水平花期时间轴（3月上旬 → 4月下旬）
- 每半月一个节点（未开/3分咲/5分咲/满开/樱吹雪）
- 当前周高亮指示器
- sakura 色系（pink-200 → pink-500）
- Tailwind CSS + Framer Motion
- 移动端可横滚

### 任务 4: 全站文案审查
扫描所有用户可见文案，检查品牌规范：
- 不能出现"AI生成" → 改为"规划师"
- 不能讲功能 → 讲结果
- CTA 要有行动感
输出审查报告 markdown：文件/行号/当前文案/问题/建议。

## 注意事项
- 先通读整个项目代码再写文档
- 不修改后端 Python 代码
```
