# Repo Index（AI 版）

> 作用：帮助 AI 和开发者快速理解仓库结构。它描述的是当前代码现实，不等于最终产品真相源。

## 一、仓库结构

### 后端
- `app/api/`：HTTP 路由入口
- `app/core/`：配置、队列、缓存、日志
- `app/db/models/`：ORM 模型，按 catalog / business / derived / snapshots 分层
- `app/domains/`：领域逻辑，主要包括 catalog / ranking / planning / rendering / geography
- `app/workers/`：异步任务
- `app/main.py`：FastAPI 入口

### 前端
- `web/app/`：Next.js App Router 页面
- `web/components/`：共享组件
- `web/lib/`：前端工具函数与数据加载器
- `web/scripts/`：前端导出、验证脚本

### 脚本与数据
- `scripts/`：数据采集、初始化、维护脚本
- `data/`：seed / sakura / route_templates / crawled 等数据
- `templates/`：Jinja2 渲染模板

### 文档
- `docs-human/`：人类文档
- `docs-ai/`：当前旧版 AI 文档
- `docs-ai-v2/`：新的 AI 指引文档
- `openspec/`：变更管理

## 二、当前代码事实
- 代码仍保留 `product_sku`、旧产品档位和旧生成链路
- 前端已有首页、问卷、价格页、/rush、提交成功页、plan 页面
- `/rush` 已有真实数据加载器和交互组件
- 行程生成主要依赖 ranking + assembler + copywriter + render

## 三、已知与新方向的偏差
1. 产品新方向强调“前台少套餐、后台多维映射”，代码里仍保留旧 SKU 设计
2. 新方向强调“总纲 + 每日固定骨架 + 条件页”，代码里还没有完整落地
3. 新方向强调“免费体验版 = 一天完整样片 + 后续钩子”，现有代码未必完全实现
4. 新方向强调“自助微调优先”，代码中该闭环仍需补全

## 四、AI 读取顺序
1. 看本文件
2. 看 `do_not_break.md`
3. 看 `runtime_entrypoints.md`
4. 看 `data_models.md`
5. 看 `dependency_map.md`
6. 再去读具体模块

## 五、不要做的事
- 不要把旧代码中的产品结构自动当成最终产品真相源
- 不要先改高风险文件再理解依赖
- 不要忽略 `/rush`、预览页、问卷和 PDF 交付这些现阶段核心链路
