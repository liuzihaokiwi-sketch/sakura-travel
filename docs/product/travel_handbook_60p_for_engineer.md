# 定制旅行手册渲染规则 v1（给 AI 程序员执行版）

> 目标：为 5–11 天的日本定制旅行手册提供统一页面规划与渲染规则。  
> 主交付：PDF 实体手册（主），H5 阅读版（辅）。  
> 设计原则：  
> - 同一套 page semantics，同源输出 PDF / H5  
> - 前半段不剧透，后半段进入按天展开  
> - 右页承载高价值执行信息，左页承载轻内容与情绪感  
> - 静态块、规则块、AI 块分层，不要让 AI 负责所有页面从头写

---

# 1. 适用范围

## 1.1 天数适用
- 支持：**5–11 天**
- **12 天及以上**：建议用户购买多个套餐或拆分为多册（例如 7+5、6+6、7+7）
- 不建议把 12+ 天强压进单册 60 页内，否则会导致：
  - 每天信息密度过高
  - 页面质量下降
  - 解释性与记忆性被压缩

## 1.2 输出目标
- PDF：正式交付主形态
- H5：补充查看与预览
- 后续允许同一 page_plan 输出不同 render adapter

---

# 2. 设计原则

## 2.1 三层结构
整本手册固定拆成三层：

1. **前置层（不剧透）**
   - 封面
   - 地图
   - 行程亮点
   - 旅行气质
   - 住宿 / 餐厅 / 预订 / 预算 / 行前准备 / 安全
   - 剧透提示页

2. **每日展开层**
   - 按天展开
   - 每天固定骨架
   - 条件页按需触发或内嵌

3. **旅后记忆层**
   - 购物 / 预算回顾 / 照片 / 心情 / 封底

## 2.2 左右页职责
- **右页（重要内容）**
  - 时间线
  - 路线执行
  - 酒店 / 餐厅 / 推荐理由
  - 预算 / 风险 / Plan B
- **左页（轻内容）**
  - 插图
  - 故事
  - 出片
  - 小地图
  - 礼仪提醒
  - 贴纸位 / 照片位 / 心情位

## 2.3 页面价值排序
优先级从高到低：
1. 可执行
2. 可解释
3. 可感知
4. 可保存

---

# 3. 页型定义（page_type）

建议最少注册以下页型：

- `cover_page`
- `map_spread`
- `trip_mood_page`
- `highlights_spread`
- `trip_logic_page`
- `hotel_overview_page`
- `restaurant_reservation_page`
- `budget_overview_page`
- `departure_prep_page`
- `safety_page`
- `spoiler_gate_page`
- `day_cover_page`
- `day_logic_page`
- `day_am_page`
- `day_pm_page`
- `day_evening_page`
- `day_backup_memory_page`
- `shopping_page`
- `budget_review_page`
- `memory_photo_page`
- `memory_reflection_page`
- `back_cover_page`

---

# 4. 7天 / 60页标准版 page_plan

## 4.1 总体结构
- 前置层：13 页（含剧透提示页）
- 每日层：42 页（7 × 6）
- 旅后层：5 页
- 封底：1 页

合计：60 页

## 4.2 标准页码表

### 前置层
- P1 `cover_page`
- P2–P3 `map_spread`
- P4 `trip_mood_page`
- P5–P6 `highlights_spread`
- P7 `trip_logic_page`
- P8 `hotel_overview_page`
- P9 `restaurant_reservation_page`
- P10 `budget_overview_page`
- P11 `departure_prep_page`
- P12 `safety_page`
- P13 `spoiler_gate_page`

### 每日层（每天 6 页）
Day 1
- P14 `day_cover_page`
- P15 `day_logic_page`
- P16 `day_am_page`
- P17 `day_pm_page`
- P18 `day_evening_page`
- P19 `day_backup_memory_page`

Day 2
- P20 `day_cover_page`
- P21 `day_logic_page`
- P22 `day_am_page`
- P23 `day_pm_page`
- P24 `day_evening_page`
- P25 `day_backup_memory_page`

Day 3
- P26 `day_cover_page`
- P27 `day_logic_page`
- P28 `day_am_page`
- P29 `day_pm_page`
- P30 `day_evening_page`
- P31 `day_backup_memory_page`

Day 4
- P32 `day_cover_page`
- P33 `day_logic_page`
- P34 `day_am_page`
- P35 `day_pm_page`
- P36 `day_evening_page`
- P37 `day_backup_memory_page`

Day 5
- P38 `day_cover_page`
- P39 `day_logic_page`
- P40 `day_am_page`
- P41 `day_pm_page`
- P42 `day_evening_page`
- P43 `day_backup_memory_page`

Day 6
- P44 `day_cover_page`
- P45 `day_logic_page`
- P46 `day_am_page`
- P47 `day_pm_page`
- P48 `day_evening_page`
- P49 `day_backup_memory_page`

Day 7
- P50 `day_cover_page`
- P51 `day_logic_page`
- P52 `day_am_page`
- P53 `day_pm_page`
- P54 `day_evening_page`
- P55 `day_backup_memory_page`

### 旅后层
- P56 `shopping_page`
- P57 `budget_review_page`
- P58 `memory_photo_page`
- P59 `memory_reflection_page`
- P60 `back_cover_page`

---

# 5. 5–11 天伸缩规则

## 5.1 核心策略
不要简单按“天数 × 固定页数”硬算，而要使用：

```text
总页数 = 固定前置层 + 每日固定骨架 + 条件页触发 + 旅后层
```

## 5.2 推荐页数区间
结合现有项目文档：
- 5 天：26–32 页
- 7 天：34–42 页（你现在扩展做成 60 页高级收藏版是特例）
- 9 天：40–50 页
- 11 天：46–60 页
参考：项目当前文档对 5/7/9/11–14 天页数范围有明确建议，且强调不要靠每天很多页堆厚度，而应靠总纲前置、固定骨架、条件页触发来堆值感。fileciteturn13file2 fileciteturn13file14

## 5.3 实际渲染建议

### 5 天版
建议：
- 前置层：10–12 页
- 每天：4 页
- 旅后层：4–6 页

适合：
- 首发轻量产品
- 入门款
- 城市单点 / 双城轻旅行

### 6–7 天版
建议：
- 前置层：12–13 页
- 每天：5–6 页
- 旅后层：5 页

适合：
- 标准主推款
- 最稳定的结构

### 8–9 天版
建议：
- 前置层：12–13 页
- 每天：4–5 页
- 额外插入 2–4 页条件页
- 旅后层：4–5 页

逻辑：
- 天数变多后，不要天天都 6 页，否则过厚
- 条件页改成按需触发

### 10–11 天版
建议：
- 前置层：12–13 页
- 每天：4 页固定骨架
- 条件页 4–8 页穿插
- 旅后层：3–4 页

逻辑：
- 每天降低展开密度
- 用条件页补“重要日”“跨城日”“高风险日”
- 保持全册不超过 60 页

## 5.4 12 天以上
策略：
- 不强行压缩
- 明确提示用户购买多个套餐
- 推荐拆分方式：
  - 12 天：7+5
  - 13 天：7+6
  - 14 天：7+7
  - 15–18 天：按城市圈拆册
- 每册单独拥有：
  - 封面
  - 地图
  - 亮点
  - 前置信息
  - 每日展开
  - 记忆页

这样实体体验更好，也更适合打印与收藏。

---

# 6. 每日固定骨架（day_page_bundle）

## 6.1 固定 6 页版（7 天高级版）
每天固定：
1. `day_cover_page`
2. `day_logic_page`
3. `day_am_page`
4. `day_pm_page`
5. `day_evening_page`
6. `day_backup_memory_page`

## 6.2 压缩 4 页版（9–11 天常规版）
每天固定：
1. `day_cover_page`（含时间线）
2. `day_logic_page`
3. `day_detail_page`（AM/PM 合并）
4. `day_backup_memory_page`

## 6.3 条件页触发规则
可触发：
- `hotel_detail_page`
- `restaurant_detail_page`
- `transport_detail_page`
- `photo_spot_page`
- `budget_focus_page`
- `route_warning_page`

触发条件参考现有文档：
- 酒店页：换酒店 / 住宿选择理由强 / 区域很重要
- 餐厅页：重点晚餐 / 纪念日晚餐 / 某餐是体验核心
- 交通页：跨城 / 复杂换乘 / 机场 / 温泉区 / 郊区
- 出片页：富士山、京都古街、夜樱、温泉街、强视觉日
- 预算感知页：某天消费结构明显
参考：项目既有文档已明确这些条件页的触发逻辑。fileciteturn13file3

---

# 7. 页面 slot 设计建议

## 7.1 cover_page
required slots:
- `city_name`
- `city_illustration`
- `brand_name`
- `greeting_line`
- `romantic_blessing`

## 7.2 trip_mood_page
required slots:
- `trip_keywords[]`
- `mood_paragraph`
- `theme_illustration`

## 7.3 highlights_spread
required slots:
- `highlight_items[]`
- `highlight_visuals[]`

规则：
- 不允许写具体日程顺序
- 只写体验型亮点

## 7.4 budget_overview_page
required slots:
- `budget_level`
- `budget_focus_areas[]`
- `worth_spending_on[]`
- `easy_to_overspend_on[]`
- `save_money_tips[]`

## 7.5 spoiler_gate_page
required slots:
- `spoiler_title`
- `spoiler_copy`
- `continue_hint`

## 7.6 day_cover_page
required slots:
- `day_number`
- `day_theme`
- `day_region`
- `day_timeline[]`
- `day_highlights[]`
- `intensity_hint`

## 7.7 day_logic_page
required slots:
- `day_structure_reasoning`
- `selected_over_skipped[]`
- `pace_explanation`
- `route_order_reason`

## 7.8 day_am_page / day_pm_page / day_evening_page
required slots:
- `primary_items[]`
- `transport_hint`
- `stay_duration_hint`
- `photo_spot_hint`
- `pitfall_alerts[]`

optional slots:
- `story_fragment`
- `illustration_asset`
- `nearby_bonus_items[]`

## 7.9 day_backup_memory_page
required slots:
- `plan_b_options[]`
- `risk_watch_items[]`
- `tomorrow_hint`

optional slots:
- `photo_slot_count`
- `mood_slot_enabled`
- `ticket_stub_slot_enabled`

---

# 8. 数据来源与内容分层

## 8.1 静态块
直接复用，不需要 AI 重写：
- 出发前准备
- 常用 App
- 支付 / eSIM / 交通卡
- 通用安全须知
- 通用礼仪
- 紧急联系方式

## 8.2 规则块
结构化生成：
- 酒店选择理由
- 餐厅推荐理由
- 路线排序理由
- 节奏说明
- 预算倾斜解释
- 条件页触发逻辑

## 8.3 AI 块
只负责高价值解释：
- 总设计思路
- 每天亮点解释
- 复杂取舍说明
- 个性化润色
参考：现有代码与文档都明确要求 AI 只承担少量高价值解释，不要让 prompt 替代结构和规则。fileciteturn13file10 fileciteturn13file17

---

# 9. 预算页规则

## 9.1 为什么必须加预算页
现有文档已明确：
- 预算与约束是主链核心模块
- 条件页中存在“预算感知页”
- 适合强调今天哪里容易花冤枉钱、哪里更值得花
参考：预算模块是主链能力之一，预算感知页也是既有条件页设计的一部分。fileciteturn13file15 fileciteturn13file3

## 9.2 两层预算设计
- `budget_overview_page`：前置层
- `budget_review_page`：旅后层

## 9.3 不做精确财务表
产品侧只做：
- 预算倾向
- 高价值花费点
- 冤枉钱风险
- 省钱建议

---

# 10. 风控与免责声明

在手册中固定加入：
- 本产品为攻略与规划服务，不替代官方签证、交通和商家公告
- 营业时间、票务、交通等动态信息请出发前复核
- 如涉及高风险天气或交通中断，以官方实时通告为准

参考：现有系统文档已将这类文案边界写入合规与风控建议。fileciteturn13file4

同时可接官方日本旅行信息：
- JNTO 规划入口
- JNTO Safety Tips
- Japan Visitor Hotline（24/7，中文可用）
- 行李寄送（Hands-Free travel）
这些信息适合支撑：
- 前置安全页
- 行李与转场提醒
- 紧急情况微卡
参考：JNTO 官方将计划、行李、热线与安全信息都放在游客 planning 主路径内。citeturn240345search7turn240345search1turn240345search0turn240345search5

---

# 11. 页面校验规则（建议）

新增页级校验：
- 每页必须有 `page_type`
- required slots 不得缺失
- 每页主承诺不得与主题冲突
- 同类对象占页规则不得冲突
- print variant 不得出现 overflow
参考：现有 Layer 3 方案已建议将校验升级到页级，而不只是结构级。fileciteturn13file19

---

# 12. 给渲染层的实现建议

## 12.1 推荐对象
- `chapter_plan`
- `page_plan`
- `page_view_model`
- `page_blueprint`（先放代码注册表）

## 12.2 推荐流程
```text
TripProfile
  -> ItineraryPayload
  -> ChapterPlanner
  -> PagePlanner
  -> PageViewModelBuilder
  -> RenderAdapters
  -> PDF / H5
```

## 12.3 推荐栈
- Web 主表达层：React / Next.js
- PDF：Playwright 或 Print CSS 管线
- 短期兼容：Jinja2 fallback
参考：现有代码与 Layer 3 文档已将 React 组件体系 + page semantics 作为中期主方向。fileciteturn13file16

---

# 13. 产品策略补充

## 13.1 当前主推
- 5–7 天：最优先
- 8–9 天：次优先
- 10–11 天：高价延展款
- 12+ 天：拆单

## 13.2 不要做的事
- 不要用“每天很多页”堆值感
- 不要把所有静态内容交给 AI
- 不要让故事页压过执行页
- 不要在前置层剧透过多具体路线

---

# 14. 程序员最终执行摘要

1. 先固定 7 天 60 页高级版 page_plan
2. 再做 5–11 天的 page planner 伸缩规则
3. 将预算页纳入前置层和旅后层双层体系
4. 首页必须支持：
   - 城市名
   - 城市插图
   - 品牌名
   - 友好互动语
   - 浪漫祝福语
5. 中间必须有 `spoiler_gate_page`
6. 12 天以上直接触发“建议拆分套餐”策略
7. 静态块 / 规则块 / AI 块严格分层
8. 页面级校验必须加上
9. 插图资源包必须按命名匹配 + 左右联动 + small/medium/large/sticker_inline 规则接入

> 这套规则的目标，不是把 PDF 填满，而是把“这份攻略懂我、能执行、也值得留住”的感觉稳定渲染出来。


---

# 15. 插图资源包接入规范（新增，优先级高）

> 本节用于规范“外部已命名插图资源包”如何被渲染层消费。  
> 前提：图片由外部提供，程序**不生成图片**，只做**匹配、选图、排版、左右联动**。

## 15.1 资源包前提
外部会提供一套插图资源包，已按名称命名好。  
程序需要根据页面对象、主题、情绪和辅助内容，自动为页面选择合适图片。

### 资源类型（第一期固定）
- `landmark`：景点 / 标志性地点 / 地标建筑
- `hotel`：酒店 / 温泉旅馆 / 住宿氛围
- `restaurant_food`：餐厅食物类型 / 菜品
- `cute_animal`：可爱动物 / 情绪插图 / 轻提醒陪伴图
- `streetscape`：街景 / 夜景 / 巷子 / 商店街 / 城市氛围
- `sticker`：贴纸型素材，可插入文字中间或角落

### 推荐命名方式
```text
{category}__{entity_or_theme}__{variant?}
```

示例：
```text
landmark__tokyo_tower
landmark__kiyomizu_dera
hotel__onsen_ryokan
restaurant_food__ramen
restaurant_food__sushi
cute_animal__shiba_inu
streetscape__kyoto_alley_night
sticker__ramen_bowl
sticker__camera
sticker__train_ticket
```

### 设计要求
- 程序**不要依赖非常复杂的命名语法**
- 只要能稳定完成：
  - `category`
  - `entity_or_theme`
  - `variant`
  三段解析即可
- 若命名中存在更多字段，也应视为可选扩展，不要作为硬依赖

---

## 15.2 资源索引结构（建议）
建议在渲染前先建立资源索引，而不是每页临时扫描目录。

```ts
IllustrationAsset {
  asset_id: string
  file_path: string
  category: 'landmark' | 'hotel' | 'restaurant_food' | 'cute_animal' | 'streetscape' | 'sticker'
  entity_or_theme: string
  variant?: string
  tags?: string[]
  orientation?: 'portrait' | 'landscape' | 'square'
}
```

推荐在启动时构建：
```ts
IllustrationRegistry {
  byCategory: Record<string, IllustrationAsset[]>
  byEntityOrTheme: Record<string, IllustrationAsset[]>
}
```

---

## 15.3 选图优先级（必须执行）
页面图片不能随机放，必须按下面顺序命中：

### 一级：实体直接命中
若页面核心对象是明确实体，优先匹配对应图：
- 景点 / 地标页 → `landmark`
- 酒店页 → `hotel`
- 餐厅 / 菜品页 → `restaurant_food`

### 二级：主题命中
若没有明确实体图，则匹配主题：
- 夜景 / 散步 / 老街 / 街区 → `streetscape`
- 温泉 / 住一晚 / 恢复感 → `hotel`
- 治愈 / 可爱 / 轻松 / 提醒 → `cute_animal`

### 三级：情绪补位
若实体和主题都不够准确，再用情绪图做轻补位：
- 剧透提示页
- 预算页
- 心情页
- 记录页
- Plan B 页
- 礼仪提示页

### 禁止规则
- 不允许为了“有图”而放强不相关图片
- 严肃提醒页（安全 / 应急）不得用卖萌图做主图
- 酒店页主图不得使用无关动物图
- 若已命中明确实体图，不要再让无关氛围图抢主视觉

---

## 15.4 左右页联动规则（必须有）
**原则：右页是主内容，左页图片/故事/提醒必须服务右页。**

### 左页资源与右页主内容至少满足一条：
1. 对应右页主对象
2. 对应右页的食物 / 建筑 / 街区 / 酒店
3. 对应右页的故事、礼仪或提醒
4. 对应右页的情绪和节奏

### 示例
- 右页写“午饭吃拉面” → 左页可放 `restaurant_food__ramen`
- 右页写“清水寺 + 东山散步” → 左页可放 `landmark__kiyomizu_dera` 或 `streetscape__kyoto_alley`
- 右页写“住温泉旅馆” → 左页可放 `hotel__onsen_ryokan`
- 右页是记录页 / 心情页 → 左页可放 `cute_animal`
- 右页写“夜晚慢慢散步” → 左页可放 `streetscape__night_walk`

### 不允许的情况
- 左页只是“好看”，但和右页毫无关系
- 右页是餐厅解释，左页却放无关地标图
- 右页是酒店基点说明，左页却放随机菜品图

---

## 15.5 图片尺寸等级（新增 image_size 枚举）
统一枚举：
- `small`
- `medium`
- `large`
- `sticker_inline`

---

## 15.6 small 图规则
> 用户要求：**四分之一版面（左右满，上下四分之一）**

### 定义
- 占当前页内容区约 **1/4 高度**
- 宽度尽量铺满当前内容栏（满宽）
- 适合放在某一栏的上方或下方
- 仍允许大量文字共存

### 用法
适合：
- 故事块上下
- 礼仪提示上下
- 轻提醒页
- 小地图旁
- 顺路小店说明旁
- 预算页轻插图

### small 图与文字关系
- 可以搭配较长文字
- 适合与 1 段故事 + 1 组提示同时出现
- 不应成为主视觉
- 不应单独占整页

### 建议内容来源
- `restaurant_food`
- `cute_animal`
- `sticker`（放大版 small 使用也可）
- `streetscape`（局部氛围）
- 小型 `landmark` 局部图

---

## 15.7 medium 图规则
> 用户要求：**二分之一版面，插入少一点内容**

### 定义
- 占当前页约 **1/2 高度**
- 一般为某页左侧主图
- 可与少量说明文字共存

### 用法
适合：
- 今日主题页左侧主图
- 上午 / 下午展开页的主要情绪图
- 酒店页主图
- 餐厅页主图
- 强视觉日的出片页

### medium 图与文字关系
- 配少量内容
- 推荐：
  - 1 个标题
  - 1 段短文
  - 或 1–3 个要点
- 不建议再堆大量文字

### 建议内容来源
- `landmark`
- `hotel`
- `restaurant_food`
- `streetscape`

---

## 15.8 large 图规则
> 用户要求：**大图最多在下面加一句话或者不加话**

### 定义
- 占整页或绝大部分页面
- 可为整页主图或跨页主图
- 主要承担氛围、章节切换、强视觉记忆点

### 用法
适合：
- 封面
- 地图跨页背景
- 亮点跨页
- 剧透提示页
- Day 封面页
- 照片页
- 封底
- 章节 opener（若后续启用）

### large 图与文字关系
- 最多 1 句 caption
- 或完全不放文字
- 不允许在 large 图页强塞大量正文
- 若某页需要较多信息，则不应使用 `large`

### 建议内容来源
- `landmark`
- `streetscape`
- `hotel`（高氛围型）
- 少数 `restaurant_food`（仅在菜品视觉极强时）

---

## 15.9 sticker_inline 规则（新增）
> 用户新增类型：**贴纸类型，可以插入文字中间**

### 定义
`sticker_inline` 不是普通图片块，而是**内嵌装饰性视觉元素**。

### 用法
适合：
- 标题旁
- 段落中间
- 清单项前
- 记录位角落
- 预算页 / 餐厅页 / 购物页的文字间隔符
- 照片页 / 心情页 / 小票页的装饰元素

### 规则
- sticker 不承担主视觉
- 不可替代 `small / medium / large`
- 应作为**文字中的视觉点缀**
- 一个区域内 sticker 数量要受控，避免变成儿童贴纸墙

### 建议尺寸
- 行内高度约等于 1–2 行文字
- 或角落点缀大小，不超过内容块高度的 15%

### sticker 来源
- `sticker__ramen_bowl`
- `sticker__camera`
- `sticker__map_pin`
- `sticker__ticket`
- `sticker__train`
- `sticker__cat`
等

---

## 15.10 页面与图片尺寸的推荐映射
建议在 page_type registry 中增加 `preferred_image_sizes`：

### 推荐映射
- `cover_page` → `large`
- `map_spread` → `large`
- `trip_mood_page` → `medium`
- `highlights_spread` → `large` 或 `medium + small`
- `hotel_overview_page` → `medium`
- `restaurant_reservation_page` → `small + sticker_inline`
- `budget_overview_page` → `small + sticker_inline`
- `departure_prep_page` → `small + sticker_inline`
- `safety_page` → `small`（严肃页慎用可爱图）
- `spoiler_gate_page` → `large`
- `day_cover_page` → `large` 或 `medium`
- `day_logic_page` → `small`
- `day_am_page` → `medium`
- `day_pm_page` → `medium`
- `day_evening_page` → `medium`
- `day_backup_memory_page` → `small + sticker_inline`
- `shopping_page` → `small + medium + sticker_inline`
- `budget_review_page` → `small`
- `memory_photo_page` → `large` 或空位优先
- `memory_reflection_page` → `small + sticker_inline`
- `back_cover_page` → `large`

---

## 15.11 每页图片数量上限（建议）
为避免“堆素材”而失控，建议：

- 含 `large` 的页：`large <= 1`，其它图片默认 0 或最多 1 个 `sticker_inline`
- 含 `medium` 的页：`medium <= 1`，可附带 `small <= 1`
- 含 `small` 的页：`small <= 2`
- `sticker_inline`：单页建议 `<= 4`

---

## 15.12 图片选择函数（建议）
建议新增统一函数：

```ts
selectIllustrationForPage(pagePlan, pageContent, illustrationRegistry): PageIllustrationPlan
```

返回结构建议：

```ts
PageIllustrationPlan {
  hero_image?: IllustrationAsset
  support_images?: IllustrationAsset[]
  inline_stickers?: IllustrationAsset[]
  image_size_mode: 'small' | 'medium' | 'large' | 'mixed'
  rationale?: string[]
}
```

### 选择逻辑建议
1. 先看 `page_type` 推荐尺寸
2. 再看页内主对象
3. 再看是否有明确实体图
4. 再看是否需要主题氛围图
5. 最后决定是否插入 sticker

---

## 15.13 与内容模块的绑定关系
建议在页面对象中支持：
- `primary_visual_topic`
- `secondary_visual_topics[]`
- `visual_mood_tags[]`

示例：
```ts
{
  "page_type": "day_evening_page",
  "primary_visual_topic": "ramen",
  "secondary_visual_topics": ["night_walk", "alley"],
  "visual_mood_tags": ["warm", "city_night", "casual"]
}
```

程序先用这些字段找图，而不是靠最终文案全文做模糊匹配。

---

## 15.14 5–11 天伸缩时的图片密度规则
随着天数变长，整本页数压力会变大，图片密度要自动调整。

### 5–7 天
- 允许更多 `medium`
- 关键页可保留 `large`
- 左页更强调故事感与插图感

### 8–9 天
- 减少 `large`
- 以 `medium + small` 为主
- 把更多图作为辅助，而不是独立占页

### 10–11 天
- `large` 只留给封面 / 地图 / 亮点 / 剧透页 / 封底
- 每天更多使用 `small` 和少量 `medium`
- 保证信息密度不被视觉页过度稀释

### 12 天以上（拆套餐）
- 每册重新按 5–7 天逻辑做图密度
- 不建议做 12+ 天超厚单册后再强塞大量大图

---

## 15.15 页面校验（图片相关，新增）
新增图片级校验：

- `IMG_001`：若 page_type 需要主图，`hero_image` 不得缺失
- `IMG_002`：`large` 图页不得同时承载大量正文
- `IMG_003`：左页图片必须与右页主对象或主题有关联
- `IMG_004`：严肃提醒页不得使用高冲突卖萌主图
- `IMG_005`：`sticker_inline` 不得超过单页上限
- `IMG_006`：同一视觉主题在相邻页不得机械重复
- `IMG_007`：若命中明确实体图，不得退化成无关通用图
- `IMG_008`：图片缺失时必须优雅降级到“无图版面”，不得破版

---

## 15.16 降级策略（必须有）
如果资源包没有命中，也不能让页面崩掉。

### 降级顺序
1. 实体图
2. 主题图
3. 情绪图
4. 仅 sticker
5. 无图版

### 原则
- 无图时页面仍然必须可读
- 不要为了补空位而塞错图
- “少一张图”比“放错图”更好

---

## 15.17 程序员执行摘要（图片部分）
1. 建立 `IllustrationRegistry`
2. 按命名规则解析 category / entity_or_theme / variant
3. 为 page_type 增加 `preferred_image_sizes`
4. 新增 `PageIllustrationPlan`
5. 先按实体命中，再按主题命中，再按情绪补位
6. small / medium / large / sticker_inline 四种尺寸严格分工
7. 左页必须服务右页，不允许视觉与内容脱节
8. 5–11 天版本随天数自动降低图片密度
9. 图片缺失时优雅降级，不许破版
