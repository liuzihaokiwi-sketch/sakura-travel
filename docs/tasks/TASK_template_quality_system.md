# 任务：模板质量三层保障系统

> 角色：主程序员
> 优先级：高
> 依赖：data/kansai_spots/templates/osaka/ 下的现有模板文件

---

## 背景

旅行手账本用"模板+微调"架构，每个城市有一组 JSON 模板文件（base_schedule.json、meals.json、hotels.json、shops.json、rules.json 等），存放在 `data/{circle}/templates/{city}/` 下。

模板由 AI 辅助编写，但已出现规则违反——rules.json 明确写了 `no_chinese`（不推荐中华料理），但 meals.json 里出现了"中国料理 燦宮"。原因是规则和数据是独立文件，没有强制校验。

需要建三层质量保障。

---

## 第1层：AI 生成时的约束（不需要写代码）

工作流层面的，确保 AI 写模板时上下文里有完整规则。不在本任务范围内。

## 第2层：rules_checkable.json + validate_template.py

### rules_checkable.json

从 rules.json 中提取机器可执行的规则子集。放在 `data/kansai_spots/templates/osaka/` 下（每个城市一份，因为规则可能有城市差异）。

需要覆盖的检查类别：

- 菜系黑名单（no_chinese 等）
- 同天菜系不重复（午餐≠晚餐）
- 跨天菜系不连续重复
- 粉物不连吃（拉面/乌冬/大阪烧/荞麦）
- 通用菜系全程上限（拉面≤2次等）
- showcase meal 上限（每城≤1、全程≤2）
- 区域约束（餐厅在当天活动区域内）
- 预算约束（经济档不出现高档餐）
- 数据完整性（必填字段：entity_hint、建议有 name_zh、entity_id）
- 预约难度过滤（排除名单里的店不应出现）

**核心原则：规则从 JSON 读取，不硬编码在 Python 里。** 符合 CLAUDE.md "配置驱动不硬编码"。

### validate_template.py

放在 `scripts/` 下。功能：

- 读取某个城市模板目录下所有 JSON + 对应的 rules_checkable.json
- 逐条检查规则
- 输出报告：PASS / WARNING / ERROR，标明具体文件、条目、违反的规则
- 支持单城市 `python scripts/validate_template.py --city osaka --circle kansai`
- 支持批量 `python scripts/validate_template.py --all`

## 第3层：review_prompt_template.md

存在 `data/kansai_spots/templates/` 下。给 Sonnet 用的体验级审核 prompt。审核方向（不是查规则，规则第2层已查）：

- 情绪弧线是否合理（day_mood / day_arc 连续两天不雷同）
- A/B 搭配是否有惊喜感（B 不是"同类型但没那么有名"）
- 人群日体验是否一体化（餐饮配合活动主题）
- 有没有连续几天同类型体验
- 峰值设计是否到位（大峰值数量、铺垫→绽放→余韵）
- 每天有没有"靠自己搜不到的 moment"

---

## 额外：修复燦宮问题

`meals.json` 里 `umeda_day1_lunch.premium.A` 的"中国料理 燦宮"违反 no_chinese 规则。替换为合适的梅田区域 premium 午餐。要求：
- 非中华料理
- 梅田步行范围内
- premium 档位（300+ CNY）
- 搜索真实数据选一家，不编造

---

## 参考文件

- 规则：`data/kansai_spots/templates/osaka/rules.json`
- 餐厅：`data/kansai_spots/templates/osaka/meals.json`
- 骨架：`data/kansai_spots/templates/osaka/base_schedule.json`
- 通用指引：`data/kansai_spots/templates/TEMPLATE_CREATION_GUIDE.md`
- 项目规范：`CLAUDE.md`

---

## 开始之前

如果你对方案有不同意见或更好的做法，在回复开头用 3-5 行简要说明，然后直接开始实现你认为最好的版本。不需要等确认。
