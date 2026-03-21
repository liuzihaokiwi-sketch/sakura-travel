## 1. 项目骨架搭建

- [x] 1.1 在 `web/` 目录初始化 Next.js 14 项目（App Router + TypeScript）
- [x] 1.2 安装并配置 Tailwind CSS（含 sakura/warm 自定义色板 + display/sans/mono 字体）
- [x] 1.3 初始化 shadcn/ui（`npx shadcn-ui@latest init`），安装 Button, Card, Badge, Tabs 组件
- [x] 1.4 安装 Framer Motion，创建 `lib/animations.ts` 动画预设（fadeInUp/staggerContainer 等 6 个）
- [x] 1.5 创建 `lib/data.ts` 数据加载层（读取 `../data/sakura/*.json`，支持 DATA_DIR 环境变量）
- [x] 1.6 创建 `lib/constants.ts` 主题常量（WeChat ID、数据统计数字等）

## 2. 设计系统组件（依赖 1.1-1.4）

- [x] 2.1 创建 `components/shared/Navbar.tsx`（logo + 页面导航 + CTA 按钮，支持 export 模式隐藏）
- [x] 2.2 创建 `components/shared/FloatingCTA.tsx`（全局浮动按钮 + 脉冲动效，支持 export 模式隐藏）
- [x] 2.3 创建 `components/shared/GlassmorphCard.tsx`（毛玻璃卡片，light/dark 两种 variant）
- [x] 2.4 创建 `components/shared/SakuraParticles.tsx`（CSS 樱花飘落动效）
- [x] 2.5 创建 `app/layout.tsx` 全局布局（Google Fonts 加载 + Navbar + FloatingCTA + 全局样式）

## 3. 首页 Landing Page（依赖 2.1-2.5, 1.5）

- [x] 3.1 创建 `components/landing/HeroSection.tsx`（全屏樱花背景 + 暗色叠加 + 标题 + CTA 按钮 + Framer Motion 入场）
- [x] 3.2 创建 `components/landing/DataAuthority.tsx`（数据指标网格：4源/58城/240+点/每天3次/200万+报告/10年/置信度评分）
- [x] 3.3 创建 `components/landing/CTABanner.tsx`（warm 渐变横幅 + 免费体验 + 微信信息 + 信任指标）
- [x] 3.4 组装 `app/page.tsx` 首页（Hero + DataAuthority + CTABanner）

## 4. 樱花冲刺排行榜页（依赖 2.1-2.5, 1.5）

- [x] 4.1 创建 `components/rush/CityTabs.tsx`（5城市切换标签 + Framer Motion 切换动效）
- [x] 4.2 创建 `components/rush/SpotCard.tsx`（景点卡片：照片/花期状态/日期/树数/夜樱/名所百选/置信度）
- [x] 4.3 创建 `components/rush/BloomTimeline.tsx`（水平花期时间轴 + 当前周高亮指示器）
- [x] 4.4 创建 `components/rush/WeeklyRush.tsx`（"本周冲"摘要卡片 + 紧迫感文案）— 已集成到 RushClient
- [x] 4.5 组装 `app/rush/page.tsx`（WeeklyRush + CityTabs + SpotCard 网格 + BloomTimeline）

## 5. 定制服务落地页（依赖 2.1-2.5, 1.5-1.6）

- [x] 5.1 创建 `components/custom/AdvantageGrid.tsx`（12项服务优势卡片网格，每张含：图标/标题/真实数据/AI痛点对比）
- [x] 5.2 创建 `components/custom/ProcessSteps.tsx`（4步流程：加微信→告知→免费攻略→满意付费）
- [x] 5.3 创建 `components/custom/WeChatCTA.tsx`（暗色背景微信模块 + 渐变文字 + 一键复制 + 信任指标）
- [x] 5.4 组装 `app/custom/page.tsx`（h-screen 三列布局：Hero暗色列 + AdvantageGrid + ProcessSteps+WeChatCTA）

## 6. 社交卡片模板 — Satori（依赖 1.5）

- [x] 6.1 下载 Noto Sans SC 字体文件到 `public/fonts/`，创建 `lib/satori.ts` 字体加载工具
- [x] 6.2 安装 satori + @resvg/resvg-js，创建 `lib/satori.ts` 渲染工具函数
- [x] 6.3 创建 `components/social/XhsCover.tsx`（小红书封面 1080×1440，Satori 兼容 Flexbox 布局）
- [x] 6.4 创建 `components/social/XhsContent.tsx`（小红书内容页 1080×1440，景点排名列表）
- [x] 6.5 创建 `components/social/MomentCard.tsx`（朋友圈卡片 1080×1080，单景点高亮）

## 7. 导出脚本（依赖 6.1-6.5, 5.4, 4.5）

- [x] 7.1 安装 playwright，创建 `scripts/export-playwright.ts`（CLI 截图脚本：--url/--width/--height/--output）
- [x] 7.2 创建 `scripts/export-satori.ts`（CLI 批量生成脚本：--template/--output，支持 xhs-cover/xhs-content/moment 模板）
- [x] 7.3 在 `package.json` 添加 npm scripts：`export:screenshot`、`export:cards`
- [x] 7.4 创建 `output/` 目录 + `.gitignore`，端到端测试导出流程

## 8. 集成验证

- [x] 8.1 全页面视觉走查（首页/排行榜/定制/导出），确保杂志级设计感
- [x] 8.2 验证 `?export=true` 模式下 Navbar/FloatingCTA 正确隐藏
- [x] 8.3 Playwright 导出 1080×1440 小红书图 + 1080×1080 朋友圈图，检查质量
- [x] 8.4 Satori 批量导出 5 城市封面卡片，检查中文渲染和布局
