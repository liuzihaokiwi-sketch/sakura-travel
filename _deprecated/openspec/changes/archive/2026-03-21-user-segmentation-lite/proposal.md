## Why

当前问卷收集了目的地、天数、同行人、风格偏好，但**完全不知道用户是第几次去日本、以及偏向多城还是一地**。这两个维度直接影响推荐权重（首次去 → 经典路线优先；熟客 → 本地化 / 避重复；多城 → 跨城效率优先；一地深玩 → 单城层次感优先）。不做分流，所有人收到的是同一套行程逻辑，高频熟客会明显感觉"跟上次没什么不同"。MVP 优先级：高（成本极低，收益直接）。

## What Changes

- **问卷新增两道题**：`japan_experience`（去过几次）+ `play_style`（多城 or 一地）插入在 `style` 题之前，位置自然、不打断流程
- **首页 / /rush 页轻入口文案**：四个场景各一句短文案（首次去、熟客、多城、一地），放在现有入口卡片或 hero 区附近，零新增页面
- **提交 payload 新增两个字段**：`japan_experience` + `play_mode`，后端据此存入 trip_request，后续生成逻辑可读取
- **推荐分流规则**：4 条简单 if-else 规则，写入 `web/lib/content/segmentation.ts` 常量，供前端预览页和后端调用
- **交付文案语气模板**：4 种语气示例常量，供文案生成时注入 prompt 前缀

## Capabilities

### New Capabilities
- `user-segmentation`: 用户分层维度定义（japan_experience × play_mode 四象限）及轻量分流规则常量

### Modified Capabilities
- `questionnaire-system`: 问卷新增两道题（题目文案、选项、插入位置、payload 映射）
- `conversion-funnel`: 首页 / 专题页轻入口文案（四个场景 hook 短句）

## Impact

- `web/app/quiz/page.tsx` — QUESTIONS 数组插入两道新题；payload 新增两字段
- `web/lib/content/segmentation.ts` — 新建，分流规则 + 语气模板常量
- `web/app/page.tsx` 或 `web/app/rush/RushClient.tsx` — 入口文案更新（轻量，不改布局）
- 后端 `/quiz` route 接受新字段（宽松，已有字段不变，新字段可选）
- 无新页面、无新路由、无新 API endpoint
