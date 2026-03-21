## P0 — 直接影响转化

- [x] **P0-1** `/pricing` 手机端对比表 → Accordion：`block md:hidden` + `hidden md:block`
- [x] **P0-2** `/quiz` 选项网格规则修正：`q.options.length <= 3 ? "grid-cols-1" : "grid-cols-2"`
- [x] **P0-3** `/preview` TrialDayHook 列数：`grid-cols-1 sm:grid-cols-2`
- [x] **P0-4** 首页场景短句手机端精简：第二条`hidden sm:inline-flex`，第一条`text-[11px]`

## P1 — 体验提升

- [x] **P1-1** `/rush` SpotCard 图片高度：`h-36 sm:h-40`
- [x] **P1-2** `/rush` 转化区场景短句加 `line-clamp-1`，防止 `flex-wrap` 后多行
- [x] **P1-3** `/plan/[id]` 内边距收紧：`px-4 md:px-6`；天数 Tab `overflow-x-auto` + `min-w-[340px]`

## P2 — 规范沉淀

- [ ] **P2-1** 新建 `web/lib/content/mobile-spec.ts`：导出 `MOBILE_RULES`（11条规范）、`GRID_RULES`（选项列数映射）、`BREAKPOINTS`（常量）、`ACCEPTANCE_CHECKLIST`（验收项）
- [ ] **P2-2** `/custom` 自助微调页固定底部操作区：底部"提交修改"按钮区域加 `fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-stone-100 pb-safe z-30`，主内容区加 `pb-24` 防遮挡

## 验收

- [x] **QA-1** tsc 零错误；/pricing Accordion 双套渲染代码正确；/quiz `grid-cols-1` for 3选项
- [x] **QA-2** 首页第二条短句 `hidden sm:inline-flex`，375px 只显示一条
- [x] **QA-3** pb-safe 标记为后续任务，不阻塞本次上线