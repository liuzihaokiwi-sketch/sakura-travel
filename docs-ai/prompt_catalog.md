# Prompt Catalog

| 位置 | 用途 | 模型 | 输入 | 输出 |
|---|---|---|---|---|
| `app/domains/catalog/tagger.py` | 9 维主题亲和度标签生成 | GPT-4o-mini (via OpenAI) | 实体名称+类别+描述 | `{shopping: 0-100, food: 0-100, ...}` |
| `app/domains/planning/copywriter.py` | 实体一句话描述+Tips | GPT-4o-mini (via OpenAI) | 实体详情+场景 | `{copy_zh: str, tips_zh: str}` |
| `app/domains/intake/intent_parser.py` | 自然语言意图解析 | 配置的 AI 模型 | 用户自由文本 | `TripIntentResult`（结构化行程意图） |
| `app/domains/catalog/ai_generator.py` | AI 生成实体数据（离线模式） | claude-opus-4-6 | 城市+数量要求 | POI/餐厅/酒店 JSON 列表 |

## Prompt 模板详情

### tagger.py — 标签生成 Prompt
- **System**: 日本旅游数据标注专家
- **User**: 包含实体名称、类别、描述，要求输出 9 维评分 JSON
- **9 维度**: shopping, food, culture_history, onsen_relaxation, nature_outdoors, anime_pop_culture, family_kids, nightlife_entertainment, photography_scenic
- **输出格式**: JSON array，每项含 entity_name + 9 个 0-100 分数

### copywriter.py — 文案润色 Prompt
- **System**: 日本旅游文案编辑
- **User**: 实体信息（名称/类别/评分/标签/场景）
- **输出**: `copy_zh`（25-40字一句话描述）+ `tips_zh`（15-25字实用建议）
- **缓存**: Redis key=`copywriter:{entity_id}:{scene}`，TTL=7天
- **降级**: GPT 超时(3s)或失败 → 返回 Catalog 原始描述

### intent_parser.py — 意图解析 Prompt
- **System**: 旅行规划意图识别
- **User**: 用户自由文本消息
- **输出**: 目的地、天数、同行人、预算、偏好标签等结构化数据