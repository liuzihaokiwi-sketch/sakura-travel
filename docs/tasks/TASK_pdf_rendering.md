# 任务：PDF 手账本渲染系统

> 角色：主程序员 + 设计迭代（你）
> 依赖：用户提供参考图后开始设计迭代

---

## 背景

现有渲染用 WeasyPrint，但直接拼字符串生成 HTML，无法维护也无法迭代设计。
目标：Jinja2 模板引擎 + WeasyPrint，18种页面类型，支持 PDF 导出。

设计规范见：
- `docs/page_system/02_intro_pages.md`
- `docs/page_system/04_data_contracts.md`
- `docs/page_system/05_design_checklist.md`

---

## 第1步：基础骨架（必须先做，其他所有页面依赖这步）

- [ ] 接入 Jinja2 模板引擎，替换现有字符串拼接
- [ ] 实现 `page_type` 枚举（18种，见下方列表）
- [ ] 实现 `page_plan` 生成器（决定有哪些页、按什么顺序）
- [ ] 实现 `page_view_model` 适配器（structured_plan.json → 每页数据）
- [ ] 实现 `Page Shell`（纸张尺寸/边距/页眉页脚/页码/安全区）
- [ ] PDF 页码稳定策略（目录页码与实际页码联动）
- [ ] 图片资源管理（本地目录 + 占位图兜底，加载失败不崩溃）

---

## 第2步：MVP 页面（11种，先出这批才能出第一本手账本）

### 第1组：固定前置页（先做）
- [ ] `cover` 封面页
- [ ] `toc` 目录页
- [ ] `preference_fulfillment` 偏好兑现页
- [ ] `major_activity_overview` 主要活动总表
- [ ] `route_overview` 大路线总览
- [ ] `hotel_strategy` 酒店策略总览

### 第2组：高价值专题页（并行做）
- [ ] `day_execution` 每日执行页（最核心，每天一页）
- [ ] `major_activity_detail` 主要活动详情
- [ ] `hotel_detail` 酒店详情
- [ ] `restaurant_detail` 餐厅详情
- [ ] `photo_theme_detail` 拍摄主题页

---

## 第3步：执行支撑页（第二批）

- [ ] `booking_window` 关键预订窗口
- [ ] `departure_prep` 出发前指引
- [ ] `transit_detail` 交通页
- [ ] `supplemental_spots` 顺路补充
- [ ] `food_guide` 城市美食图鉴
- [ ] `weather_tips` 天气穿衣页
- [ ] `practical_info` 实用信息页（紧急联系/退税/Wi-Fi）
- [ ] `budget_tracker` 预算追踪页（空白表格）
- [ ] `shops_guide` 店铺推荐页

---

## 第4步：后置页（最后做）

- [ ] `chapter_opener` 章节开场页
- [ ] `fallback_plan` Plan B 调整页
- [ ] `live_notice` 动态注意事项页

---

## 设计迭代流程

1. 用户提供参考图（手账本/日系旅行杂志风格）
2. AI 分析参考图提取配色/排版/字体风格
3. AI 生成 HTML/CSS 模板初稿（优先：封面、每日执行页、餐厅详情）
4. 用户看效果反馈调整
5. 迭代满意后主程序员接入 Jinja2 动态数据

**设计规范（已定）：**
- 配色：暖白底 `#FAFAF8`、深灰正文 `#2C2C2C`、朱红强调 `#C0392B`
- 字体：标题 Noto Serif SC，正文 Noto Sans SC
- 原则：一页一个主焦点，视觉3层，留白是价值感的一部分

---

## 数据缺口（渲染时需要但现在没有）

- `preference_fulfillment_items[]` — 偏好兑现页需要
- `emotional_goal_by_day` — 每日执行页情绪目标
- `page-level hero assets` — 每页配图
- `per-page highlight sentence` — 每页一句话亮点
- `chapter_goal` — 章节开场页需要

---

## 开始之前

如果你对方案有不同意见或更好的做法，在回复开头用 3-5 行简要说明，然后直接开始实现你认为最好的版本。不需要等确认。
