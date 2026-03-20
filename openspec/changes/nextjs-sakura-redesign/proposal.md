## Why

当前樱花平台的前端由纯 HTML 手写页面组成（`sakura_rush.html`、`custom_onepage.html`、`xiaohongshu_v3.html`），存在三大问题：
1. **设计感不足**：原生 CSS 难以系统化管理，组件无法复用，每次改版都从零开始
2. **社交传播断裂**：小红书/朋友圈分享图需要手工截图，无法批量生成，无法程序化控制尺寸和质量
3. **无法承接转化**：定制服务页面是静态 HTML，没有表单、没有数据绑定、无法追踪转化

迁移到 Next.js + shadcn/ui + Framer Motion 可一次解决：组件化设计系统 → 杂志级视觉 → 程序化图片导出 → 转化闭环。

**MVP 优先级**：🔴 P0 — 直接影响引流转化，是所有产品价位（¥19.9~¥1999）的展示入口和信任建设基础。

## What Changes

- **新建 Next.js 14 App Router 项目**（`web/` 目录），使用 Tailwind CSS + shadcn/ui + Framer Motion
- **重构核心页面**为 React 组件化页面：
  - 首页（数据权威展示 + 引流 CTA）
  - 樱花冲刺排行榜（TOP 10 景点 + 实时花期）
  - 定制行程服务页（高转化落地页）
  - 城市详情页（各城市景点卡片 + 地图）
- **社交卡片导出系统**：
  - Playwright 截图模式：高保真 HTML → PNG（单张/全页）
  - Satori + resvg-js 批量模式：JSX → SVG → PNG（小红书封面/朋友圈卡片）
- **移除现有纯 HTML 文件**的页面职责（`data/sakura/*.html` 仅保留为数据参考）
- **接入现有 JSON 数据**：直接读取 `data/sakura/` 下的景点、评分、花期数据

## Capabilities

### New Capabilities
- `nextjs-app-shell`: Next.js 14 App Router 项目骨架，含 Tailwind + shadcn/ui + Framer Motion 集成，全局布局、字体、主题色配置
- `sakura-landing-page`: 首页 — 数据权威展示（4大数据源、58城市、240+景点）+ 定制服务 CTA 引流入口
- `sakura-rush-page`: 樱花冲刺排行榜页 — TOP 景点卡片、城市切换、实时花期状态、置信度评分
- `custom-service-page`: 定制行程服务落地页 — 服务优势展示（8条路线/9维问卷/Tabelog评分/杂志PDF/旅居团队）、4步流程、微信 CTA
- `social-card-export`: 社交分享图导出系统 — Playwright 全页截图 + Satori 批量卡片生成（小红书 1080×1440 / 朋友圈 1080×1080）
- `design-system`: 樱花主题设计系统 — 色板（Sakura/Warm/Stone）、排版规范、动画预设、可复用卡片/Hero/CTA 组件

### Modified Capabilities
<!-- 无现有 spec 需要修改 -->

## Impact

- **新增依赖**：next 14、react 18、tailwindcss、@shadcn/ui、framer-motion、satori、@resvg/resvg-js、playwright
- **目录结构**：新建 `web/` 目录作为 Next.js 项目根目录，与现有 Python 后端并存
- **数据流**：Next.js 页面通过 `fs.readFileSync` 读取 `data/sakura/*.json`（SSG/SSR），不依赖 API
- **部署**：可独立部署到 Vercel / Netlify，或与 FastAPI 通过 reverse proxy 合并
- **现有文件**：`data/sakura/*.html` 不删除，但不再作为主要展示入口
