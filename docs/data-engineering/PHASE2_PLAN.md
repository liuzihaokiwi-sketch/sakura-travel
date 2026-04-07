# Phase 2: Selection Ledger + Evidence Generation

> 版本: 2.0 (重写)
> 更新: 2026-04-01
> 前置: 发现池已完成 + 数据归一化(MASTER_GUIDE 3.1节)已执行
> 输入: 归一化后的候选池 CSV (restaurants/hotels/spots)
> 输出: selection_ledger.json (主) + GUIDE_*.md (审稿层)

---

## 一、核心原则

### 1. Sonnet 批量结构化短证据 + Opus 审关键条目

不对每个候选写 500-800 字长证据。改为:
- 每条生成**结构化证据块**: 120-220 字正文 + JSON 字段
- Sonnet 做批量生成（速度+成本）
- Opus 只审四类关键条目（判断力花在刀刃上）

### 2. 先用现有字段跑第一轮，不先做全量爬取

不为 Phase 2 先做一轮大爬取。用归一化后的现有数据跑第一版 selection ledger。
只对触发项补抓:
- traveler_fit 证据明显缺失
- risk_watch 被触发
- 同一 slot 内竞争很挤，需要 tie-break
- mid/budget/street 缺口明显

### 3. editorial_exclusion 纳入主流程

```
候选 → 结构化证据 → 初排 → editorial_exclusion / risk_watch → 终排
```

不是"先正向选完，再顺手删几个"。

### 4. JSON 为主输出，Markdown 为审稿层

- 主输出: `*_selection_ledger.json` — 系统和后续脚本消费
- 副输出: `GUIDE_*.md` — 给编辑审稿

---

## 二、Phase 2A: 纯 Python 预处理（不调 API）

> 前置条件: MASTER_GUIDE 3.1 节的 N1-N5 归一化步骤已完成

### 2A-1. 计算 base_quality_score

按 MASTER_GUIDE 四b章 "Base Quality Score 计算铁律" 执行:
- 餐厅: 组内 percentile（city × cuisine × budget_tier），不做全局 min-max
- 酒店: OTA/Keys 评分做主轴，hotel_type/features 只做修正
- 景点: japan_guide_level 映射 + 城市特色加成

### 2A-2. 计算 indie_support_score

按 MASTER_GUIDE 八章独立站规则:
- 从 source/mention_count 字段推算
- 前2条满权重，第3条起×0.5，封顶0.5

### 2A-3. Slot 分组

```
餐厅 slot: {city_code}_{corridor}_{cuisine_normalized}_{budget_tier}
酒店 slot: {city_code}_{area}_{hotel_type}_{price_level}
景点 slot: {city_code}_{area}_{sub_type}
```

### 2A-4. City-relative Percentile + Same-slot Cap

样本量门槛（MASTER_GUIDE 六章）:
- >=15: 取前 10-20%
- 6-14: 固定 top N + editorial
- <6: editorial only

Same-slot cap: 每 slot 最多 3 家

### 2A-5. 标记 Phase 2B 候选

Phase 2A 输出每条候选的状态:
```
selected     — 入选（需要 Sonnet 证据）
borderline   — 边界（需要 Sonnet 证据 + 可能 Opus 审）
excluded     — 淘汰（不调 API）
needs_editorial — 小样本组，待编辑判断
```

预计进入 Phase 2B 的数量: 250-400 条（不是全量 1200+）

---

## 三、Phase 2B: evidence_extraction（真实来源抽取 + 规则化生成）

> **铁律：evidence 字段不由 AI 编写。AI 只做编辑判断，不做事实陈述。**
> Structured Outputs 只保证格式一致，不保证事实是真的。

### 3.1 quality_evidence — 规则化生成，不调 AI

直接用已有真实信号按模板生成：

```python
# 餐厅（已有 tabelog_score + percentile）
f"Tabelog {score}，{city}×{cuisine}类组内前{pct:.0%}"
# 有 michelin 则追加: "，{michelin}"
# 无 tabelog: f"来源: {source}，{budget_tier}层候选"

# 酒店（已有 michelin_keys / ota_rating）
f"MICHELIN {n} Keys"  # 或 f"OTA ★{rating}（{count}件）"

# 景点（已有 japan_guide_level）
f"japan-guide {level}，{sub_type}类"
```

### 3.2 traveler_fit_evidence — 仅对 shortlist 真实抓取

**只对 selected + borderline（约 362 条）补抓，不做全量。**

```
来源（按优先级）:
  携程 Trip.com: 搜索该景点/餐厅/酒店，取评分+评论数+TOP评论关键词
  小红书: WebSearch "{name_ja} 攻略" / "{name_ja} 值得吗"
  Google Maps: 评分 + 评论数（官方定义: 已发布评分的平均值）

没有找到真实来源 → traveler_fit_modifier=0, evidence=null，不猜测
```

### 3.3 execution_evidence — 从官网/Google Maps 抓取

```
对 shortlist 抓取: 营业时间、定休日、预约方式、常见排队时间
没有真实来源 → execution_penalty=0, evidence=null
```

### 3.4 data_confidence 重新判定

```
single_source:  只有一个轴有真实来源（如仅 japan-guide，无携程/Google）
cross_checked:  quality + traveler_fit 或 quality + execution 有真实来源
verified:       三轴均有真实来源
ai_generated:   无任何真实来源 — 不可进入 Guide
```

> 关西教训: spots_ledger 里 source="japan-guide" 的条目被标为 cross_checked，这是错的。
> 单源必须标 single_source，等补了携程/Google 才能升级为 cross_checked。

---

## 四、Phase 2C: editorial_annotation（仅最终入选条目）

> **这才是 AI 可以参与的步骤。** 编辑判断不是事实陈述。

### 适用范围（四类，预计 60-100 条）

1. **所有 S/A 候选** — 写 one_line_editorial_note + selection_tags
2. **边界升级项** — percentile 在 cutoff ±5% 的 borderline 条目，判断升降
3. **risk_watch >= medium** — 确认风险评估，决定是否排除
4. **slot 超载组** — 同一 slot 超过 3 家，做最终取舍

AI 在此步骤的输入：**真实证据摘要**（quality_evidence + traveler_fit_evidence + execution_evidence，均来自真实来源）。AI 的输出：**判断**（grade、editorial_note、exclusion 决定）。

### 输出结构

```json
{
  "grade": "S",
  "selection_tags": ["city_icon", "local_benchmark"],
  "one_line_editorial_note": "京都怀石最高峰，午餐8000起是性价比入口",
  "editorial_exclusion": false,
  "editorial_exclusion_reason": null,
  "opus_reviewed": true
}
```

### 成本估算

```
每条: ~800 input（喂真实证据摘要）+ ~200 output（只输出判断）= ~1000 tokens
80 条: ~80,000 tokens
Opus 单价: 约 $0.015/1K input + $0.075/1K output
估计总成本: ~$3-5 (Opus)
```

---

## 五、Phase 2D: 生成 Selection Ledger

### 输出文件

```
data/kansai_spots/
├── restaurants_selection_ledger.json   # 150-200 条入选
├── hotels_selection_ledger.json        # 80-120 条入选
├── spots_selection_ledger.json         # 80-100 条入选
└── selection_excluded.json             # 被排除的候选 + 排除理由
```

### Ledger 结构

```json
{
  "version": "2.0",
  "generated_at": "2026-04-02T00:00:00+09:00",
  "city_circle": "kansai",
  "summary": {
    "total_candidates": 1243,
    "selected": 350,
    "excluded": 893,
    "by_grade": {"S": 12, "A": 45, "B": 120, "C": 173},
    "by_city": {"kyoto": 130, "osaka": 100, ...}
  },
  "entries": [
    {
      "name_ja": "...",
      "city_code": "...",
      "cuisine_type": "...",
      "budget_tier": "...",
      "corridor": "...",
      "selection_slot": "...",
      "base_quality_score": 4.8,
      "quality_evidence": "...",
      "traveler_fit_modifier": 0.25,
      "traveler_fit_evidence": "...",
      "execution_penalty": -0.25,
      "execution_evidence": "...",
      "risk_watch": "mild",
      "indie_support_score": 0.35,
      "house_score": 5.15,
      "grade": "S",
      "selection_tags": ["city_icon", "local_benchmark"],
      "editorial_exclusion": false,
      "one_line_editorial_note": "...",
      "score_basis": "tabelog_percentile",
      "opus_reviewed": true,
      "data_confidence": "single_source"
    }
  ]
}
```

---

## 六、Phase 2E: Markdown Review Guide（审稿层）

从 ledger 编译，给编辑审:

```
GUIDE_RESTAURANTS.md — 按城市 → 走廊 → 预算层组织
GUIDE_HOTELS.md     — 按城市 → 区域 → 价位组织
GUIDE_SPOTS.md      — 按城市 → 走廊 → 类型组织
```

Guide 是审稿短名单（150-200 餐厅、80-120 酒店、80-100 景点），不是后台主库总量。
后台主库会比 Guide 大（更多 B/C 级备选），但 Guide 是编辑审核的入口。

---

## 七、执行顺序与检查点

```
Phase 2A (纯 Python，不调 API)
  ├── N1-N5 归一化 → 检查: cuisine唯一值<40, price_level分布合理
  ├── base scores → 检查: 每条有score, 分布不全挤一个区间
  ├── slot 分组 → 检查: 每slot最多3条
  └── 标记候选 → 检查: selected+borderline 在 250-400 范围

Phase 2B (Sonnet 批量)
  └── 结构化证据 → 检查: JSON schema 100% 通过, evidence 非空

Phase 2C (Opus 审核)
  └── 关键条目审 → 检查: S/A 全部reviewed, slot冲突全部resolved

Phase 2D (Ledger)
  └── JSON 输出 → 检查: grade 分布合理, 每城市覆盖率>80%

Phase 2E (Guide)
  └── Markdown → 检查: 一个日本旅行顾问审稿会认可
```

---

## 八、触发项补抓规则

Phase 2B 过程中发现以下情况时，触发定向补抓（不做全量）:

| 触发条件 | 补抓范围 | 方式 |
|---------|---------|------|
| traveler_fit 证据全组缺失 | 该城市该菜系的携程/小红书 | WebSearch |
| risk_watch >= medium 但证据不足 | 该店的近期评论 | WebFetch |
| 同 slot 3+ 家且 tie-break 无依据 | 该 slot 的 Tabelog 详情页 | WebFetch/OpenCLI |
| 某城市某预算层缺口明显 | 该城市的 Tabelog 分品类排名 | WebSearch |

补抓结果回填到 ledger，不单独生成新文件。

---

## 九、预期产出数量

### Selection Ledger (审稿短名单)

| 品类 | 数量 | 备注 |
|------|------|------|
| 餐厅 | 150-200 | 覆盖主要城市×走廊×预算层 |
| 酒店 | 80-120 | 覆盖主要城市×区域×价位 |
| 景点 | 80-100 | 覆盖主要城市×走廊×类型 |

### Grade 分布目标

| Grade | 餐厅 | 酒店 | 景点 |
|-------|------|------|------|
| S | 10-15 | 5-8 | 10-15 |
| A | 30-40 | 15-25 | 20-30 |
| B | 60-80 | 30-50 | 30-40 |
| C | 50-65 | 30-37 | 20-15 |
