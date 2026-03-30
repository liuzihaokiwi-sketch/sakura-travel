# AI 模型分配策略

> 原则：用最便宜的模型完成能完成的任务，只在需要判断力的环节用强模型。
> 不是"哪个模型最好"，而是"这个任务的最低能力要求是什么"。

---

## 一、可用模型 & 特性

| 模型 | 强项 | 弱项 | 成本 | 适合场景 |
|------|------|------|------|---------|
| **GPT-4o** | 想象力、创意文案、多语言翻译 | 结构化输出偶尔不稳 | 中 | 创意规划、文案生成、翻译 |
| **Claude Opus** | 严谨分析、长文理解、复杂推理、质量审核 | 贵 | 高 | 质量门控、复杂决策、最终审核 |
| **Claude Sonnet** | 均衡、代码能力强、结构化输出稳定 | 创意稍弱 | 中 | 数据处理、评论提取、标签生成 |
| **Claude Haiku** | 快、便宜、简单任务够用 | 复杂推理弱 | 低 | 分类、格式转换、简单校验 |
| **DeepSeek V3** | 中文理解强、便宜、推理能力不错 | 英文/日文弱一些 | 低 | 中文内容处理、中国城市数据 |
| **Qwen (通义千问)** | 中文极强、阿里生态、免费额度大 | 创意一般 | 极低 | 大量中文文本处理、兜底 |

---

## 二、按数据生命周期阶段分配

### 阶段 1：发现（Discovery）

| 任务 | 模型 | 原因 |
|------|------|------|
| 从攻略网页提取地点名称列表 | **Haiku / Qwen** | 纯提取任务，不需要判断力 |
| 判断提取的名称是景点/餐厅/酒店 | **Haiku** | 简单分类 |
| 多源候选去重（名称相似度判断） | **代码逻辑** | 不用 AI，用 Levenshtein + 规则 |

### 阶段 2：采集（Collection）

| 任务 | 模型 | 原因 |
|------|------|------|
| 爬虫数据解析 | **代码逻辑** | 不用 AI，HTML 解析用代码 |
| 日文名 → 中文名翻译 | **GPT-4o** | 多语言翻译 GPT 最稳 |
| 从非结构化攻略文本提取结构化字段 | **Sonnet** | 结构化输出稳定 |

### 阶段 3：清洗（Cleaning）

| 任务 | 模型 | 原因 |
|------|------|------|
| 去重合并 | **代码逻辑** | dedup engine，不用 AI |
| 坐标/评分异常检测 | **代码逻辑** | 规则判断，不用 AI |
| 判断是否旅游相关实体（过滤医院/加油站） | **Haiku** | 简单判断 |
| 营业状态检测 | **代码逻辑** | Google Places API 字段 |

### 阶段 4：整合（Integration）

| 任务 | 模型 | 原因 |
|------|------|------|
| 评分归一化 | **代码逻辑** | 数学公式，不用 AI |
| 从评论提取维度评分 | **Sonnet** | 需要理解评论语义，但量大需要性价比 |
| 从评论生成一句话摘要 | **Sonnet** | 文本总结，Sonnet 够用 |
| 从评论判断评价是否有信息量（过滤无脑好评/差评） | **Haiku** | 简单判断 |
| 从攻略原文提取标签 | **DeepSeek / Qwen**（中文攻略） / **Haiku**（日英攻略） | 分语言用不同模型 |
| 城市特色菜系提取 | **Sonnet** | 需要理解"什么是这个城市的特色" |

### 阶段 5：加工（Processing）

| 任务 | 模型 | 原因 |
|------|------|------|
| 活动簇 anchor 实体选择 | **代码逻辑** | 按评分排序选 top N |
| 用户-实体匹配（标签过滤+评分排序） | **代码逻辑** | 规则引擎 |
| 用户-实体匹配（AI 个性化判断 top 20） | **Sonnet** | 需要理解用户偏好，但不需要最强模型 |
| 生成推荐理由（match_reason） | **GPT-4o** | 创意文案 GPT 更自然 |

### 阶段 6：编排（Orchestration）

| 任务 | 模型 | 原因 |
|------|------|------|
| 骨架构建 | **代码逻辑** | 算法，不用 AI |
| 主活动排序 | **代码逻辑** | scorer 评分 |
| 次要活动填充 | **代码逻辑** | 按时间余量+地理距离 |
| 餐食分配 | **代码逻辑 + Haiku** | 基础匹配用代码，菜系多样性判断可用 Haiku |
| Plan B 生成 | **Sonnet** | 需要理解"为什么这个是好的替代" |
| 整体行程合理性检查 | **Opus** | 最关键的质量门控，需要最强判断力 |

### 阶段 7：渲染（Rendering）

| 任务 | 模型 | 原因 |
|------|------|------|
| 每日主题文案 | **GPT-4o** | 创意性强，"港町漫步日"这种需要想象力 |
| 实用提示文案 | **不用 AI** | 直接用 practical_tip 字段 |
| 行前准备页/退税说明等固定内容 | **不用 AI** | 模板化内容 |
| 最终文案润色 | **GPT-4o** | 文字风格统一 |
| 最终质量审核（全文检查） | **Opus** | 找逻辑漏洞、时间冲突、事实错误 |

---

## 三、质量门控：多模型交叉审核

行程生成完成后，用不同模型做不同维度的审核：

```
┌──────────────────────────────────────┐
│          生成完成的行程                │
└───────────────┬──────────────────────┘
                │
    ┌───────────┼───────────────┐
    ▼           ▼               ▼
┌────────┐ ┌────────────┐ ┌──────────┐
│ Haiku  │ │ Sonnet     │ │ Opus     │
│ 快速检查│ │ 逻辑检查    │ │ 深度审核  │
│        │ │            │ │          │
│·时间是否│ │·路线是否合理│ │·整体体验  │
│ 连续    │ │·同类型是否  │ │ 是否好    │
│·营业时间│ │ 太密集     │ │·推荐理由  │
│ 是否对  │ │·预算是否    │ │ 是否令人  │
│·格式是否│ │ 超标       │ │ 信服      │
│ 正确    │ │·餐食间隔   │ │·有没有    │
│        │ │ 是否合理    │ │ 明显遗漏  │
│ 0.5秒  │ │·交通衔接   │ │·是否值    │
│ $0.001 │ │ 是否可行    │ │ 298元    │
│        │ │            │ │          │
│        │ │ 2秒        │ │ 5秒      │
│        │ │ $0.01      │ │ $0.05    │
└───┬────┘ └─────┬──────┘ └────┬─────┘
    │            │              │
    ▼            ▼              ▼
  pass/fail   pass/fail     pass/fail + 具体修改建议
```

**只有三层都 pass 才发布。**
Haiku 不过 → 格式/基础错误，自动修复后重跑。
Sonnet 不过 → 逻辑问题，重新编排后重跑。
Opus 不过 → 体验问题，人工介入或重新生成。

---

## 四、成本估算

按一个 5 天北海道行程计算：

| 环节 | 模型 | 调用次数 | 单次成本 | 小计 |
|------|------|---------|---------|------|
| 城市特色菜系提取 | Sonnet | 1 | $0.01 | $0.01 |
| 评论维度提取（50实体×1次） | Sonnet | 50 | $0.01 | $0.50 |
| 一句话摘要生成（50实体） | Sonnet | 50 | $0.005 | $0.25 |
| 标签提取 | Haiku/Qwen | 50 | $0.001 | $0.05 |
| 翻译（日→中） | GPT-4o | 20 | $0.01 | $0.20 |
| 用户匹配（top20） | Sonnet | 1 | $0.02 | $0.02 |
| 推荐理由生成 | GPT-4o | 15 | $0.01 | $0.15 |
| Plan B | Sonnet | 5 | $0.01 | $0.05 |
| 每日主题文案 | GPT-4o | 5 | $0.02 | $0.10 |
| 最终文案润色 | GPT-4o | 1 | $0.05 | $0.05 |
| 质量门控 Haiku | Haiku | 1 | $0.002 | $0.002 |
| 质量门控 Sonnet | Sonnet | 1 | $0.02 | $0.02 |
| 质量门控 Opus | Opus | 1 | $0.10 | $0.10 |
| **总计** | | | | **≈ $1.50** |

**每单 AI 成本约 ¥10**，对比售价 ¥298，AI 成本占 3.4%，完全可控。

注意：评论维度提取是一次性的（提取完存 DB，后续复用），不是每生成一个行程都跑。
实际每单运行时的 AI 成本只有匹配+编排+文案+审核部分，约 **¥5/单**。

---

## 五、代码实现

### 模型路由器

```python
# app/core/ai_router.py

from enum import Enum
from app.core.config import get_settings

class ModelTier(str, Enum):
    CREATIVE = "creative"       # GPT-4o：创意、翻译、文案
    ANALYTICAL = "analytical"   # Sonnet：分析、提取、结构化
    JUDGE = "judge"             # Opus：质量审核、复杂决策
    FAST = "fast"               # Haiku：简单分类、格式校验
    CHEAP_CN = "cheap_cn"       # DeepSeek/Qwen：大量中文处理

# 各 tier 对应的模型配置
MODEL_CONFIG = {
    ModelTier.CREATIVE: {
        "provider": "openai",
        "model": "gpt-4o",
        "base_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "max_tokens": 4000,
        "temperature": 0.7,
    },
    ModelTier.ANALYTICAL: {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "base_url": "https://api.anthropic.com",
        "env_key": "ANTHROPIC_API_KEY",
        "max_tokens": 4000,
        "temperature": 0.3,
    },
    ModelTier.JUDGE: {
        "provider": "anthropic",
        "model": "claude-opus-4-20250514",
        "base_url": "https://api.anthropic.com",
        "env_key": "ANTHROPIC_API_KEY",
        "max_tokens": 4000,
        "temperature": 0.2,
    },
    ModelTier.FAST: {
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "base_url": "https://api.anthropic.com",
        "env_key": "ANTHROPIC_API_KEY",
        "max_tokens": 1000,
        "temperature": 0.2,
    },
    ModelTier.CHEAP_CN: {
        "provider": "dashscope",
        "model": "deepseek-v3",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "env_key": "DASHSCOPE_API_KEY",
        "max_tokens": 4000,
        "temperature": 0.3,
    },
}

async def ai_call(
    prompt: str,
    tier: ModelTier,
    system: str = "",
    **kwargs,
) -> str:
    """
    统一 AI 调用入口。
    根据 tier 自动选择模型、provider、参数。
    """
    config = MODEL_CONFIG[tier]
    # ... 实现调用逻辑
```

### 任务标记

```python
# 每个用到 AI 的地方标记用哪个 tier

# 评论提取
result = await ai_call(
    prompt=f"从以下评论中提取维度评分...\n{reviews_text}",
    tier=ModelTier.ANALYTICAL,
)

# 翻译
result = await ai_call(
    prompt=f"将以下日文翻译为中文：{name_ja}",
    tier=ModelTier.CREATIVE,
)

# 质量审核
result = await ai_call(
    prompt=f"审核以下行程是否合理...\n{itinerary_json}",
    tier=ModelTier.JUDGE,
)

# 简单分类
result = await ai_call(
    prompt=f"这个名称是景点还是餐厅还是酒店？{name}",
    tier=ModelTier.FAST,
)
```

---

## 六、降级策略

当某个模型 API 不可用时的降级链：

```
CREATIVE:   GPT-4o → Sonnet → DeepSeek
ANALYTICAL: Sonnet → DeepSeek → GPT-4o
JUDGE:      Opus → Sonnet（降级时标记需人工复核）
FAST:       Haiku → Qwen → DeepSeek
CHEAP_CN:   DeepSeek → Qwen → Haiku
```

**JUDGE 层不能降级到 FAST** — 质量审核宁可人工做也不能用弱模型凑合。
