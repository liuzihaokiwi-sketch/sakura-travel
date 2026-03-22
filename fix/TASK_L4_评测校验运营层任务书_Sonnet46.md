# Layer 4: 评测校验运营层 — Sonnet 4.6 任务书

> 创建：2026-03-23
> 执行者：Sonnet 4.6
> 依据：docs/Layer_4_评测校验运营层修改建议_v1.md（批判性采纳）
> 前置完成：Layer 1-2 全完，Layer 4 补充接入（接入 1-5）全完

---

## 对设计文档的批判性评估

文档提出了 10 项建议，我的逐条判断：

### 采纳

| 建议 | 采纳理由 |
|------|----------|
| §二.4 operator_overrides 显式建模 | **真正的缺口**。目前运营无法说"这家酒店暂时不推荐"或"樱花季加权该活动"。必须有 |
| §二.2 live_risk_monitor 规则表 | 方向对，但**只建框架+规则表**，不接真实 API（没有天气/列车数据源，现在接了也是假数据） |
| §二.5 版本管理 | 方向对，但 **8 个独立版本号是过度设计**。一个 `pipeline_versions: dict` 写入 plan_metadata 就够 |
| §三 Layer 4 拆四段 | 概念上对，但**不需要建 4 个子目录**。现有文件按职责归类即可 |

### 已完成（不重复做）

| 建议 | 当前状态 |
|------|----------|
| §二.1 trace 拆成 decisions + step_runs | ✅ E1 已做：decision_writer + generation_decisions + step_runs 分离 |
| §1 validation/engine 前置 | ✅ 接入 2 已做：generate_trip.py 红灯阻断 |
| §2 review_ops 纳入 Layer 4 | ✅ 接入 4 已做：review_writeback.py 回写飞轮 |
| §3 feedback/distillation 回流 | ✅ 接入 5 已做：_update_entity_quality 到 decisions |
| §4 offline_eval 接入 | ✅ 接入 3 已做：6 维评分写入 plan_metadata |

### 不采纳 / 降级

| 建议 | 理由 |
|------|------|
| §二.3 grader 8 维新维度 | **已有 offline_eval 6 维够用**（completeness/feasibility/diversity/preference_match/quality/safety）。新增 factual_reliability 可以，但 emotional_value 无法自动评分，fallback_quality 是 regression test 的事不是 grader 的事。只加 2 个维度 |
| §3 feedback dampening（时间窗+样本门槛+衰减） | 方向对但**现阶段样本量为零**。等有 100+ 反馈再建。现在写入 decisions 已足够追溯 |
| §4 route_matrix 监控 | 纯运维需求，不影响生成质量。**P2 以后做** |
| §二.5 拆 8 个版本字段 | 过度设计。一个 dict 即可 |
| §1 followup_question_router | 这是**表单 UX 问题不是 Layer 4 的事**。表单追问逻辑应在前端 form wizard 里 |

---

## 最终任务列表（5 个任务）

执行顺序：L4-01 → L4-02 → L4-03 → L4-04 → L4-05

### L4-01: operator_overrides 数据模型

**文件**: 新建 `app/db/models/operator_overrides.py`

**任务**: 创建运营干预表，支持运营人员在不改代码的情况下控制推荐行为。

```python
class OperatorOverride(Base):
    __tablename__ = "operator_overrides"

    override_id: int  # BigInteger, primary_key
    
    # 作用范围
    scope: str  # "entity" / "cluster" / "circle" / "corridor" / "global"
    target_id: Optional[str]  # entity_id / cluster_id / circle_id / corridor_id / null(global)
    
    # 干预类型
    override_type: str  # 以下之一：
    # "block"     — 屏蔽：不出现在任何行程中
    # "boost"     — 加权：在同等条件下优先推荐
    # "demote"    — 降权：在同等条件下靠后
    # "pin"       — 钉住：对特定画像强制推荐
    # "swap_lock" — 锁定：不允许"换一个"替换掉
    # "note"      — 标注：在报告中追加说明文字
    
    # 干预参数
    weight_delta: Optional[float]  # boost/demote 时的分数增减（如 +10 / -20）
    note_text: Optional[str]       # note 类型的说明文字
    pin_conditions: Optional[dict]  # JSONB: pin 时的匹配条件（party_type/season 等）
    
    # 生效时间
    effective_from: datetime       # 生效开始时间
    effective_until: Optional[datetime]  # 结束时间（null = 永久）
    
    # 原因
    reason_code: str  # "seasonal" / "maintenance" / "quality_issue" / "promotion" / "safety" / "manual"
    reason_text: Optional[str]
    
    # 操作者
    created_by: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
```

**索引**:
- `(scope, target_id, is_active)` — 查某实体有没有生效中的 override
- `(override_type, is_active)` — 按类型查
- `(effective_until)` — 过期清理

**注册到 `__init__.py`**。

---

### L4-02: operator_overrides 查询服务

**文件**: 新建 `app/domains/planning/override_resolver.py`

**任务**: 创建一个查询服务，供 Layer 2 各模块调用。

```python
class OverrideResolver:
    """运营干预解析器，带内存缓存。"""
    
    async def load_active(self) -> None:
        """加载所有生效中的 override 到内存。"""
        # WHERE is_active = True 
        # AND (effective_until IS NULL OR effective_until > NOW())
    
    def get_overrides(self, scope: str, target_id: str) -> list[OperatorOverride]:
        """查某个目标的所有生效干预。"""
    
    def is_blocked(self, entity_id: str) -> bool:
        """实体是否被屏蔽。"""
    
    def get_weight_delta(self, entity_id: str) -> float:
        """实体的分数增减值（多条 override 叠加）。"""
    
    def get_notes(self, entity_id: str) -> list[str]:
        """实体的运营备注列表。"""
    
    def should_pin(self, entity_id: str, profile: dict) -> bool:
        """实体是否应被 pin（强制推荐）到该画像。"""
```

**接入点提示**（Sonnet 4.6 只需要建模块，接入由后续任务完成）:
- `eligibility_gate.py`: `is_blocked()` → EG 规则追加
- `major_activity_ranker.py`: `get_weight_delta()` → 加到 context_fit 分
- `secondary_filler.py`: `is_blocked()` → 候选池过滤
- `report_generator.py`: `get_notes()` → 追加到报告

---

### L4-03: live_risk_monitor 规则表

**文件**: 新建 `app/db/models/live_risk_rules.py` + `app/domains/planning/live_risk_monitor.py`

**任务**: 创建规则表和规则引擎框架。**不接外部 API**，只建骨架。

**规则表**:
```python
class LiveRiskRule(Base):
    __tablename__ = "live_risk_rules"
    
    rule_id: int  # BigInteger, primary_key
    rule_code: str  # "LR_WEATHER_001" / "LR_CLOSURE_001" / "LR_TRAIN_001"
    
    # 触发条件
    risk_source: str      # "weather" / "transport" / "venue" / "event"
    trigger_window: str   # "T-72h" / "T-24h" / "T-6h" / "T-0h"
    trigger_condition: dict  # JSONB: {"type": "rain_probability_gt", "threshold": 0.7}
    
    # 动作
    action_type: str  # "badge" / "suggest_alternative" / "force_recompute" / "notify_user" / "info_only"
    action_params: Optional[dict]  # JSONB: {"badge_text": "⚠️可能下雨", "fallback_entity_id": "xxx"}
    
    # 作用范围
    applies_to_entity_types: list  # JSONB: ["poi", "activity"]
    applies_to_corridors: Optional[list]  # JSONB: ["kyo_arashiyama"] 或 null(全部)
    
    # 元数据
    priority: int = 50
    is_active: bool = True
    created_at: datetime
```

**引擎框架**:
```python
class LiveRiskMonitor:
    """
    风险监控引擎（框架级，无外部数据源）。
    
    真实数据源将来接入时只需实现 RiskDataProvider 接口。
    """
    
    async def load_rules(self) -> None:
        """加载生效规则。"""
    
    async def evaluate_plan(self, plan_id, trip_date) -> list[RiskAlert]:
        """
        对一个 plan 跑所有适用规则。
        
        当前：只检查 entity_temporal_profiles 中的 closed_day / seasonal 信息。
        将来：接入天气 API、交通 API 后扩展。
        
        Returns:
            [{entity_id, rule_code, risk_level, message, suggested_action}]
        """
    
    async def write_alerts_to_plan(self, plan_id, alerts) -> None:
        """将 alerts 写入 plan_metadata.live_risk_alerts。"""
```

**关键原则**: 引擎本身只消费规则表 + entity_temporal_profiles。**不调任何外部 API**。评估结果写入 plan_metadata。

---

### L4-04: pipeline_versions 跟踪

**文件**: 修改 `app/domains/planning/itinerary_builder.py`

**任务**: 在 `build_itinerary_records()` 写入 plan_metadata 时，追加 `pipeline_versions` 字典。

```python
# 在 plan_metadata 中增加:
plan_metadata["pipeline_versions"] = {
    "scorer": "base_quality_v2",
    "planner": "circle_v1",
    "report_schema": "v2",
    "review_pipeline": "6_agent_v1",
    "itinerary_builder": "shadow_v1" if mode == "shadow" else "live_v1",
}
```

同时在 `report_generator.py` 的 `generate_report_v2()` 输出中追加:
```python
report["meta"]["pipeline_versions"] = {
    "scorer": "base_quality_v2",
    "planner": "circle_v1",
    "report_schema": "v2",
    "report_generator": "v2_circle",
}
```

这不是建新模块，只是在两个已有函数中**各加 5 行代码**。

---

### L4-05: offline_eval 补 2 个评分维度

**文件**: 修改 `app/domains/evaluation/offline_eval.py`

**任务**: 在 EvalScore 中新增 2 个维度，调整权重。

```python
@dataclass
class EvalScore:
    completeness: float = 0.0       # 0-10 (现有)
    feasibility: float = 0.0        # 0-10 (现有)
    diversity: float = 0.0          # 0-10 (现有)
    preference_match: float = 0.0   # 0-10 (现有)
    quality: float = 0.0            # 0-10 (现有)
    safety: float = 0.0             # 0-10 (现有)
    factual_reliability: float = 0.0  # 0-10 (新增)
    pacing_quality: float = 0.0       # 0-10 (新增)
    
    @property
    def overall(self) -> float:
        weights = [0.15, 0.20, 0.10, 0.15, 0.10, 0.10, 0.10, 0.10]
        dims = [self.completeness, self.feasibility, self.diversity,
                self.preference_match, self.quality, self.safety,
                self.factual_reliability, self.pacing_quality]
        return round(sum(w * d for w, d in zip(weights, dims)), 2)
```

新增 2 个评分函数:

```python
def _score_factual_reliability(plan: dict, case: EvalCase) -> float:
    """
    事实可靠性评分。检查：
    - 实体是否有 google_rating（有 = 加分，说明来源可靠）
    - 实体是否有 opening_hours_json（有 = 加分）
    - 餐厅是否有 tabelog_score（有 = 加分）
    - data_tier A 比 B 加分
    - 有 field_provenance 且非 stale = 加分
    
    纯规则统计，不调 API。
    """

def _score_pacing_quality(plan: dict, case: EvalCase) -> float:
    """
    节奏质量评分。检查：
    - 每天 item 数量方差（低 = 好）
    - intensity 分布是否有"先松后紧"或"张弛有度"
    - 是否有连续 2 天都是 dense
    - arrival day 是否 light / balanced
    - departure day 是否 light
    
    纯规则统计，不调 API。
    """
```

在 `score_plan()` 中调用这两个函数并写入 EvalScore。

---

## 注意事项（给 Sonnet 4.6）

1. L4-01 和 L4-03 是**建新表**，必须注册到 `app/db/models/__init__.py`
2. L4-02 是**纯查询服务**，不改任何 Layer 2 模块的调用逻辑（接入是后续任务）
3. L4-03 的 LiveRiskMonitor **不调外部 API**。只读 DB 中已有的 temporal/provenance 数据
4. L4-04 只改两个文件各加 5 行，**不要重构函数**
5. L4-05 的 `to_dict()` 和 `asdict()` 要包含新字段。**权重总和必须 = 1.0**
6. 所有 Python 文件头部写 docstring，说明输入/输出/依赖
7. 新建的文件结构:
   ```
   app/db/models/
     operator_overrides.py    # L4-01
     live_risk_rules.py       # L4-03
   app/domains/planning/
     override_resolver.py     # L4-02
     live_risk_monitor.py     # L4-03
   ```
