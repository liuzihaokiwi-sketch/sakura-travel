## Why

当前价格页存在两个关键问题：①深度版（¥888）的核心差异化价值（深度比价系统，帮用户节省 20-30% 旅行开销）在前端完全未体现，导致用户无法感知 ¥640 溢价的理由；②价格展示逻辑不清晰，"7 天参考价 + 其他天数浮动"的口径、PDF 水印说明、FAQ 均缺失，造成用户困惑和信任流失。本次变更是价格页的一次完整产品化升级，目标是让用户在页面上就能理解"买什么、值多少、怎么交付"，减少咨询摩擦，提升从价格页到付款的转化率。MVP 优先级：P0。

## What Changes

- **新增** 深度版核心差异化模块：「深度比价系统」说明（帮用户节省旅行开销 20-30%）
- **新增** 两张价格卡的完整前端文案（标准版 ¥248 / 深度版 ¥888，均以"7 天参考价"展示）
- **新增** 价格浮动说明口径："其他天数小幅浮动，制作前与你确认"
- **新增** 页面小字（最终版）：最有转化感版本
- **新增** PDF 交付策略：PDF 为正式交付主形态，H5 为补充，PDF 附轻水印
- **新增** 水印设计规范：页脚淡灰色小字，含订单号 + 仅供本人使用
- **新增** 三处 PDF 说明文案：购买页小字 / 提交成功页 / 交付页
- **新增** FAQ 口径：8 条，覆盖价格逻辑、天数浮动、PDF 水印、预览机制
- **修改** `web/app/pricing/page.tsx`：实装上述所有文案与展示逻辑
- **修改** `web/app/plan/[id]/page.tsx`：加入 PDF 交付说明模块
- **修改** `web/app/order/success/page.tsx`：加入提交成功页说明

## Capabilities

### New Capabilities

- `pricing-copy`: 价格卡文案、小字说明、价格浮动口径的内容规范与前端实现
- `savings-claim`: 深度版「节省 20-30% 旅行开销」比价系统的价值主张展示模块
- `pdf-delivery-ux`: PDF 交付策略、水印设计规范、三处交付说明文案的前端实现
- `pricing-faq`: 8 条 FAQ 口径的内容规范与前端展示组件

### Modified Capabilities

- `pricing-page`: 价格卡结构调整（加入"7 天参考价"标注、比价系统亮点、浮动说明）
- `delivery-page`: 交付页新增 PDF 说明模块

## Impact

- `web/app/pricing/page.tsx` — 主要修改文件
- `web/components/pricing/PricingCard.tsx` — 价格卡组件（新建或重构）
- `web/components/pricing/PricingFAQ.tsx` — FAQ 组件（新建）
- `web/components/pricing/SavingsClaim.tsx` — 节省金额展示组件（新建）
- `web/app/plan/[id]/page.tsx` — 交付页新增 PDF 说明
- `web/app/order/success/page.tsx` — 成功页新增说明
- `web/lib/constants.ts` — 新增/更新 FAQ 内容常量、水印文案常量
- 无后端 API 变动，无数据库变动，无 breaking change
