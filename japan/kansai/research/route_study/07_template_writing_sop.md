# 模板写作 SOP（从 Arashiyama 样板沉淀）

> 从 Arashiyama 早春日模板（含 2 次 AI 外评、3 轮修改）沉淀的方法论。
> 目标：剩下 20 个模板不用反复打磨，按 SOP 一次做到 80% 水平。

---

## 1. 核心原则（不妥协项）

### 1.1 数据真实性红线（CLAUDE.md 核心）

**所有事实性字段必须可验证，不编造。**

| 类型 | 规则 |
|------|------|
| 精确数字（比例/百分比）| 不写"1/3""40%"这种——无权威来源就改定性（"明显低于""大部分"） |
| 店铺/餐厅 | 必须搜索过店名+位置；不确定的不写，或改为类别描述（"本地豆腐老铺"）|
| 票价/开放时间 | 搜索一次作为基线，并标"出发前查官网" |
| 影视/动漫取景地 | 必须搜索确认，不凭印象 |
| 历史典故/民间传说 | 标"相传""传说""据说"，不把民间说法写成史实 |
| 温度/天气 | 避免过度具体预测（"5-8°C"），写定性或提示"查天气预报" |

### 1.2 peak-end 必须钉死
黄昏/收尾 slot 是独立 slot，不能被晚餐、自由漫游挤掉。`day_peak.peak_end_line` 必须对应一个具体 slot 的时间段。

### 1.3 core_entities 反映真实核心
不只是当天活动主体。如 Arashiyama 最终核心是**竹林+天龙寺+渡月桥**三个，不是只写前两个。

### 1.4 minimum_viable 体现品牌诚意
保底方案要真诚——"只做渡月桥 1 小时也算来过岚山"比"无法成立就换其他模板"有诚意。

### 1.5 不煞风景原则（fun_fact）
fun_fact 氛围必须匹配当时场景。见 06 文档 §1.2。

### 1.6 绝不让用户在最终报告里做选择（产品哲学硬规则）

**brief.md §1 定义：策展产品，不是定制工具。**

模板正文（slot note / description）里**不能出现**：
- "三个方向任选"
- "都不会错，选一个"
- "(1) A (2) B (3) C"
- "两个方向：..."
- "分支可选" 作为 note 直接文字

这些全部属于"把决策扔回给用户"，违反产品哲学。

**正确写法**：
- `note` 字段写**默认人群的单一推荐**（用户看到的最终文案）
- `_assembly_variants` 字段写按人群/兴趣的变体覆盖（只给装配系统看）

**示例（Arashiyama 下午漫游段）：**
```json
{
  "time": "14:30-17:00",
  "type": "walk",
  "note": "嵐電嵐山站方向漫游：和服森林+駅の足湯泡脚...",  // 用户看到的单一方案
  "_assembly_variants": {
    "couple": "改为大河内山荘（小众庭院+抹茶）",
    "family": "改为嵐山モンキーパーク",
    "quiet_seeking": "改为嵯峨鳥居本"
  }
}
```

**只有 `contingencies`（应急预案）和 `nearby_shops`（附录信息）可以列多项**——因为那是"意外情况的参考"和"附录推荐"，不是主线决策。

**2026-04-17 Arashiyama 样板踩过的坑**：21 个模板里 16 个早期版本都犯了这个错误，必须扫描统一修复。

---

## 2. 字段必填/选填清单

### 2.1 所有模板必填
- template_id / label / template_kind / core_entities / weather_sensitive / selectable_tag / night_options
- score (含 base_score)
- description / hotel_area_note / slots
- day_peak
- contingencies (rain_light/rain_heavy/crowd/minimum_viable/swap_candidates)

### 2.2 选填（按模板性格判断）
- design_rationale —— 复杂动线/独特策展思路的模板填；简单打卡型（如任天堂博物馆单点）可略
- photo_spots —— 拍照型/景观型模板必填；体验型（手工艺/博物馆）可略
- nearby_shops —— 有自由时间的模板必填（按 brief §7 数量规则）；赶场型/主题乐园日可略
- fun_fact —— slot 内选填，不是每个 slot 都有
- early_spring_notes —— 早春特有信息有值得说的才填

---

## 3. 模板分层策略（不是每个都做到样板深度）

### Tier A 王牌模板（5-6 个）—— 完整版
定位：用户最可能选中、核心体验分 45+、装配高频出现。
- higashiyama_day（东山精华）
- kinkaku_kitano_day（金阁北山）
- nintendo_museum_day（任天堂）
- teamlab_kyoto_day（teamLab）
- arashiyama_day（本样板）
- (选) fushimi_sake_day / jonangu_shidare_ume_day

投入：所有字段+搜索验证+photo_spots 4 个+nearby_shops 5 家+fun_fact 2-3 个。

### Tier B 稳妥模板（8-10 个）—— 精简版
定位：主线候补、主题/人群专属、核心体验分 35-45。
- audience_couple_day / audience_friends_day
- kitano_ume_day / zuishinin_ono_ume_day
- kyoto_railway_aquarium_day
- fushimi_sake_day / jonangu_shidare_ume_day
- nijo_gosho_day / kyoto_craft_day
- sagano_torokko_day

投入：所有必填+photo_spots 2-3 个+nearby_shops 3 家+fun_fact 1-2 个。

### Tier C 小众/补位（4-5 个）—— 最小版
定位：用户要特定偏好才触发、核心体验分 20-35。
- ohara_day（大原）
- sagano_deep_day（奥嵯峨深度）
- okazaki_day（冈崎）
- kyoto_recovery_day（恢复日）
- kyoto_gear_night（GEAR 夜）
- arashiyama_onsen_stay（岚山温泉一泊）

投入：所有必填+contingencies+photo_spots 1-2 个（可略）+nearby_shops 略+fun_fact 0-1 个。

---

## 4. 写作流程（每个模板 SOP）

### Step 1：读旧模板 + 基础搜索（5-10 分钟）
- 读 `content/kansai/early_spring/kyoto/{xxx}.json` 旧模板
- 搜索关键信息：景点最新开放时间/票价、季节特有事件、近 1 年新开店铺或停业
- 搜索 1-2 个 fun_fact 素材（如有合适）

### Step 2：分层定位（1 分钟）
- 判断 Tier A/B/C
- 决定 score 范围（王牌 48-54 / 稳妥 40-47 / 中等 30-39 / 小众 20-29）

### Step 3：字段填充（15-30 分钟，按 Tier 投入）
按 §2 清单逐项填，slot 内 note 是大头。

### Step 4：自检（5 分钟，必做）
对照 §5 清单过一遍。

### Step 5：写入新目录
`content/kansai_v2/early_spring/kyoto/{new_id}.json`

---

## 5. 自检清单（每个模板必过）

### 5.1 逻辑一致性
- [ ] 时间线内部无矛盾（slot 时间 vs note 内容）
- [ ] peak-end 位置对应具体 slot
- [ ] core_entities 包含模板真正的核心（不只是主景点）
- [ ] priority 字段只标可删的 slot（必排不标）

### 5.2 数据真实性
- [ ] 所有店铺/餐厅名都是真实存在的（不确定的删掉）
- [ ] 精确数字（比例/价格/时长）都有来源或改为定性
- [ ] 历史典故/传说有"相传""据说"限定
- [ ] 影视取景地搜索过
- [ ] 温度/天气不过度预测

### 5.3 体验完整性
- [ ] contingencies 覆盖 rain_light/rain_heavy/crowd/minimum_viable
- [ ] rain_heavy 先本地版再跨模板
- [ ] minimum_viable 真诚不敷衍
- [ ] swap_candidates 3 个以内，真有替代性

### 5.4 语言规范
- [ ] 正文全中文
- [ ] 专有名词中日并存（天龍寺（天龙寺）、嵯峨野小火车（トロッコ列車））
- [ ] 不用"让我们""请注意"等教学体
- [ ] fun_fact 不煞风景（氛围匹配）

### 5.5 架构层次
- [ ] template_id 格式：`{核心实体ID}__{变种名}`
- [ ] 删除旧字段（tags/fit_audience/condition/assembly/slot_id/slot.area/duration_min）
- [ ] 每个 slot 要么有 entity（景点），要么有 meal_area（餐饮），要么都无（walk/free/info）

---

## 6. 容易踩坑清单（Arashiyama 踩过的坑，别再踩）

| 坑 | 原因 | 避免 |
|----|------|------|
| 时间线矛盾 | note 里写了"10 点做 X"但 slot 3 是 10 点做别的 Y | slot note 只写本 slot 的事，跨 slot 的动作不写 |
| peak-end 被挤 | 自由漫游放在黄昏后、晚餐放在峰值位置 | 黄昏 slot 必须是 daytime 最后一个硬 slot，晚餐定为"补给不是峰" |
| 数据 AI 编造 | "游客量不到下旬 1/3" 这种精确数字 | 所有数字都问"哪里查的"——查不到就改定性 |
| core_entities 漏核心 | 渡月桥本应是 core 之一但只写竹林+天龙寺 | minimum_viable 说的那个"灵魂景点"必须进 core_entities |
| 未验证店铺 | 编造"豆腐専門店 稲" 这种店名 | 店名必须有来源；不确定就删或改类别描述 |
| 晚餐 priority 标错 | 晚餐标 P2（可删），但晚餐本应必排 | "吃晚餐"必排（不标 priority），"在某地吃"才可变（写在 note） |
| 温度过度具体 | "清晨 5-8°C，白天 10-13°C，黄昏 8-10°C"被 AI 评审说过度担心 | 一句话"早春偏冷，查天气预报"就够 |

---

## 7. 如何"学习经验做到位" —— 防止退化

### 7.1 每次写新模板后
- 新发现的坑（Arashiyama 清单之外）→ 补到 §6
- 新发现的 fun_fact 素材 → 补到 06 文档 §2
- 新发现的店铺验证结果 → 记录数据来源

### 7.2 看自己的产出
批量做完 5 个模板后，抽一个回读，问：
- 我会不会付 348 元买这个模板？
- 如果是真的旅行顾问看到，会不会觉得我用了脑子？

如果不会 → 回改上一批。

### 7.3 不要过度优化
**单个模板不要反复评审 3 轮以上**。SOP 目标是"一次做到 80%"，不是"一次做到 100%"。做完 5 个再集体回改，比单个反复调整成本低。
