# 页面数据协议与实现顺序

## 1. 目标
把“页型设计”真正落成前端可执行的协议，而不是停留在文案目录。

---

## 2. 推荐数据层级

### Level 1：report_payload_vNext
完整攻略的数据真相源。
包含：
- trip_meta
- page_plan[]
- chapters[]
- days[]
- major_activities[]
- hotels[]
- restaurants[]
- photo_themes[]
- risks[]
- prep_modules[]

### Level 2：page_plan[]
由 planner 决定“有哪些页、按什么顺序出现”。

每条 page_plan 至少包含：
- page_id
- page_type
- topic_family
- object_refs[]
- chapter_id（可空）
- day_index（可空）
- size_mode（full / dual / compact）
- priority
- trigger_reason
- merge_rule

### Level 3：page_view_model
真正给前端页组件消费的数据。
一页一个 view model，不让组件自己去拼业务。

---

## 3. 推荐 page_type 枚举

- cover
- toc
- preference_fulfillment
- major_activity_overview
- route_overview
- hotel_strategy
- booking_window
- departure_prep
- live_notice
- chapter_opener
- day_execution
- major_activity_detail
- hotel_detail
- restaurant_detail
- photo_theme_detail
- transit_detail
- supplemental_spots
- fallback_plan

---

## 4. 推荐组件层

### A. Page Shell
负责纸张尺寸、内边距、页眉页脚、页码、安全区。

### B. Page Template
一类页型一个模板组件，例如：
- CoverPage
- TocPage
- DayExecutionPage
- HotelDetailPage

### C. Page Blocks
块级组件，跨页复用：
- HeroHeader
- KeyReasonList
- Timeline
- StatStrip
- ChoiceCard
- ReservationCard
- RiskCard
- MiniEntityCard
- QuoteLikeDecisionCard

### D. Data Adapters
把后端的结构转成页面可消费的 view model。

---

## 5. 哪些一起实现

### 第一组：必须一起做
1. page_type enum
2. page_plan generator
3. page_view_model adapters
4. Page Shell
5. 目录页页码联动
6. PDF 页码稳定策略

原因：
没有这组，后面每一种页型都会失控。

### 第二组：可以并行做
- 封面页
- 目录页
- 偏好兑现页
- 主要活动总表页
- 大路线总览页
- 酒店策略总览页

### 第三组：第二批并行做
- 每日执行页
- 主要活动页
- 酒店详情页
- 餐厅详情页
- 拍摄主题页

### 第四组：后置实现
- 交通页
- 顺路补充页
- 调整 / Plan B 页
- 动态注意事项页

---

## 6. 哪些必须按顺序实现

### 顺序 1：先定 page_plan，再写页面组件
不能先写很多漂亮组件，再回头决定页面顺序。

### 顺序 2：先做固定前置页，再做高价值专题页
因为前置页决定整本攻略的信息框架。

### 顺序 3：先做每日执行页，再做补充页
执行页是骨架，补充页是增值。

### 顺序 4：先做 PDF 稳定导出，再做复杂视觉增强
否则开发后期很容易因为打印问题返工。

---

## 7. 与当前技术栈的具体分工

### Next.js App Router
- Page planner 和 data adapter 尽量放服务端
- 页面渲染默认走 Server Components
- 少量交互块再下沉到 Client Components

### TypeScript
- page_type
- page_plan schema
- page_view_model schema
- block props 都应严格类型化

### Tailwind CSS
- 统一 spacing、grid、排版节奏
- 建议建立 print tokens 与 screen tokens

### shadcn/ui
适合做：
- Card
- Badge
- Separator
- Callout 样式块
不适合直接当整页版式系统

### Satori
优先用于：
- 封面 Hero
- 章节页 Hero
- 主要活动分享图
不建议用于整本正文

### Playwright
- 负责最终 PDF 导出
- 基于 print 视图导出
- 验证分页、裁切、页码

---

## 8. 后端 / 前端接口建议

### 后端输出
`GET /api/report/:id/pages`

返回：
- meta
- page_plan[]
- page_models{ page_id: view_model }

### 前端消费
- 先拿 page_plan 渲染顺序
- 再根据 page_type 选择模板
- 模板只消费自己的 view model

---

## 9. 数据缺口清单（当前页型落地最缺的）
为了让最终页型真正成立，数据层至少还需要补这些字段：

### 已有但需更稳定映射
- major activity 的 why_selected
- hotel 的 served_days / route_role
- restaurant 的 detour_cost / meal_slot
- photo theme 的 best_time_window
- day 的 must_keep / cut_order

### 现阶段明显缺少或不稳定
- preference_fulfillment_items[]
- skipped_options_with_reasons[]
- chapter_goal
- emotional_goal_by_day
- page-level hero assets
- fallback_corridor
- live risk 绑定到 page 的能力
- per-page highlight sentence

---

## 10. 阶段性模板哪些值得存

### 值得存数据库 / 配置层
1. page_type schema
2. page block layout presets
3. page_plan generation rules
4. chapter opener presets
5. fixed block copy skeletons
6. hotel / restaurant / photo detail reason templates

### 不建议存成死模板
1. 最终整页 HTML
2. 具体用户的完整成文页
3. 带实时数据的整页快照
4. 每次 trip 独有的自由文案

建议：
- 存“页型骨架”和“块级模板”
- 不存“整个用户页面成品”

原因：
后者对复用帮助有限，还容易随着视觉调整整体报废。

---

## 11. 是否存储阶段性产物

### 建议存的阶段性产物
- normalized_profile
- selected_city_circle
- selected_major_activities
- hotel_base_strategy
- day_frames
- page_plan
- page_view_model_cache（可选，带版本）

### 不建议长期存的
- 完整最终 HTML 长字符串
- 导出前临时拼装的中间 DOM
- 大量不可复用的 copywriter 草稿

### 最优做法
数据库存“可复用的决策层结果”，
对象存储存“最终导出产物”，
不要把“临时渲染层脏数据”塞进数据库。
