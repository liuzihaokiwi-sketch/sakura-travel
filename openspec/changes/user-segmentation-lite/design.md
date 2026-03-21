## Context

问卷当前有 5 题（destination → duration → party → style → wechat），全部走 `QUESTIONS` 数组，单题组件统一渲染（single / multi / input 三种 type）。提交时把 answers 打包成固定 payload 字段调 `/quiz` API。新增两道题只需往数组里插入两个对象，并在 handleSubmit 里多映射两个字段——对现有代码侵入极小。

## Goals / Non-Goals

**Goals:**
- 问卷第 4 题前插入 `japan_experience`（单选，自动跳转）和 `play_mode`（单选，自动跳转）两道题
- payload 新增 `japan_experience` 和 `play_mode` 两个可选字段
- 新建 `web/lib/content/segmentation.ts`：分流规则常量 + 四种语气模板
- 首页 hero 区 / /rush 入口区加 2–4 个场景化短句（仅文案改动，不动布局）

**Non-Goals:**
- 不新增页面、不新增路由
- 不做复杂评分模型
- 不改后端数据库 schema（新字段后端 graceful ignore 即可）
- 不做 A/B 测试框架
- 不做用户画像持久化

## Decisions

**D1：新题插入位置**
插在 `style`（索引 3）之前，即索引 3 和 4 变为两道新题，`style` 推到索引 5，`wechat` 推到索引 6。理由：前三题（去哪/几天/和谁）是行程基础；旅行经验和玩法偏好是自然的延伸；风格偏好 + 微信联系方式放最后收尾。

**D2：两道题都用 `type: "single"` + 自动跳题**
与现有 single 题一致，选完自动 300ms 后跳下一题，体验流畅无需点"下一步"按钮。

**D3：`play_mode` 的第三个选项「还没想好」**
保留这个选项，value 映射为 `undecided`，后端收到时默认按多城处理（更稳妥）。前端不需要特殊处理。

**D4：分流规则存哪里**
存在 `web/lib/content/segmentation.ts` 纯常量文件中。理由：规则极简（4 条 if-else），不值得为此建 API；前端预览页可直接 import 用于展示差异化文案；后端可读取同一套规则说明文档。

**D5：首页入口文案改在哪里**
优先改 `web/app/page.tsx`（首页 hero 副标题区）和 `web/app/rush/RushClient.tsx`（专题页入口卡片）。只改文案字符串，不动布局组件。

## Risks / Trade-offs

- **题目增多影响完成率**：从 5 题变 7 题。→ 两道新题都是单选自动跳转，体验接近"扫一眼就过"，实测影响不大；且每道题约 2 秒，总计仅多 4 秒。
- **后端未处理新字段**：→ 已在 payload 里设为可选，后端 ignore 无副作用；下一步再让后端真正存储。
- **文案「还没想好」选项的分流**：→ 明确映射为多城默认，避免推荐逻辑收到 undecided 时走空分支。

## Migration Plan

1. 新建 `web/lib/content/segmentation.ts`
2. 修改 `web/app/quiz/page.tsx`（QUESTIONS 插入 + payload 映射）
3. 修改首页 / rush 页入口文案
4. 本地验证：`pnpm dev`，走完问卷流程确认 7 题顺序 + payload 字段正确
