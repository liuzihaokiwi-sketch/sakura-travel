# 审核发布闸门 (Review Gate)

## 概述
交付前的自动校验 + 人工抽检，确保攻略质量。

## 自动审核规则
| 规则 | 严重级别 | 触发条件 |
|---|---|---|
| 跨城过多 | ERROR | 单日跨 2 城以上 |
| 营业时间冲突 | ERROR | 到达时间在营业时间外 |
| 单日过满 | WARN | 超过节奏上限 POI 数 |
| 预算超限 | WARN | 日预算超用户预算 130% |
| 缺雨天替代 | WARN | 天气敏感 POI 无 backup |
| 缺签证/安全提醒 | ERROR | 模板中缺少合规组件 |
| 过期快照 | WARN | 引用数据 freshness_ts > 90天 |
| 暴走检测 | WARN | 步行 > 节奏上限 |
| 换乘过多 | WARN | 单日换乘 > 5 次 |
| 餐饮时段冲突 | ERROR | 午/晚餐时段无安排（利润款+） |

## 人工抽检策略
| 产品级别 | 抽检比例 | 审核方式 |
|---|---|---|
| 引流款（19.9~29.9） | 5%~15% | 随机抽检 |
| 利润款（69~99） | 20%~40% | 随机 + 关键词触发 |
| 利润款（128~199） | 40%~60% | 重点抽检 |
| 高客单 | 100% | 全量人工过稿 |

## 数据结构

### qa_review_log 审核日志
| 字段 | 类型 | 说明 |
|---|---|---|
| review_id | UUID | 主键 |
| plan_id | UUID | 关联行程 |
| review_type | VARCHAR | auto / manual |
| result | VARCHAR | pass / warn / fail |
| issues | JSONB | 问题列表 [{rule, severity, detail}] |
| reviewer_id | UUID | 审核人（人工时） |
| note | TEXT | 审核备注 |
| reviewed_at | TIMESTAMP | 审核时间 |

## 审核流程
1. 行程生成完成后自动触发 auto review
2. ERROR 级别 → 自动拦截，不允许发布（hard_fail）
3. WARN 级别 → 标记，允许发布但记录（soft_fail）
4. 按抽检比例抽取进入人工审核队列
5. 人工审核通过 → 标记 reviewed，允许交付
6. 人工审核不通过 → 退回修改或标记废弃

---

## 实现规格

### 自动审核函数设计
文件路径：`app/domains/review_ops/guardrails.py`

```python
@dataclass
class GuardrailIssue:
    rule: str           # 规则标识（如 "cross_city_overload"）
    severity: str       # "hard_fail" / "soft_fail"
    detail: str         # 可读描述
    day_number: int | None  # 关联的天数（可选）

@dataclass
class GuardrailResult:
    passed: bool                    # 无 hard_fail 则 True
    hard_fail_count: int
    soft_fail_count: int
    issues: list[GuardrailIssue]

def run_guardrails(plan: ItineraryPlan, days: list[ItineraryDay], items: list[ItineraryItem]) -> GuardrailResult:
    """纯函数：对完整行程运行所有审核规则。"""
```

### 规则实现优先级
| 规则 | 级别 | 实现优先级 | 判断逻辑 |
|---|---|---|---|
| 跨城过多 | hard_fail | P0 | 单日 cities > 2 |
| 营业时间冲突 | hard_fail | P0 | item.start_time 在 entity.opening_hours 外 |
| 餐饮时段冲突 | hard_fail | P0 | 午餐/晚餐时段无 restaurant/free_time item |
| 缺签证/安全提醒 | hard_fail | P1 | 模板渲染缺 compliance 组件 |
| 单日过满 | soft_fail | P0 | items.count(type=attraction) > intensity.max_poi |
| 暴走检测 | soft_fail | P0 | day.walking_minutes > intensity.max_walk |
| 换乘过多 | soft_fail | P0 | day.transfer_count > intensity.max_transit |
| 预算超限 | soft_fail | P1 | day_budget > user_budget_per_day × 1.3 |
| 过期快照 | soft_fail | P1 | source_snapshot.fetched_at 距今 > 90 天 |
| 缺雨天替代 | soft_fail | P1 | weather_sensitivity=高 的 POI 无 backup item |

### 与其他模块集成
- planner 生成行程后自动调用 `run_guardrails()`
- hard_fail → plan.status 保持 "draft"，不进入发布流程
- soft_fail → plan.status 可为 "reviewed"，issues 写入 review_jobs 表
- 审核结果写入 `review_jobs` + `review_actions` 表

---

## 实现状态

| 组件 | 状态 | 说明 |
|---|---|---|
| 审核规则数据结构（review_jobs/review_actions） | ✅ ORM 已建 | app/db/models/business.py |
| guardrails.py 规则引擎 | ❌ 待建 | app/domains/review_ops/guardrails.py |
| 自动审核 API/Job 集成 | ❌ 待建 | planner 调用 guardrails 后写 review_jobs |
| POST /ops/trips/{id}/review | ❌ 待建 | 人工审核接口 |
| POST /ops/trips/{id}/publish | ❌ 待建 | 发布接口 |
| 审核工作台前端 | ❌ 不在当前范围 | Phase 2 |
