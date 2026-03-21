## Context

### 第一性原理判断

**用户为什么为日本攻略付费？**
不是为了"信息"——Google Maps、小红书、ChatGPT 都能免费提供信息。用户付费是因为**决策焦虑**：面对海量选择，他们需要一个"替我做判断的靠谱人"。付费的本质是**购买决策确定感**——"跟着这份攻略走，不会踩雷、不浪费时间、会有惊喜"。

**预览为什么成交？**
用户看到 Day 1 时，付费冲动来自三个判断的叠加：
1. **"这人懂我"** → 推荐的地方和我的偏好高度匹配
2. **"这比我自己做得好"** → 推荐理由有证据（评分/步行距离/避坑），排列顺路
3. **"后面肯定更好"** → Day 1 足够好但故意留了悬念（锁住的天数让人想看完整版）

**用户为什么喜欢、复购、转介绍？**
- 喜欢 = 攻略在实际旅行中"可执行"（不会到了发现关门/排队3小时/走冤枉路）
- 复购 = 第一次体验超预期 + 下次旅行时想到"上次那个服务挺好"
- 转介绍 = 攻略的交付形态本身值得分享（长图好看/信息密度高/朋友看了也想要）

**真正的长期壁垒是什么？**
不是 prompt（任何人都能写），不是规则（可以被抄），而是：
**城市上下文数据 × 用户反馈校准 × 评分权重迭代 × 审核经验沉淀**
这四层叠在一起，形成一个随时间增长的数据飞轮，竞品无法快速复制。

### 当前系统状态

已有：完整的 entity_base → scorer → assembler → renderer 管线，35+ ORM 表，三层评分（base/context/editorial），路线模板，护栏检查框架。

缺失（本次设计范围）：

| 模块 | 已有 | 缺失 | 不补会怎样 |
|------|------|------|-----------|
| 产品真相源 | product_sku 表有 features JSONB | 文案/权益/规则分散在前端代码、客服话术、后台逻辑中 | 用户看到的承诺和实际权益不一致 → 客诉 |
| 预览引擎 | assembler 可生成完整行程 | 无独立预览模式，无"选最佳天"逻辑，无预览级校验 | 免费预览质量不稳定 → 转化率低 |
| 自助微调 | 无 | 完全缺失 | 所有修改靠人工 → 单效率极低 |
| 城市上下文 | entity_base 有 area_name, city_code | 无时段/季节/天气/客群维度数据 | AI 推荐"下午去筑地市场"（实际上午就关了）→ 信任崩塌 |
| 软规则 | scorer.py 有维度权重 | 权重硬编码，无客群/阶段差异 | 情侣和亲子家庭得到同样的推荐 |
| 质量评审 | guardrails.py 有基础检查 | 无多模型流水线 | 人工审核成本高，漏检率不可控 |
| 反馈学习 | 无 | 完全缺失 | 评分权重永远是"拍脑袋"→ 质量不提升 |
| 离线评测 | 无 | 完全缺失 | 无法判断改动是好是坏 |

## Goals / Non-Goals

**Goals:**
1. 建立从"问卷输入 → 预览成交 → 完整生成 → 自助微调 → 质量评审 → 交付 → 反馈回收"的完整闭环
2. 让免费预览成为独立的成交引擎（目标转化率 > 25%）
3. 让 80% 的用户不满意可通过自助微调解决，不消耗正式修改次数
4. 让人工审核时间 < 3 分钟/单（当前预估 > 15 分钟）
5. 让评分权重可基于真实数据持续校准

**Non-Goals:**
- 不做多国扩展（只做日本）
- 不做实时导航/地图路线规划
- 不做机酒预订交易
- 不做视频/AR 体验
- 不做完美的评测体系（先做最小可用版本）
- 不追求 token 最优（先保证效果，再优化成本）

## Decisions

### D1: 单一产品真相源 → 配置驱动而非代码驱动

**选择**：将所有 SKU 权益定义为一个 `product_config` 表 + JSONB schema，所有页面/API/客服/后台都从这个表读取。

**替代方案**：继续在前端 constants.ts + 后端 features JSONB 分别维护 → 拒绝：无法保证一致性。

**配置模型**：

```python
class ProductConfig(Base):
    __tablename__ = "product_config"
    config_key: str  # PK, e.g. "sku_standard_248"
    config_value: dict  # JSONB
    version: int
    is_active: bool
    updated_at: datetime
```

config_value schema:
```json
{
  "sku_id": "standard_248",
  "display_name": "标准版",
  "price_cny": 248,
  "preview": {
    "days_shown": 1,
    "modules_shown": ["day_overview", "top3_pois", "lunch_pick", "transport_summary"],
    "modules_locked": ["hotel_detail", "dinner_picks", "insider_tips", "full_schedule"],
    "show_total_days": true,
    "show_locked_count": true
  },
  "entitlements": {
    "full_days": true,
    "self_serve_swaps_unlimited": true,
    "formal_revision_count": 2,
    "formal_revision_includes": ["restructure_day", "change_city_order", "add_custom_requirement"],
    "hotel_recommendation": "area_only",
    "restaurant_detail": true,
    "transport_detail": true,
    "pdf_export": true,
    "share_link": true,
    "wechat_consult_unlimited": true,
    "travel_day_support": false
  },
  "copywriting": {
    "tagline": "完整行程 + 随时问我",
    "value_props": ["5-7天完整规划", "餐厅精选+避坑", "2次深度修改", "无限微信咨询"],
    "cta_text": "立即获取完整方案"
  }
}
```

### D2: Preview Engine → "选最佳天"而非固定 Day 1

**选择**：预览不固定展示 Day 1。系统从完整行程中挑选"最能成交的一天"——即 preview_score 最高的一天。

**preview_score 计算**：
```
preview_score(day) = 
    0.30 × visual_appeal       # 有图片/有名景点/有特色餐厅
  + 0.25 × wow_factor          # 有独特体验/有季节限定/有 insider tip
  + 0.20 × variety             # 景点+餐厅+体验类型多样性
  + 0.15 × evidence_density    # 有 Tabelog 分数/步行距离/具体证据的条目占比
  + 0.10 × route_compactness   # 一天内移动距离短/顺路
```

**理由**：Day 1 往往是"到达日"（下午才到，只能逛周边），Day 2 或 Day 3 通常更精彩。选"最佳天"能最大化"一天就想付费"的效果。

**预览必须通过的校验**：
1. 至少包含 3 个 POI + 1 个餐厅
2. 所有推荐实体必须在数据库中存在且 is_active = true
3. 时间线无冲突（不会出现"11:00 在浅草，11:30 在新宿"）
4. 至少 1 个条目有证据化推荐理由（Tabelog 分数/评论数/步行距离）
5. 预览天不能是"移动日"（纯交通转移的天）

**预览失败降级**：校验不通过 → 换下一个 preview_score 最高的天 → 仍不通过 → 退回 Day 1 → 仍不通过 → 标记为 needs_human_review

### D3: Self-Serve Tuning → 替换 + 局部重排 + 自动重检

**开放给用户的微调**：

| 可调模块 | 替换来源 | 边界 | 不消耗修改次数 |
|----------|----------|------|---------------|
| 酒店 | 同区域同价位候选 Top 5 | 不可跨城市 | ✅ |
| 午餐/晚餐 | 同时段同区域候选 Top 5 | 不可改为早餐 | ✅ |
| 体验景点 | 同类型同区域候选 Top 5 | 不可删除必去项 | ✅ |
| 节奏轻重 | 增删 1 个可选项 | 每天最少 2 项 | ✅ |
| 夜间方案 | 开启/关闭 + 推荐切换 | 不影响次日出发时间 | ✅ |

**锁定不可调**：
- 天数/城市顺序（→ 消耗正式修改次数）
- 必去项（由 editorial_boost > 5 的实体自动标记）
- 交通方式（系统自动计算）
- 预算范围（→ 消耗正式修改次数）

**局部重排流程**：
```
用户点击"换一个" 
  → API 返回 swap_candidates（预计算，存在 itinerary_items.swap_candidates）
  → 用户选择替换目标
  → 后端执行 partial_reassemble(day_id, item_id, new_entity_id)
    → 重算该天时间线（调整 start_time/end_time/transit 时间）
    → 检查相邻天是否受影响（酒店换了→次日出发地变了）
    → 运行 guardrails(day_id) 单天校验
    → 通过 → 写入新版本
    → 不通过 → 回退 + 提示用户"换了这个会导致XX问题，要不试试这个？"
```

**什么时候消耗正式修改次数**：
1. 修改天数、城市顺序
2. 增减整天行程
3. 添加原始问卷没有的特殊需求
4. 自助微调后仍不满意，要求"整体重新规划"

### D4: City Context Data → 6 张核心表

| 表名 | 用途 | 核心字段 | 服务于 |
|------|------|----------|--------|
| `area_profiles` | 区域画像 | area_code, city_code, area_type(商业/住宅/观光/美食), best_time_slots[], peak_months[], crowd_pattern_json, nearest_station | 主生成+预览排序 |
| `timeslot_rules` | 时段规则 | entity_id, valid_slots(morning/afternoon/evening/night), best_slot, closed_slots[], reason | 主生成+护栏 |
| `seasonal_events` | 季节活动 | event_id, city_code, area_code, event_name, start_date, end_date, crowd_impact, booking_required, best_timing_tips | 预览排序+生成 |
| `transport_links` | 交通连接 | origin_area, dest_area, mode, typical_duration_min, cost_jpy, rush_hour_penalty_min, last_train_time | 主生成+护栏 |
| `audience_fit` | 客群适配 | entity_id, audience_type(couple/family/solo/senior/group), fit_score(1-5), reason | 评分+替换排序 |
| `entity_operating_facts` | 营业事实 | entity_id, day_of_week, open_time, close_time, last_entry_time, holiday_schedule, reservation_window_days, typical_wait_min | 护栏+生成 |

**必须先做的 3 张表（否则系统跑不起来）**：
1. `timeslot_rules` — 没有它会推荐"下午去筑地"（已关门）
2. `entity_operating_facts` — 没有它无法检查营业时间冲突
3. `audience_fit` — 没有它情侣和亲子得到同样推荐

**AI 维护这些表的方式**：
- 事实抽取：从 Google Places / 官网 / 爬虫数据中提取结构化信息 → 写入
- 交叉审查：同一实体的多源数据对比 → 冲突时标记 needs_verification
- 定期刷新：updated_at > 90 天的记录自动进入刷新队列

### D5: Soft Rules + Weight Packs → 可配置权重矩阵

**当前问题**：scorer.py 中的 DIMENSIONS_BY_TYPE 权重是硬编码的。所有客群、所有套餐、所有阶段用同一套权重。

**解决方案**：引入 weight_packs 表：

```python
class WeightPack(Base):
    __tablename__ = "weight_packs"
    pack_id: str  # PK, e.g. "couple_premium_preview"
    pack_type: str  # "audience" | "sku_tier" | "stage"
    target_entity_type: str  # "poi" | "hotel" | "restaurant"
    weights: dict  # JSONB: {dimension_key: weight_float}
    description: str
    is_active: bool
    version: int
```

**权重包组合逻辑**：
```
final_weights = merge(
    base_weights,                    # 默认权重（当前硬编码的值）
    audience_pack[party_type],       # 客群覆盖
    sku_pack[sku_tier],              # 套餐覆盖
    stage_pack[stage],               # 阶段覆盖（preview / full / swap）
)
```

**关键权重包**：

| pack_id | 影响 | 核心差异 |
|---------|------|----------|
| `couple_*` | 情侣 | 氛围分 +40%，夜景 +30%，亲子设施 -50% |
| `family_child_*` | 亲子 | 安全分 +50%，步行距离惩罚 +100%，夜间 -70% |
| `preview_*` | 预览排序 | visual_appeal +60%，wow_factor +40%，evidence_density +30% |
| `swap_*` | 替换排序 | 同类型多样性 +50%，距离相近 +40%，价位接近 +30% |

**最影响免费转付费的软规则**：evidence_density（有 Tabelog 分数/步行距离等具体数据）、wow_factor（有独特卖点的推荐）
**最影响用户喜欢和分享的软规则**：visual_appeal（有好图片）、route_compactness（顺路感）
**最影响复购的软规则**：实际旅行可执行性 → timeslot_rules + entity_operating_facts 的准确性

### D6: Multi-Agent Review → 5 步流水线

```
┌──────────┐     ┌────────┐     ┌────────────┐     ┌───────────┐     ┌────────────┐
│ Planner  │────▶│  QA    │────▶│ User Proxy │────▶│ Ops Proxy │────▶│Final Judge │
│ (生成)   │     │(挑错)  │     │(客群视角)  │     │(执行视角) │     │(裁决)      │
└──────────┘     └────────┘     └────────────┘     └───────────┘     └────────────┘
```

| 步骤 | 模型 | 输入 | 输出 | 自动通过条件 | 触发重写条件 | 触发人工条件 |
|------|------|------|------|-------------|-------------|-------------|
| Planner | GPT-4o | trip_profile + ranked_entities | itinerary_plan | — | — | — |
| QA | GPT-4o-mini | plan + timeslot_rules + operating_facts | issues[] | issues.length == 0 | issues.severity == "high" | — |
| User Proxy | GPT-4o-mini | plan + trip_profile + audience_fit | complaints[] | complaints.length == 0 | complaints with fix_suggestion | complaints.length > 3 |
| Ops Proxy | GPT-4o-mini | plan + transport_links + seasonal_events | warnings[] | warnings.length == 0 | warnings.severity == "high" | warnings with no_auto_fix |
| Final Judge | GPT-4o-mini | all_issues + all_complaints + all_warnings | verdict | verdict == "pass" | verdict == "rewrite" (max 2次) | verdict == "human" |

**Token 控制**：
- QA/UserProxy/OpsProxy 用 GPT-4o-mini（便宜 10x）
- 每步输入只传相关上下文（不传完整数据库）
- 总预算 < 8K tokens/单（约 ¥0.05）
- 如果 rewrite 2 次仍不通过 → 人工介入

### D7: Feedback & Learning Loop

**埋点事件**：

| 事件 | 触发时机 | 回写目标 |
|------|----------|----------|
| preview_view | 预览页打开 | preview_score 校准 |
| preview_stay_duration | 预览页停留 > 30s | preview_score 校准 |
| preview_to_paid | 预览 → 付费 | preview_score 校准 + entity 成交率 |
| swap_triggered | 用户点击"换一个" | 原 entity 负反馈 |
| swap_accepted | 用户确认替换 | 新 entity 正反馈 + 替换排序校准 |
| swap_reverted | 用户撤销替换 | 新 entity 负反馈 |
| formal_revision_requested | 触发正式修改 | 自助微调覆盖率 |
| share_link_clicked | 分享链接 | entity visual_appeal 校准 |
| feedback_submitted | 旅行后反馈 | editorial_score 校准 |

**回写机制**：
- preview_to_paid 率高的天 → 该天所有 entity 的 preview_score +1
- swap_triggered 率 > 30% 的 entity → 该 entity 的 base_score -2
- feedback_submitted 满意度 < 3 的 entity → editorial_boost -1

### D8: Offline Eval → 最小可用评测集

**评测集构成**（目标：20 个样本）：
- 5 个 Tokyo 标准情侣 5 日
- 5 个 Tokyo+Kyoto 亲子 7 日
- 5 个 Osaka+Kyoto 闺蜜 3 日
- 5 个 边缘案例（冬季北海道/单城市1日/10日深度）

**评测维度**（每个维度 1-5 分）：
1. 时间线合理性（无冲突、营业时间正确）
2. 路线效率（不走冤枉路）
3. 客群匹配度（推荐符合画像）
4. 证据密度（有具体数据支撑的推荐占比）
5. 多样性（不重复类型）
6. 可执行性（到了真的能按这个走）

**验收标准**：平均分 ≥ 3.5 且无任何维度 < 2.0

## Risks / Trade-offs

| 风险 | 影响 | 缓解 |
|------|------|------|
| City Context 数据不准 | 推荐"已关门的店" → 信任崩塌 | 优先覆盖 P0 城市 Top 100 实体，人工抽检 |
| Multi-Agent 串行延迟 | 5 步 LLM 调用 → 生成慢 | QA/UserProxy/OpsProxy 可并行执行 |
| Self-Serve 被滥用 | 用户无限替换 → 服务器压力 | 每天限制 10 次 swap |
| Weight Pack 初始值不准 | 情侣和亲子区分不够 | 先用 seed 值，每 50 单校准一次 |
| 离线评测集太小 | 20 个样本代表性不足 | 每完成 10 个真实订单补充 1 个评测样本 |

## Migration Plan

1. **Phase 0（第 1 周）**：创建新表 + seed 数据，不影响现有系统
2. **Phase 1（第 2-3 周）**：Preview Engine + Product Config 上线，旧接口保持兼容
3. **Phase 2（第 4-5 周）**：Self-Serve Tuning 上线，前端增加微调 UI
4. **Phase 3（第 6-8 周）**：Multi-Agent Review 上线，逐步减少人工审核
5. **Phase 4（持续）**：Feedback Loop 积累数据，Weight Pack 持续校准

回退策略：每个 Phase 有独立的 feature flag，可以在不影响其他模块的情况下回退。
