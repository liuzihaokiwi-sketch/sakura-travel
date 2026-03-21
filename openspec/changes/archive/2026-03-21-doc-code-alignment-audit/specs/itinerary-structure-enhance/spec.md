## ADDED Requirements

### Requirement: 总纲页数据结构占位
assembler 输出的 `plan_metadata` SHALL 包含 `overview_page` 字段，用于后续总纲页渲染。该字段在本阶段 MUST 自动从行程数据汇总生成。

#### Scenario: 总纲页自动生成摘要
- **WHEN** `assemble_trip` 完成行程装配
- **THEN** `plan_metadata.overview_page` 包含 `{ cities: [...], total_days, highlight_entities: top3, theme_summary }` 结构

#### Scenario: 总纲页字段不影响现有渲染
- **WHEN** renderer 读取 plan_metadata 进行渲染
- **THEN** 如果模板不引用 `overview_page`，渲染不受影响（向后兼容）

### Requirement: 条件页触发占位
assembler 输出的 `plan_metadata` SHALL 包含 `conditional_pages` 列表，标识哪些条件页应当渲染（如雨天 PlanB、温泉礼仪等）。本阶段仅做数据占位，不实际触发渲染。

#### Scenario: 条件页列表自动填充
- **WHEN** 行程包含温泉类实体（entity_type=poi, tags 包含 onsen_relaxation≥3）
- **THEN** `conditional_pages` 列表包含 `{ page_type: "onsen_etiquette", trigger: "entity_tag" }`

#### Scenario: 无触发条件时为空列表
- **WHEN** 行程不包含任何触发条件页的实体
- **THEN** `conditional_pages` 为空列表 `[]`