# Spec: ai-copywriter

## 概述

AI 文案润色层在行程装配完成后，用 GPT-4o-mini 为每个实体生成一句话中文描述和旅行 Tips。LLM 只改表达，不改事实，所有事实信息已由 Catalog 数据锁定。

---

## Prompt 规格

### 系统 Prompt

```
你是一位专业的日本旅游文案编辑。请根据提供的景点信息，用简洁优美的中文写出：
1. 一句话描述（25-40字）：突出最核心的体验感，有画面感，不要介绍性的废话
2. 旅行 Tips（15-25字）：最实用的一条建议（时间/排队/必看/注意）

严格规则：
- 只使用提供的信息，不要添加任何未提供的内容
- 不要以"这里"/"该景点"/"它"开头
- 不要出现"著名"/"知名"/"有名"等形容词
- 描述要有温度，像朋友推荐一样
```

### 用户 Prompt 模板

```
景点名称：{name_zh}
类型：{entity_type}（{primary_type}）
城市：{city}，区域：{area}
标签：{tags}（如：文化历史/拍照圣地）
Google 评分：{rating}（{review_count} 条评价）
编辑备注：{editorial_reason}（如有）

请输出 JSON：
{{"copy_zh": "...", "tips_zh": "..."}}
```

---

## 缓存策略

- 缓存 Key：`copywriter:{entity_id}:{scene}`
- TTL：7 天
- 场景不同（couple/family/solo）可能有不同文案，分开缓存
- 人工录入的 `editorial_reason` 优先于 AI 生成

---

## 降级方案

若 GPT 调用失败或超时（3s）：
- `copy_zh` = `entity.description_zh`（Catalog 原始描述）
- `tips_zh` = `"建议提前查看官方开放时间"`

---

## 验收标准

- [ ] `generate_copy(entity_id, scene)` 函数实现，调用 GPT-4o-mini
- [ ] 输出格式校验（JSON with copy_zh + tips_zh）
- [ ] 缓存命中时不重复调用 GPT
- [ ] 降级逻辑正常（GPT 失败时不阻塞装配流程）
- [ ] 人工 editorial_reason 优先展示
