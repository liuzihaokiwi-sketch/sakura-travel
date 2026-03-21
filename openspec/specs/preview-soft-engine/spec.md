## ADDED Requirements

### Requirement: 免费 Day 1 选天引擎

系统 SHALL 实现 preview day selector，从完整行程的 N 天中选出 preview_day1_score 最高的一天作为免费预览，而非固定展示第一天。

选天公式：
```
preview_day1_score = 0.30 × avg_entity_soft_score  # 当天实体的加权平均软规则分（使用 preview_day1 阶段权重）
                   + 0.25 × variety_score           # 当天实体类型丰富度（POI + 餐厅 + 体验 mix）
                   + 0.20 × hero_moment_score        # 是否有 1-2 个记忆点极高的实体
                   + 0.15 × shareability_score       # 当天所有实体的平均 shareability
                   + 0.10 × completeness_score       # 是否包含完整的早中晚餐 + 夜间内容
```

选天护栏：
1. 选出的天 MUST 是"自包含的"——不需要前一天的前置体验才能理解
2. 到达日（第一天）和离开日（最后一天）如果时间碎片化（可用时间 < 6 小时），SHALL 被降权 30%
3. 预览天的 avg_soft_score 与全行程均分的比值 SHALL 不超过 1.5（防止预览太精彩正式版失望）

#### Scenario: 5 日行程选天

- **WHEN** 系统完成 5 日行程装配
- **THEN** 计算每天的 preview_day1_score，选最高分的一天作为免费预览

#### Scenario: 到达日降权

- **WHEN** 第一天为到达日，可用时间仅 4 小时
- **THEN** 第一天的 preview_day1_score 乘以 0.7 降权系数

#### Scenario: 防过度精彩护栏

- **WHEN** 选出的预览天 avg_soft_score = 8.5，全行程均分 = 5.0（比值 1.7 > 1.5）
- **THEN** 该天被跳过，选下一个最高分且比值 <= 1.5 的天

### Requirement: 预览模块露出与锁定策略

系统 SHALL 对免费预览天实施以下露出/锁定策略：

**必须露出的内容**：
- 当天的时间轴骨架（几点到几点做什么）
- 核心 POI 名称和一句话描述
- 交通方式概要（步行/地铁，不含具体线路细节）
- 1-2 张高质量配图
- 餐厅推荐的存在感（"中午推荐了一家..."，但不给店名）

**必须锁定的内容**：
- 具体餐厅名称和地址（显示模糊占位）
- 具体酒店信息
- 详细交通指引（换乘步骤）
- 其他天的内容（完全不可见）
- 实用 Tips 和避坑指南

**半露出内容**（制造好奇心）：
- 显示"Day 2-5 还有 XX 个精选推荐"计数
- 显示其他天的主题标签（如"Day 3: 京都寺庙深度游"）但不展开
- 显示"我们还为你准备了雨天备案"但不展开

#### Scenario: 预览页露出完整性

- **WHEN** 用户查看免费 Day 1 预览
- **THEN** 可见到当天时间轴、POI 名称、配图、餐厅存在感；不可见到具体餐厅名/酒店/交通细节/其他天内容

#### Scenario: 锁定内容有解锁引导

- **WHEN** 用户在预览页点击被锁定的模块
- **THEN** 显示解锁 CTA（"解锁完整攻略 ¥19.9"），不泄露具体内容

### Requirement: 预览 CTA 联动

预览引擎 SHALL 在以下位置插入 CTA 触发点：

1. 餐厅模糊区域旁："查看完整餐厅推荐 →"
2. 当天底部："解锁 Day 2-N 完整行程"
3. 锁定内容区域："解锁雨天备案 / 交通指引 / 酒店推荐"
4. 页面固定底栏："¥19.9 解锁全部 N 天攻略"

CTA 触发点的数量 SHALL 不少于 3 个，不超过 6 个（过多会让用户反感）。

#### Scenario: CTA 数量合理

- **WHEN** 渲染免费预览页面
- **THEN** 页面中包含 3-6 个 CTA 触发点，分布在不同模块旁

### Requirement: 预览评分数据表

系统 SHALL 创建 preview_trigger_scores 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 主键 |
| plan_id | UUID NOT NULL | 关联行程 |
| day_index | INT NOT NULL | 第几天（0-based） |
| avg_entity_soft_score | DECIMAL(5,2) | 实体平均软规则分 |
| variety_score | DECIMAL(5,2) | 丰富度分 |
| hero_moment_score | DECIMAL(5,2) | 高光时刻分 |
| shareability_score | DECIMAL(5,2) | 分享感分 |
| completeness_score | DECIMAL(5,2) | 完成度分 |
| preview_day1_score | DECIMAL(5,2) | 最终预览分 |
| is_selected | BOOLEAN DEFAULT FALSE | 是否被选为预览天 |
| calculated_at | TIMESTAMP | 计算时间 |

索引：plan_id + is_selected

#### Scenario: 评分记录持久化

- **WHEN** 系统计算预览选天后
- **THEN** 所有天的 preview_trigger_scores 被写入表中，被选中的天 is_selected=TRUE
