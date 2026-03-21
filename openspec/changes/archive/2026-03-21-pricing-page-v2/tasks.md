## 文案常量层（基础，其他任务依赖）

- [x] **A1** 创建 `web/lib/content/pricing.ts` — 所有价格页文案的集中常量文件
  - 标准版价格卡文案（标题/价格/副标题/权益列表/浮动说明/CTA）
  - 深度版价格卡文案（同上 + 比价系统 block 文案）
  - 页面小字文案（最终转化感版本）
  - PDF 说明文案（价格页/成功页/交付页，三个版本）
  - FAQ 8 条问答数组（`{ q: string; a: string }[]`）

## 核心组件实现

- [x] **B1** 新建 `web/components/pricing/SavingsClaim.tsx` — 比价系统高亮 Block 组件
  - 背景：`amber-50`，左侧竖线 `amber-400`
  - 展示：💰 图标 + 标题 + 三行文案 + 括号免责小字
  - 严格按 `savings-claim/spec.md` 中的文案规范

- [x] **B2** 新建/重构 `web/components/pricing/PricingCard.tsx` — 价格卡组件
  - Props：`{ tier: 'standard' | 'pro'; isRecommended?: boolean }`
  - 从 `web/lib/content/pricing.ts` 读取文案
  - 深度版卡内插入 `<SavingsClaim />` 组件（在权益列表最上方）
  - 移动端：`w-full`；桌面端：并排 `flex-row`
  - 深度版有角标 `★ 最受欢迎`
  - CTA：标准版次要按钮（描边），深度版主要按钮（`rose-600` 填充）

- [x] **B3** 新建 `web/components/pricing/PricingFAQ.tsx` — FAQ 手风琴组件
  - 使用原生 `<details>/<summary>`，无新依赖
  - 从 `web/lib/content/pricing.ts` 读取 FAQ 数组
  - 展开/收起有 CSS transition 动画（`max-height` 过渡）
  - 默认全部收起

## 价格页集成

- [x] **C1** 修改 `web/app/pricing/PricingClient.tsx` — 集成新组件
  - 替换现有占位价格卡为 `<PricingCard tier="standard" />` + `<PricingCard tier="pro" isRecommended />`
  - 价格卡下方加页面小字（从常量读取）
  - 页面小字下方加 PDF 说明一行（从常量读取）
  - 价格卡 + 小字区域之后加 `<PricingFAQ />`
  - 移动端布局：纵向堆叠（standard 在上，pro 在下）
  - 桌面端布局：`md:flex-row`，两卡并排

## 其他页面 PDF 说明

- [x] **D1** 修改 `web/app/submitted/page.tsx` — 加入 PDF 交付完整说明
  - 位置：提交确认信息下方
  - 内容：从 `web/lib/content/pricing.ts` 读取成功页版本 PDF 说明
  - 样式：`bg-stone-50` 信息框，带 📄 图标

- [x] **D2** 修改 `web/app/plan/[id]/page.tsx` — 加入交付页 PDF 说明
  - 位置：PDF 下载/查看按钮下方
  - 内容：操作指引式说明（从常量读取交付页版本）
  - 样式：折叠收起式，默认收起，点击展开

## 质量检查

- [x] **E1** 移动端视觉验收 ✅ PricingCard w-full + 堆叠布局，深度版在下有角标
- [x] **E2** 桌面端视觉验收 ✅ md:grid-cols-3 并排，深度版 ring-2 突出
- [x] **E3** 文案检查 ✅ pricing.ts 顶部禁用语表已注释，全文无"每天 ¥XX"等禁用表达
- [x] **E4** FAQ SEO 检查 ✅ `<details>/<summary>` 原生 HTML，内容在 DOM 中可被抓取