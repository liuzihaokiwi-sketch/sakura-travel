# Layer 3：报告与渲染层补充设计方案 v1

> 目标：把 Layer 2 的决策结果，稳定地变成「有价值感、好阅读、可导出、可复用」的最终攻略。
> 
> 本文不是重写当前方案，而是在现有 Layer 3 现状之上，补全真正落地时最容易缺的架构、顺序、边界和演进策略。

---

## 0. 先给结论

当前 Layer 3 的方向没有问题，但还少一个真正的中枢：

**现在已有：**
- `report_schema.py`
- `report_generator.py` v1/v2
- `copywriter.py`
- `fragment_pipeline.py`
- `renderer.py` v1/v2
- `templates/itinerary_v2.html`
- Next.js 阅读页
- Playwright 导出

**真正还缺：**
- `chapter_system`
- `page_plan`
- `page_type registry`
- `page_view_model`
- `page blueprint / slot contract`
- `decision explanation layer`
- `render adapter split`
- `page-level validation`

一句话：

**Layer 3 不能再是“生成 payload → 一张大 HTML 模板流出来 → print 成 PDF”，而要升级成“生成 payload → 章节规划 → 分页规划 → 页视图模型 → 多端渲染”。**

---

## 1. 对当前现状的判断

### 1.1 现状能继续复用的部分

可以继续保留：
- `report_generator.py` 作为 Layer 2 → Layer 3 的入口
- `copywriter.py` 继续负责少量高价值解释
- `fragment_pipeline.py` 继续做片段复用
- `renderer.py` 保留为 adapter 层
- `itinerary_v2.html` 先继续作为兼容模板
- Playwright 继续作为 PDF 输出层

这些都不需要推翻。

### 1.2 当前最大的结构问题

当前问题不是“模板不够好看”，而是**渲染语义还停留在长 section 流式文档**。

现有 PDF 结构已经暴露了这个问题：
- 当前报告还是封面 + overview + 连续 day-card 的长流结构
- 通过 `break-inside: avoid` 和 `window.print()` 来尽量规避打印断裂
- `report-block / hl-card / planb-grid / prep-grid` 仍然是附着在同一个长页面流上的局部块，而不是独立页型
- 日页同时承担了执行、亮点、Plan B、准备提示等多种阅读任务

这说明：

**目前的分页主要靠 CSS 和打印行为兜底，而不是上游信息结构先规划好页面。**

---

## 2. Layer 3 的正确职责边界

Layer 3 不负责重新做决策。

Layer 3 负责三件事：

### 2.1 结构化表达
把 Layer 2 已经得到的结果转成：
- 总纲
- 章节
- 页面
- 槽位
- 每页重点
- 每页情绪目标

### 2.2 解释与定制感显化
把“系统为什么这么选”转成用户能看懂、且会觉得被理解的表达：
- 你的偏好如何被兑现
- 为什么是这个酒店/餐厅/拍摄页
- 为什么没放某些高热度选项
- 每一天的情绪目标和节奏目标

### 2.3 多端输出
同一套页面语义，输出到：
- Web 阅读页
- PDF 打印版
- OG / 分享图

也就是：

**Layer 3 的核心不是 HTML，而是 page semantics。HTML/React/Jinja 只是表现层。**

---

## 3. 我建议新增的主链

在现有 `generate_report_v2` 和 `renderer_v2` 之间，补出 4 个明确阶段：

```text
Layer 2 output
  -> ReportPayloadV2
  -> ChapterPlanner
  -> PagePlanner
  -> PageViewModelBuilder
  -> RenderAdapters
  -> Web / PDF / OG
```

### 3.1 ChapterPlanner
输入：`ReportPayloadV2`

输出：`chapter_plan[]`

负责：
- 先把整份报告切成章节，而不是直接切页
- 为 7 天 / 14 天自动控制展开粒度
- 决定哪些内容按天展开，哪些按章节合并

### 3.2 PagePlanner
输入：`chapter_plan[]`

输出：`page_plan[]`

负责：
- 决定一共有哪些页
- 每页是什么页型
- 哪些对象占整页，哪些半页，哪些双卡页
- 页序、页间过渡、章节 opener、专项页触发

### 3.3 PageViewModelBuilder
输入：`page_plan[] + report payload + fragment outputs`

输出：`page_view_models[]`

负责：
- 把抽象页面变成组件能直接渲染的数据结构
- 不再让模板自己到处判断 if/else

### 3.4 RenderAdapters
输入：`page_view_models[]`

输出：
- HTML（Web）
- HTML（Print）
- PDF
- OG images

负责：
- 让一个页面语义可以有不同媒介的输出
- 但不改变页面本身的数据意义

---

## 4. 最该补的 8 个对象

## 4.1 `chapter_plan`

建议新增：

```ts
ChapterPlan {
  chapter_id: string
  chapter_type: 'frontmatter' | 'circle' | 'days' | 'special' | 'appendix'
  title: string
  subtitle?: string
  goal?: string
  mood?: string
  covered_days: number[]
  primary_circle_id?: string
  trigger_reason?: string
  importance: 'high' | 'medium' | 'low'
}
```

用途：
- 7 天和 14 天的展开差异，不应该由模板硬写死，而应该由 chapter planner 控制
- 让“章节 opener”成为真正的数据对象，而不是视觉装饰

---

## 4.2 `page_plan`

这是 Layer 3 最核心的新对象。

```ts
PagePlan {
  page_id: string
  page_order: number
  chapter_id: string
  page_type: string
  page_size: 'full' | 'half' | 'dual-half'
  topic_family: string
  object_refs: PageObjectRef[]
  required_slots: string[]
  optional_slots: string[]
  trigger_reason?: string
  merge_policy?: string
  overflow_policy?: string
  priority: number
}
```

用途：
- 把“目录、酒店页、餐厅页、拍摄页、每日执行页”变成明确的页面单位
- 避免 renderer 再靠流式自然换页

---

## 4.3 `page_type registry`

建议不是散落很多模板，而是一张统一注册表：

```ts
PageTypeDefinition {
  page_type: string
  topic_family: string
  default_size: 'full' | 'half' | 'dual-half'
  required_slots: string[]
  optional_slots: string[]
  visual_priority: string[]
  mergeable_with: string[]
  print_constraints: string[]
  web_constraints: string[]
}
```

例如：
- `cover_page`
- `toc_page`
- `preference_fulfillment_page`
- `chapter_opener_page`
- `daily_execution_page`
- `hotel_detail_page`
- `restaurant_detail_page`
- `photo_theme_page`
- `conditional_special_page`
- `risk_watch_page`

用途：
- 让“每种页型是什么”成为可维护的产品协议
- 不是把规则埋进模板和 prompt 里

---

## 4.4 `page_view_model`

这是模板真正消费的对象。

```ts
PageViewModel {
  page_id: string
  page_type: string
  page_size: string
  heading: HeadingVM
  hero?: HeroVM
  highlight?: HighlightVM
  sections: SectionVM[]
  footer?: FooterVM
  print_meta?: PrintMetaVM
}
```

用途：
- renderer 不再拼业务逻辑
- 前端组件和 Jinja / React 都能共用一套渲染协议

---

## 4.5 `decision_explanations`

现在虽然有 AI prompt，但还缺“解释层对象”。

建议新增：

```ts
DecisionExplanation {
  object_type: 'circle' | 'major' | 'hotel' | 'day' | 'restaurant' | 'photo'
  object_id: string
  why_selected: string
  why_here?: string
  what_to_expect?: string
  tradeoff_note?: string
  skipped_alternatives?: string[]
}
```

用途：
- 让“为什么这样安排”不只是生成时顺嘴写出来，而是可复用、可上页、可验收

---

## 4.6 `visual_anchor_items`

后面要做设计感和情绪价值，不能只靠排版，需要页面资产层。

```ts
VisualAnchorItem {
  object_type: string
  object_id: string
  image_candidates: string[]
  hero_priority: number
  orientation: 'landscape' | 'portrait' | 'square'
  crop_hint?: string
  caption_hint?: string
  emotion_tags: string[]
}
```

用途：
- 封面、章节页、酒店页、拍摄页、主要活动页都需要稳定选图
- 避免前端临时抓图

---

## 4.7 `chapter_summaries` / `emotional_goal`

这一类字段必须补进 payload：
- `preference_fulfillment_items[]`
- `skipped_options_with_reasons[]`
- `chapter_summaries[]`
- `emotional_goal`（按 day）
- `selection_evidence[]`
- `risk_watch_items[]`

用途：
- 不是为了堆字，是为了让“这份攻略懂我”的感觉可被稳定渲染

---

## 4.8 `page_blueprints`

长期建议做一层 blueprint，而不是把页型定义和实际渲染完全绑死。

```ts
PageBlueprint {
  blueprint_id: string
  page_type: string
  slot_order: string[]
  visual_pattern: string
  supported_sizes: string[]
  print_variant?: string
  web_variant?: string
  version: string
}
```

用途：
- 后面你们改设计风格时，不用重写 page type 和 payload
- 只替换 blueprint / 组件组合即可

---

## 5. 现有技术栈下的推荐实现

## 5.1 Web：React / Next.js 做主表达层

建议：

**中期把 Web 端作为主表达层。**

原因：
- 你们已经有 Next.js App Router 和前端阅读页
- App Router 天然支持 layouts、server/client components 和按 route segment 组织页面
- Layer 3 最终需要的是“页面系统”，不是单一 HTML 字符串模板

建议目录：

```text
web/
  app/
    plan/[planId]/page.tsx
    plan/[planId]/print/page.tsx
  components/report/
    page-types/
      CoverPage.tsx
      TocPage.tsx
      PreferencePage.tsx
      ChapterOpenerPage.tsx
      DailyExecutionPage.tsx
      HotelDetailPage.tsx
      RestaurantDetailPage.tsx
      PhotoThemePage.tsx
      RiskWatchPage.tsx
    slots/
    primitives/
  lib/report/
    page-plan.ts
    view-model.ts
    registry.ts
```

---

## 5.2 Jinja2：短期兼容层，不建议继续做主战场

当前 `renderer.py + itinerary_v2.html` 可以继续保留，但建议角色调整为：

- v1/v2 历史链路兼容
- 快速 fallback
- 内部导出应急

不建议再在 Jinja2 大模板里继续膨胀 page semantics。

原因：
- 你们已经要做复杂页型、章节、双端渲染
- 这些能力在 React 组件体系里会比在一个巨大的 Jinja 模板中更稳

推荐路线：

**短期：** Jinja 和 React 共用 `page_view_model`

**中期：** React 成为主渲染层，Jinja 只保留 fallback

---

## 5.3 Playwright：继续作为 PDF 层，不替代页面结构规划

Playwright 继续保留，职责不变：
- 加载 print route
- 使用 print CSS
- 输出 PDF

但要明确：

**Playwright 负责导出，不负责决定怎么分页。**

因此需要：
- `page-plan` 先定义页边界
- print CSS 再用 `@page`、`break-before`、`break-after`、`break-inside` 去尊重这些边界

不要再让 PDF 主要依赖“浏览器自己分”。

---

## 5.4 Satori：只做封面 / 章节 / 分享图，不做正文

这个边界必须写死。

Satori / ImageResponse 适合：
- 封面 hero card
- 章节 opener 背景图
- 社交分享图

不适合：
- 酒店详情页正文
- 每日执行页
- 长文档布局

原因：
- 只支持 flexbox 和部分 CSS
- 不适合复杂长文档排版
- 更适合小而稳定的视觉资产

---

## 6. 对你现在 Layer 3 的 10 条补充建议

## 6.1 不要让 `report_generator_v2` 直接面向 HTML

它应该只负责产出：
- `ReportPayloadV2`
- `chapter_plan`
- `page_plan`
- `decision explanations`

不要直接决定模板块怎么拼。

---

## 6.2 条件页触发要前移到 `PagePlanner`

现在 `_trigger_conditional` 还在 `report_generator.py` 里。

建议：
- 保留规则定义
- 但让真正的“是否占页”“插到第几页”“插在哪个章节”都在 `PagePlanner` 完成

否则条件页仍然只是文案插块，而不是页面对象。

---

## 6.3 `copywriter.py` 只写高价值句子，不填结构

建议明确边界：
- AI 写：why selected / highlights / what to expect / tradeoff
- 规则写：预约提示 / 营业风险 / 到达提示 / 通用准备 / 固定说明

不要让 AI 决定：
- 这一页有没有
- 这一页放几个块
- 哪些内容合并

---

## 6.4 片段复用不应该只给 report_generator 用

`fragment_pipeline.py` 未来要支持到页级复用：
- route fragment
- decision fragment
- dining fragment
- logistics fragment
- photo fragment
- appendix fragment

也就是：

**fragment 的落点不只是日文案，也可以是 page slot。**

---

## 6.5 `chapter system` 必须先于 `page system`

因为：
- 7 天和 14 天的不同，本质是展开粒度不同
- 展开粒度应该由 chapter 决定，而不是 page type 自己瞎判断

建议顺序：

```text
payload -> chapter plan -> page plan -> page vm -> render
```

不是直接：

```text
payload -> page plan
```

---

## 6.6 每页必须有 `primary promise`

这是 Layer 3 的产品原则，不是 UI 原则。

每一页只承担一个主承诺：
- 决策页：告诉你为什么这样玩
- 每日执行页：告诉你今天怎么跑
- 酒店页：告诉你为什么住这家
- 餐厅页：告诉你为什么吃这家
- 拍摄页：告诉你为什么值得拍、什么时候拍
- 风险页：告诉你什么要提前看

这条会直接降低信息拥挤感。

---

## 6.7 每页都要有“设计感位置”字段

建议页型定义中显式约定：
- `hero_zone`
- `highlight_zone`
- `evidence_zone`
- `utility_zone`

因为后面你要的“情绪价值”和“被认真设计过”的感觉，很大程度来自：
- 视觉锚点先看见
- 重点结论马上被抓住
- 证据和理由随后出现
- 执行信息在下面兜底

这不是美术稿，而是 page semantics。

---

## 6.8 页面校验要升级到页级，不只是结构校验

新增建议：
- `PAGE_001`：每页必须有明确 page_type
- `PAGE_002`：required slots 不得缺失
- `PAGE_003`：主承诺不得和 topic_family 冲突
- `PAGE_004`：同类对象占页规则不得冲突
- `PAGE_005`：整页对象不得被压成半页
- `PAGE_006`：print variant 不得出现 overflow

---

## 6.9 不要太早做 page_blueprint 数据库存储

`page_plan` 值得落库。

但 `page_blueprint` 我建议先放代码注册表，不要第一期就进数据库。

原因：
- 这阶段会频繁改
- 数据库存它，反而增加版本迁移成本
- blueprint 更像前端/渲染协议，不像业务事实

建议：
- Phase 1：代码注册表
- Phase 2：稳定后再考虑 DB

---

## 6.10 Layer 3 也要有 fallback，但粒度要细

建议：
- 无 page_plan → fallback 到 chapter-less long report
- 有 page_plan 但缺某 page_type → fallback 到 generic_detail_page
- React print route 失败 → fallback 到 Jinja print
- 某些 conditional page 数据不全 → 只跳过该页，不回退整份报告

也就是：

**Layer 3 的 fallback 应该页级降级，不是整份回滚。**

---

## 7. 我建议的实现顺序

## Phase A：把 Layer 3 先从“长模板”升级成“页面系统”

1. 扩 `ReportPayloadV2`
2. 新建 `chapter_plan`
3. 新建 `page_plan`
4. 新建 `page_type registry`
5. 新建 `page_view_model`
6. 让 `renderer_v2` 先吃 page_view_model

这一阶段不改前端主战场，也能显著改善结构。

---

## Phase B：把 Web 与 PDF 共用 page semantics

1. Next.js 新建 `/plan/[id]` 和 `/plan/[id]/print`
2. React 组件实现前置页、章节页、每日执行页、酒店页、餐厅页、拍摄页
3. Playwright 改为打 `print` route
4. Jinja2 保留 fallback

这一阶段结束后：
- Web / PDF 的语义层统一
- Jinja 退到兼容层

---

## Phase C：补“设计感”和“定制感”

1. preference_fulfillment 页
2. skipped_options 页
3. chapter opener
4. visual anchors
5. hero image / Satori share card
6. page-level highlight zones

这阶段不是为了多做页，而是为了让用户感觉到：
- 这份攻略懂我
- 这份攻略有主次
- 这份攻略是认真设计的

---

## Phase D：补持久化和复用

1. page_plan 落库
2. generation_decisions 与 page_plan 关联
3. 页面 trace
4. 渲染质量检查
5. blueprint 稳定后再考虑存储

---

## 8. 最值得先做的 6 件事

如果只看投入产出比，我建议 Layer 3 先做这 6 件：

1. `ReportPayloadV2` 扩字段
2. `chapter_plan`
3. `page_plan`
4. `page_view_model`
5. `page_type registry`
6. Next.js print route + Playwright 对接

这 6 件做完，整份报告的“结构感、页感、导出稳定性”都会明显提升。

---

## 9. 最后一句判断

你现在的 Layer 3 并不是方向错了，而是：

**已经有“报告生成”和“HTML 渲染”，但还没有真正的“页面系统”。**

而你们下一阶段想要的所有东西：
- 固定页型
- 7 天 / 14 天差异化展开
- 目录
- 酒店/餐厅/拍摄独立页
- 情绪价值
- 定制感
- Web/PDF 一套语义

本质上都依赖同一个中枢：

**chapter_plan + page_plan + page_view_model。**

建议就从这里开工。
