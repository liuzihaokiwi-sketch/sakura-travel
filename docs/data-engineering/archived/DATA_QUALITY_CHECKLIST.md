# 数据质量检查清单

> 版本: 1.0
> 更新: 2026-04-01
> 用途: 每批数据生成后、导入DB前执行

---

## 〇、现有关西数据真实性盘点

**核心发现：所有数据均为AI生成（`claude_knowledge`），无真实平台数据验证。**

| 类别 | 条数 | 看起来像真实数据的字段 | 实际来源 | 可信度 |
|------|------|----------------------|---------|--------|
| 景点 | 171 | google_rating, google_review_count | `claude_knowledge`（AI根据训练数据推断，未经API验证） |  格式像真的但值可能不准 |
| 餐厅 | 380 | tabelog_score, google_rating, michelin_stars | `claude_knowledge`（AI推断，非爬取） |  米其林星级较可信，Tabelog分可能偏差>0.1 |
| 酒店 | ~250 | 无真实平台评分 | 全部AI估算 |  score_range是模糊区间，价格全估算 |

**验证方法：随机抽10家餐厅去Tabelog官网对比tabelog_score，如偏差>0.1则全量标记不可信。**

**注意：data_sources_registry.json里明确列了Tabelog状态"available"、Google Places也"available"，说明爬虫能力是有的，但没用上就直接让AI编了。这个错误不可再犯。**

---

## 一、已知问题清单（关西 2026-04）

### CRITICAL

| # | 问题 | 文件 | 影响 | 状态 |
|---|------|------|------|------|
| 0 | **全量数据无真实数据源验证** | 所有文件 | 全部数据不可信 | 待真实数据回填 |
| 1 | 坐标经纬度反转 | hotels_hyogo.json (22条), hotels_onsen.json (15条), hotels_onsen_p2.json (18条) | 地图定位全错 | 待修 |

### HIGH

| # | 问题 | 文件 | 影响 | 状态 |
|---|------|------|------|------|
| 2 | 景点缺 reservation_required 字段 | 8个景点JSON | 171条全缺 | 待修 |
| 3 | 奈良景点 open_hours 为空 | nara.json | 22条 | 待修 |
| 4 | 餐厅时间格式含括号注释 | restaurants_kyoto_high.json 等 | 44条 | 待修 |

### MEDIUM

| # | 问题 | 文件 | 影响 | 状态 |
|---|------|------|------|------|
| 5 | 餐厅 grade 使用 A+/B+ | 多个餐厅文件 | A+:43条, B+:8条 | 待修 |
| 6 | 酒店 experience.grade 为 null | 多个酒店文件 | 79条(39%) | 待修 |
| 7 | 酒店缺 check_in/check_out 字段 | 全部酒店文件 | 全部缺失 | 待修 |
| 8 | 酒店缺 meals_included 字段 | 全部酒店文件 | 全部缺失 | 待修 |
| 9 | 景点 last_entry 为 null | 多个景点文件 | 93条 | 低优先 |

---

## 二、自动校验规则

以下规则应写入校验脚本 `scripts/validate_data.py`，每次数据变更后运行。

### 2.1 通用规则

```
RULE-001: JSON文件必须能正确解析
RULE-002: 所有ID在同类数据中唯一（跨文件检查）
RULE-003: coord[0]（纬度）在 24.0-46.0 之间
RULE-004: coord[1]（经度）在 122.0-154.0 之间
RULE-005: 如果 coord[0] > 100，标记为"经纬度反转"
RULE-006: grade 只允许 S/A/B/C，不允许 null/A+/B+
```

### 2.2 景点规则

```
RULE-101: when.open_hours 非空时必须匹配 /^\d{2}:\d{2}-\d{2}:\d{2}$/
RULE-102: when.reservation_required 必须是 boolean
RULE-103: cost.admission_jpy >= 0
RULE-104: visit_minutes > 0
RULE-105: main_type 必须是 fixed_spot/area_dest/experience
RULE-106: sub_type 必须在 taxonomy.json 中定义
```

### 2.3 餐厅规则

```
RULE-201: when.lunch_hours 非空时匹配 /^\d{2}:\d{2}-\d{2}:\d{2}$/（无括号）
RULE-202: when.dinner_hours 同上
RULE-203: cost.lunch_min_cny == cost.lunch_min_jpy * 0.05（允许±1误差）
RULE-204: budget_tier 必须是 luxury/premium/mid/budget/street
RULE-205: cuisine 必须在 DATA_SCHEMA.md 菜系码枚举中
RULE-206: wagyu_grade 非null时必须是 kobe_a5/tajima/omi/matsusaka/a4_wagyu/domestic
RULE-207: is_city_must_eat 为 true 时 must_eat_reason 不能为空
```

### 2.4 酒店规则

```
RULE-301: experience.grade 不允许 null（功能性住宿标C）
RULE-302: hotel_type 必须在枚举中
RULE-303: pricing.*_jpy 必须是长度2的数组，且 [0] <= [1]
RULE-304: check_in 匹配 /^\d{2}:\d{2}$/
RULE-305: check_out 匹配 /^\d{2}:\d{2}$/
RULE-306: meals_included 必须包含 breakfast 和 dinner 两个 boolean 字段
RULE-307: price_level 必须是 luxury/expensive/moderate/budget/backpacker
```

---

## 三、修复操作规范

### 3.1 坐标反转修复

```python
# 检测：coord[0] > 100
# 修复：交换 coord[0] 和 coord[1]
for hotel in data['hotels']:
    if hotel['coord'][0] > 100:
        hotel['coord'] = [hotel['coord'][1], hotel['coord'][0]]
```

### 3.2 Grade 标准化

```python
# 餐厅: A+ → A, B+ → B
grade_map = {'A+': 'A', 'B+': 'B'}
for r in data['restaurants']:
    if r['grade'] in grade_map:
        r['grade'] = grade_map[r['grade']]

# 酒店: null → C（功能性住宿）
# 但如果 experience.types 非空，需要人工判断
for h in data['hotels']:
    if h['experience']['grade'] is None:
        if h['experience']['types']:
            # 有体验标签但没评级 → 标记待人工审核
            pass
        else:
            h['experience']['grade'] = 'C'
```

### 3.3 时间格式清洗

```python
import re

def clean_hours(s):
    """去掉括号注释，提取 HH:MM-HH:MM"""
    if not s or s == 'null':
        return None
    # 去掉括号内容
    s = re.sub(r'[（(][^）)]*[）)]', '', s).strip()
    # 匹配时间格式
    match = re.match(r'(\d{2}:\d{2})-(\d{2}:\d{2})', s)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    # 只有开始时间
    match = re.match(r'(\d{2}:\d{2})-?$', s)
    if match:
        return None  # 需要人工补结束时间
    return None
```

### 3.4 缺失字段批量补充

```python
# 景点补 reservation_required
for spot in data['spots']:
    if 'reservation_required' not in spot.get('when', {}):
        # 默认 False，以下情况标 True：
        # - risk_flags 含 'requires_reservation'
        # - tags 含 '需预约'
        needs = ('requires_reservation' in spot.get('risk_flags', []) or
                 '需预约' in spot.get('tags', []))
        spot['when']['reservation_required'] = needs

# 酒店补 check_in/check_out/meals_included
for hotel in data['hotels']:
    if 'check_in' not in hotel:
        # 默认值（后续人工或API补充精确值）
        hotel['check_in'] = '15:00'
        hotel['check_out'] = '11:00' if hotel['hotel_type'] != 'ryokan' else '10:00'
    if 'meals_included' not in hotel:
        # 从 price_note 推断
        pn = hotel.get('pricing', {}).get('price_note', '')
        hotel['meals_included'] = {
            'breakfast': '早' in pn or '朝食' in pn,
            'dinner': '晚' in pn or '夕食' in pn or '两餐' in pn
        }
```

---

## 四、校验脚本使用

```bash
# 校验全部数据
python scripts/validate_data.py --all

# 只校验某个文件
python scripts/validate_data.py --file data/kansai_spots/hotels_hyogo.json

# 自动修复可修复的问题
python scripts/validate_data.py --all --fix

# 只报告不修复
python scripts/validate_data.py --all --report-only
```

---

## 五、数据变更日志

每次批量修改数据后，在此记录：

| 日期 | 操作 | 影响文件 | 影响条数 | 操作人 |
|------|------|---------|---------|--------|
| 2026-04-01 | 初始采集 | 全部 | 景点171+餐厅380+酒店300 | AI |
| | | | | |
