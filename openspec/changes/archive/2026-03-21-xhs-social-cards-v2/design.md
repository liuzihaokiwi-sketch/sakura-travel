## Context

现有 Satori 卡片生成系统（`web/scripts/export-satori.ts` + `web/lib/satori.ts`）已可运行，支持 `React.createElement` → SVG → PNG 渲染链路。但 3 个旧模板视觉风格、品牌文案和 CTA 均已过时。

**当前技术栈**:
- `satori` — React → SVG（支持 flexbox 子集，不支持 CSS Grid/transforms）
- `@resvg/resvg-js` — SVG → PNG
- `NotoSansSC-Regular.ttf` 作为中文字体
- 数据源: `weathernews_all_spots.json` 已包含 photo URL、trees、lightup、meisyo100 等字段

**约束**:
- Satori 不支持 `<img>` 标签直接加载远程 URL；需要先 `fetch` → `ArrayBuffer` → base64 data URI
- Satori 不支持 CSS `background-image`；需要用 `<img>` 元素 + position absolute 模拟
- 字体仅有 Regular 400，粗体需要用 fontSize 和 letterSpacing 模拟

## Goals / Non-Goals

**Goals:**
- G1: 5 个模板全部重做，视觉与 `/rush` 页面一致（warm 暖色系 + 石灰底 + 品牌 orange）
- G2: 单景点种草卡 (`xhs-spot`) 使用 weathernews 实景照片作为封面背景
- G3: CTA 统一引导小红书关注 + 私信咨询
- G4: `export-satori.ts` 脚本一键批量生成 5 城 × 5 模板 = 25+ PNG
- G5: API route `/api/share/card` 也更新支持新模板（动态按需生成）

**Non-Goals:**
- NG1: 不做视频生成（仅静态 PNG）
- NG2: 不做自动发布到小红书 API（手动上传）
- NG3: 不增加新字体包（保持 NotoSansSC-Regular.ttf）
- NG4: 不做二维码生成（小红书规则不允许）

## Decisions

### D1: 图片加载策略 — 预下载 + 本地缓存

**选择**: 在批量生成脚本中，先 `fetch` 远程 photo URL → 存为 `/tmp/photo-cache/{id}.jpg`，然后转 base64 data URI 传给 Satori。

**替代方案**:
- A: 每次渲染时实时 fetch → 慢且不可靠（Weathernews CDN 有时超时）
- B: 全部预下载到 repo → 太多文件、repo 太大

**理由**: 临时缓存平衡了速度和存储大小。

### D2: 配色系统 — 复用 Tailwind warm 色板

| Token | Value | 用途 |
|-------|-------|------|
| bg-primary | `#fefaf6` (warm-50) | 卡片底色 |
| bg-dark | `#1c1917` (stone-900) | 深色头部 |
| text-primary | `#1c1917` | 标题 |
| text-secondary | `#78716c` (stone-500) | 副标题 |
| accent | `#f7931e` (warm-500) | 分数、CTA |
| bloom-full | `#ec4899` (pink-500) | 满开 |
| bloom-half | `#22c55e` (green-500) | 五分咲 |

### D3: 模板结构

每个模板函数签名统一:
```typescript
function createXxxElement(data: TemplateData): React.ReactElement
```

`TemplateData` 包含:
```typescript
interface TemplateData {
  city: string;
  cityName: string;
  spots: Spot[];
  photoBuffers: Record<string, string>; // name → base64 data URI
  updatedAt: string;
}
```

### D4: CTA 文案方案

| 位置 | 文案 |
|------|------|
| 底部主 CTA | `🌸 关注我，获取每日花期更新` |
| 底部副 CTA | `私信"樱花"获取完整景点推荐 ↗` |
| 品牌标识 | `SAKURA RUSH 2026 · 6大数据源融合` |
| 数据来源 | `JMA · JMC · Weathernews · 地方官方 · 历史 · AI引擎` |

### D5: 脚本 CLI 接口

```bash
# 生成全部
npx tsx scripts/export-satori.ts --all --output output/xhs/

# 按模板
npx tsx scripts/export-satori.ts --template xhs-cover --output output/xhs/

# 按城市
npx tsx scripts/export-satori.ts --template xhs-spot --city tokyo --output output/xhs/

# 指定景点
npx tsx scripts/export-satori.ts --template xhs-spot --city tokyo --spot "上野恩賜公園" --output output/xhs/
```

## Risks / Trade-offs

- **[Risk] Weathernews 图片 CDN 不可用** → Mitigation: 缓存到本地 + 无图 fallback 用渐变色占位
- **[Risk] Satori 渲染复杂布局有限制** → Mitigation: 保持 flexbox-only 布局，避免 CSS Grid、transform
- **[Risk] NotoSansSC-Regular 无 Bold** → Mitigation: 用大 fontSize + 粗 letterSpacing 模拟层次感；后续可考虑加 Bold 字体文件
- **[Trade-off] 实景照片质量参差** → 选 score 前三的景点（通常照片质量更好）
