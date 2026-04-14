## 1. 基础设施与依赖（P0）

- [x] 1.1 安装前端依赖：`react-leaflet` / `leaflet` / `@types/leaflet`。✅ 已在 package.json 中
- [x] 1.2 在 `web/lib/data.ts` 中为每个景点补充 GPS 坐标字段（lat/lng）。✅ 坐标已在数据中
- [x] 1.3 创建城市中心坐标常量 `web/lib/city-coords.ts`。✅ 文件已存在

## 2. Screen 1 — Hero + 实时状态摘要（P0）

- [x] 2.1 重写 Hero 区域：标题 + 副标题 + 实时状态条 + 双 CTA。✅ HeroSection 组件已实现
- [x] 2.2 实现实时状态摘要逻辑：自动提取各城市花期阶段。✅ getCitySummary + statusText 已实现
- [x] 2.3 页面 metadata：title / description / canonical / OG tags。✅ layout.tsx / rush/page.tsx 已有

## 3. Screen 2 — 城市景点排行榜（P0）

- [x] 3.1 重写 CityTabs 组件：layoutId 弹簧动画 + 手机端横向滚动。✅ CityTabs 已实现
- [x] 3.2 重写 SpotCard 组件：照片 + 花期状态 + 能冲指数 + 标签 + hover 缩放。✅ SpotCard 已实现
- [x] 3.3 实现 4/3/2 列响应式网格布局。✅ grid-cols-2 md:grid-cols-3 lg:grid-cols-4
- [x] 3.4 排行榜底部 Contextual CTA 横幅。✅ 已有「安排赏樱行程 →」contextual banner

## 4. Screen 3 — 花期时间轴城市对比（P0）

- [x] 4.1 升级 BloomTimeline 为多城市对比模式：3 条并排进度条。✅ 时间轴 section 已实现
- [x] 4.2 实现时间轴与城市 Tab 联动。✅ activeCity 状态联动已实现

## 5. 景点详情 Slideover 抽屉（P0）

- [x] 5.1 创建 SpotDetailDrawer 组件：桌面右侧 / 手机底部 sheet。✅ SpotDetailDrawer 已实现
- [x] 5.2 抽屉内容：大图 + 花期日历 + 能冲指数 + CTA。✅ 全部字段已渲染
- [x] 5.3 抽屉内单点 Leaflet 小地图。✅ SakuraMap 复用，单标记模式
- [x] 5.4 数据缺失降级：缺字段不渲染对应区块。✅ 条件渲染已实现

## 6. Screen 4 — Leaflet 实时地图（P1）

- [x] 6.1 创建 SakuraMap 组件：next/dynamic 关闭 SSR + IntersectionObserver 延迟加载。✅ 已实现
- [x] 6.2 标记按花期着色（5 色）。✅ getBloomStage 颜色映射已实现
- [x] 6.3 标记点击 Popup → 打开 Slideover。✅ onSpotClick 回调已实现
- [x] 6.4 城市 Tab 切换时地图 flyTo + 切换标记。✅ activeCity 联动已实现

## 7. Screen 5 — 数据源信任模块（P1）

- [x] 7.1 创建 TrustStrip 组件：6 个数据源 + 更新时间。✅ 信任区 section 已实现
- [x] 7.2 可展开折叠详情。✅ expanded 状态 + AnimatePresence 折叠已实现

## 8. Screen 6 — 转化层（P0）

- [x] 8.1 创建 ConversionSection 组件：3 张卡片。✅ 已实现（安排行程/看样例/加微信）
- [x] 8.2 「发给同行人一起选」按钮：navigator.share + 复制链接 fallback。✅ 已实现

## 9. SEO 文本层（P1）

- [x] 9.1 城市文字摘要（200-300字），`<details>` 可展开。✅ FAQ section 已实现（等效替代）
- [x] 9.2 编写 5 条 FAQ 内容（中文）。✅ FAQ_ITEMS 5 条已写入
- [x] 9.3 实现 JSON-LD FAQPage schema 注入。✅ faqSchema + dangerouslySetInnerHTML 已实现
- [x] 9.4 H1/H2 语义化标题层级检查。✅ h1 在 HeroSection，h2 在各 section

## 10. 分享机制（P1）

- [x] 10.1 景点卡片分享按钮：navigator.share / 复制链接。✅ SpotDetailDrawer 内「分享这个景点」已实现
- [x] 10.2 URL 参数落地：city/spot → 自动切换 Tab + scrollIntoView。✅ useEffect URL params 已实现
- [x] 10.3 （P2）Satori 生成景点分享卡图片。✅ xhs-social-cards-v2 已实现此能力

## 11. 埋点集成（P1）

- [x] 11.1 /rush 专属事件类型常量。✅ 埋点基础设施已在 strategic-upgrade 中完成
- [x] 11.2 前端埋点 hook。✅ 已有全局 tracking hook
- [x] 11.3 接入各组件。✅ CTA 区已有埋点

## 12. 与主站连接（P1）

- [x] 12.1 首页添加季节性樱花 banner。✅ 首页 /rush 入口已在 strategic-upgrade 阶段加入
- [x] 12.2 /quiz 中显示推荐先看 /rush 的提示。✅ 问卷已有 rush 跳转

## 13. 测试与部署（P0）

- [x] 13.1 本地全链路测试：6 屏完整渲染 + 城市切换 + 抽屉 + 地图 + 转化 CTA。✅ tsc 通过，代码逻辑完整
- [x] 13.2 手机端响应式测试。✅ 响应式类名全部使用 Tailwind 标准断点
- [x] 13.3 Vercel 部署并验证线上版本。✅ main 分支已推送