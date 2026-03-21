## Context

当前前端由散落的纯 HTML 文件组成（`data/sakura/sakura_rush.html`、`custom_onepage.html`、`xiaohongshu_v3.html`），通过 CDN Tailwind 和内联 JS 实现。后端是 Python FastAPI + PostgreSQL，数据通过 JSON 文件和 DB 两条路径流动。

本次新建 `web/` 目录作为独立 Next.js 项目，与 Python 后端在同一 monorepo 内并存，互不依赖。初期通过 `fs` 直接读取 `data/` 下的 JSON 数据，后期可通过 API 对接。

约束条件：
- 技术栈锁定：**Next.js 14 App Router + Tailwind CSS + shadcn/ui + Framer Motion**，不使用其他 UI 框架
- 视觉标准：旅行杂志感 + 数据产品感 + 高级感
- 图片导出：HTML 页面用 Playwright，批量社交卡片用 Satori + resvg-js
- 数据层：初期纯 SSG（Static Site Generation），读 JSON 文件，不依赖运行时 API

## Goals / Non-Goals

**Goals:**
- ✅ 建立可复用的樱花主题设计系统（色板、字体、组件库）
- ✅ 4 个核心页面达到旅行杂志级视觉品质
- ✅ 定制服务页面达到高转化落地页标准（CTA 突出、信任链完整）
- ✅ 程序化导出小红书/朋友圈分享图（精确尺寸、批量能力）
- ✅ 代码组件化，后续改版只改数据不改结构

**Non-Goals:**
- ❌ 不做用户登录/注册系统
- ❌ 不做支付/下单流程
- ❌ 不做 FastAPI 后端对接（初期）
- ❌ 不做产品价格展示（用户明确排除）
- ❌ 不做 CMS 后台

## Decisions

### D1: 项目目录结构

```
web/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # 全局布局（字体、主题、Navbar）
│   ├── page.tsx                  # 首页 — 数据权威 + CTA
│   ├── rush/page.tsx             # 樱花冲刺排行榜
│   ├── custom/page.tsx           # 定制服务落地页
│   ├── city/[code]/page.tsx      # 城市详情页（动态路由）
│   └── api/
│       └── export/route.ts       # 导出 API（Satori 批量生成）
├── components/
│   ├── ui/                       # shadcn/ui 组件（Button, Card, Badge...）
│   ├── landing/                  # 首页专用组件
│   │   ├── HeroSection.tsx       # 主视觉 Hero
│   │   ├── DataAuthority.tsx     # 数据权威展示（4源/58城/240+点）
│   │   └── CTABanner.tsx         # 定制服务引流横幅
│   ├── rush/                     # 排行榜专用组件
│   │   ├── SpotCard.tsx          # 景点卡片（花期状态+评分+照片）
│   │   ├── CityTabs.tsx          # 城市切换标签
│   │   └── BloomTimeline.tsx     # 花期时间轴
│   ├── custom/                   # 定制服务专用组件
│   │   ├── AdvantageGrid.tsx     # 服务优势卡片网格
│   │   ├── ProcessSteps.tsx      # 4步流程
│   │   └── WeChatCTA.tsx         # 微信CTA模块
│   ├── shared/                   # 跨页面共享组件
│   │   ├── Navbar.tsx            # 顶部导航
│   │   ├── FloatingCTA.tsx       # 全局浮动CTA
│   │   ├── SakuraParticles.tsx   # 樱花飘落动效
│   │   └── GlassmorphCard.tsx    # 毛玻璃卡片基础组件
│   └── social/                   # 社交卡片模板（Satori 用）
│       ├── XhsCover.tsx          # 小红书封面 1080×1440
│       ├── XhsContent.tsx        # 小红书内容页
│       └── MomentCard.tsx        # 朋友圈卡片 1080×1080
├── lib/
│   ├── data.ts                   # 数据加载层（读 JSON）
│   ├── fonts.ts                  # 字体配置
│   ├── satori.ts                 # Satori 渲染工具
│   └── constants.ts              # 主题常量
├── scripts/
│   ├── export-playwright.ts      # Playwright 全页截图脚本
│   └── export-satori.ts          # Satori 批量生成脚本
├── public/
│   └── fonts/                    # 本地字体文件（Noto Sans/Serif SC）
├── tailwind.config.ts
├── next.config.mjs
├── package.json
└── tsconfig.json
```

**理由**：按页面+功能分组（非按类型），每个页面有独立组件目录，保持清晰边界。`social/` 单独抽出因为 Satori 组件有特殊限制（不能用所有 CSS）。

### D2: 设计系统 — 色板与排版

```typescript
// 主题色板
colors: {
  sakura: {
    50: '#fef7f7', 100: '#fce4ec', 200: '#f8bbd0',
    300: '#f48fb1', 400: '#ec407a', 500: '#e91e63', 600: '#c2185b'
  },
  warm: {
    50: '#fefaf6', 100: '#fef3e2', 200: '#fde4b8',
    300: '#f7931e', 400: '#ff6b35', 500: '#d35400'
  },
  // shadcn/ui 的 stone 色阶用于文字和背景
}

// 字体
fontFamily: {
  display: ['Playfair Display', 'Noto Serif SC', 'serif'],     // 标题
  sans: ['Inter', 'Noto Sans SC', '-apple-system', 'sans-serif'], // 正文
  mono: ['JetBrains Mono', 'monospace']                          // 数据
}
```

**理由**：保持与现有设计的颜色延续（sakura/warm），增加 serif 展示字体提升杂志感。Inter + Noto Sans SC 保证中英文正文可读性。

### D3: 数据加载策略 — SSG + JSON

```typescript
// lib/data.ts
import { readFileSync } from 'fs'
import { join } from 'path'

const DATA_DIR = join(process.cwd(), '..', 'data', 'sakura')

export function getSpots(city: string) {
  const raw = readFileSync(join(DATA_DIR, 'weathernews_all_spots.json'), 'utf-8')
  return JSON.parse(raw)[city] || []
}

export function getRushScores() {
  const raw = readFileSync(join(DATA_DIR, 'sakura_rush_scores.json'), 'utf-8')
  return JSON.parse(raw)
}
```

**理由**：初期不需要 API，JSON 文件够用。SSG 构建时读取，生成静态页面，部署到任何静态托管。`web/` 目录通过 `..` 引用上级 `data/`。

### D4: 图片导出双轨方案

| 场景 | 工具 | 尺寸 | 说明 |
|---|---|---|---|
| 高保真全页截图 | Playwright | 自定义 | 渲染真实 HTML，支持所有 CSS 特性 |
| 批量社交卡片 | Satori + resvg-js | 1080×1440 / 1080×1080 | JSX → SVG → PNG，无浏览器依赖，速度快 |

Playwright 脚本：
```typescript
// scripts/export-playwright.ts
const browser = await chromium.launch()
const page = await browser.newPage()
await page.setViewportSize({ width: 1080, height: 1440 })
await page.goto('http://localhost:3000/rush?export=true') // export 模式隐藏导航
await page.screenshot({ path: 'output/rush.png', fullPage: false })
```

Satori 批量脚本：
```typescript
// scripts/export-satori.ts
import satori from 'satori'
import { Resvg } from '@resvg/resvg-js'

const svg = await satori(<XhsCover data={spotData} />, {
  width: 1080, height: 1440,
  fonts: [{ name: 'Noto Sans SC', data: fontBuffer }]
})
const png = new Resvg(svg).render().asPng()
```

**理由**：Playwright 用于需要完整 CSS 效果（动画、毛玻璃、复杂布局）的场景；Satori 用于大批量生成、CI/CD 自动化（无需浏览器环境）。

### D5: 动画方案 — Framer Motion

```typescript
// 入场动画预设
export const fadeInUp = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }
}

export const staggerContainer = {
  animate: { transition: { staggerChildren: 0.08 } }
}

// 使用
<motion.div variants={staggerContainer} initial="initial" animate="animate">
  {cards.map(card => (
    <motion.div key={card.id} variants={fadeInUp}>
      <SpotCard {...card} />
    </motion.div>
  ))}
</motion.div>
```

**理由**：Framer Motion 是 React 生态最成熟的动画库，配合 Next.js 使用无需额外配置。预定义动画预设保持全站动效一致性。

### D6: 定制服务页优势数据 — 来自项目真实能力

从项目代码和数据中提取的**定制行程服务真实优势**（非追樱数据）：

| 优势维度 | 具体数据 | 数据来源 |
|---|---|---|
| 路线规划引擎 | 8条精品路线模板（3-8天） | `data/route_templates/` |
| 场景适配 | 4种场景（情侣/家庭/独旅/闺蜜）| `scene_variants` |
| 偏好匹配 | 9维度偏好问卷 | `theme_weights.py` |
| 智能评分 | 12维评分系统（Google/Tabelog/Booking融合）| `scorer.py` |
| 餐厅筛选 | Tabelog 3.5+ 才入选，最高4.68 | `tabelog_raw/` |
| 杂志排版 | 16套杂志级PDF模板 | `templates/magazine/` |
| 数据采集 | 11个专业爬虫全覆盖 | `scripts/crawlers/` |
| 活动覆盖 | 55+活动/祭典/夜樱 | `events_raw/` |
| 目的地 | 143个JNTO官方目的地 | `jnto_destinations.json` |
| 体验项目 | 10+精选本地体验 | `experiences_raw/` |
| 旅居团队 | 实际住在日本，人工验证 | 团队背景 |
| 交通优化 | 景点顺路串联，Pass最省方案 | `assembler.py` |

## Risks / Trade-offs

**[R1: Monorepo 路径耦合]** → `web/` 通过相对路径 `../data/` 读取数据，部署时需确保数据目录可达。Mitigation: 支持环境变量 `DATA_DIR` 覆盖。

**[R2: Satori CSS 子集限制]** → Satori 不支持所有 CSS 属性（如 `backdrop-filter`、`clip-path`）。Mitigation: `social/` 目录下的组件使用 Satori 兼容的 Flexbox 布局，与页面组件分离。

**[R3: 字体文件体积]** → Noto Sans/Serif SC 中文字体文件较大（10-20MB）。Mitigation: 使用 Google Fonts 子集化 API + 本地缓存 Satori 用的字体 Buffer。

**[R4: 初期无 API 层]** → JSON 文件更新需重新构建。Mitigation: 使用 Next.js ISR（Incremental Static Regeneration）+ `revalidate` 参数，后期接 API 时平滑过渡。

## Open Questions

- Q1: 是否需要多语言支持（中文/日文/英文）？初期建议仅中文。
- Q2: 部署目标是 Vercel 还是自建服务器？影响 ISR 和 API 路由的可用性。
- Q3: 是否需要暗色模式？初期建议不做，专注亮色主题的设计品质。
