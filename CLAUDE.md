# 项目工程规范

## 质量第一原则

本项目的产出是**付费旅行手账本**（国内298/国外348元），质量标准是"十个日本旅游专家联合做出的攻略"级别。

- 每个推荐必须有充分理由（为什么推这家而不是那家）
- 不允许为了赶进度降低标准，宁可少覆盖城市也要做到极致
- 最终判断标准：一个真实的日本旅行顾问看到方案会不会认可

## Token 与资源使用规范

### 上下文管理
- 上下文过长时主动压缩，不要等系统自动截断
- 长文件不要全部读入，用 offset/limit 读需要的部分
- 搜索代码先用 Grep/Glob 精确查找，不要用 Agent 做简单搜索

### 并发控制
- Agent 最多 3 个并发，不要开更多
- Anthropic API 串行调用，不做高并发（会被限速）
- 高并发场景用阿里云（qwen-max）

### 避免重复工作
- 读过的文件内容记住关键信息，不要反复读同一个文件
- Agent 完成的研究结果要提炼总结，不要让多个 Agent 做重复搜索
- 修改代码前先确认修改方案，不要改了又改回来

### 输出精简
- 回复简洁直接，不要重复用户说过的话
- 不要在每次工具调用后总结"我刚刚做了什么"
- 代码修改后不需要把整个文件内容贴出来

## 绝对禁止的行为

### 1. 不许硬编码业务数据
配置数据（城市圈映射、grade 阈值、价格上限、人群分类）必须从配置文件或 DB 读取，不许写死在 Python 代码里。

**错误示例：**
```python
# 写死在代码里，加新城市就要改代码
_EXTENDED_CITIES = {"uji": "kyoto", "arima": "kobe"}
```

**正确做法：**
```python
# 从 taxonomy.json 读取，加新城市只改 JSON
region_map = _build_region_city_map()  # 读 taxonomy.json.regions
day_trips = _build_day_trip_targets()  # 读 taxonomy.json.day_trip_links
```

**判断标准：** 如果一个值将来可能变（新城市、新人群类型、价格调整），它就不该在代码里。用 dataclass config、JSON 配置文件、或 DB 记录。

### 2. 不许打补丁绕过问题
遇到 bug 或设计缺陷时，必须修根因，不许用 workaround 跳过。

**错误示例：**
```python
# DB 连接失败 → 加 force_ai=True 跳过爬虫
# 测试发现问题 → 写断言"不在池里"让测试通过
# party_type 不识别 → 在消费端列举所有可能值
```

**正确做法：**
```python
# DB 连接失败 → 修连接配置
# 测试发现问题 → @pytest.mark.xfail(strict=True, reason="...") 追踪
# party_type 不识别 → 在 party_type 定义本身携带属性
```

### 3. 不许用 AI 知识代替真实数据
所有事实性字段（评分、价格、坐标、营业时间）必须来自真实数据源验证。搜不到填 null，绝不编造。

**数据可信度分级：**
- `verified`: 2+ 个 P0/P1 源交叉验证 → 可上生产
- `cross_checked`: 1 个 P0/P1 + 其他 → 可用，标注
- `single_source`: 仅 P2 源 → 可用，标注
- `ai_generated`: 无真实源 → **不可上生产**

### 4. 不许在函数体内重复 import
所有 import 放模块顶部。函数体内 `from datetime import datetime` 这种写法是偷懒。

### 5. 不许假装修了实际没修
典型模式：S/A 和 B/C 两个分支写了不同注释但做了相同的事（都 continue）。如果逻辑相同就写一个分支，不要用注释掩盖。

---

## 系统设计原则

### 配置驱动，不硬编码
- 城市圈归属 → `taxonomy.json.regions`
- 跨圈可达 → `taxonomy.json.day_trip_links`
- 画像加成 → `taxonomy.json.profile_boost_rules`
- Grade 策略 → `PoolConfig` dataclass（可被 orchestrator/测试覆盖）
- Budget 阈值 → `PoolConfig.admission_cap`
- Party type 属性 → `PoolConfig.children_party_types` / `elderly_party_types`

### 数据契约对齐
上游步骤的输出字段必须与下游步骤的期望输入完全对齐。每次加新字段或改字段名，检查所有消费该输出的下游步骤。

已知的关键数据流：
- Step 7 `meals_included` → Step 8 `hotel_breakfast/dinner_included` → Step 13 跳过对应餐池
- Step 13.5 输出 `{meal_selections: [{day, breakfast, lunch, dinner}]}` → Step 14 必须理解这个格式
- CandidatePool.city_code → Step 5 按城市分组（不用 tag 匹配）

### Thinking tokens 提取
Anthropic API 中 extended thinking tokens 计入 `output_tokens`。SDK 没有独立的 `thinking_tokens` 字段。不要用 `cache_creation_input_tokens`，不要用 budget 值兜底。

```python
# 正确
output_tokens = getattr(response.usage, "output_tokens", 0)

# 错误
thinking_tokens = getattr(usage, "cache_creation_input_tokens", 0)  # 错误字段
thinking_tokens = THINKING_BUDGET_TOKENS  # 保守估算 = 假数据
```

### 安全访问可选字段
`review_signals` 和 `open_hours` 是 `Optional[dict]`，访问前必须防 None：

```python
# 正确
(c.review_signals or {}).get("in_main_corridor", False)

# 错误 — AttributeError when None
c.review_signals.get("in_main_corridor", False)
```

---

## API 调用规范

### Anthropic API
- **不许高并发**。串行或最多 2-3 个并行。高并发会被限速。
- 高并发场景用阿里云（qwen-max）。
- 模型 ID 用精确版本：`claude-opus-4-6`、`claude-sonnet-4-6`，不写泛称。

### Google Routes API
- `computeRouteMatrix` transit 模式上限 100 elements。
- Step 9 不做全量 N×N POI 矩阵，只算稀疏矩阵（当日活动+候补+住宿）。
- 必须带 field mask。

---

## 测试规范

### 生产级别原则

**测试的目的是观察攻略质量，不是验证用例通过。用例通过但攻略质量差 = 测试失败。**

#### 1. 测试必须完美模拟生产环境
- 测试跑的路径必须和生产一模一样，不允许用 fallback 或 mock 替代 AI 步骤
- AI 步骤（Step 3/5/7/9/12/13.5/15）：Anthropic Opus/Sonnet 可用时用 Anthropic，不可用时用阿里云 qwen-max（OpenAI 兼容接口），绝不用规则 fallback 代替
- 系统步骤（Step 1/2/4/6/8/10/13/14）：必须连真实数据源（DB 或 JSON），不允许构造假数据

#### 2. 不准偷懒，不准打补丁
- 遇到 DB 连不上 → 修连接配置，不换成 SQLite mock
- 遇到 API 报错 → 换阿里云或查 key，不改成 fallback
- 遇到数据缺失 → 上报为数据问题（xfail 追踪），不改断言让测试通过
- 遇到 entity_id 不存在 → 上报数据问题，不改测试用例的 id 凑合

#### 3. 最终标准是攻略质量，不是用例是否通过
- 每次测试必须输出可读的攻略文本（Markdown），供人工判断质量
- 结构断言（字段存在、天数正确）是底线检查，不是目标
- 以下问题结构断言检测不到，但会让用户退款：
  - 情侣 mid 档推了主题乐园（USJ）
  - 7天行程每天只有 1 个景点
  - 城市来回折腾（Day1 京都→Day2 大阪→Day3 京都）
  - 走廊名用 tag 而不是地名

#### 4. 发现问题必须上报，不自行修复
- 测试发现数据问题（entity_id 缺失、city_code 不在 circle.cities）→ `xfail(strict=True)` 标注，不改数据
- 测试发现逻辑问题（fallback 推了 USJ、每天只有 1 个景点）→ 在测试报告中记录，不改测试断言放水
- 上报格式：`[数据问题]`/`[逻辑问题]` + 具体现象 + 影响

### xfail 追踪问题，不掩盖问题
```python
# 正确：问题可见，修复后 XPASS 强制去标注
@pytest.mark.xfail(strict=True, reason="数据问题：hyo_arima_kinsen.city_code='arima' 不在 circle.cities，需修 circle_registry.json")
def test_must_visit_in_pool_13d_complex(): ...

# 错误：断言问题存在 = 绿灯 = 问题被掩盖
def test_must_visit_in_pool_13d_complex():
    assert "hyo_arima_kinsen" not in pool_ids  # "通过"但 must_visit 无法满足
```

### 效果测试 > 无 bug 测试
测试工程师的核心标准：**一个真实的日本旅行顾问看到这个方案，会不会觉得合理？**
不是"代码没报错"就行。

---

## 16 步管线架构

```
Step  1: resolve_user_constraints       系统(DB)
Step  2: build_region_summary           系统(DB)
Step  3: plan_city_combination          Opus AI
Step  4: build_poi_pool                 系统(DB) ← PoolConfig 驱动
Step  5: plan_daily_activities          Opus AI
Step  5.5: validate_and_substitute      Sonnet AI（5种冲突检测）
Step  6: build_hotel_pool               系统(DB) ← 两阶段：Haversine粗筛+通勤精排
Step  7: select_hotels                  Sonnet AI
Step  7.5: check_commute_feasibility    系统(API)
Step  8: build_daily_constraints_list   系统(DB+astral)
Step  9: plan_daily_sequences           Opus AI
Step 10: check_feasibility              系统(纯Python) ← buffer块不参与检查
Step 11: resolve_conflicts              系统+Opus ← hard_infeasible vs capacity_overload
Step 12: build_timeline                 Sonnet AI
Step 13: build_restaurant_pool          系统(DB) ← 营业时段校验
Step 13.5: select_meals                 Sonnet AI
Step 14: estimate_budget                系统(纯Python)
Step 15: build_plan_b                   Sonnet AI
Step 16: generate_handbook_content      Sonnet AI（非阻塞）
```

入口：`app/workers/jobs/generate_trip.py` → `run_planning_v2()`。

---

## 代码质量规范

### 错误处理
- 不要用 `except Exception` 吞掉所有异常。区分数据错误（ValueError/KeyError → error 级别）和网络错误（ConnectionError/TimeoutError → warning 级别）
- fallback 值必须在日志中标记来源（`mode="fallback_data_error"` 而不是静默用默认值）
- Step 16（手账本）失败不阻塞主管线，其他步骤失败必须上报

### 代码改动范围
- 不加用户没要求的功能、重构、文档注释
- Bug 修复不需要"顺便"清理周围代码
- 不加 feature flag 或向后兼容层，能直接改就直接改

### Git 规范
- 不主动 commit，用户要求时才 commit
- 不 push，不 force push，不 amend，除非用户明确要求
- commit message 写"为什么改"而不是"改了什么"
- 分支命名: `feature/<name>` / `fix/<name>` / `refactor/<name>` / `docs/<name>`
- Commit 格式: `<type>(<scope>): <description>` (type: feat/fix/chore/docs/refactor/test)

### 代码格式化
- Python: `ruff check --fix app/ scripts/ && ruff format app/ scripts/`
- TypeScript: `cd web && pnpm lint`
- 数据库迁移: `alembic revision --autogenerate -m "描述"`

### 文件管理
- 不创建 README、文档文件，除非用户要求
- 优先编辑现有文件，不新建文件（防止文件膨胀）
- 不留死代码、注释掉的代码、`# removed` 标记

---

## 数据源优先级

```
P0 (权威源): Tabelog / Michelin / 一休 / 楽天 / Google Maps API
P1 (中国用户源): 小红书 / 携程 / 大众点评 / 马蜂窝
P2 (参考源): japan-guide / JNTO / 旅行博客
P3 (兜底): AI 知识库 — 仅用于结构化、分类、推荐语，不用于事实性数据
```

所有事实性字段（评分、价格、坐标、营业时间）必须来自 P0-P2 验证。P3 数据标记 `data_confidence: "ai_generated"`，不可直接用于生产输出。

---

## 关键配置文件

| 文件 | 用途 | 代码消费方 |
|------|------|-----------|
| `data/circle_registry.json` | 圈元数据、预算配置、城市列表、时区坐标 | CircleProfile（models.py） |
| `data/{circle}/taxonomy.json` | 分类体系、regions、画像加成、day_trip_links、sub_region_codes | step04 PoolConfig |
| `data/{circle}/corridor_definitions.json` | 走廊地理定义 | step05、step13 |
| `data/{circle}/*.json` | 景点/餐厅/酒店候选数据 | 数据导入脚本 |
| `app/domains/planning_v2/orchestrator.py` | 16步编排器 | generate_trip.py |
| `app/workers/jobs/generate_trip.py` | 主入口 → `run_planning_v2()` | arq worker |

> 注：`{circle}` 指 CircleProfile.data_dir，如 `kansai_spots`、`guangfu_spots`。
> 新增圈需要：circle_registry.json 条目 + taxonomy.json + corridor_definitions.json + DB 数据。
> orchestrator 启动时会调用 `CircleProfile.validate()` 校验配置齐备，缺失则拒绝运行。
