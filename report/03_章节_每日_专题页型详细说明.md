# 章节、每日与专题页型详细说明

---

# 1. 城市圈章节页

## 主要是干什么的
把长行程切成有节奏的阶段，让用户感到“这一段旅程开始了”。

## 设计思路
章节页像一本书的章首页，不承担细节，只承担阶段氛围与阶段目标。

## 放哪些数据
- chapter_title
- city_circle_name
- covered_days
- chapter_goal
- chapter_keywords
- key_major_activities[]
- base_summary
- hero_visual

## 排版顺序
1. 大标题
2. 这一阶段怎么玩
3. 关键词与节奏说明
4. 这一阶段的主要活动
5. 基点与区域提示

## 哪里要单独有设计感
- 章节页必须比普通页更“像开场”
- Hero 区要明显
- 关键词与阶段目标要有情绪感

## 工程注意点
- 章节页适合用 Satori 或服务端生成 Hero
- 不应包含过多执行信息
- 长行程推荐强制启用

---

# 2. 每日执行页

## 主要是干什么的
这是每天最重要的一页。
它只负责告诉用户：今天怎么跑。

## 设计思路
这页不能再承担餐厅细讲、拍摄细讲、酒店细讲。
它只做“日执行总控”。

## 放哪些数据
- day_index
- day_title
- day_goal
- primary_corridor
- main_driver
- secondary_activities[]
- timeline[]
- transit_burden
- walking_burden
- must_keep
- cut_first
- day_capacity_summary

## 排版顺序
1. Day 标题 + 今日情绪目标
2. 今日主线摘要
3. 今日主要活动 / 次要活动
4. 时间轴
5. 步数 / 换乘 / 节奏摘要
6. 今天最不能砍
7. 今天最先砍

## 哪里要单独有设计感
- Day 标题区必须强
- “今天最值得期待的事”必须有视觉焦点
- 时间轴要有明显阅读路线，不要堆成列表

## 工程注意点
- 这是必有页，所有 trip 都要生成
- timeline 项数要限制
- Web 和 PDF 采用同一内容顺序

---

# 3. 主要活动页

## 主要是干什么的
把真正值得单独去、单独住、单独预约或单独期待的活动讲透。

## 设计思路
主要活动页不是景点介绍页，而是“为什么它值得占据这趟行程核心位置”。

## 放哪些数据
- activity_title
- activity_type
- why_selected
- best_time_window
- reservation_need
- execution_notes
- emotional_value
- route_relationship
- fallback_options
- activity_media

## 排版顺序
1. 活动标题与一句定性
2. 为什么是它
3. 什么时候去最值
4. 怎么执行最稳
5. 路线与酒店关系
6. 风险与备选

## 哪里要单独有设计感
- 首屏必须有明显“核心亮点”
- 最佳时间窗应有清晰强调
- 这页可以有更强的图文对照感

## 工程注意点
- 每个主要活动对象 1 个 page model
- 活动页可被多个 day 引用，但正文只保留 1 次
- 条件触发逻辑需稳定

---

# 4. 酒店详情页

## 主要是干什么的
让用户感到：这家酒店不是随手填进去的，而是路线的一部分。

## 设计思路
酒店详情页讲的是“为什么住这里值”，不是 OTA 描述页。

## 放哪些数据
- hotel_name
- hotel_role（主要 / 次要 / 体验型 / 过渡型）
- why_this_hotel
- nights
- served_days
- checkin_checkout_logic
- access_summary
- room_or_view_highlights
- breakfast_or_bath_highlights
- caveats
- alternatives[]

## 排版顺序
1. 酒店名与定位
2. 选择理由
3. 服务哪些天 / 哪些活动
4. 入住退房逻辑
5. 真正值得在意的卖点
6. 提醒与替代

## 哪里要单独有设计感
- 酒店页应该有“住进去”的想象感
- 但不能像 OTA 广告图
- 关键价值点要像策展说明，而不是参数表

## 工程注意点
- 主要酒店独占整页
- 次要酒店允许双卡拼页
- 酒店亮点应优先使用 editor notes / 规则块

---

# 5. 餐厅详情页

## 主要是干什么的
解释为什么这家餐厅值得保留在路线里，以及何时去最合理。

## 设计思路
餐厅页不是菜谱页，也不是纯种草页，而是“餐厅作为这一天体验结构的一部分”。

## 放哪些数据
- restaurant_name
- meal_slot
- why_selected
- reservation_need
- queue_risk
- budget_band
- signature_items
- route_detour_cost
- nearby_context
- alternatives[]

## 排版顺序
1. 餐厅名与餐段
2. 为什么吃这家
3. 最适合放在今天哪个时段
4. 排队 / 预约 / 预算
5. 推荐点单
6. 替代与边界

## 哪里要单独有设计感
- 主图 / 主标题要有食欲感但不俗
- 推荐点单区可做成亮点标签
- “值不值得为它绕路”是很有判断感的内容，可重点设计

## 工程注意点
- 主要餐厅独占整页
- 次要餐厅可合并
- 必须控制文本长度，避免像点评合集

---

# 6. 拍摄主题页

## 主要是干什么的
给用户明确的“出片价值”和“最佳拍法”，而不是一句“这里好拍”。

## 设计思路
拍摄页不按景点，而按“拍摄主题 / 拍摄路线 / 时间窗”组织。

## 放哪些数据
- photo_theme_title
- related_places[]
- best_time_window
- lighting_notes
- crowd_notes
- route_for_shooting
- visual_style_keywords
- weather_sensitivity
- fallback_if_bad_weather

## 排版顺序
1. 主题标题
2. 想拍到什么感觉
3. 最佳时间窗
4. 推荐拍法 / 路线
5. 人流与天气提醒
6. 替代方案

## 哪里要单独有设计感
- 这是最该有情绪价值的一类页
- 主视觉区要有大片感
- 标题、时间窗、风格关键词应该非常抓眼

## 工程注意点
- 主要拍摄主题整页
- 次要拍摄点允许合并
- 页面高度依赖图像质量与裁切策略

---

# 7. 交通页

## 主要是干什么的
把复杂日的交通执行风险讲清楚，减少用户临场焦虑。

## 设计思路
交通页只在复杂场景出现，不机械触发。
它讲“怎么过去最稳”，不讲通用交通百科。

## 放哪些数据
- transit_scenario_title
- start_node
- end_node
- key_steps[]
- luggage_consideration
- station_or_transfer_notes
- ticket_or_pass_notes
- time_margin
- fallback_route

## 排版顺序
1. 交通目标
2. 最稳路线
3. 关键换乘点
4. 行李 / 时间余量提醒
5. 替代方案

## 哪里要单独有设计感
- 路线步骤要非常清晰
- 关键换乘节点应像流程图
- 不要过度装饰，重点是稳

## 工程注意点
- 复杂交通日才生成
- 与 route matrix 数据强关联
- 允许 Web 版提供展开说明，PDF 保留主干

---

# 8. 顺路补充页

## 主要是干什么的
放那些“值得知道，但不值得独立一整页”的次要内容。

## 设计思路
它是加分页，不是主舞台。
目的：让攻略看起来更完整，但不打乱重点。

## 放哪些数据
- secondary_dining[]
- shopping_spots[]
- minor_photo_spots[]
- flexible_stops[]
- stop_value_labels
- can_skip_labels

## 排版顺序
1. 本页主题
2. 顺路可去
3. 更适合什么时候顺便去
4. 不值得专门去的边界
5. 可砍优先级

## 哪里要单独有设计感
- 不需要太华丽
- 但要非常好扫
- 建议使用统一小卡片系统

## 工程注意点
- 这是最适合合并输出的页型
- 字数和卡片数必须严格限制
- 不能替代主要内容页

---

# 9. 调整 / Plan B 页

## 主要是干什么的
当遇到下雨、晚点、体力不足或实时扰动时，告诉用户最优调整方式。

## 设计思路
Plan B 页讲的是“优先级”和“替换逻辑”，不是简单说“可以去别的地方”。

## 放哪些数据
- trigger_conditions[]
- must_keep_ids[]
- cut_order[]
- fallback_corridor
- replacement_options[]
- recovery_advice
- transport_adjustment_notes

## 排版顺序
1. 什么情况下需要启动调整
2. 先保什么
3. 先砍什么
4. 替代方向
5. 如果更糟，怎么继续收缩

## 哪里要单独有设计感
- “先保 / 先砍”必须极清晰
- 替代方向要像决策树
- 可以用轻量色块做层级，不要做灾难警报风

## 工程注意点
- 只在复杂高风险日或高价值日触发
- 内容必须来自结构化 fallback 逻辑
- 不能让 AI 随意自由发挥替代路线
