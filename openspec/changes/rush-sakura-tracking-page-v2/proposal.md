## Why

/rush 樱花追踪页是当前产品在樱花季（3-4月）最核心的免费引流入口。旧版是纯 HTML 独立页面（Leaflet 地图 + 6 大数据源展示 + 城市排行），功能丰富但和主站完全割裂——品牌不统一、无转化路径、无埋点、无分享机制。

迁移到 Next.js 后，大量旧功能丢失（地图、数据源信任展示、景点详情面板、景点照片），现有版本只是一个精简的卡片列表页，既没有独立用户价值，也没有转化设计。

**Why now**：樱花季正在进行中（2026.3.21 当前三分咲），每天都有真实用户通过小红书/搜索引擎找花期信息。这是验证「免费工具 → 付费定制」转化漏斗的最佳窗口。

**在产品价位梯度中的作用**：/rush 本身不是付费产品，而是漏斗顶部的「免费工具型内容」，为所有价位层级（引流款 19.9~29.9 / 利润款 69~199 / 高客单定制）提供高意图流量入口。

**MVP 优先级**：P0 — 樱花季窗口期紧迫，需要在 1 周内上线完整版。

## What Changes

- **恢复旧版核心功能**：Leaflet 实时地图、景点详情面板、景点照片、花期日期、数据源信任模块
- **品牌统一**：从独立粉色风格改为主站暖色石色系
- **新增转化层**：每个触点都有通向 /quiz 的自然路径
- **新增分享机制**：景点分享卡生成、「发给同行人」功能
- **新增 SEO 文本层**：城市摘要、FAQ、结构化数据，让搜索引擎和 AI 摘要能抓取
- **新增埋点体系**：覆盖全链路（Hero → 城市切换 → 景点点击 → 地图互动 → CTA → 转化）
- **新增花期时间轴升级**：城市对比模式（东京/京都/大阪三线并排）
- **新增景点详情 slideover 抽屉**：替代旧版右侧固定面板，移动端更友好
- **性能优化**：地图延迟加载、图片 lazy load、ISR 热更新

## Capabilities

### New Capabilities
- `rush-page-structure`: /rush 页面整体信息架构与 6 屏结构设计（Hero、时间轴、排行榜、地图、信任、转化）
- `rush-spot-detail`: 景点详情 slideover 抽屉（花期日历、地图定位、祭典、树木数量、加入行程）
- `rush-leaflet-map`: Leaflet 实时地图模块（花期着色、标记交互、迷你卡片弹窗）
- `rush-conversion-layer`: /rush 页面转化设计（CTA 分层、分享卡生成、同行人分享、quiz 引导）
- `rush-seo-content`: SEO 文本层设计（城市摘要、FAQ schema、meta、H1/H2 层级、helpful content）
- `rush-tracking-events`: /rush 页面埋点与实验设计（全链路事件 + A/B 实验位）

### Modified Capabilities
- `scoring-engine`: 景点排行榜的「能冲指数」需要在 /rush 前端展示评分公式简要说明，增强用户信任

## Impact

- **前端**：`web/app/rush/` 目录完全重写，新增 5+ 组件（SpotDetailDrawer、LeafletMap、CityTimeline、TrustStrip、ConversionCTA）
- **数据层**：`web/lib/data.ts` 需要支持从 weathernews 合并完整字段（photo/trees/region/half/full/fall）— 已完成
- **后端**：无新 API，现有数据已足够；但需要新增 /rush 相关的 tracking events
- **依赖**：新增 `react-leaflet` / `leaflet` 前端依赖
- **SEO**：新增 JSON-LD 结构化数据、FAQ schema
- **部署**：Vercel ISR revalidate 已配置（30min），无额外部署变更
