# Naming Conventions（AI 版）

## 保持现有约定
- Python：snake_case / PascalCase / UPPER_SNAKE_CASE
- TypeScript：组件 PascalCase，工具 camelCase
- DB：表和列 snake_case

## 新文档与新配置建议命名
- 人类文档：数字前缀 + snake_case
- AI 文档：功能直名，如 `single_source_of_truth.yaml`
- 规则文件：`*_rules_v1.json`
- 方案树文件：`*_families_v1.json`
- 时间扩展包：`time_expansion_pack_*.json`

## 命名原则
- 产品前台名称不要等于后台字段名
- 后台维度名称要可组合、可映射、可扩展
