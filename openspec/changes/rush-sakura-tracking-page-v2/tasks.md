## 1. 基础设施与依赖（P0）

- [ ] 1.1 安装前端依赖：`react-leaflet` / `leaflet` / `@types/leaflet`。Owner: frontend。~30min
- [ ] 1.2 在 `web/lib/data.ts` 中为每个景点补充 GPS 坐标字段（lat/lng），从 weathernews 数据合并。Owner: frontend/data。~1h。依赖：weathernews 数据有坐标
- [ ] 1.3 创建城市中心坐标常量 `web/lib/city-coords.ts`（tokyo/kyoto/osaka/nagoya/hiroshima）。Owner: frontend。~20min

## 2. Screen 1 — Hero + 实时状态摘要（P0）

- [ ] 2.1 重写 Hero 区域：标题 + 副标题 + 实时状态条 + 双 CTA（查看城市 ↓ / 安排进行程 →）。品牌统一暖色石色系。Owner: frontend。~2h
- [ ] 2.2 实现实时状态摘要逻辑：从 RushScores 数据自动提取各城市花期阶段，生成一行文本（如「东京已满开 · 京都三分咲」）。Owner: frontend。~1h。依赖：2.1
- [ ] 2.3 页面 metadata：title / description / canonical / OG tags。Owner: frontend/seo。~30min

## 3. Screen 2 — 城市景点排行榜（P0）

- [ ] 3.1 重写 CityTabs 组件：layoutId 弹簧动画 + 手机端横向滚动。Owner: frontend。~1.5h
- [ ] 3.2 重写 SpotCard 组件：照片（带 fallback）+ 花期状态 + 能冲指数 + 夜樱/名所标签 + hover 缩放。Owner: frontend。~2h。依赖：1.2
- [ ] 3.3 实现 4/3/2 列响应式网格布局（lg:4 / md:3 / sm:2）。Owner: frontend。~30min
- [ ] 3.4 排行榜底部 Contextual CTA 横幅：「喜欢这些景点？帮你排进赏樱路线 →」。Owner: frontend。~30min

## 4. Screen 3 — 花期时间轴城市对比（P0）

- [ ] 4.1 升级 BloomTimeline 为多城市对比模式：3 条并排进度条（东京/京都/大阪）+ 当前日期指示线。Owner: frontend。~2h
- [ ] 4.2 实现时间轴与城市 Tab 联动：切换城市时高亮对应进度条。Owner: frontend。~1h。依赖：3.1, 4.1

## 5. 景点详情 Slideover 抽屉（P0）

- [ ] 5.1 创建 SpotDetailDrawer 组件：桌面右侧 400px slideover / 手机底部 85vh sheet。Owner: frontend。~2h
- [ ] 5.2 抽屉内容：大图 + 名称 + 花期日历条 + 能冲指数 + 树木数量 + 夜樱/祭典 + CTA。Owner: frontend。~2h。依赖：5.1
- [ ] 5.3 抽屉内单点 Leaflet 小地图（复用地图组件，单标记）。Owner: frontend。~1h。依赖：5.1, 6.1
- [ ] 5.4 数据缺失降级：缺字段不渲染对应区块。Owner: frontend。~30min。依赖：5.2

## 6. Screen 4 — Leaflet 实时地图（P1）

- [ ] 6.1 创建 SakuraMap 组件：`next/dynamic` 关闭 SSR + IntersectionObserver 延迟加载。Owner: frontend。~2h。依赖：1.1, 1.2, 1.3
- [ ] 6.2 标记按花期着色（绿/浅粉/粉/红/灰 5 色）。Owner: frontend。~1h。依赖：6.1
- [ ] 6.3 标记点击 Popup：名称 + 分数 + 状态 + 「查看详情」→ 打开 Slideover。Owner: frontend。~1h。依赖：6.1, 5.1
- [ ] 6.4 城市 Tab 切换时地图 flyTo + 切换标记。Owner: frontend。~1h。依赖：6.1, 3.1

## 7. Screen 5 — 数据源信任模块（P1）

- [ ] 7.1 创建 TrustStrip 组件：一行 6 个数据源名称 + 一句话 + 更新时间。Owner: frontend。~1h
- [ ] 7.2 可展开折叠详情：点击展开每个数据源的一句话描述。Owner: frontend。~1h。依赖：7.1

## 8. Screen 6 — 转化层（P0）

- [ ] 8.1 创建 ConversionSection 组件：3 张卡片（安排行程 / 看样例 / 加微信）。Owner: frontend。~1.5h
- [ ] 8.2 「发给同行人一起选」按钮：navigator.share + 复制链接 fallback。Owner: frontend。~1h。依赖：8.1

## 9. SEO 文本层（P1）

- [ ] 9.1 为每个城市编写文本摘要（200-300 字），以 `<details>` 可展开形式呈现。Owner: content/seo。~2h
- [ ] 9.2 编写 5 条 FAQ 内容（中文），确保事实准确。Owner: content。~1h
- [ ] 9.3 实现 JSON-LD FAQPage schema 注入。Owner: frontend/seo。~1h。依赖：9.2
- [ ] 9.4 H1/H2 语义化标题层级检查与修正。Owner: frontend/seo。~30min

## 10. 分享机制（P1）

- [ ] 10.1 景点卡片分享按钮：navigator.share 或复制 `/rush?city=X&spot=Y` 链接。Owner: frontend。~1h
- [ ] 10.2 URL 参数落地处理：从 URL 读取 city/spot → 自动切换 Tab → scrollIntoView + 高亮动画。Owner: frontend。~1.5h
- [ ] 10.3 （P2）Satori 生成景点分享卡图片。Owner: frontend。~3h。依赖：10.1

## 11. 埋点集成（P1）

- [ ] 11.1 定义 /rush 专属事件类型常量（12 个），追加到 `app/domains/tracking/events.py`。Owner: backend。~30min
- [ ] 11.2 前端埋点 hook `useRushTracking`：封装所有 /rush 事件发送逻辑。Owner: frontend。~2h
- [ ] 11.3 接入各组件：Hero、CityTabs、SpotCard、Drawer、Map、CTA、Share。Owner: frontend。~2h。依赖：11.2

## 12. 与主站连接（P1）

- [ ] 12.1 首页添加季节性樱花 banner：「🌸 樱花季来了，查看实时花期 →」。Owner: frontend。~1h
- [ ] 12.2 /quiz 问卷中选择樱花季出行时，显示推荐先看 /rush 的提示。Owner: frontend。~30min

## 13. 测试与部署（P0）

- [ ] 13.1 本地全链路测试：6 屏完整渲染 + 城市切换 + 抽屉 + 地图 + 转化 CTA。Owner: frontend。~2h
- [ ] 13.2 手机端响应式测试（Chrome DevTools 模拟 iPhone/Android）。Owner: frontend。~1h
- [ ] 13.3 Vercel 部署并验证线上版本。Owner: frontend。~30min。依赖：13.1
