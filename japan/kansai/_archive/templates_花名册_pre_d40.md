# 模板装配

> 装配引擎（Opus）读这份 markdown 决定"用户的 N 天行程每天装哪个模板"。
> 建于 2026-04-22（D36）。
> 消费方：AI 装配。用中文书写。

## 这份文档回答什么

- 哪些模板存在、每个长什么样（不重复模板 JSON 的动线细节，只抽装配要看的元属性）
- 每个模板什么条件下入候选池（天数门槛、季节窗口、selectable_tag 勾选）
- 模板之间的关系（哪些互斥、哪些能接夜模块）
- 模板在不同人群/档位下的打分

不回答：
- 具体动线怎么排（看模板 JSON 的 slots）
- 餐厅挑哪家（看 [餐厅装配.md](餐厅装配.md)）
- 酒店挑哪家（看 [酒店装配.md](酒店装配.md)）
- 字段定义（看 [SCHEMA.md §3](../../../docs/03_数据契约/SCHEMA.md)）

---

## 一、装配原则（人读；AI 按这些判断）

### 1.1 模板是"原料"，不是"菜单"

模板自己只管"一条动线怎么走"。**是否装入、跟什么搭配、餐厅酒店挑哪家**——全由装配决定。模板不 claim 自己"适合 5 天以下行程"或"适合情侣"，那是这份文档管的。

### 1.2 装入候选池的四道筛

按顺序筛：

1. **季节窗口命中**：用户出行日期落在模板 `applicable_dates` 范围内。常年模板（`applicable_dates: []`）任何日期都命中。
2. **最少天数门槛**：用户总天数 ≥ `min_days`（若不配置则默认 0，所有天数都过）。
3. **selectable_tag 过滤**：如果模板有 `selectable_tag`（USJ / 温泉 / 和服 / 手作等），用户表单必须勾选对应项。`null` 的不过滤。
4. **互斥检查**：同一天不能装 `exclusive_with` 关系里的两个模板。

### 1.3 打分用于排序，不是入选

模板入候选池后，用打分决定"哪个模板排在哪一天、哪些被挤掉"。**入池是硬筛，排序是软筛**。

`final_score = core_experience × (1 + audience_bonus[人群] / 100) + execution_risk`

- `core_experience`：0-60 通用体验质量
- `audience_bonus`：-15 ~ +20，除 100 作乘数（保留高分模板的差距）
- `execution_risk`：0 / -1 / -2 / -3 负数修正

### 1.4 day_type 决定"这天能不能降档"

某些模板是"这天的灵魂"，任何密度都不能砍：
- `theme_park`（USJ 日）→ 无论用户选 packed/balanced/relaxed，都用 packed slots
- `audience_day`（人群日）→ 核心序列不砍
- `arrival` / `departure`（到达/离开日）→ 专属处理
- `regular`（常规）→ 按用户密度档正常取三档 slots 之一

### 1.5 night_options：夜模块怎么挂

白天模板结束后可以挂 `night_module` 类型的模板。白天模板在这份文档里列出 `night_options: [night_template_ids]`。装配按用户密度 + 体力余量决定要不要挂。

### 1.6 selectable_tag 枚举

| 值 | 触发 | 示例模板 |
|---|---|---|
| `null` | 装配自动判断 | 多数常规模板 |
| `onsen` | 用户勾选"想泡温泉一泊" | 有马 2day / 岚山温泉 2day |
| `usj` | 用户勾选"想去环球影城" | osk_usj_core_full |
| `kimono` | 用户勾选"想穿和服" | 东山和服日 / 岚山和服日 |
| `craft` | 用户勾选"想体验手作" | 京都工艺 half |
| `teamlab` | 用户勾选"想看数字艺术" | teamLab 模板 |
| `nintendo` | 用户勾选"想去任天堂博物馆" | 任天堂模板 |
| `maiko` | 用户勾选"想体验舞妓" | 舞妓座敷 |
| `gear` | 用户勾选"想看沉浸剧" | GEAR 齿轮秀 |

---

## 二、pace_type 特殊模板总库（D39·2026-04-24）

> 装配层读这两张表判「用户行程能装几个 fixed_early / deep_stay」，硬顶在这里。
> 详细判准见 [SCHEMA §1.3.1](../../../docs/03_数据契约/SCHEMA.md)。

### 2.1 fixed_early 总库（全关西 5 个·一次行程 ≤ 1）

四要素硬规（缺一不做）：(A) 出片价值+早晚差异大到"灵魂不同" (B) 晨光独家窗口 6:30-8:00 不可替代 (C) 用户 6:30-7:00 起床可达 (D) 市区短交通+拍完能回酒店睡回笼。

| # | 模板 | 季节 | 差异化灵魂 | 状态 |
|---|---|---|---|---|
| 1 | kyo_arashiyama_5 岚山出片一日 | 常年（樱/红加成）| 三机位晨光轨迹（6:30 渡月桥→7:30 竹林→8:30 曹源池）| ✅ 已有·**D39 唯一远郊例外**（不依赖睡回笼·晨光轨迹叙事本身是产品）|
| 2 | kyo_higashiyama_X 清水独享·樱花版 | 3/28-4/5 | 7:00 前清水舞台樱花无人+石塀小路空镜 | ⏳ 待建 |
| 3 | kyo_higashiyama_X 清水独享·红叶版 | 11/15-12/5 | 7:00 前清水红叶+子安塔背景无人 | ⏳ 待建 |
| 4 | kyo_higashiyama_X 清水独享·常年版 | 常年 | 7:00 前石塀小路+三年坂无人+和服空镜 | ⏳ 待建 |
| 5 | kyo_fushimi_X 伏见稻荷无人鸟居 | 常年（含樱/红加成）| 7:00 前千本鸟居独走 vs 10:00 每 2 米一人 | ⏳ 待建 |

**硬规**：
- 一次行程 **≤ 1 个 fixed_early**（用户必须明确勾选「愿意为出片早起一次」才入池）
- 装配优先级：deep_stay > fixed_early > adaptive（两日深度覆盖出片体验的不再叠 fixed_early）
- 触发失败（未按时到锚点）降级到对应 adaptive 模板

**远郊不合格**（D39 硬规·永久排除）：岚山（除 5 号出片例外）/ 高雄 / 吉野山 / 高野山 / 金阁寺 / 天龙寺 / 多数塔头寺院。

### 2.2 deep_stay 总库（全关西 7 个·onsen ≤ 1 · deep_local ≤ 1）

两个子类：
- **onsen**：温泉旅馆本身是产品核心（怀石+汤浴+朝食+浴衣仪式）
- **deep_local**：住本地才能捕捉的晨/夜独享片段

| # | 模板 | 子类 | 季节 | 住一夜的独家价值 |
|---|---|---|---|---|
| 1 | kyo_arashiyama_8 岚山温泉一泊 | onsen | 常年 | 翠岚等岚山本地温泉旅馆·怀石+朝食+D2 松节奏 |
| 2 | kyo_arashiyama_9 岚山红叶深度两日 | deep_local | 红叶 11/15-12/5 | D2 6:45 无人红叶竹林+三寺从容+D1 宝严院夜枫 |
| 3 | kyo_arashiyama_10 岚山樱花深度两日 | deep_local | 樱花 3/28-4/5 | D2 6:30 无人樱花竹林+曹源池 2h+D1 天龙寺/宝严院夜樱 |
| 4 | arm_arima_1 有马温泉一泊 | onsen | 常年 | 金泉银泉旅馆+怀石+D2 温泉规范 |
| 5 | arm_arima_3 有马红叶温泉一泊 | onsen | 红叶 11 月上旬 | 比京都早 1-2 周红叶+温泉 |
| 6 | kns_kinosaki_1 城崎温泉外湯巡り | onsen | 常年（冬蟹加成）| 7 馆外湯巡り+浴衣街道+松叶蟹会席 |
| 7 | kys_koyasan_1 高野山宿坊一泊 | deep_local | 常年 | 宿坊精进料理+早朝勤行+奥之院夜间+D2 清晨 |

**硬规**：
- 一次行程 **onsen ≤ 1 个**·**deep_local ≤ 1 个**（资源占位考虑）
- 装配优先级：deep_stay > fixed_early > adaptive
- onsen 和 deep_local 可同行程并存（如「有马 1 + 岚山 10」两日深度并立）
- arm_arima_4（神户+有马三日组合）不贴 deep_stay 标·是装配层拼接的行程模板·不计入本表

**不贴 deep_stay 的伪候选**（排除理由）：
- nar_nara_2 法隆寺斑鸠两日 → 是"一日延伸"不是"住本地才成立"，归 adaptive
- kyo_takao_2 高雄温泉一泊 → 有马/岚山温泉已覆盖 onsen 名额·takao_2 作为 onsen 候选池不入 deep_stay 主库（用 day_type=onsen_2day 区分）

### 2.3 其他动线统一归 adaptive

除上面 12 个模板外，全关西所有变体归 **adaptive 默认档**（按用户 8/9/10 出门档自动平移 slots）。这包括：
- 所有带时间约束的模板（小火车班次 / 抽签时刻 / 祭典 / 夜樱 / 日出机位）——用 `time_sensitivity=soft/hard` 字段表达，不贴 fixed_early
- 所有远郊动线（鞍马贵船 / 宇治 / 高雄 / 吉野山 / 奈良 / 神户等）
- 所有半日 / 特殊事件 / 到达离开日

---

## 三、关西 7 条化学反应（互斥与顺序硬规）

> 复刻自 [产品原则.md §12](../产品原则.md)，装配遇到这几种情况必须遵守。

1. **先京都后大阪** —— 状态好时沉浸京都，末尾切换大阪。例外：特种兵档反向更合理（大阪适合时差恢复）。
2. **奈良永远作为"桥"** —— 奈良→大阪 JR 直通 50 分钟，不独立安排过夜，顺路塞。
3. **姬路+神户一天组合** —— 姬路上午、神户下午，铁路顺路。
4. **宇治不能和姬路/奈良同一天** —— 宇治要慢，跟大景点组合变走马观花。
5. **京都-大阪不需要过渡缓冲** —— 15 分钟新干线，切换快反而产生对比。例外：沉浸式町家住宿切换大阪商业区，京都吃完晚饭再过去。
6. **京都超过 5 天切日归模式** —— 第 4-5 天安排奈良/宇治/嵯峨保持新鲜。
7. **神户 2 晚 + 有马温泉** —— 第 1 天港口/牛肉/灘酒造，第 2 天下午有马。

装配层的 `exclusive_with` 字段用于表达第 4 条（宇治 vs 姬路/奈良）这种"不能同日"的硬约束。

---

## 三、模板花名册

> 每个模板一段元属性 + 打分。按 D37 城市/动线组织。
> 打分依据：`[XHS]` 小红书爆款（opencli，优先 collects>likes）；`[JG]` japan-guide；`[Entity]` 事实层数据；`[Research]` japan/kansai/research/insights.md；`[原则]` 产品原则.md。
> 打分公式：`final_score = core_experience × (1 + audience_bonus/100) + execution_risk`

### 字段说明

- **core_experience**（0-60）：通用体验质量。60 = 国际级必到（稻荷/清水/岚山/奈良公园），40-50 = 京都大阪核心不可错过，30-40 = 优质延伸，20-30 = 利基/小众。
- **audience_bonus**（-15 ~ +20）：人群加成。情侣/朋友/家庭三档。
- **execution_risk**（0 / -1 / -2 / -3）：执行风险扣分。依赖早起/班次/预约/路远/天气敏感。
- **min_days**：用户总天数 ≥ 此值才入池。0 = 任意天数。
- **day_type**：`regular` / `theme_park` / `audience_day` / `arrival` / `departure` / `onsen_2day` / `remote_2day` / `special_event` / `fixed_early` / `half_day` / `night_module`。
- **selectable_tag**：用户必须勾选的标签才入池；`null` = 常规自动判断。
- **exclusive_with**：同日不可共存的 template_id 列表。
- **night_options**：白天模板结束后可挂的夜模块 template_id 列表。

---

### 3.1 京都·岚山（kyoto/arashiyama·10 变体）

**打分依据**：
- [XHS] 「京都岚山真的好治愈🍃一日游攻略」collects=4236 likes=4 —— 岚山是京都一日游最高传播力动线，小火车+御发神社+竹林+天龙寺+佑斋亭+渡月桥串联即成片
- [XHS] 「5.11实况京都初夏」collects=851 —— 佑斋亭（门票 ¥2000·官网预约·10:00 开门）作为半日独立钩子，初夏/红叶季出片力强
- [JG] Arashiyama overview —— "Arashiyama becomes most attractive (and busy) around early April and the second half of November"，核心区 4-6 小时够撑，北区延伸可到奥嵯峨三寺
- [Entity] 竹林 7:30 前无人，天龙寺 8:30 开门，小火车首发 9:00，奥嵯峨三寺（常寂光寺/二尊院/祇王寺）组合是深度钩子
- [原则] 岚山单独成立一日；和服日可直接套用岚山（京都 3 大和服区：东山/岚山/祇园）

#### kyo_arashiyama_1（岚山标准日·9 点档·全年通用）

- 季节：common
- 打分：core_experience 50
- 人群加成：情侣 +5 / 朋友 +0 / 家庭 +0
- 执行风险：-1（午后竹林爆人、旺季天龙寺排队）
- min_days：0
- day_type：regular
- selectable_tag：null
- 互斥：与 arashiyama 其他 1-10 变体同组互斥（同一天只装 1 个岚山变体）
- 可接夜模块：无（岚山日落后天黑店闭，回市区接 higashiyama/night）

#### kyo_arashiyama_2（早春一日·fixed_early·7:00 前竹林+云龙图+奥嵯峨苔色）

- 季节：early_spring
- 打分：core_experience 46（早春独享竹林+云龙图特别开放+三寺苔色组合）
- 人群加成：情侣 +10 / 朋友 +0 / 家庭 -5
- 执行风险：-2（早起触发 + 住本地优先）
- min_days：3
- day_type：fixed_early
- selectable_tag：null
- 互斥：arashiyama 其他变体
- 可接夜模块：无
- 降级目标：arashiyama/1（fixed_early 触发失败时）

#### kyo_arashiyama_3（樱花一日·fixed_early·8:30 曹源池开门即进）

- 季节：sakura
- 打分：core_experience 54（樱花季曹源池空景+10 点前渡月桥+奥嵯峨山樱）
- 人群加成：情侣 +15 / 朋友 +5 / 家庭 +0
- 执行风险：-2（早起触发 + 樱花季人流峰值）
- min_days：3
- day_type：fixed_early
- selectable_tag：null
- 互斥：arashiyama 其他变体
- 可接夜模块：无
- 降级目标：arashiyama/1

#### kyo_arashiyama_4（岚山 10 点档氛围日·适合佑斋亭+渡月桥慢游）

- 季节：common
- 打分：core_experience 46
- 人群加成：情侣 +15 / 朋友 +5 / 家庭 -5
- 执行风险：-1（10 点档人流高但可错峰去佑斋亭）
- min_days：0
- day_type：regular
- selectable_tag：null
- 互斥：arashiyama 其他变体
- 可接夜模块：无

#### kyo_arashiyama_5（出片一日·fixed_early·三机位晨光轮转）

- 季节：common（樱花/红叶季加成·染井盛期+红叶盛期）
- 打分：core_experience 48（三机位晨光轮转+下午嵯峨野漫步+黄昏第二次渡月桥）
- 人群加成：情侣 +20 / 朋友 +5 / 家庭 -10
- 执行风险：-2（早起触发 + 三脚架/定焦装备要求）
- min_days：4
- day_type：fixed_early
- selectable_tag：null
- 互斥：arashiyama 其他变体
- 可接夜模块：无
- 降级目标：arashiyama/1（晨光机位全部消失时）

#### kyo_arashiyama_6（红叶一日·fixed_early·7:00 前竹林+奥嵯峨三寺）

- 季节：koyo
- 打分：core_experience 56（红叶季全关西最挤动线仅晨段可成立）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +0
- 执行风险：-3（红叶季早到 + 奥嵯峨三寺路线长 + 人流峰值）
- min_days：4
- day_type：fixed_early
- selectable_tag：null
- 互斥：arashiyama 其他变体
- 可接夜模块：无
- 降级目标：arashiyama/1（红叶体验打 5 折·砍到常寂光寺 1 家）

#### kyo_arashiyama_7（嵯峨野小火车+保津川漂流一日·fixed_early·班次锚定）

- 季节：common（3/1-12/29 运行期·冬季 12/30-2 月末停运）
- 打分：core_experience 50（火车+漂流两段体验感最强的一日）
- 人群加成：情侣 +10 / 朋友 +15 / 家庭 +15
- 执行风险：-2（9:00 首发班次锚定 + 旺季提前 1 个月预约 + 漂流停运备选 JR 返程）
- min_days：4
- day_type：fixed_early
- selectable_tag：null
- 互斥：arashiyama 其他变体
- 可接夜模块：无
- 降级目标：arashiyama/1（取消小火车+漂流仅走岚山标准日）

#### kyo_arashiyama_8（岚山温泉一泊·D1 9 点档 + D2 温泉 D2 规范）

- 季节：common
- 打分：core_experience 52（两日深度）
- 人群加成：情侣 +20 / 朋友 +5 / 家庭 +10
- 执行风险：-1（温泉旅馆预约 + D2 退房 12:00 约束）
- min_days：5（温泉日必须连住）
- day_type：onsen_2day
- selectable_tag：onsen
- 互斥：arashiyama 其他变体（同组）+ arm_arima 系列（同一行程不重复温泉日）
- 可接夜模块：无（温泉日 D1 晚餐在旅馆）

#### kyo_arashiyama_9（红叶两日深度·fixed_early·D1 夜枫点灯+D2 清晨独享红叶竹林+奥嵯峨三寺完整）

- 季节：koyo
- 打分：core_experience 56（两日深度独家价值：清晨无人+三寺完整+夜枫）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +0
- 执行风险：-2（旅馆 3-6 个月预约 + D2 清晨早起触发）
- min_days：6
- day_type：fixed_early（两日）
- selectable_tag：null
- 互斥：arashiyama 其他变体 + kyo_arashiyama_6（同季节）
- 可接夜模块：无（D1 夜枫自含）
- 降级目标：arashiyama/1 + arashiyama/6（拆两天走·红叶体验 7 折）

#### kyo_arashiyama_10（樱花两日深度·fixed_early·D1 夜樱+D2 清晨独享曹源池 2h+三寺山樱）

- 季节：sakura
- 打分：core_experience 56（两日深度独家价值：夜樱仪式+曹源池 2h+两次黄金光渡月桥）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +0
- 执行风险：-2（旅馆 6-8 个月预约 + D2 清晨早起触发）
- min_days：6
- day_type：fixed_early（两日）
- selectable_tag：null
- 互斥：arashiyama 其他变体 + kyo_arashiyama_3（同季节）
- 可接夜模块：无（D1 夜樱自含）
- 降级目标：arashiyama/1 + arashiyama/3（拆两天走·樱花体验 7 折）

---

### 3.2 京都·东山（kyoto/higashiyama·6 变体 + night）

**打分依据**：
- [XHS] 「没去就白来了！京都最经典一日游线路」collects=1981 —— 东山动线（清水+高台+八坂+知恩院+永观堂+银阁+哲学）是中文用户公认的京都一日游天花板，信息密度最大
- [XHS] 「京都就东山区一带能打」—— 东山区作为京都片区自立性最强的动线
- [JG] Higashiyama 核心 4-6 小时够撑，清水寺年 500 万访客峰值，早 8:00 前/晚 16:30 后是错峰窗口
- [Entity] 清水寺票价 ¥500 加诸堂 +¥300；高台寺 ¥600；知恩院三门免费外观；圆山公园 12m 枝垂樱夜樱点灯 17:00-22:00
- [原则] 和服日首选东山（3 大和服区之一）；东山密度高可夜游（圆山公园/夜樱）；清水→二年坂→产宁坂→高台寺→八坂→圆山→知恩院是动线骨架，反向也可

#### kyo_higashiyama_1（东山核心一日·9 点档·全年通用）

- 季节：common
- 打分：core_experience 56（国际级：清水+三年坂+高台+八坂全打包）
- 人群加成：情侣 +10 / 朋友 +5 / 家庭 +0
- 执行风险：-1（旺季清水寺爆人、午后人流峰值）
- min_days：0
- day_type：regular
- selectable_tag：null
- 互斥：higashiyama 其他变体
- 可接夜模块：kyo_higashiyama_night

#### kyo_higashiyama_2（东山氛围日·10 点档·慢游版）

- 季节：common
- 打分：core_experience 50
- 人群加成：情侣 +15 / 朋友 +5 / 家庭 -5
- 执行风险：-2（10 点档清水已峰值，每点停 30 分限时）
- min_days：0
- day_type：regular
- selectable_tag：null
- 互斥：higashiyama 其他变体
- 可接夜模块：kyo_higashiyama_night

#### kyo_higashiyama_3（东山和服出片日·9:30 起装）

- 季节：common
- 打分：core_experience 52
- 人群加成：情侣 +20 / 朋友 +15 / 家庭 -10
- 执行风险：-2（起装预约 + 还装 13:00 硬约束 + 和服行走慢 2 倍）
- min_days：3
- day_type：audience_day
- selectable_tag：kimono
- 互斥：higashiyama 其他变体 + 岚山/祇园和服变体（同行程和服只装一次）
- 可接夜模块：kyo_higashiyama_night

#### kyo_higashiyama_4（东山红叶一日·9 点档·永观堂+清水寺夜特别拜观）

- 季节：koyo
- 打分：core_experience 58（红叶峰值：永观堂"红叶之永观堂"+清水寺夜枫）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +0
- 执行风险：-2（红叶季人流峰值 + 清水寺夜特别 17:30-21:30 须再入场）
- min_days：3
- day_type：regular
- selectable_tag：null
- 互斥：higashiyama 其他变体
- 可接夜模块：kyo_higashiyama_night（清水夜特别已含，不再加）

#### kyo_higashiyama_5（东山樱花一日·白天·9 点档·圆山枝垂+岸边疏水）

- 季节：sakura
- 打分：core_experience 54
- 人群加成：情侣 +15 / 朋友 +5 / 家庭 +0
- 执行风险：-2（樱花季圆山峰值，首次爆衣+夜樱另选 6.json）
- min_days：3
- day_type：regular
- selectable_tag：null
- 互斥：higashiyama 其他变体 + kyo_higashiyama_6（白天/夜樱同日才会共装）
- 可接夜模块：kyo_higashiyama_6（如选夜樱）

#### kyo_higashiyama_6（圆山公园枝垂樱夜樱·特殊时段 17:00-22:00）

- 季节：sakura
- 打分：core_experience 48（特殊时段钩子）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 -5
- 执行风险：-2（点灯时段拥挤、雨天取消）
- min_days：3
- day_type：special_event
- selectable_tag：null
- 互斥：其他夜模块同日（只接一个夜模块）
- 出门档：无效（夜樱绝对时间锚定）
- 可接夜模块：不适用（自身是夜模块）

#### kyo_higashiyama_night（东山夜模块·GEAR 齿轮秀/舞妓座敷 二选一）

- 季节：common
- 打分：core_experience 38（夜模块锚定于白天 higashiyama 后）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +0
- 执行风险：-2（GEAR 需提前预约 + 舞妓座敷预约难度最高）
- min_days：3
- day_type：night_module
- selectable_tag：gear 或 maiko（二选一用户勾选）
- 互斥：其他夜模块（夜模块每行程限 1-2 次）
- 可接夜模块：不适用

---

### 3.3 京都·伏见（kyoto/fushimi·5 变体）

**打分依据**：
- [XHS] 「白色的伏見稲荷大社 white fushimi inari」collects=5191 —— 稻荷雪景（深冬偶发）是高传播力钩子；稻荷本身无门票 24h 可进是错峰核心优势
- [XHS] 「完美错开人挤人的伏见稻荷大社」—— 7:30 前/17:00 后稻荷峰值外窗口，在中文用户认知里已成常识
- [JG] Fushimi Inari：免费 + 24h 开放 + 最受欢迎外国人神社；登顶往返 2-3 小时，四辻途中观景点 30-45 分钟上升半山
- [Entity] 稻荷 JR 奈良線→稻荷站步行 0 分；伏见酒蔵地区（月桂冠/寺田屋/十石舟/伏水酒蔵小路）是"稻荷之外"小众日
- [原则] 伏见可半日（稻荷核心）或一日（稻荷 + 酒蔵）；紫阳花季藤森神社是关西稀有内容

#### kyo_fushimi_1（稻荷核心半日·9 点档·全年通用）

- 季节：common
- 打分：core_experience 54（国际级稻荷 + 半日易装配）
- 人群加成：情侣 +5 / 朋友 +0 / 家庭 +0
- 执行风险：-1（10 点后四辻以下爆人）
- min_days：0
- day_type：half_day
- selectable_tag：null
- 互斥：fushimi 其他变体 + 同日另装半日
- 可接夜模块：无（半日，下午接另一动线）

#### kyo_fushimi_2（稻荷+酒蔵一日·9 点档·月桂冠/寺田屋/伏水酒蔵小路）

- 季节：common
- 打分：core_experience 46（酒蔵小众深度）
- 人群加成：情侣 +5 / 朋友 +15 / 家庭 -5
- 执行风险：-1（酒蔵周一闭馆要查）
- min_days：4
- day_type：regular
- selectable_tag：null
- 互斥：fushimi 其他变体
- 可接夜模块：无

#### kyo_fushimi_3（稻荷傍晚半日·16:00 出发·特殊时段）

- 季节：common
- 打分：core_experience 44（夜间稻荷氛围钩子）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 -10
- 执行风险：-1（夜间山路需手电）
- min_days：3
- day_type：half_day
- selectable_tag：null
- 出门档：无效（16:00 绝对时间锚定）
- 互斥：fushimi 其他变体
- 可接夜模块：无（自身是夜半日）

#### kyo_fushimi_4（伏见樱花专线·9 点档·背割堤京阪南下·十石舟）

- 季节：sakura
- 打分：core_experience 48（樱花季背割堤 1.4km 双岸樱花隧道·八幡市小众）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +0
- 执行风险：-2（樱花季十石舟要预约 + 京阪南下路线长）
- min_days：5
- day_type：regular
- selectable_tag：null
- 互斥：fushimi 其他变体
- 可接夜模块：无

#### kyo_fushimi_5（藤森紫阳花半日·6 月·关西稀有）

- 季节：tsuyu
- 打分：core_experience 44（紫阳花 3500 株 + 关西唯一带"勝ち馬御守"内容）
- 人群加成：情侣 +10 / 朋友 +5 / 家庭 +0
- 执行风险：-1（6 月梅雨天气不定）
- min_days：4
- day_type：half_day
- selectable_tag：null
- 互斥：fushimi 其他变体 + 同季节 kyo_half_day_5（柳谷寺紫阳花）
- 可接夜模块：无

---

### 3.4 京都·北山（kyoto/kitayama·5 变体）

**打分依据**：
- [XHS] 京都 DAY4 金阁寺-龙安寺-北野天满宫-二条城 —— 中文用户标准北山动线
- [XHS] 「我心目中京都枯山水庭院的 TOP8」collects 稳定 —— 龙安寺石庭作为枯山水代表国际地位
- [JG] 金阁寺年 400 万访客，停留 45-60 分钟；龙安寺加配金阁 2-3 小时组合
- [Entity] 金阁寺门票 ¥500 不可改签；龙安寺 ¥600；北野天满宫梅苑 2-3 月 ¥1200；平野神社 985 年樱花祭夜间无限时
- [原则] 金阁+龙安+北野是北山骨架；季节特化：梅苑（早春）/ 樱花祭（樱花）/ 雪景金阁（深冬·fixed_early）

#### kyo_kitayama_1（北山标准日·9 点档·金阁+龙安+仁和寺+北野→peak 夕/西阵）

- 季节：common
- 打分：core_experience 54（金阁国际 top + 龙安枯山水国际 top 双钩子）
- 人群加成：情侣 +5 / 朋友 +5 / 家庭 +0
- 执行风险：-1（金阁下午逆光、冬季闭门早）
- min_days：0
- day_type：regular
- selectable_tag：null
- 互斥：kitayama 其他变体
- 可接夜模块：无（北山日落后冷清）

#### kyo_kitayama_2（北野梅苑一日·early_spring·50 品种 1500 株）

- 季节：early_spring
- 打分：core_experience 46（梅苑深度 + 梅苑副菜）
- 人群加成：情侣 +15 / 朋友 +5 / 家庭 +0
- 执行风险：-1（梅苑期 2/5-3/20 短窗口）
- min_days：3
- day_type：regular
- selectable_tag：null
- 互斥：kitayama 其他变体
- 可接夜模块：无

#### kyo_kitayama_3（平野神社樱花祭一日·sakura·60 种 400 株 985 年）

- 季节：sakura
- 打分：core_experience 50（平野神社夜樱+金阁樱花）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +0
- 执行风险：-1（樱花祭周末拥挤）
- min_days：3
- day_type：regular
- selectable_tag：null
- 互斥：kitayama 其他变体
- 可接夜模块：平野神社夜樱（特殊时段挂）

#### kyo_kitayama_4（金阁雪景半日·fixed_early 占位·特殊时段）

- 季节：deep_winter
- 打分：core_experience 56（占位·金阁雪景是京都深冬第一钩子）
- 人群加成：情侣 +20 / 朋友 +15 / 家庭 +5
- 执行风险：-3（雪景不可预测 + 开门 9:00 即进才能拍无脚印 + 冬季凌晨严寒）
- min_days：5
- day_type：fixed_early
- selectable_tag：null
- 互斥：kitayama 其他变体
- 可接夜模块：无

#### kyo_kitayama_5（嵯峨御苑·樱花·奥嵯峨·小众两日）

- 季节：sakura
- 打分：core_experience 44（奥嵯峨樱花 + 吾妻御所等小众内容）
- 人群加成：情侣 +15 / 朋友 +5 / 家庭 +0
- 执行风险：-2（奥嵯峨路线长、交通不便）
- min_days：5
- day_type：regular
- selectable_tag：null
- 互斥：kitayama 其他变体 + kyo_kitayama_3（同樱花季）
- 可接夜模块：无

---

### 3.5 京都·冈崎哲学之道（kyoto/okazaki_tetsugaku·3 变体）

**打分依据**：
- [XHS] 「京都最经典一日游线路」东山线含南禅+永观+哲学+银阁——东山南段与冈崎哲学重叠，是中文用户共识动线
- [JG] Philosopher's Path 2km 运河散步 + 银阁寺（足利义政·枯山水）+ 南禅寺（水道桥·三门）+ 永观堂（紅葉で有名）
- [Entity] 银阁寺 ¥500；南禅寺境内免费/方丈 ¥600/水道桥免费；永观堂 ¥600 紅葉期特别 ¥1000；瑠璃光院春秋特别公开需抽签
- [原则] 哲学之道一日可纳南禅+银阁+永观；瑠璃光院深度需 fixed_early

#### kyo_okazaki_tetsugaku_1（南禅+永观+哲学红叶日·9 点档·koyo）

- 季节：koyo
- 打分：core_experience 56（红叶峰值：永观堂"红叶之永观堂"+南禅水道桥+哲学红叶）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +0
- 执行风险：-2（红叶季人流峰值 + 永观堂排队）
- min_days：3
- day_type：regular
- selectable_tag：null
- 互斥：okazaki 其他变体 + kyo_higashiyama_4（红叶核心二选一）
- 可接夜模块：kyo_higashiyama_night

#### kyo_okazaki_tetsugaku_2（瑠璃光院+银阁+哲学红叶日·fixed_early·抽签时刻锚定）

- 季节：koyo（11/8-12/7 完全预约制·10 月初抽签）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 -5
- 打分：core_experience 58（瑠璃光院秋季テーブル紅葉京都秋季第一钩子+银阁哲学南禅完整下半场）
- 执行风险：-3（抽签落选率高 + 指定时刻锚定 + 八瀬交通远）
- min_days：5
- day_type：fixed_early
- selectable_tag：null
- 互斥：okazaki 其他变体
- 可接夜模块：kyo_eikando（永观堂红叶夜間拝観可接 17:30-20:30）
- 降级目标：okazaki/1（未中签时·真如堂+永观堂+哲学之道是完美替代）

#### kyo_okazaki_tetsugaku_3（哲学之道樱花日·9 点档·2km 疏水樱花）

- 季节：sakura
- 打分：core_experience 50（哲学之道 2km 樱花步道 + 银阁 + 南禅）
- 人群加成：情侣 +20 / 朋友 +5 / 家庭 +0
- 执行风险：-1（樱花季午后峰值）
- min_days：3
- day_type：regular
- selectable_tag：null
- 互斥：okazaki 其他变体
- 可接夜模块：无

---

### 3.6 京都·二条（kyoto/nijo·3 变体）

**打分依据**：
- [JG] 二条城（幕府京都据点·二之丸御殿·国宝）年 200 万访客；周围锦市场/京都御苑 20 分钟圈
- [Entity] 二条城 ¥1300；NAKED Flowers 夜樱需提前网上预约 ¥2000-2500 浮动；锦市场免费
- [原则] 二条城可白天（历史）或夜樱（NAKED Flowers 沉浸式投影·特殊时段）；锦市场食べ歩き配二条是京都"文化+食"中轴日

#### kyo_nijo_1（二条城+御苑一日·9 点档·预约推荐）

- 季节：common
- 打分：core_experience 44（二之丸御殿国宝但需室内限流）
- 人群加成：情侣 +0 / 朋友 +5 / 家庭 +5
- 执行风险：-1（旺季网上预约、鹂鸣地板限流）
- min_days：0
- day_type：regular
- selectable_tag：null
- 互斥：nijo 其他变体
- 可接夜模块：无

#### kyo_nijo_2（二条城夜樱 NAKED Flowers·特殊时段·沉浸式投影）

- 季节：sakura
- 打分：core_experience 48（投影灯光艺术 + 樱花夜间动态体验）
- 人群加成：情侣 +20 / 朋友 +15 / 家庭 +5
- 执行风险：-2（网上预约 + 雨天影响投影体验 + 限定期）
- min_days：3
- day_type：special_event
- selectable_tag：null
- 出门档：无效（夜樱绝对时间锚定）
- 互斥：nijo 其他变体 + 同日其他夜模块
- 可接夜模块：不适用

#### kyo_nijo_3（二条城+锦市场白天·常规·御苑散步+锦市场边走边吃）

- 季节：common
- 打分：core_experience 46（锦市场食べ歩き钩子）
- 人群加成：情侣 +5 / 朋友 +15 / 家庭 +5
- 执行风险：-1（锦市场中午峰值、部分店拒外卖）
- min_days：0
- day_type：regular
- selectable_tag：null
- 互斥：nijo 其他变体
- 可接夜模块：无

---

### 3.7 京都·鞍马贵船（kyoto/kurama_kibune·2 变体）

**打分依据**：
- [XHS/JG] 贵船川床料理（夏季 5/1-9/30）+ 鞍马寺（天狗信仰）组合是京都夏避暑第一动线；红叶季叡山电铁鞍马线隧道是高传播红叶钩子
- [Entity] 贵船神社免费；鞍马寺 ¥300；川床要提前 1 个月预约；叡山电铁展望车厢"きらら"旺季需取整理券

#### kyo_kurama_kibune_1（贵船川床夏日·summer_low·夏避暑首选）

- 季节：summer_low
- 打分：core_experience 50（夏避暑·川床料理是关西独有内容）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +10
- 执行风险：-2（川床要提前预约 + 夏季偶发豪雨取消 + 山路湿滑）
- min_days：4
- day_type：regular
- selectable_tag：null
- 互斥：kurama 其他变体
- 可接夜模块：无

#### kyo_kurama_kibune_2（鞍马贵船红叶日·koyo·叡山电车红叶隧道）

- 季节：koyo
- 打分：core_experience 52（红叶隧道 + 鞍马山红叶 + 贵船石板路红叶）
- 人群加成：情侣 +20 / 朋友 +15 / 家庭 +5
- 执行风险：-2（红叶季きらら整理券排队 + 鞍马山步行量大）
- min_days：5
- day_type：regular
- selectable_tag：null
- 互斥：kurama 其他变体
- 可接夜模块：无

---

### 3.8 京都·宇治（kyoto/uji·5 变体）

**打分依据**：
- [XHS] 「京都宇治 vlog｜平等院·宇治川·抹茶」collects 1000+ —— 平等院 + 中村藤吉抹茶 + 宇治川是中文用户标准宇治日
- [XHS] 「中村藤吉平等院店」专题多条 —— 中村藤吉作为宇治抹茶国际 IP，本店比京都分店更稀缺
- [JG] 平等院凤凰堂（¥600 + 凤凰堂内部拝观 ¥300 定时入场）国宝建筑 + 宇治上神社（世界遗产）
- [Entity] 平等院 ¥600 内部拝观需抽整理券；三室户寺紫阳花（6 月 10000 株·国际 Top）+ 三室户红叶（11 月）
- [原则] 宇治要慢，不能和奈良/姬路同日（关西 7 条 §4）；半日可但错失抹茶深度；紫阳花/红叶期各自有专属变体

#### kyo_uji_1（宇治标准一日·9 点档·平等院凤凰堂+中村藤吉+宇治川+源氏物语）

- 季节：common
- 打分：core_experience 52（平等院国宝 + 抹茶本店国际钩子）
- 人群加成：情侣 +10 / 朋友 +10 / 家庭 +5
- 执行风险：-1（中村藤吉排队 60-90 分钟、凤凰堂抽整理券）
- min_days：0
- day_type：regular
- selectable_tag：null
- 互斥：uji 其他变体 + other_nara（关西 7 条：不同日）+ other_姬路（关西 7 条）
- 可接夜模块：无（宇治日落后冷清）

#### kyo_uji_2（御守抽签+宇治一日·宇治上神社御守专题）

- 季节：common
- 打分：core_experience 46（宇治上神社世界遗产 + 御守专题）
- 人群加成：情侣 +15 / 朋友 +5 / 家庭 +0
- 执行风险：-1（御守专题对非神社文化爱好者弱）
- min_days：3
- day_type：regular
- selectable_tag：null
- 互斥：uji 其他变体 + other_nara + other_姬路
- 可接夜模块：无

#### kyo_uji_3（三室户寺紫阳花一日·tsuyu·6 月·10000 株关西 top）

- 季节：tsuyu
- 打分：core_experience 52（三室户 10000 株紫阳花是关西紫阳花第一）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +5
- 执行风险：-2（梅雨天气不定 + 紫阳花期 2-3 周窗口短）
- min_days：4
- day_type：regular
- selectable_tag：null
- 互斥：uji 其他变体 + kyo_fushimi_5 + kyo_half_day_5（同季节紫阳花）+ other_nara + other_姬路
- 可接夜模块：无

#### kyo_uji_4（宇治红叶日·koyo·兴圣寺+三室户红叶）

- 季节：koyo
- 打分：core_experience 48（宇治红叶 + 文学背景 + 抹茶配红叶）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +0
- 执行风险：-2（红叶季人流 + 部分寺院旺季特别开放）
- min_days：4
- day_type：regular
- selectable_tag：null
- 互斥：uji 其他变体 + other_nara + other_姬路
- 可接夜模块：无

#### kyo_uji_5（宇治川 Illumination 冬夜·12 月·4km 水边灯光+鹈饲圣堂）

- 季节：deep_winter
- 打分：core_experience 42（冬季灯光装置小众）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +5
- 执行风险：-2（冬夜严寒 + 灯光期限定）
- min_days：5
- day_type：special_event
- selectable_tag：null
- 出门档：无效（夜间灯光绝对时间锚定）
- 互斥：uji 其他变体 + other_nara + other_姬路
- 可接夜模块：不适用（自身是夜模块）

---

### 3.9 京都·高雄（kyoto/takao·2 变体）

**打分依据**：
- [JG] Takao（高雄）京都红叶最早红叶圈（11 月上中旬）+ 神护寺 400 石阶 + 川床夏避暑
- [Entity] 神护寺 ¥1000；西明寺 ¥600；高山寺鸟兽戏画 ¥800 + 特别公开另计；山阴本线+市营巴士 8 号约 60 分钟
- [原则] 高雄红叶比市区早 1-2 周，错峰峰值首选；温泉一泊 D2 按温泉 D2 规范（朝食+自由时间+12:00 退房）

#### kyo_takao_1（高雄红叶一日·koyo·9 点档·神护寺+西明寺+高山寺+川床）

- 季节：koyo
- 打分：core_experience 52（高雄红叶早峰值 + 神护寺 400 石阶氛围 + 川床体验）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +0
- 执行风险：-2（9 号巴士 60 分钟 + 400 石阶体力 + 17:00 前离开山区）
- min_days：4
- day_type：regular
- selectable_tag：null
- 互斥：takao 其他变体
- 可接夜模块：无（市区返回晚）

#### kyo_takao_2（高雄红叶温泉一泊·koyo·2day·D1 三山+D2 温泉 D2 规范）

- 季节：koyo
- 打分：core_experience 54（两日深度 + 温泉连住 + 朝食高雄山朝雾）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +5
- 执行风险：-1（温泉旅馆预约 + D2 退房 12:00 约束）
- min_days：6
- day_type：onsen_2day
- selectable_tag：onsen
- 互斥：takao 其他变体 + kyo_arashiyama_8（同行程温泉日限 1 次）+ arm_arima（同样）
- 可接夜模块：无（D1 晚餐在旅馆）

---

### 3.10 京都·半日池（kyoto/half_day·7 个）

**打分依据**：
- [Entity/Research] 7 个半日是"满天数后要补什么"的池：工艺/teamLab/紫阳花/梅花/樱花/和服/抹茶——消费场景是"白天已装主动线，还剩半天"
- [原则] 半日不与主动线互斥，按 selectable_tag 或季节窗口自然入池；不过分追求深度，目标是"这半天做了有意义的事"

#### kyo_half_day_1（京都工艺体验半日·工艺品 DIY 选一·common）

- 季节：common
- 打分：core_experience 38（体验型·消费场景半日）
- 人群加成：情侣 +10 / 朋友 +15 / 家庭 +15
- 执行风险：-1（需提前预约工艺店）
- min_days：3
- day_type：half_day
- selectable_tag：craft
- 互斥：同日另装半日
- 可接夜模块：无

#### kyo_half_day_2（城南宫枝垂梅半日·early_spring·150 株枝垂梅）

- 季节：early_spring
- 打分：core_experience 40（京都枝垂梅独家钩子）
- 人群加成：情侣 +15 / 朋友 +5 / 家庭 +0
- 执行风险：-1（梅期 2/15-3/15 窗口短）
- min_days：3
- day_type：half_day
- selectable_tag：null
- 互斥：kyo_half_day_7（同季节梅花半日二选一）+ 同日另装半日
- 可接夜模块：无

#### kyo_half_day_3（岚山路疏水+蹴上倾斜铁道半日·sakura·90 株枝垂+哲学之道）

- 季节：sakura
- 打分：core_experience 42（蹴上倾斜铁道樱花是中文用户爆款）
- 人群加成：情侣 +20 / 朋友 +5 / 家庭 +0
- 执行风险：-1（蹴上道窄人多）
- min_days：3
- day_type：half_day
- selectable_tag：null
- 互斥：同日另装半日
- 可接夜模块：无

#### kyo_half_day_4（teamLab 京都半日·全年·数字艺术 90 分钟）

- 季节：common
- 打分：core_experience 40（数字艺术固定钩子）
- 人群加成：情侣 +15 / 朋友 +15 / 家庭 +10
- 执行风险：-1（需提前网上购票）
- min_days：3
- day_type：half_day
- selectable_tag：teamlab
- 互斥：同日另装半日
- 可接夜模块：无

#### kyo_half_day_5（柳谷寺花手水紫阳花半日·tsuyu·发祥地+5000 株）

- 季节：tsuyu
- 打分：core_experience 46（花手水发祥地 + 西山小众）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +0
- 执行风险：-2（阪急长冈天神站接驳巴士班次有限）
- min_days：4
- day_type：half_day
- selectable_tag：null
- 互斥：kyo_fushimi_5 + kyo_uji_3（同季节紫阳花）+ 同日另装半日
- 可接夜模块：无

#### kyo_half_day_6（水路阁蹴上樱花半日·early_spring·早樱+疏水）

- 季节：early_spring
- 打分：core_experience 38（早春早樱小众）
- 人群加成：情侣 +15 / 朋友 +5 / 家庭 +0
- 执行风险：-1（早樱期 3 月中下旬窗口小）
- min_days：3
- day_type：half_day
- selectable_tag：null
- 互斥：同日另装半日
- 可接夜模块：无

#### kyo_half_day_7（随心院小野梅苑半日·early_spring·230 株枝垂梅+小野小町）

- 季节：early_spring
- 打分：core_experience 40（小野小町文学背景 + 枝垂梅苑）
- 人群加成：情侣 +15 / 朋友 +5 / 家庭 +0
- 执行风险：-1（梅苑期窗口短）
- min_days：3
- day_type：half_day
- selectable_tag：null
- 互斥：kyo_half_day_2（同季节梅花半日二选一）+ 同日另装半日
- 可接夜模块：无

---

### 3.11 大阪（osaka·11 变体）

**打分依据**：
- [XHS] 「大阪一日 citywalk 路线」collects 574 likes —— 道顿堀+心斋桥是中文用户大阪第一动线
- [XHS] 「从道顿堀到环球影城」「大阪环球不早起一日」多条中等爆款 —— USJ 独立成日是大阪第一"目的地"体量
- [Entity] USJ ¥9800 起·1 日票动态定价·超级任天堂世界需 APP 整理券；海游馆 ¥2700（以官网为准）；大阪城天守阁 ¥600；通天阁展望台 ¥1000；造币局樱花季预约制
- [原则] 京都后大阪（关西 7 条 §1）；大阪适合时差恢复期；USJ 固定 theme_park 日不降档（9-10 小时）

#### osk_namba_1（难波·道顿堀一日·9 点档·心斋桥+黒門市場+道顿堀夜）

- 季节：common
- 打分：core_experience 48（中文用户大阪第一动线 + 食べ歩き钩子）
- 人群加成：情侣 +10 / 朋友 +15 / 家庭 +5
- 执行风险：-1（周末道顿堀夜爆人）
- min_days：4
- day_type：regular
- selectable_tag：null
- 互斥：同日大阪其他变体（namba 是大阪核心，不可与其他大阪日同装）
- 可接夜模块：无（道顿堀本身就是夜动线）

#### osk_osakajo_1（大阪城+天守阁+历史博物馆一日·9 点档·common）

- 季节：common
- 打分：core_experience 42（大阪城国际知名度高于体验深度）
- 人群加成：情侣 +0 / 朋友 +10 / 家庭 +15
- 执行风险：-1（夏暑冬寒）
- min_days：5
- day_type：regular
- selectable_tag：null
- 互斥：同日大阪其他变体 + osk_osakajo_2
- 可接夜模块：无

#### osk_osakajo_2（大阪城樱花日·西の丸庭园+夜樱点灯·sakura）

- 季节：sakura
- 打分：core_experience 48（西の丸 300 棵染井吉野 + 夜樱点灯 19:30-21:00）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +5
- 执行风险：-2（夜樱点灯期 + 天守阁排队）
- min_days：4
- day_type：regular
- selectable_tag：null
- 互斥：同日大阪其他变体 + osk_osakajo_1
- 可接夜模块：无（夜樱自含）

#### osk_kaiyukan_1（海游馆一日·9 点档·8 楼螺旋向下 2.5h+天保山摩天轮·common）

- 季节：common
- 打分：core_experience 46（海游馆日本顶级水族馆 + 家庭钩子）
- 人群加成：情侣 +10 / 朋友 +10 / 家庭 +20
- 执行风险：-1（周末/节假日人流峰值）
- min_days：5
- day_type：regular
- selectable_tag：null
- 互斥：同日大阪其他变体
- 可接夜模块：osk_kaiyukan_night（海游馆夜场，同日自含）

#### osk_tennoji_1（新世界·串炸·通天阁·四天王寺一日·common）

- 季节：common
- 打分：core_experience 40（新世界昭和氛围 + 串炸发源地钩子，但体量小）
- 人群加成：情侣 +5 / 朋友 +15 / 家庭 +5
- 执行风险：-1（新今宮站北口治安观感差，走動物園前站）
- min_days：5
- day_type：regular
- selectable_tag：null
- 互斥：同日大阪其他变体
- 可接夜模块：无

#### osk_nakazakicho_1（中崎町·梅田散步日·古民家咖啡+梅田空中庭园黄昏·common）

- 季节：common
- 打分：core_experience 42（中崎町古民家咖啡是中文用户大阪文艺 IP）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 -5
- 执行风险：-1（中崎町周一部分店闭）
- min_days：5
- day_type：regular
- selectable_tag：null
- 互斥：同日大阪其他变体
- 可接夜模块：无（梅田空中庭园黄昏自含）

#### osk_expo_1（万博纪念公园·太阳塔一日·太阳塔内部参观须提前网上预约·common）

- 季节：common
- 打分：core_experience 38（太阳塔内部 1970 万博原作是建筑史钩子，但体量偏小众）
- 人群加成：情侣 +10 / 朋友 +10 / 家庭 +10
- 执行风险：-2（太阳塔内部需提前预约 + 地铁御堂筋線 30 分钟单程）
- min_days：5
- day_type：regular
- selectable_tag：null
- 互斥：同日大阪其他变体
- 可接夜模块：无

#### osk_usj_1（环球影城一日·theme_park·no_pace_downgrade·common）

- 季节：common
- 打分：core_experience 54（USJ 日本最大主题乐园 + 超级任天堂/哈利波特/侏罗纪国际 IP）
- 人群加成：情侣 +5 / 朋友 +15 / 家庭 +20
- 执行风险：-2（任天堂整理券 + 快速通道购票决策 + 闭园拥挤）
- min_days：5
- day_type：theme_park
- selectable_tag：usj
- 特殊：no_pace_downgrade（任何密度 packed slots）
- 互斥：同日大阪其他变体
- 可接夜模块：无（闭园拖到 21:00 后）

#### osk_half_day_1（造币局樱花通り抜け半日·sakura·八重樱·预约制·特殊时段）

- 季节：sakura
- 打分：core_experience 44（八重樱 1 周限定 + 造币局通り抜け 130 年传统）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +5
- 执行风险：-2（预约制 + 期间短 1 周）
- min_days：4
- day_type：special_event
- selectable_tag：null
- 出门档：无效（造币局指定入场时段）
- 互斥：同日另装半日
- 可接夜模块：无

#### osk_half_day_2（生驹山遊乐园半日·周末限定·缆车约束）

- 季节：common
- 打分：core_experience 34（生驹山复古游乐园小众钩子）
- 人群加成：情侣 +10 / 朋友 +10 / 家庭 +15
- 执行风险：-2（周末限定运营 + 缆车班次有限）
- min_days：5
- day_type：half_day
- selectable_tag：null
- 互斥：同日另装半日
- 可接夜模块：无

#### osk_half_day_3（久安寺紫阳花半日·tsuyu·关西唯一浮紫阳花）

- 季节：tsuyu
- 打分：core_experience 40（浮紫阳花是关西唯一 + 小众避峰）
- 人群加成：情侣 +20 / 朋友 +5 / 家庭 +0
- 执行风险：-2（梅雨天气 + 池田市交通远）
- min_days：4
- day_type：half_day
- selectable_tag：null
- 互斥：kyo_fushimi_5 + kyo_uji_3 + kyo_half_day_5（同季节紫阳花）+ 同日另装半日
- 可接夜模块：无

---

### 3.12 奈良（other/nara·4 变体）

**打分依据**：
- [XHS] 奈良看鹿攻略常规传播（likes 中等） —— 奈良公园"鹿"是中文用户第一钩子
- [XHS] 「去奈良真的不要再在奈良公园喂鹿了」—— 避坑反向爆款，说明奈良动线已到"信息饱和期"
- [JG] 奈良公园 + 东大寺（大佛 15m）+ 春日大社（3000 石灯笼）+ 兴福寺（五重塔）核心半日够；法隆寺（世界最古木造）独立半日在斑鸠町
- [Entity] 东大寺 ¥800；春日大社本殿 ¥500；法隆寺 ¥1500；吉野山 1000 本山樱覆盖 4 段（下/中/上/奥千本）
- [原则] 奈良作为"桥"，顺路塞（关西 7 条 §2）；与姬路/宇治不同日（§4）；京都→奈良→大阪 JR 直通 50 分钟

#### nar_nara_1（奈良核心一日·9 点档·东大寺+春日+兴福+奈良町·common）

- 季节：common
- 打分：core_experience 52（国际级鹿 + 国宝大佛 + 石灯笼）
- 人群加成：情侣 +10 / 朋友 +10 / 家庭 +20
- 执行风险：-1（夏暑冬寒 + 鹿仙贝投喂攻击性）
- min_days：4
- day_type：regular
- selectable_tag：null
- 互斥：nara 其他变体 + kyo_uji_*（关西 7 条 §4）+ other/kobe_3（姬路日同日·§3）
- 可接夜模块：无

#### nar_nara_2（法隆寺+斑鸠町二日·深度·世界最古木造）

- 季节：common
- 打分：core_experience 44（法隆寺世界最古木造但体量小众）
- 人群加成：情侣 +5 / 朋友 +10 / 家庭 +0
- 执行风险：-2（斑鸠町交通不便 + 需两日连住奈良）
- min_days：7
- day_type：regular
- selectable_tag：null
- 互斥：nara 其他变体
- 可接夜模块：无

#### nar_nara_3（奈良樱花日·sakura·公园染井吉野+鹿+樱花）

- 季节：sakura
- 打分：core_experience 52（樱花+鹿同框国际传播）
- 人群加成：情侣 +20 / 朋友 +15 / 家庭 +15
- 执行风险：-1（樱花季公园峰值）
- min_days：4
- day_type：regular
- selectable_tag：null
- 互斥：nara 其他变体 + kyo_uji_*
- 可接夜模块：无

#### nar_nara_4（奈良红叶日·koyo·公园红叶+水谷茶屋+若草山）

- 季节：koyo
- 打分：core_experience 48（红叶+鹿+茶屋氛围）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +10
- 执行风险：-1（红叶季人流）
- min_days：4
- day_type：regular
- selectable_tag：null
- 互斥：nara 其他变体 + kyo_uji_*
- 可接夜模块：无

---

### 3.13 神户（other/kobe·4 变体）

**打分依据**：
- [JG] 神户：北野异人馆 + 港口 + 神户牛 + 灘酒造（五乡之一）；姬路城日归 1 小时 JR
- [Entity] 神户牛有专店列表；六甲缆车 2026 年 1 月起大修停运（需确认）；摩耶山夜景"1000 万美金夜景"日本三大夜景之一；姬路城 2026-03-01 起涨至 ¥2500
- [原则] 神户 2 晚 + 有马温泉（关西 7 条 §7）；姬路+神户一天组合（§3）；六甲缆车停运期间大巴约 40 分钟替代

#### kob_kobe_1（神户港湾+北野异人馆一日·9 点档·common）

- 季节：common
- 打分：core_experience 46（港口 + 异人馆 + 神户牛三件套）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +5
- 执行风险：-1（神户牛店预约难度中等）
- min_days：5
- day_type：regular
- selectable_tag：null
- 互斥：kobe 其他变体
- 可接夜模块：无（港口夜景自含）

#### kob_kobe_2（摩耶山+六甲山夜景半日·特殊时段·日本三大夜景）

- 季节：common
- 打分：core_experience 44（国际三大夜景 + 日落前后）
- 人群加成：情侣 +20 / 朋友 +15 / 家庭 +5
- 执行风险：-3（⚠️六甲缆车 2026 停运大修·大巴 40 分钟替代 + 摩耶山缆车天气依赖 + 冬季山顶严寒）
- min_days：5
- day_type：special_event
- selectable_tag：null
- 出门档：无效（日落时段锚定·季节浮动）
- 互斥：kobe 其他变体 + 同日其他夜模块
- 可接夜模块：不适用（自身是夜模块）

#### kob_kobe_3（姬路城日归·9 点档·common·三大樱花名城外观）

- 季节：common
- 打分：core_experience 46（姬路城国宝白鹭城 + 日归可控）
- 人群加成：情侣 +10 / 朋友 +10 / 家庭 +15
- 执行风险：-1（姬路→神户 JR 1 小时 + 天守阁登顶排队）
- min_days：5
- day_type：regular
- selectable_tag：null
- 互斥：kobe 其他变体 + kyo_uji_* + nar_nara_*（关西 7 条 §3+§4）
- 可接夜模块：无（姬路返神户晚）

#### kob_kobe_4（六甲山森林植物园紫阳花半日·tsuyu·35 万株）

- 季节：tsuyu
- 打分：core_experience 42（六甲 35 万株紫阳花深度）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +5
- 执行风险：-3（⚠️六甲缆车停运·大巴 40 分钟 + 梅雨天气不定）
- min_days：5
- day_type：half_day
- selectable_tag：null
- 互斥：kobe 其他变体 + kyo_fushimi_5 + kyo_uji_3 + kyo_half_day_5 + osk_half_day_3（同季节紫阳花）
- 可接夜模块：无

---

### 3.14 有马温泉（other/arima·4 变体）

**打分依据**：
- [XHS] 「关西温泉天花板有马温泉」collects/likes 414 + 「有马温泉六甲北麓深秋」779 likes —— 有马是中文用户关西温泉第一认知
- [XHS] 陶泉御所坊等高端旅馆作为小红书打卡钩子
- [JG] 有马温泉日本最古温泉（金泉·银泉双泉）+ 太阁丰臣秀吉爱泉 + 距神户三宫 30 分钟
- [原则] 神户 2 晚 + 有马（关西 7 条 §7）；温泉 D2 规范统一（朝食 90 分 + 自由时间 + 12:00 退房）

#### arm_arima_1（有马温泉一泊·D1 金泉银泉体验+D2 温泉 D2 规范·common）

- 季节：common
- 打分：core_experience 52（双泉深度 + 温泉文化钩子）
- 人群加成：情侣 +20 / 朋友 +5 / 家庭 +10
- 执行风险：-1（温泉旅馆预约 + D2 12:00 退房）
- min_days：5
- day_type：onsen_2day
- selectable_tag：onsen
- 互斥：arima 其他变体 + kyo_arashiyama_8 + kyo_takao_2 + kns_kinosaki_1（同行程温泉日限 1 次）
- 可接夜模块：无

#### arm_arima_2（有马温泉日归·半日·金泉银泉外汤巡り·common）

- 季节：common
- 打分：core_experience 40（日归错失旅馆深度 + 但灵活度高）
- 人群加成：情侣 +10 / 朋友 +5 / 家庭 +5
- 执行风险：-1（大巴 60 分钟从神户）
- min_days：4
- day_type：half_day
- selectable_tag：null
- 互斥：arima 其他变体
- 可接夜模块：无

#### arm_arima_3（有马红叶温泉一泊·koyo·温泉+红叶）

- 季节：koyo
- 打分：core_experience 54（温泉 + 红叶双峰钩子）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +10
- 执行风险：-2（红叶季旅馆满房 + 需提前 2-3 个月预约）
- min_days：6
- day_type：onsen_2day
- selectable_tag：onsen
- 互斥：arima 其他变体 + kyo_arashiyama_8 + kyo_takao_2 + kns_kinosaki_1
- 可接夜模块：无

#### arm_arima_4（神户连泊+有马温泉组合·3day·common·关西 7 条 §7 标准配方）

- 季节：common
- 打分：core_experience 54（神户 2 晚 + 有马 1 晚是关西 7 条标准配方）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +10
- 执行风险：-1（3 日行程协调）
- min_days：7
- day_type：onsen_2day
- selectable_tag：onsen
- 互斥：arima 其他变体 + kyo_arashiyama_8 + kyo_takao_2 + kns_kinosaki_1 + kobe 其他变体（3 日自含 kobe 内容）
- 可接夜模块：无

---

### 3.15 高野山（other/koyasan·1 变体）

**打分依据**：
- [JG] 高野山 1200 年真言宗总本山 + 奥之院 20 万墓碑 + 宿坊体验 + 精进料理 + 朝课
- [Entity] 高野山→南海高野线特急約 2 小时从难波；宿坊一泊 ¥15000-25000
- [原则] 高野山独立成立 2day；宿坊是关西独有灵修体验

#### kys_koyasan_1（高野山宿坊一泊·D1 奥之院+壇上伽蓝+D2 朝课+精进料理+灵宝馆·common）

- 季节：common
- 打分：core_experience 50（宿坊体验 + 精进料理 + 朝课是关西独有灵修内容）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +0
- 执行风险：-2（南海高野线 2 小时 + 宿坊预约 + 冬季严寒）
- min_days：7
- day_type：onsen_2day（规格类似·朝课 D2 锚定）
- selectable_tag：null（灵修独立钩子，不需勾选；或未来加 temple_stay 标）
- 互斥：同行程其他 onsen_2day（资源占位考虑）
- 可接夜模块：无

---

### 3.16 城崎温泉（other/kinosaki·1 变体）

**打分依据**：
- [XHS] 城崎温泉七馆外汤巡り + 松叶蟹季（11-3 月）关西冬季第一美食钩子
- [JG] 城崎温泉 1300 年历史 + 七馆外汤 + 志贺直哉"城之崎にて"文学背景
- [Entity] 城崎温泉距大阪 JR 特急 2.5 小时；温泉外汤一日券 ¥1500；松叶蟹季会席 ¥25000+

#### kns_kinosaki_1（城崎温泉外汤巡り一泊·D1 7 馆+浴衣漫步+松叶蟹会席（蟹季）+D2 温泉 D2 规范·common）

- 季节：common
- 打分：core_experience 54（松叶蟹季 52+2 内容深度 + 浴衣七馆体验关西独有）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +10
- 执行风险：-2（大阪 2.5 小时 JR + 松叶蟹季预约 + 旅馆预约 + D2 退房）
- min_days：7
- day_type：onsen_2day
- selectable_tag：onsen
- 互斥：kyo_arashiyama_8 + kyo_takao_2 + arm_arima_1/3/4（同行程温泉日限 1 次）
- 可接夜模块：无

---

### 3.17 吉野山（other/yoshino·1 变体）

**打分依据**：
- [JG] 吉野山 1000 本山樱 + 4 段（下/中/上/奥千本）阶梯开花 + 世界遗产
- [Entity] 吉野山→近铁特急 1.5 小时从大阪；桜まつり 4 月上中旬；ロープウェイ（缆车）停运时段需步行备选

#### yos_yoshino_1（吉野山樱花日·sakura·4 段山樱+世界遗产金峯山寺）

- 季节：sakura
- 打分：core_experience 56（千本樱花阶梯开花国际级·日本三大赏樱名所）
- 人群加成：情侣 +20 / 朋友 +15 / 家庭 +10
- 执行风险：-2（樱花期人流峰值 + 近铁 1.5 小时 + ロープウェイ停运备选步行 20 分钟）
- min_days：5
- day_type：regular
- selectable_tag：null
- 互斥：yoshino 其他变体（目前仅 1）
- 可接夜模块：无（返大阪晚）

---

### 3.18 其他半日（other/half_day·1 变体）

#### other_half_day_1（琵琶湖·大津散步半日·common·JR 京都 10 分钟）

- 季节：common
- 打分：core_experience 38（大津作为"消失的目的地"小众钩子）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +5
- 执行风险：-1（大津游客少但冬季湖岸冷）
- min_days：5
- day_type：half_day
- selectable_tag：null
- 互斥：同日另装半日
- 可接夜模块：无

---

### 3.19 到达/离开（arrivals/departures·2 变体）

**打分依据**：
- [原则] 到达日轻量（时差+第一印象·避免城市 citywalk 深度耗体力）；离开日 551 蓬莱+机场提前 3 小时（关西产品共识）
- [Entity] 关西空港→大阪难波/京都 关空特急 40/75 分钟

#### arrivals_1（到达日·便利店+早睡调时差·common）

- 季节：common
- 打分：core_experience 30（到达日本身不追求深度，体验=顺利到达）
- 人群加成：情侣 +0 / 朋友 +0 / 家庭 +5
- 执行风险：-1（航班延误不可控）
- min_days：3
- day_type：arrival
- selectable_tag：null
- 特殊：no_pace_downgrade（到达日序列固定）
- 互斥：同日不装其他（arrival 专属日）
- 可接夜模块：无

#### departures_1（离开日·551 蓬莱+机场提前 3 小时·common）

- 季节：common
- 打分：core_experience 30（离开日体验=顺利离开+最后一顿）
- 人群加成：情侣 +0 / 朋友 +0 / 家庭 +5
- 执行风险：-1（机场手续时间）
- min_days：3
- day_type：departure
- selectable_tag：null
- 特殊：no_pace_downgrade
- 互斥：同日不装其他
- 可接夜模块：无

---

### 3.20 特殊事件（special_events·10 变体）

**打分依据**：
- [JG] 祇园祭（7/17 山鉾巡行）+ 天神祭（7/25 船渡御）+ 大文字送り火（8/16 20:00）都是日本三大祭/五山送火级别
- [Entity] 特殊事件时段绝对锚定，出门档无效（D38 §9.5）
- [原则] 特殊事件入池硬筛：applicable_dates 必须精准匹配用户日期；装配层按绝对时间执行

#### special_kyo_gion_matsuri（祇园祭山鉾巡行·7/17·日本三大祭首尾）

- 季节：matsuri_peak_summer
- 打分：core_experience 58（日本三大祭之一 + 京都千年传统 + 国际遗产）
- 人群加成：情侣 +15 / 朋友 +20 / 家庭 +10
- 执行风险：-2（7/17 人流峰值 + 酷暑 + 需提早定位）
- min_days：5
- day_type：special_event
- selectable_tag：null（日期命中即入池）
- 出门档：无效（巡行时刻 9:00 起锚定）
- 互斥：同日其他模板
- 可接夜模块：无

#### special_kyo_daimonji（大文字送り火·8/16 20:00·五山送火）

- 季节：matsuri_peak_summer
- 打分：core_experience 54（京都盂兰盆会送火 + 五山 20:00-20:30 绝对时刻）
- 人群加成：情侣 +20 / 朋友 +15 / 家庭 +10
- 执行风险：-2（20:00 绝对时段 + 观景点竞争 + 雨天可延期/取消）
- min_days：4
- day_type：special_event
- selectable_tag：null
- 出门档：无效（20:00 绝对时间）
- 互斥：同日其他模板
- 可接夜模块：无

#### special_osk_tenjin_matsuri（天神祭船渡御·7/25·日本三大祭之一·大阪）

- 季节：matsuri_peak_summer
- 打分：core_experience 56（大阪第一祭 + 船渡御水上巡行 + 花火）
- 人群加成：情侣 +15 / 朋友 +20 / 家庭 +10
- 执行风险：-2（酷暑 + 人流峰值 + 船渡御观景需提早定位）
- min_days：5
- day_type：special_event
- selectable_tag：null
- 出门档：无效（船渡御 18:00 起锚定）
- 互斥：同日其他模板
- 可接夜模块：无（花火自含）

#### special_kyo_setsubun（节分祭吉田神社·2/2-4·早春开春第一祭）

- 季节：early_spring
- 打分：core_experience 44（节分祭神事 + 鬼火祭 + 福豆撒き）
- 人群加成：情侣 +10 / 朋友 +15 / 家庭 +15
- 执行风险：-2（2/3 鬼火祭夜间 + 冬季严寒 + 人流峰值）
- min_days：4
- day_type：special_event
- selectable_tag：null
- 出门档：无效（祭典绝对时间）
- 互斥：同日其他模板
- 可接夜模块：无

#### special_kyo_hatsumode（初詣京都三社·1/1-3·伏见/八坂/下鸭）

- 季节：deep_winter
- 打分：core_experience 46（初詣 1/1-3 日本全民传统 + 京都三社并拜）
- 人群加成：情侣 +15 / 朋友 +10 / 家庭 +15
- 执行风险：-3（1/1-3 全日本最拥挤 + 严寒 + 餐饮/交通超负荷）
- min_days：5
- day_type：special_event
- selectable_tag：null
- 出门档：无效（初詣时段锚定）
- 互斥：同日其他模板
- 可接夜模块：无

#### special_shg_biwako_hanabi（琵琶湖花火大会·8/8·1 万发·日本最大湖花火）

- 季节：matsuri_peak_summer
- 打分：core_experience 50（琵琶湖 1 万发花火 + 湖面反射钩子）
- 人群加成：情侣 +20 / 朋友 +15 / 家庭 +10
- 执行风险：-2（观景位竞争 + 会场附近酒店提前 3 个月订 + 雨天延期）
- min_days：5
- day_type：special_event
- selectable_tag：null
- 出门档：无效（19:30 花火点火锚定）
- 互斥：同日其他模板 + other_half_day_1（琵琶湖大津同日可组合：白天大津+夜花火）
- 可接夜模块：无（花火自含）

#### special_kyo_daigoji_sakura（醍醐寺樱花半日·sakura·太阁秀吉爱樱）

- 季节：sakura
- 打分：core_experience 46（醍醐寺世界遗产 + 丰臣秀吉醍醐の花見 + 枝垂+染井+山樱多品种）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +5
- 执行风险：-1（樱花季峰值）
- min_days：4
- day_type：half_day
- selectable_tag：null
- 互斥：同日另装半日 + kyo_kitayama_3 + kyo_higashiyama_5（樱花主动线二选一）
- 可接夜模块：无

#### special_kyo_ohara_sanzenin（大原三千院·バス 60 分钟·紫阳花/红叶/雪景）

- 季节：koyo/tsuyu/deep_winter（多季适配）
- 打分：core_experience 46（三千院"わらべ地藏"苔庭+大原小众 + 紫阳花/红叶/雪景多季钩子）
- 人群加成：情侣 +20 / 朋友 +10 / 家庭 +0
- 执行风险：-2（京都バス 17 系统 60 分钟 + 班次有限 + 冬季雪路）
- min_days：5
- day_type：regular（一日，非 half_day）
- selectable_tag：null
- 互斥：同日其他 regular 主动线
- 可接夜模块：无

#### special_kyo_tsuinagiya（通し矢三十三间堂·1/13-16·60 米弓道大会）

- 季节：deep_winter
- 打分：core_experience 40（新成人弓道大会 + 三十三间堂 1001 尊观音国宝背景）
- 人群加成：情侣 +10 / 朋友 +15 / 家庭 +5
- 执行风险：-2（1/13-16 限定 + 早朝 9:00 开始 + 冬季严寒）
- min_days：5
- day_type：special_event
- selectable_tag：null
- 出门档：无效（9:00 起锚定）
- 互斥：同日其他模板
- 可接夜模块：无

#### special_kyo_mitarashi_matsuri（御手洗祭·下鸭神社·7/28-8/4·踩水消灾）

- 季节：summer_low
- 打分：core_experience 44（脱鞋入池踩水参拜 + 京都人夏日习俗 + 糺の森避暑）
- 人群加成：情侣 +15 / 朋友 +15 / 家庭 +20（踩水最适合家庭小孩）
- 执行风险：-1（7/28-8/4 限定 + 需带换洗袜子）
- min_days：4
- day_type：special_event
- selectable_tag：null
- 出门档：无效（祭典期锚定）
- 互斥：同日其他模板
- 可接夜模块：无

---

## 四、花名册维护 SOP

- 新增模板 → 同时在本文档对应子节加一段元属性，否则不入装配池
- 模板 JSON 删除 → 本文档对应段同步删
- 打分调整 → PR 需附依据（opencli 新爆款 / japan-guide 更新 / entity 事实变更）
- fixed_early 8 个模板已统一设计（2026-04-24 阶段 2.4）：arashiyama 2/3/5/6/7/9/10 + okazaki 2·每个有 `降级目标` 字段指向对应 adaptive 9 点档模板·触发失败按降级目标走

### 3.3 大阪（待填）

### 3.4 其他城市（待填）

### 3.5 到达/离开/特殊事件（待填）
