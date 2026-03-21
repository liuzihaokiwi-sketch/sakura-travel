## ADDED Requirements

### Requirement: 城市季节活动表

系统 SHALL 创建 `city_seasonal_events` 表，存储城市级季节活动/花期/节日信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 主键 |
| city_code | VARCHAR NOT NULL | 城市代码 |
| event_name_zh | VARCHAR | 活动中文名 |
| event_type | VARCHAR | cherry_blossom / autumn_leaves / festival / illumination / seasonal_food |
| start_date | DATE | 开始日期（每年更新） |
| end_date | DATE | 结束日期 |
| peak_start | DATE NULL | 最佳观赏期开始 |
| peak_end | DATE NULL | 最佳观赏期结束 |
| related_areas | JSONB | 关联区域列表 |
| related_entity_ids | JSONB | 关联实体 ID 列表 |
| description_zh | TEXT | 一句话描述 |
| copywriter_hint | TEXT | 给 AI 文案润色的提示（"可以提到此时正值满开期"） |
| confidence | VARCHAR | confirmed / estimated / historical |
| source | VARCHAR | jnto / manual / ai_estimated |
| year | INT | 适用年份 |
| updated_at | TIMESTAMP | 更新时间 |

用途：① 行程装配时注入当季推荐理由 ② copywriter 润色时引用季节信息 ③ 预览页展示"现在去能看到什么"

#### Scenario: 花期数据查询

- **WHEN** 装配 2026 年 3 月底东京行程
- **THEN** 查询到 cherry_blossom 事件，peak_start=3/25, peak_end=4/5，system 注入"此时正值东京樱花满开期"到 copywriter_hint

### Requirement: 区域人流密度表

系统 SHALL 创建 `area_crowd_patterns` 表，存储区域 × 时段 × 日类型的人流密度信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 主键 |
| city_code | VARCHAR NOT NULL | 城市代码 |
| area_code | VARCHAR NOT NULL | 区域代码 |
| day_type | VARCHAR | weekday / weekend / holiday |
| time_slot | VARCHAR | morning / midday / afternoon / evening / night |
| crowd_level | INT | 1-5（1=很空，5=极拥挤） |
| wait_time_minutes | INT NULL | 典型排队等候时间（分钟） |
| best_visit_hint | TEXT | "建议上午 10 点前到达，避开旅行团" |
| source | VARCHAR | google_popular_times / manual / ai_estimated |
| updated_at | TIMESTAMP | 更新时间 |

索引：city_code + area_code + day_type + time_slot

用途：① 装配时选择更合理的到访时段 ② 推荐理由中写"这个时段去人少" ③ 自助微调候选排序考虑拥挤度

#### Scenario: 避开高峰推荐

- **WHEN** 装配浅草区域下午行程
- **THEN** 查到 afternoon + weekend 的 crowd_level=5，system 建议改为 morning 或标注"下午人很多，建议一早去"

### Requirement: 实体运营上下文表

系统 SHALL 创建 `entity_operational_context` 表，存储实体级营业日历和预约信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| entity_id | UUID PK | 关联实体 |
| entity_type | VARCHAR | poi / hotel / restaurant |
| regular_closed_days | JSONB | 固定定休日 ["monday"] |
| irregular_closed_dates | JSONB | 不规则休业日 ["2026-04-15"] |
| reservation_required | BOOLEAN | 是否需要预约 |
| reservation_difficulty | VARCHAR | easy / moderate / hard / lottery |
| reservation_lead_days | INT NULL | 建议提前几天预约 |
| peak_season_months | JSONB | 旺季月份 [3,4,10,11] |
| last_verified_at | TIMESTAMP | 最后验证时间 |
| verification_source | VARCHAR | official_site / google / manual / ai |
| notes_zh | TEXT | 运营备注 |

用途：① 护栏检查避免安排在定休日 ② 预约困难的实体提前提醒 ③ copywriter 写"建议提前 X 天预约"

#### Scenario: 定休日护栏

- **WHEN** 装配周一行程包含实体 X
- **THEN** 检查 entity_operational_context，若 regular_closed_days 包含 "monday"，触发 hard_fail

### Requirement: 交通卡券推荐表

系统 SHALL 创建 `transport_pass_recommendations` 表。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 主键 |
| pass_name_zh | VARCHAR | 卡券中文名 |
| pass_name_en | VARCHAR | 英文名 |
| city_codes | JSONB | 适用城市 |
| price_cny | INT | 价格（人民币折算） |
| valid_days | INT | 有效天数 |
| covers_lines | JSONB | 覆盖线路 |
| best_for_scenario | TEXT | "适合在东京连续 3 天以上使用地铁的游客" |
| purchase_location | TEXT | "可在成田/羽田机场购买" |
| notes_zh | TEXT | 使用注意事项 |
| updated_at | TIMESTAMP | 更新时间 |

用途：① 行程装配后自动推荐最划算的交通卡 ② 交付页交通模块展示

#### Scenario: 交通卡推荐

- **WHEN** 5 日东京行程装配完成，每天使用地铁 3+ 次
- **THEN** 推荐 Tokyo Subway Ticket 72 小时券，并在交付页交通模块展示

### Requirement: 城市上下文数据维护流程

城市上下文数据 SHALL 通过以下方式维护：

1. **初始种子**：人工整理 + AI 辅助提取（从 JNTO/官方网站/Google Places）
2. **定期刷新**：每月 batch job 校验 entity_operational_context 的 last_verified_at
3. **事实抽取**：AI 从实体描述和评论中提取定休日/预约信息，人工确认后入库
4. **冲突检查**：当 AI 提取结果与现有数据冲突时，标记为 needs_review

#### Scenario: AI 事实抽取

- **WHEN** AI 从某餐厅 Google 评论中提取到"周三定休"
- **THEN** 创建一条 pending_review 记录，管理员确认后写入 entity_operational_context
