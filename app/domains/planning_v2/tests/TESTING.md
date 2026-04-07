# planning_v2 测试规范

## 目录结构

```
app/domains/planning_v2/tests/
├── TESTING.md              # 本文件
├── conftest.py             # astral 缺失时的 mock patch
├── test_cp1.py             # CP1 契约测试（Step 1-4，52个）
├── test_cp1_quality.py     # CP1 效果测试（12用例，80个+7 xfail）
├── test_cp2.py             # CP2 契约测试（Step 5-7.5，44个）
└── test_cp2_quality.py     # CP2 效果测试（12用例，89个+1 xfail）
```

运行全套：

```bash
pytest app/domains/planning_v2/tests/ -v
```

---

## 测试分层

### 层 1：契约测试（test_cp1.py / test_cp2.py）

**目的**：验证步骤间的数据接口正确——字段存在、类型正确、边界行为符合预期。

**特征**：
- 不依赖真实 JSON 数据，用最小 fixture 构造输入
- AI 调用全部 mock（`unittest.mock.AsyncMock`）
- 运行极快（<2秒），适合 CI 阻断
- 覆盖：字段完整性、边界条件（空池、API 失败）、错误处理

### 层 2：效果测试（test_cp1_quality.py / test_cp2_quality.py）

**目的**：用真实关西数据验证业务逻辑的效果——攻略顾问视角，结果合不合理。

**特征**：
- 依赖 `data/kansai_spots/archived_ai_generated/` 真实数据
- AI 调用使用规则 fallback，不打真实 API
- 用 `@pytest.mark.xfail(strict=True)` 追踪已知问题
- 覆盖：12个真实用例（见下表），4个维度（人群/天数/季节/预算）

---

## 12 个效果测试用例

| ID | 名称 | 人群 | 天数 | 季节 | 预算 | 城市 | must_visit | 特殊验证 |
|----|------|------|------|------|------|------|-----------|---------|
| c01 | 情侣初次5天 | couple | 5 | 春/樱花 | mid | kyoto/osaka/nara | 伏见稻荷/金阁寺/道顿堀 | 京都天数≥大阪；樱花景点入池 |
| c02 | 闺蜜4天夏 | friends | 4 | 夏 | premium | kyoto/osaka | 心斋桥 | 大阪景点≥5；summer-only不混入 |
| c03 | 独行7天冬 | solo | 7 | 冬 | budget | 5城 | — | 5城全出现；spring景点被过滤；budget上限 |
| c04 | 带娃4天秋 | family_young_child | 4 | 秋 | mid | kyoto/osaka | USJ | USJ→大阪天；do_not_go/visited排除 |
| c05 | 带父母5天红叶 | family_parents | 5 | 红叶 | premium | kyoto/osaka/nara | 金阁寺/岚山 | 红叶景点大量入池；有马温泉(xfail) |
| c06 | 蜜月6天春 | honeymoon | 6 | 新绿 | luxury | kyoto/osaka/kobe | — | 神户独立安排；luxury≠mid |
| c07 | 二刷3天梅雨 | couple | 3 | 梅雨 | mid | kyoto/osaka | — | 6个visited全排除；深度景点入池 |
| c08 | 大学生4天暑假 | friends | 4 | 夏 | budget | osaka/kyoto | USJ/道顿堀 | budget cap=1000；夜生活景点 |
| c09 | 带学龄娃5天冬 | family_school_age | 5 | 冬/年末 | premium | kyoto/osaka/nara | USJ | spring景点被过滤；年末活动缺失(数据) |
| c10 | 独行女3天初秋 | solo | 3 | 初秋 | mid | kyoto | — | 只有kyoto圈；photo景点；3天=short tier |
| c11 | 6人团5天春 | group | 5 | 春初 | mid | kyoto/osaka/nara | 伏见/奈良鹿 | 奈良有独立安排；spring景点入池 |
| c12 | 程序员8天黄金周 | solo | 8 | 黄金周 | mid | 7城 | — | 7城全出现；5个visited排除；最大候选池 |

---

## 复用层设计

效果测试通过导入共用数据层，避免重复实现：

```python
# test_cp2_quality.py 复用 test_cp1_quality.py 的数据层
from app.domains.planning_v2.tests.test_cp1_quality import (
    ALL_SPOTS,          # 所有关西景点 dict（id → spot）
    DATA_DIR,           # data/kansai_spots/archived_ai_generated/
    simulate_poi_pool,  # 模拟 Step 4 过滤逻辑（含 taxonomy.json 配置）
    simulate_fallback_plan,  # 模拟 Step 3 fallback 城市组合
    _expand_cities,     # taxonomy.json 城市圈扩展
    _ADMISSION_CAP,     # budget_tier → 门票上限
)
```

### simulate_poi_pool 参数说明

```python
simulate_poi_pool(
    circle_cities: list[str],   # 用户选择的城市（不含子区域，函数内自动扩展）
    travel_month: int,          # 旅行月份（1-12）
    do_not_go: list[str] = [],
    visited: list[str] = [],
    must_visit: list[str] = [], # must_visit 豁免门票上限过滤
    party_type: str = "couple",
    budget_tier: str = "mid",
    total_days: int = 5,        # 决定 grade_filter: ≤3→[S,A], 4-5→[S,A,B], ≥6→[S,A,B,C]
) -> list[dict]                 # 返回原始 spot dict，不是 CandidatePool
```

### _build_poi_candidates（CP2 层的包装）

```python
# test_cp2_quality.py 内部函数，将 simulate_poi_pool 的 dict 转为 CandidatePool
def _build_poi_candidates(...) -> list[CandidatePool]
```

### _make_hotel_pool（CP2 层的酒店构造）

```python
# 从 archived_ai_generated/hotels_*.json 构造酒店候选池
# 读取字段：area.city_code, pricing.off_season_jpy, tags
def _make_hotel_pool(circle_cities: list[str], budget_tier: str) -> list[CandidatePool]
```

---

## xfail 已知问题追踪

xfail 使用 `strict=True`，修复后会变 XPASS（pytest 报错），强制更新标注。

| 测试 | 根因 | 修复责任 |
|------|------|---------|
| `test_c03_himeji_castle_in_winter_pool` | 姬路城 `best_season=spring`，全年开放 | 数据：改为 `all` |
| `test_c05_arima_onsen_in_pool` | arima 属于 hyogo region，不在 kyoto/osaka/nara 圈 | taxonomy.json 配置 |
| `test_c05_kimono_in_autumn_pool` | 和服体验 `best_season=spring`，全年可穿 | 数据：改为 `all` |
| `test_c10_b_grade_photo_spots_present` | 3天 short tier 只含 S/A，哲学之道/蹴上(B)不入 | 产品决策（3天要不要B级）|
| `test_c12_uji_byodoin_in_spring_pool` | 平等院 `best_season=autumn`，全年开放 | 数据：改为 `all` |
| `test_c12_hieizan_in_spring_pool` | 比叡山 `best_season=autumn`，全年开放 | 数据：改为 `all` |
| `test_p1_arima_reachable_from_osaka_nara_circle` | arima 跨圈关联未建立 | taxonomy.json 配置 |
| `test_cp2_core_assertions[c03]` | 姬路城 spring only，himeji 冬季池为空 | 数据（同上） |

---

## 测试规范

### 不做的事

- 不调真实 Anthropic API（用 mock 或规则 fallback）
- 不写 `assert xxx not in ids` 来"验证问题存在"——改用 `xfail`
- 不用测试内部参数（如 `grade_filter`）模拟未实现的生产功能
- 不在 xfail reason 里写"数据有待优化"——写具体的修复路径

### 必须做的事

- xfail 用 `strict=True`，修复后框架自动提醒
- 每个 xfail 的 reason 说明：问题是什么 + 怎么修
- AI 调用 mock 用 `unittest.mock.AsyncMock`
- 效果测试的断言必须反映顾问视角，不只是结构正确性

### CI 运行

```bash
# 快速：只跑契约测试（阻断 CI）
pytest app/domains/planning_v2/tests/test_cp1.py app/domains/planning_v2/tests/test_cp2.py

# 完整：包含效果测试
pytest app/domains/planning_v2/tests/ -v

# 只看失败和 xfail
pytest app/domains/planning_v2/tests/ -v --tb=short 2>&1 | grep -E "FAILED|XFAIL|XPASS|ERROR"
```

---

## 数据路径说明

```
data/kansai_spots/
├── taxonomy.json                    # 城市圈定义、grade 体系、画像加成规则
├── corridor_definitions.json        # 走廊定义
└── archived_ai_generated/           # AI 生成的关西景点/餐厅/酒店数据
    ├── kyoto_city.json              # 京都市区 48 个景点
    ├── kyoto_extended.json          # 京都外围（宇治/天桥立）7 个景点
    ├── osaka_city.json              # 大阪 24 个景点
    ├── nara.json                    # 奈良 22 个景点
    ├── hyogo.json                   # 兵库（神户/姬路/有马/城崎）32 个景点
    ├── shiga.json                   # 滋贺（大津/彦根）10 个景点
    ├── hotels_kyoto.json            # 京都酒店
    ├── hotels_osaka.json            # 大阪酒店
    ├── hotels_nara.json             # 奈良酒店
    ├── hotels_hyogo.json            # 兵库酒店
    └── ...
```

总计：143 个景点，182 家酒店（用于效果测试）。
