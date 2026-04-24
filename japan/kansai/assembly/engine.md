# 装配引擎行为规范（D40·2026-04-24）

> 装配引擎（脚本+Opus）读这份 md 决定「模板 JSON + 用户参数 → 实际时间表」怎么算。
> 消费方：`scripts/assemble_schedule.py`（时间平移）+ 装配 Opus（餐厅/酒店挑选）。
> 关联：[plans/写作规范.md](../plans/写作规范.md)（方案作者）+ [SCHEMA.md §1.3](../../../docs/03_数据契约/SCHEMA.md)（字段定义）。

---

## 一、装配引擎的 4 个职责

1. **匹配预制方案**：用户输入 → `plans/{天数}日_{主题}.md` 挑一套
2. **解读方案**：按方案骨架执行·方案写死 template_id 直接装·方案给候选列表按规则挑
3. **时间平移**：`assemble_schedule.py` 按 `pace_type` + `time_sensitivity` + 用户出门档 → 实际时刻
4. **餐厅/酒店挑选**（Opus）：按 slot 的 `meal_area` / `hotel_area` 读 `assembly/restaurants/` + `assembly/hotels/` 挑

**装配引擎不做**的事：
- 不从全关西模板池里打分挑最优（那是方案作者手工排的优先级）
- 不检查跨日互斥（由方案作者写方案时保证）
- 不判 fixed_early/deep_stay 数量限制（方案作者自律）

---

## 二、pace_type 三档装配行为

模板 JSON 顶层字段 `pace_type`·决定时间平移逻辑。

| pace_type | 定义 | 装配行为 |
|---|---|---|
| `adaptive`（默认） | 用户主导节奏 | slots 按 9 点档基准写·按用户出门档（8/9/10）自动平移·午晚餐锚点另算（见 §三） |
| `fixed_early` | 体验主导节奏·晨光轨迹 | **绝对时间不平移**·用户必须勾选「愿意为出片早起一次」才入候选·起晚了读 contingencies.late_start |
| `deep_stay` | 两日连住 | **D1/D2 slots 不平移**·子类 `onsen` / `deep_local` |

**写作约定**：
- `adaptive` 是默认·可省略字段
- `fixed_early` / `deep_stay` 必写

---

## 三、adaptive 三档平移（assemble_schedule.py 实现）

adaptive 模板 slots 以 **9 点档为基准**·装配按用户档位平移：

| 档位 | start | lunch | dinner |
|---|---|---|---|
| 8 点 | 08:00 | 12:00 | 18:00 |
| 9 点 | 09:00 | 12:30 | 18:30 |
| 10 点 | 10:00 | 13:00 | 19:00 |

**关键**：lunch / dinner 锚点**按档位走**·不跟早出门整体前移（吃饭是生理约束·8 点出门也 12:00 才吃）。

**slot.time 支持两种写法**：
- `09:00-10:00` 绝对时间（9 点档基准）·引擎就近归锚点自动平移 ✅ **推荐**
- `start+0h00-+1h00` 显式相对锚点偏移（留给极特殊情况）

---

## 四、time_sensitivity 三档装配行为

模板 JSON 顶层字段 `time_sensitivity`·回答「时间约束有多硬」。

| time_sensitivity | 定义 | 装配行为 |
|---|---|---|
| `flexible`（默认） | 早去晚去都无所谓 | 不提醒·按 pace 平移·可省略字段 |
| `soft` | 晚去光线差 / 定期班次可对齐 | 装配侧小提醒·引擎可 ±20 分钟微调 start 匹配光线/班次/场次（lunch/dinner 不动）|
| `hard` | 固定时刻·错过 = 产品崩 | 装配层按约束时刻判用户档兼容性·不兼容换模板·手账本重点提醒·必须写 `contingencies.late_start` Plan B |

**举例**：
- `flexible`：锦市场/商店街/鸭川散步
- `soft 光线型`：金阁寺/伏见稻荷/岚山竹林/日出日落机位
- `soft 班次型`：嵯峨野小火车 1 小时一班·抽签每 20 分钟一场
- `hard`：祇园祭巡行 9:00 / 五山送火 20:00 / USJ 快速券 / 一天一场预约餐厅

---

## 五、pace_type × time_sensitivity 组合

| pace_type | time_sensitivity | 写作要求 |
|---|---|---|
| adaptive | flexible | 默认组合·两个字段可省 |
| adaptive | soft | time_sensitivity_note 必写·引擎 ±20 分钟弹性匹配 |
| adaptive | hard | time_sensitivity_note 必写·contingencies.late_start 必写 |
| fixed_early | hard | 标配·contingencies.late_start 必写（错过晨光窗口怎么办）|
| deep_stay | flexible | 标配·D1/D2 不平移 |

**错配禁止**：
- ❌ `fixed_early + flexible`（fixed_early 本质就是 hard）
- ❌ `deep_stay + hard`（两日连住节奏不应有硬时刻·jingji 夜樱那种写在 D1 slot 的 note 里即可）

---

## 六、餐厅/酒店装配

slot 层写 `meal_area` / `hotel_area`·**不写具体 entity**·装配 Opus 按规则从池挑。

- **餐厅装配**：读 `assembly/restaurants/准入标准.md` + `写作规范.md` + `{城市}/{区域}.md`·按 A/B 档位 + 人群 + 避让规则 + 价格档挑
- **酒店装配**：读 `assembly/hotels/准入标准.md` + `写作规范.md` + `{城市}/{类型}/*.md`·按便利型/体验型 + 预算 + 动线起点挑

详见各自的 `准入标准.md` 和 `写作规范.md`·本文不重复。

---

## 七、不在引擎层处理的事

**这些是方案作者职责**（见 [plans/写作规范.md](../plans/写作规范.md)）：

- 跨日互斥（温泉 ≤1·fixed_early ≤1·宇治不和奈良同日）
- 关西 7 条化学反应
- 候选列表优先级排序
- 内容防重复（D1 神户走港口线·D3 神户不再装）
- 跨城组合（神户+有马 / 神户+姬路）

**这些是模板作者职责**（见各动线的 `动线说明.md`）：

- 动线内的变体设计
- 同动线变体互斥
- 动线骨架（peak-end / 情绪弧线）

---

## 八、assemble_schedule.py 调用约法

```bash
python scripts/assemble_schedule.py <template.json> <user_pace> [start_shift_min]
```

- `user_pace`：`08:00` / `09:00` / `10:00`
- `start_shift_min`：可选·±20 范围内·仅 soft/hard 模板可用（默认 0）

输出：每个 slot 的实际时刻 + pace_type / time_sensitivity 说明 + 锚点状态。

引擎内部处理：
- `adaptive` 模板：按 user_pace 就近归锚点平移
- `fixed_early` 模板：绝对时间不平移（user_pace 参数被忽略）
- `deep_stay` 模板：D1/D2 slots 不平移（user_pace 参数被忽略）

**引擎不处理**：
- 模板挑选（方案层决定）
- 候选优先级（方案层决定）
- 餐厅酒店装配（装配 Opus 决定）
