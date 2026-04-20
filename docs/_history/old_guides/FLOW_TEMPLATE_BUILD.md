# 模板构建流程

> 从零到交付一个可用的 day 模板,要经过的步骤。

## 大阶段

```
选素材 → 写骨架 → 填文案 → 自检 → 入库
```

## 细分步骤

| 步 | 在做什么 | 产物 |
|---|---|---|
| 1. 选 core_entity | 从景点池挑 score ≥ 4.0 的 S 级 | 定下 1-2 个灵魂景点 |
| 2. 判类型 | 常规/人群替代/季节/日期锁定/小众/文化深度/两日 | 选 7 类之一 |
| 3. 地理分区 | 同区域排同一天,不来回跑 | 骨架区域 |
| 4. 四维度交叉搜 | 区域/榜单/体验类型/地理扫描 | 候选素材 |
| 5. 写 flow 引用 | 时间 + entity_id / meal_type / 自然语言 | flow 数组 |
| 6. 补 flow detail | 进入方式 + 关键画面 + 局部 Plan B | 每条 flow ≥ 30 字 |
| 7. 补灵魂细节 | 10% 惊喜 moment(小店/老铺/本地氛围) | 让这一天被记住的部分 |
| 8. 体力预演 | 步行距离/累积疲劳/节奏弹性 | 调序或砍条目 |
| 9. 写 story | 七要素(时间/坑点/原因/画面/本地视角/替代/贴士) | ≥ 150 字专家密度文案 |
| 10. 跨天自检 | core_entities 不重复 + 菜系不连天重 | 机械检查通过 |
| 11. 人感复核 | B 是否够惊喜 / 有无温度 / 峰值合理 | 人工复核通过 |
| 12. 入库 | 存进 `content/<circle>/<city>/days/{template_id}.json` | 可被装配引擎消费 |

## 和内容池的关系

模板只写**引用和自然语言描述**,具体的餐厅/酒店/店铺**全在内容池里**。

```
模板 flow detail:                       内容池候选:
"高台寺附近,京料理小馆级别" ───────→ restaurants.json 里 area=东山、cuisine_tag=京料理、
                                        budget_tier=middle 的所有条目
                                               ↓
                                        Opus 装配时读模板描述 + 候选字段 + editor_note,
                                        自己决定选哪家
```

模板不写具体餐厅名。具体选哪家是 Opus 的事。

## 文档去哪找

| 要做的事 | 读哪份 |
|---|---|
| 完整 SOP | [templates/TEMPLATE_CREATION_GUIDE.md](templates/TEMPLATE_CREATION_GUIDE.md) |
| 字段长什么样 | [SCHEMA.md](SCHEMA.md) §1 |
| 内容池怎么写 | [templates/CONTENT_POOL_WRITING_GUIDE.md](templates/CONTENT_POOL_WRITING_GUIDE.md) |
| 季节模板 | [templates/SEASONAL_SYSTEM_DESIGN.md](templates/SEASONAL_SYSTEM_DESIGN.md) |
| 数据从哪采 | [data-engineering/](data-engineering/) |

## 产出质量底线

**一个真实的日本旅行顾问看到方案会不会认可。** 写不出"为什么这家餐厅即便不贵也值得专门安排"的理由 = 不合格。story 只是路线描述(不是专家密度)= 不合格。没有 10% 惊喜 moment = 不合格。
