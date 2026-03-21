# buchong.md 口径对齐 — 剩余待实现任务

> 文档已全部同步完成。以下是 buchong.md 中要求的、代码层面尚未实现的功能。

## 已完成的文档对齐 ✅

- [x] `01-product-scope.md` 免费版口径改为"1 天样片 + 高光钩子"
- [x] `00-overview.md` 商业模式同步
- [x] `04-generation-workflow.md` 补充报告 3 层结构 + 生成分工 + 完整硬/软规则
- [x] `05-delivery-workflow.md` 免费预览描述 + 自助微调 → 正式修改
- [x] `06-ops-and-customer-service.md` FAQ 口径同步
- [x] `07-content-engine.md` 小红书 4 支柱 + CTA 原则 + 回访系统

## 待实现的代码任务

### 1. Quiz 补充"预算偏向"步骤（🟢 中低级 AI）
- [x] 1.1 在 `web/app/quiz/page.tsx` 增加一步：预算更想花在哪里？~30min
  - 选项：住得更好 · 吃得更好 · 体验更特别 · 更均衡 · 更看重性价比
  - 字段名 `budget_focus`，提交到后端
- [x] 1.2 后端 TripProfile 模型增加 `budget_focus` 字段 ~15min
- [x] 1.3 assembler 在构建 user_weights 时考虑 budget_focus 权重 ~30min

### 2. 免费预览页改造为"1 天样片 + 高光钩子"（🟡 中高级 AI）
- [ ] 2.1 `web/app/plan/[id]/page.tsx` preview 模式：Day 1 完整展示，其余天数只显示标题 + 2-3 个亮点关键词 ~2h
  - 当前实现：Day 1 完整 + Day 2-3 摘要 → 改为 Day 1 完整 + 其余天数高光钩子
  - 高光钩子：每天一个卡片，显示"Day X · [主题]"+ 3 个亮点 icon
  - 底部统一 CTA：「解锁完整 X 天方案」
- [ ] 2.2 后端 preview 接口适配：返回非预览天的 summary 字段（标题+亮点标签）~1h

### 3. 报告 3 层结构模板实现（🔴 高级 AI）
- [x] 3.1 创建总纲模板 `templates/magazine/overview.html.j2` ✅
  - 包含：设计思路、总览表、关键预订提醒、出发准备
- [x] 3.2 每日固定骨架已有 `day_card.html.j2`（已包含时间轴+交通+实体卡片+文案） ✅
- [x] 3.3 条件页模板已有（hotel_report / restaurant_report / photo_guide），渲染管线已接入条件触发 ✅
- [x] 3.4 渲染引擎增加条件页触发逻辑 + _build_overview_context ✅
  - has_hotel_change / has_highlight_restaurant / has_photo_spots 标记
  - 自动在每天之后按条件插入对应报告页

### 4. 静态块模板化（🟢 中低级 AI）
- [x] 4.1 创建静态知识块 `templates/static_blocks/` ~1.5h
  - `pre_departure.html`（出发前准备）
  - `safety.html`（安全事项）
  - `esim_payment.html`（eSIM/支付/交通卡）
  - `useful_apps.html`（常用 App）
  - `emergency.html`（医疗与紧急联系）
- [x] 4.2 渲染引擎改为引用静态块而非每次生成 ~30min

### 5. PDF 水印功能（🟢 中低级 AI）
- [x] 5.1 WeasyPrint 渲染时注入水印层 ~1h
  - 内容：用户昵称/手机尾号/订单号尾号 + "仅供本人行程使用"
  - 样式：对角线半透明文字，不影响阅读
- [x] 5.2 验证水印在不同页面长度下均正常显示 ~15min

### 6. 后台 4 维产品模型（🟡 中高级 AI）
- [ ] 6.1 数据库增加 `theme_family` 枚举 ~15min
  - classic_first / couple_aesthetic / food_shopping / onsen_healing / culture_deep / family_easy
- [ ] 6.2 数据库增加 `budget_focus` 枚举 ~10min
  - better_stay / better_food / better_experience / balanced / best_value
- [ ] 6.3 TripProfile 与 ItineraryPlan 关联 theme_family + budget_focus ~30min
- [ ] 6.4 assembler 根据 4 维模型选择路线模板变体 ~1h

### 7. 自助微调功能（🔴 高级 AI，需前后端协作）
- [x] 7.1 后端 swap API 已存在 `app/api/self_adjustment.py`（GET alternatives + POST swap + GET swap-log） ✅
  - 注意：当前使用 raw SQL 引用 plan_slots/entities/plan_swap_logs 表，需后续迁移到 ORM
- [ ] 7.2 前端：plan 页面增加"替换"按钮 ~2h（前端任务，后续实现）
- [ ] 7.3 后端：正式修改计数器独立于自助微调 ~30min

### 8. 价格页同步（🟢 中低级 AI）
- [x] 8.1 `web/app/pricing/page.tsx` 同步为 buchong 口径 ~30min
  - 标准版描述：去掉"2 次行程精调"，改为"1 次正式修改（自助微调不限）"
  - 增加"7 天参考价"标注
  - 增加"其他天数小幅浮动"说明
