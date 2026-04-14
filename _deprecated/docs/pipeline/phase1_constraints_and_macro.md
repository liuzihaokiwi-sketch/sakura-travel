# Phase 1: 收集约束 + 宏观方案 (Step 1-4)

> 代码位置：`app/domains/planning_v2/step01~step04`
> 执行方：系统(DB) + Opus AI
> 目的：从用户输入到"有哪些景点可以选"，完成所有前置收缩

---

## 本阶段的核心目标

把一个模糊的用户需求（"我想去关西5天"）收缩为一个**有边界的决策空间**：
- 哪几天、什么画像、什么约束 → Step 1
- 这个圈有多少可用实体 → Step 2
- AI 给出 3 个城市组合候选 → Step 3
- 系统缩减 POI 池到 50-100 个 → Step 4

Phase 1 结束时，后续所有 step 都在这个池子里做选择，不会再扩大范围。

---

## Step 1: resolve_user_constraints

### 职责
从 DB 读取 TripProfile，规范化为 `UserConstraints` 三件套：trip_window + user_profile + constraints。

### 输入
- `trip_request_id: str` — 订单 UUID

### 输出
```python
UserConstraints(
    trip_window = {
        "start_date": "2026-04-01",   # YYYY-MM-DD
        "end_date": "2026-04-05",
        "total_days": 5                # 含首末日
    },
    user_profile = {
        "party_type": "couple",        # 同行人类型
        "budget_tier": "mid",          # budget/mid/premium/luxury
        "must_have_tags": ["temple"],   # 偏好标签
        "nice_to_have_tags": [],
        "companion_breakdown": {},
        "special_requirements": {}
    },
    constraints = {
        "must_visit": ["kyo_kinkaku"],  # 必去
        "do_not_go": [],                # 不去
        "visited": [],                  # 已去过
        "booked_items": []              # 已订项目
    }
)
```

### 关键规则
- `total_days` 最小值为 1
- `party_type` 缺失时默认 `"couple"`
- `budget_tier` 缺失时默认 `"mid"`
- 所有列表字段经过 `_ensure_list()` 规范化（None→[], str→[str]）

### 错误处理
- TripRequest/TripProfile 不存在 → 直接抛 ValueError，管线终止
- 日期解析失败 → fallback 到 `duration_days` 字段

### 测试要点
- 验证各种 party_type 都能正确解析（family_young, senior, couple 等）
- 验证 must_visit/do_not_go 的 None/string/list 三种输入都能规范化
- 验证缺失 TripProfile 时抛出明确错误

---

## Step 2: build_region_summary

### 职责
SQL 聚合查询，统计圈内实体的类型分布和等级分布。给 Step 3 的 AI 提供"这个圈有什么"的宏观信息。

### 输入
- `circle_name: str` — 圈标识（如 "kansai"）
- `circle_cities: list[str]` — 圈内城市代码

### 输出
```python
RegionSummary(
    circle_name = "kansai",
    cities = ["kyoto", "osaka", "kobe", "nara"],
    entity_count = 450,
    entities_by_type = {"poi": 245, "restaurant": 180, "hotel": 45, "event": 0},
    grade_distribution = {"S": 50, "A": 120, "B": 180, "C": 75}
)
```

### 关键规则
- 只统计 `is_active=true` 的实体
- 确保标准类型（poi/restaurant/hotel/event）和标准等级（S/A/B/C）缺失时补 0
- `circle_cities` 为空时直接抛 ValueError

### 设计决策
**为什么不在 Step 1 里做？**
Step 1 解析用户输入，Step 2 查询系统数据。分开是因为 Step 2 需要 circle 信息（来自 orchestrator 的 `_resolve_circle`），而不是用户输入。

### 测试要点
- 空城市列表应报错
- 验证返回的类型和等级覆盖完整
- 验证 NULL data_tier 映射为 "unknown"

---

## Step 3: plan_city_combination (Opus AI)

### 职责
用 Opus 深度思考，根据用户约束和圈内数据，生成 3 个风格不同的城市组合方案。

### 输入
- `UserConstraints` — 用户时间、画像、约束
- `RegionSummary` — 圈内实体统计
- `CircleProfile` — 圈环境（用于提示词注入 region_desc）

### 输出
```python
{
    "candidates": [
        {
            "plan_name": "经典文化线",
            "cities_by_day": {
                "day1": {"city": "osaka", "theme": "到达+道顿堀", "intensity": "light"},
                "day2": {"city": "kyoto", "theme": "东山祇园", "intensity": "heavy"},
                ...
            },
            "reasoning": "推荐理由",
            "trade_offs": "取舍说明"
        },
        ...  # 共 3 个
    ],
    "recommended_index": 0,
    "thinking_tokens_used": 8500
}
```

### AI 调用规格
| 参数 | 值 |
|------|-----|
| 模型 | claude-opus-4-6 |
| max_tokens | 16000 |
| thinking_budget | 10000 |
| 重试次数 | 1 次（共尝试 2 次） |

### 提示词设计原则
1. 第一天和最后一天 intensity 必须为 light（到达/离开日）
2. 同一城市建议连续 2+ 天（减少搬酒店）
3. 必须覆盖 must_visit，不能安排 do_not_go
4. 3 个方案风格明显不同（文化 vs 美食 vs 自然）

### Fallback（API 失败时）
调用 `_generate_fallback_plan()`：
- 城市列表均匀轮换分配到各天
- 首末日 light，其余 medium
- 返回单个候选方案，标记 `"fallback": true`

### 关键设计决策
**为什么用 Opus 而不是 Sonnet？**
城市组合是整个行程的骨架决策，需要综合考虑用户画像、城市间交通、季节因素、强度平衡。这种多维度取舍需要深度推理能力。且整个行程只调用 1 次，成本可接受。

**为什么生成 3 个而不是 1 个？**
给后续客服人工审核和用户选择留空间。3 个方案覆盖不同偏好维度。

### 测试要点
- Fallback 方案的首末日必须为 light
- must_visit 在 cities_by_day 中有对应城市
- 3 个方案的城市安排应有差异
- thinking_tokens_used 应为正数（非 0，非 budget 值）

---

## Step 4: build_poi_pool (系统过滤)

### 职责
从 DB 读取所有活跃 POI，经过 10 条规则顺序过滤，输出 50-100 个候选景点池。这是后续所有 step 的"菜单"。

### 输入
- `UserConstraints` — 约束和画像
- `RegionSummary` — 城市列表
- `travel_dates: list[str]` — 日期列表（用于季节判断）
- `CircleProfile` — taxonomy 路径和货币
- `PoolConfig` — 过滤策略参数（可覆盖）

### 输出
`list[CandidatePool]` — 每个元素包含：
| 字段 | 类型 | 说明 |
|------|------|------|
| entity_id | str | UUID |
| name_zh | str | 中文名 |
| grade | str | 画像加成后的有效等级 |
| latitude/longitude | float | 坐标 |
| tags | list[str] | 语义标签 |
| visit_minutes | int | 建议停留时间 |
| cost_local | int | 本地货币门票费 |
| currency | str | JPY/CNY |
| city_code | str | 城市代码 |
| open_hours | dict | 营业时间 |
| review_signals | dict | 评分信号 |

### 10 条过滤规则

| # | 规则 | 阶段 | 说明 |
|---|------|------|------|
| 1 | city_code | SQL WHERE | 扩展后的城市集合（含 regions + day_trip_links） |
| 2 | is_active | SQL WHERE | 必须为活跃实体 |
| 3 | grade | Python | 画像加成后 → allowed_grades(total_days) |
| 4 | party_type | Python | 儿童排除 adults_only/bar；老人排除 extreme_physical/hiking |
| 5 | budget+cost | Python | admission_fee > admission_cap[tier] → 过滤（must_visit 豁免） |
| 6 | season | Python | best_season 不含旅行季节 → 过滤 |
| 7 | do_not_go | Python | 用户黑名单 |
| 8 | visited | Python | 用户已访问 |
| 9 | 定休日 | Python | permanently_closed / long_term_closed |
| 10 | risk_flags | Python | renovation / construction / unstable / dangerous |

### 城市圈两层扩展
1. **行政归属**（taxonomy.json → regions）：kyoto 包含 uji/天桥立/伊根
2. **当日往返**（taxonomy.json → day_trip_links）：osaka → arima/himeji 等

`sub_region_codes` 从 taxonomy.json 读取，不在代码中硬编码。

### 画像加成
从 `taxonomy.json.profile_boost_rules` 读取规则。例：
- 海游馆 base=B, family_kids → +1 → effective=A（入池）
- USJ base=S, culture_deep → -1 → effective=A（仍入池，但降优先级）

### PoolConfig 关键参数
```python
grade_tiers = {
    "short": ["S", "A", "B"],        # ≤3天
    "medium": ["S", "A", "B", "C"],  # 4-5天
    "long": ["S", "A", "B", "C"],    # ≥6天
}
admission_cap = {"budget": 1000, "mid": 3000, "premium": 8000, "luxury": 999999}
```

### 关键设计决策
**为什么不在 SQL 里做所有过滤？**
画像加成需要加载 taxonomy.json 的 boost_rules，这是 JSON 配置不是 DB 字段。季节检查需要解析 best_season 字符串。保持 SQL 层简单（只做城市+活跃过滤），复杂逻辑在 Python 层。

**为什么 must_visit 豁免 budget 过滤？**
用户明确说"必去"，即使门票贵也要进池。但仍受 grade 过滤。

### 测试要点
- 3 天行程 B 级景点是否入池（取决于 PoolConfig）
- 家庭画像是否过滤了 adults_only 标签景点
- do_not_go 中的景点不在池中
- 不同季节的 best_season 过滤是否正确
- 跨圈 day_trip_links 扩展是否生效（如大阪行程能看到有马温泉）

---

## Phase 1 整体原则

1. **系统做收缩，AI 做取舍** — Step 1/2/4 是确定性的系统缩圈，Step 3 是 AI 判断。边界清晰。
2. **配置驱动** — PoolConfig、taxonomy.json、circle_registry.json 三层配置，代码无硬编码。
3. **CircleProfile 贯穿** — 从 Step 2 开始，circle 信息流经整个管线。taxonomy 路径、货币、提示词角色都从它获取。
4. **Fallback 不是空架子** — Step 3 的 fallback 方案是可执行的（均匀轮换城市），不是返回空。Step 4 无 POI 则返回空列表，后续步骤需自行处理。

## Phase 1 数据流

```
TripRequest ID
    │
    ▼
Step 1: resolve_user_constraints
    │ → UserConstraints {trip_window, user_profile, constraints}
    │
    ├──▶ orchestrator: _resolve_circle() → CircleProfile
    │
    ▼
Step 2: build_region_summary
    │ → RegionSummary {entity_count, type_distribution, grade_distribution}
    │
    ├──▶ Step 3: plan_city_combination (Opus)
    │       → {candidates[3], recommended_index}
    │
    └──▶ Step 4: build_poi_pool (系统过滤)
    
            → list[CandidatePool] (50-100 个 POI)
```
