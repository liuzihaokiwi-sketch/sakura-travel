## 1. 常量层（其余任务依赖）

- [x] 1.1 新建 `web/lib/content/segmentation.ts` — 导出：`JapanExperience` / `PlayMode` 类型、`SEGMENTATION_RULES`（4条分流规则）、`DELIVERY_TONE`（4种语气模板）、`ENTRY_COPY`（首页/专题页四个场景入口短文案）

## 2. 问卷新增两道题

- [x] 2.1 修改 `web/app/quiz/page.tsx` — 在 QUESTIONS 数组索引 3 处插入 `japan_experience` 题（3 个选项，type: single）和 `play_mode` 题（3 个选项，type: single）
- [x] 2.2 修改 `web/app/quiz/page.tsx` — `handleSubmit` 里 payload 新增 `japan_experience` 和 `play_mode` 字段（从 answers 读取，未选时传 null）

## 3. 首页 / 专题页入口文案

- [x] 3.1 查看 `web/app/page.tsx` 首页 hero 区，将副标题或辅助文案改为场景化短句（从 `ENTRY_COPY` 常量读取），覆盖首次去 + 熟客两个场景
- [x] 3.2 查看 `web/app/rush/RushClient.tsx`，在现有入口卡片或 CTA 区域附近加一行场景化提示文案（从 `ENTRY_COPY` 常量读取）

## 4. 验收

- [x] 4.1 走完问卷全流程（7 道题），确认题目顺序正确，新题选完自动跳转，最终 payload 包含两个新字段
- [x] 4.2 访问首页和 /rush 页，确认场景化入口文案可见，不破坏现有布局