# Rush 全功能恢复 — 任务分组

> 旧版 HTML: `archive/legacy-html/sakura_rush.html` (1184行)
> 目标: 100% 恢复旧版 5 个城市 240+ 景点的全部功能，融入现有 Next.js 站点

## 架构决策

- 樱花是网站的**独立子功能**，不占导航 C 位
- 定制页面用现有的 `/quiz` `/pricing`
- 手机优先 UI（另一个 AI 负责响应式细节）
- 数据源: `weathernews_all_spots.json`（240景点）为主，`sakura_rush_scores.json` 为辅

## 导航结合方案

```
主站导航: 首页(/) | 方案与价格(/pricing) | [免费看行程 CTA]
                                 ↑ C 位给主业务
樱花入口:
  - 首页底部季节性 Banner → /rush
  - Navbar 右侧小标签 "🌸 樱花季" (季节性，非常驻)
  - /rush 页面内部 CTA → /quiz (引流回主业务)
```

---

## 🔴 高难度任务 (我做)

### H1. 数据层重构 — `web/lib/rush-data.ts`
- 新建独立的 rush 数据加载器
- 直接读 `weathernews_all_spots.json` 作为主源（5城 240+ 景点）
- 移植旧版 `calcScore()` 评分算法
- 合并 `sakura_rush_scores.json` 的 AI 评分（有则优先）
- 导出: `getRushData()` → 完整 5 城数据 + 排名 + 地标
- 导出: `CITIES` 配置（5城 + center/zoom/emoji/status）
- 导出: `LANDMARKS` 配置（车站、名胜）

### H2. 地图组件 — `web/components/rush/SakuraMap.tsx`
- 用 `react-leaflet` 重写旧版三栏地图布局
- 左栏: 城市 TOP20 排行列表 (带花期小进度条)
- 中间: Leaflet 地图 + 圆形标记 + 永久标签 (TOP6)
- 右栏: 景点详情面板 (照片/评分/花期日期/标签/描述)
- 地标 marker (车站/名胜 emoji 图标)
- 点击景点 → 高亮排行 + 显示详情
- 手机端: 左栏隐藏 → 底部抽屉，右栏 → 底部 sheet

### H3. 时间轴页面 — `web/components/rush/Timeline.tsx`
- 按区域分组的卡片列表 (旧版 tl-cards)
- 每张卡: 照片/名称/评分/满开日/倒计时/标签/花期进度条/中文描述
- 城市切换 tab
- 花期进度条 (3/10~4/25 区间，today 标记线)
- 点击卡片 → 跳转地图页对应景点

### H4. 导航整合
- 修改 `Navbar.tsx`: Logo 改为主站品牌（不是 Sakura Rush）
- 樱花入口降级为季节性小标签
- `/rush` 页面内子导航: 首页/地图/时间轴 (Tab 切换)
- `/rush` 内 CTA 引流回 `/quiz`

---

## 🟡 中低难度任务 (另一个 AI 做)

### M1. Rush 首页 Section — `web/components/rush/RushHome.tsx`
- 迁移旧版 home-page 的内容:
  - Hero (数据平台统计: 240+景点, 6大数据源, 3次/天, ±2天)
  - 本周 HOT 推荐卡片网格 (每城 TOP3)
  - 城市概览卡 (emoji/状态/TOP3照片/统计)
  - 数据来源信任条
- 从 H1 的 `getRushData()` 取数据

### M2. 定制服务 Section — `web/components/rush/RushCTA.tsx`
- 迁移旧版 custom-page 的内容:
  - 痛点卡片网格 (行程规划烦恼 → 我们的解决方案)
  - 流程步骤 (加微信→告知日期→免费1天→满意付费)
  - 微信号复制按钮
  - 信任标签 (不满意不收费/满意再付费/旅居团队)
- CTA 按钮链接到 `/quiz`

### M3. 花期进度条组件 — `web/components/rush/BloomBar.tsx`
- 独立的花期进度条组件 (复用在地图/时间轴/首页)
- 参数: half/full/fall 日期，today 标记
- 颜色: 粉色(开花中) / 深粉(满开) / 紫色(飘落)

### M4. 响应式适配
- 确保 H2 地图在手机端切换为底部抽屉模式
- 确保 H3 时间轴卡片在手机端单列堆叠
- 确保 M1 首页网格在手机端自适应
- **这块另一个 AI 已经在做，只需确保新组件用 Tailwind 响应式前缀**

### M5. 数据文件同步
- 确保 `web/data/sakura/weathernews_all_spots.json` 是最新的
- 添加 LANDMARKS 数据文件 (从旧版 HTML 提取)
- 添加 CITIES 配置数据 (从旧版 HTML 提取)

---

## 依赖关系

```
H1 (数据层) ← 无依赖，最先做
    ↓
H2 (地图) ← 依赖 H1 + M3
H3 (时间轴) ← 依赖 H1 + M3
H4 (导航) ← 无依赖，可并行
    
M1 (首页) ← 依赖 H1
M2 (CTA) ← 无依赖
M3 (进度条) ← 无依赖，可并行
M5 (数据) ← 无依赖，最先做
```

## 可并行方案

```
我(高):   H1 → H2 → H3 → H4
另一个AI: M5 → M3 → M1 → M2 → M4
```
