# 大阪模板数据补全任务

## 背景

请先阅读以下文件了解项目上下文：
- `data/kansai_spots/templates/selection_rules.md` — 酒店/餐厅/店铺选择规则
- `data/kansai_spots/templates/osaka_full_5.5d.md` — 大阪完整行程设计
- `data/kansai_spots/templates/osaka_tips.md` — 大阪实用小技巧
- `data/kansai_spots/templates/osaka_seasonal_events.md` — 季节活动

再阅读以下JSON文件了解现有数据和格式：
- `data/kansai_spots/templates/osaka/manifest.json` — 模板入口
- `data/kansai_spots/templates/osaka/base_schedule.json` — 日程骨架
- `data/kansai_spots/templates/osaka/meals.json` — 餐厅数据（部分完成）
- `data/kansai_spots/templates/osaka/shops.json` — 店铺数据（部分完成）
- `data/kansai_spots/templates/osaka/hotels.json` — 酒店数据（部分完成）
- `data/kansai_spots/templates/osaka/ratings.json` — 多维评级
- `data/kansai_spots/templates/osaka/rules.json` — 规则集
- `data/kansai_spots/templates/osaka/seasonal_events.json` — 季节活动

## 任务

读完以上文档后，你会发现JSON文件中有很多 `_todo`、`待排`、`待补采` 的字段。请并行启动agent把这些全部补全。

另外新建 `reviews.json` 和 `poi_extras.json`：
- `reviews.json`：所有已推荐的餐厅/酒店/活动的专业点评（排队/推荐菜/口味/注意/环境/一句话总结）
- `poi_extras.json`：每天的拍照打卡点和咖啡休息点

## 规范

遵守 `selection_rules.md` 和 `CLAUDE.md` 中的所有规范。数据必须来自真实搜索，不允许编造。
