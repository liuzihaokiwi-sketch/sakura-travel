# 数据精选主文档

> 版本: 3.0
> 更新: 2026-04-01
> 地位: 唯一权威执行文档。所有品类子文档(GUIDE_*.md)遵循本文规则。如有冲突以本文为准。
> 品类子文档: GUIDE_RESTAURANTS.md / GUIDE_HOTELS.md / GUIDE_SPOTS.md / GUIDE_SHOPS.md

---

## 一、产品目标

纸质手账本(298/348元)，让中国20-40岁游客照着走就行。

用户付费买的: 确定性 + 信息准确 + 惊喜感 + 节奏感。
用户最怕: 到了店关门了 / 推荐的不好 / 和免费攻略一样。

**因此: 手账本上印的每一条推荐，都必须是"真的值得写"。宁缺毋滥。**

---

## 二、铁律

1. **真实数据优先** -- 没有真实数据源验证的数据标记 ai_generated，不可用于生产。
2. **每步判断先搜索** -- 不能凭AI记忆填写评分/价格/坐标/营业时间。搜不到填null，不编造。
3. **品类内相对排名** -- 不用固定分数阈值。"京都怀石top 5"而不是"Tabelog >= 3.5"。
4. **允许稀疏** -- 某区域某预算没好选项就空着，不补"还行"的。
5. **负向取舍** -- 精选的价值在"明明很多人写，我却不收"。
6. **不偷懒** -- 每步都搜索验证。监督agent也不偷懒。搜不到填null不编造。

---

## 二b、效率规则(不降质量的前提下)

### 规则0（最高优先级）: AI 不写事实，AI 只做判断

**这是所有规则的前提。违反此规则会产生误导性数据，比没有数据更危险。**

```
AI 禁止做的事:
  - 写 quality_evidence / traveler_fit_evidence / execution_evidence 等事实性证据字段
  - 补写评分、价格、坐标、营业时间等任何可以从真实来源获取的字段
  - 用 Structured Outputs / JSON schema 生成"看起来像真实来源支持"的内容
    (Structured Outputs 只保证格式/schema 一致，不保证事实是真的)

AI 可以做的事（判断，不是事实）:
  - one_line_editorial_note / why_selected / skip_if
  - grade 判断 + selection_tags
  - 负向信号识别（基于喂给它的真实证据）
  - 只对最终入选的 S/A 级或关键边界项写编辑注释
```

**evidence 字段的正确产生方式：**

```
quality_evidence:
  → 规则化生成，直接引用真实信号：
    餐厅: "Tabelog {score}，{city}×{cuisine}类前{pct}%"
    酒店: "MICHELIN {n} Keys / 楽天 ★{rating}({count}件)"
    景点: "japan-guide {level}，{sub_type}类推荐"
  → 不让 AI 自由发挥

traveler_fit_evidence:
  → 从携程/小红书真实抓取后提炼
  → 只对 shortlist（selected+borderline）补抓，不做全量
  → 没有真实来源就填 null，不编

execution_evidence:
  → 从官网/Google Maps 抓取营业时间、预约、排队信息
  → 规则化提炼，不让 AI 编写
  → 没有真实来源就填 null
```

**Phase 2 正确流程名称：**

```
旧（错误）: "evidence generation" — 暗示 AI 可以"生成"证据
新（正确）:
  Phase 2B: evidence_extraction   — 从真实来源抽取/规则化写证据
  Phase 2C: editorial_annotation  — 只给少数入选条目写编辑注释（AI 可参与）
```

**data_confidence 的判定基于实际来源，不能乐观填写：**

```
cross_checked ≠ "来自两个来源"，而是"三轴中至少两轴有真实来源覆盖"
single_source = 只有一个真实来源（如仅有 japan-guide，无携程/小红书/Google）
ai_generated  = 无任何真实来源 — 不可用于生产
```

> 关西教训: spots_ledger 里大量条目只有 source="japan-guide"，却被标为 cross_checked。
> 这是错误的。单源必须标 single_source，等补了 traveler/execution 真实来源才能升级。

---

### 规则1: 模型只做选品判断，脚本补齐结构字段

```
模型负责(需要判断力):
  - 候选列表筛选
  - why_selected / skip_if / grade_reason（编辑判断，不是事实陈述）
  - grade判断 + selection_tags标注
  - 负向信号识别（基于喂给它的真实证据摘要）

脚本/真实来源补齐(机械性工作):
  - 坐标(Google Places API)
  - 价格(OTA API/爬虫)
  - 营业时间(Google Places / 官网)
  - 基础结构字段(id、city_code、corridor_tags等)
  - JSON完整格式生成(种子CSV -> 完整JSON)
  - quality_evidence（规则模板 + 真实信号）
  - traveler_fit_evidence（携程/小红书真实抓取后提炼）
  - execution_evidence（官网/Google Maps 真实信息）
```

这是最大的单点token节约。模型产出种子CSV(选品+判断)，脚本扩展为完整JSON。

### 规则2: S/A深审，B/C轻审

| 等级 | 审核深度 | 审核内容 |
|------|---------|---------|
| S/A | 完整三轴审查 | quality+traveler_fit+execution全验证，负向信号审查，替代品比较，编辑辩护 |
| B/C | 真实性+执行性 | 确认"是真的、还在开、能去"即可，不写长篇编辑辩护 |

用户感知品牌力的是S/A级骨架推荐，不是每个B/C条目的推荐理由。

### 规则3: API分层取数

不要一上来就查全量细节。按阶段逐层加深:

```
发现层(批量，低成本):
  - Google Places: 只要 name + rating + place_id + user_ratings_total
  - 楽天: Keyword/Area/Ranking API
  - 携程: 列表搜索

入围层(中等，只对入围候选):
  - Google Places: + address + opening_hours + price_level
  - 楽天: + 评分详情 + 价格带
  - 一休: 评分排名

终选层(完整，只对终选条目):
  - Google Places: Full Detail (field mask指定需要的字段)
  - 楽天: Detail API + Vacant API
  - 一休: 完整设施信息 + 含餐信息
  - 官网: 预约方式、定休日确认
```

Google Places必须用field mask，跨SKU字段会按最高SKU计费。

### 规则4: 模型吃证据摘要，不吃原始网页

```
错误: 把整页Tabelog评论、整页攻略文章喂给模型
正确: 先脚本提取结构化摘要，再喂给模型

每个候选的evidence block(8-12行):
  name_ja: 菊乃井本店
  quality: Tabelog 4.52 / 百名店2024 / 米其林三星
  traveler_fit: 携程4.8(1200评论) / 小红书提及频率高
  execution: 需预约(difficulty:hard) / 周一定休
  negative: 价格极高 / 需提前1个月
  editorial: 京都怀石最高峰，首次来京都的foodie必体验
```

模型只需要这个摘要就能做选品判断，不需要读原始网页。

### 规则5: 城市级公共事实抽成一次性资产

以下内容每个城市圈只做一次，后续每条数据引用不重复搜索:

```
城市级research pack(一次性产出):
  - taxonomy.json: 分类体系、regions、画像加成
  - corridor_definitions.json: 走廊定义、连接关系、交通时间
  - indie_sites_evaluation.json: 独立站评估(10-15个核心站)
  - seasonal_calendar.json: 旺季日历、节庆活动
  - city_cuisine_map: 城市特有菜系和代表店概览
  - city_hotel_landscape: 各区域酒店价位分布概览

每条数据只引用pack中的结论，不重新解释"京都是什么样的城市"。
```

### 规则6: 候选发现设停机规则

精选不是学术穷举。发现阶段的停机条件:

```
停机条件(满足任一即停):
  - 某组连续新增10个候选，无1个能进入入围池
  - 某组已有3个高质量终选 + 2个备选，召回足够
  - 新增来源只是重复提及已有候选，无增量信息
  - 成熟类目(如京都怀石)已从主源获得充足候选
```

### 搜索语言的效率规则

五语搜索(简中+繁体台+繁体港+日文+英文)只在以下场景全开:
- 新城市圈首次采集
- 不熟悉的类目/菜系
- 小众目的地(资料稀缺)

成熟城市圈的成熟类目，默认从**日文主源 + 中文traveler源**开始，够用就不开五语。

---

## 三、三层池架构

```
发现池 (尽量不漏)
  - 五语搜索全开
  - 任何一个可信数据源提及即进入
  - 数量: 终选的5-10倍
      |
      v
入围池 (交叉验证)
  - 至少2个独立数据源确认
  - 核验语言收窄: 日文 + 官方 + 简中
  - 数量: 终选的2-3倍
      |
      v
终选池 (编辑精选)
  - "如果朋友第一次去，我会专门推荐这个吗？"
  - 品类内相对排名(样本>=15时取top 10-20%，小样本用编辑判断)
  - 同一决策位最多3家(首推/稳妥替代/机动备选)
  - 允许稀疏
  - 检查负向信号
```

### 3.1 发现池→入围池: 数据归一化步骤（必做）

> 关西教训: 多源合并后 cuisine_type 75+种混乱、酒店 price_level 85%被默认值覆盖、
> OTA评分/JPY价格等强信号在合并时被丢掉。导致 Phase 2 无法直接跑选择模型。

**合并脚本的 schema 保留规则:**

```
合并时必须保留的字段（不可丢弃）:
  餐厅: name_ja, city_code, area, cuisine_type, budget_tier, tabelog_score, michelin, source
  酒店: name_ja, city_code, area, hotel_type, price_level, source,
        + ranking_info(来自luxury源), brief_note(含OTA评分/JPY价格), key_features
  景点: name_en, name_ja, city_code, area, japan_guide_level, main_type, sub_type

合并时必须从原始文件回溯提取的信号:
  酒店 mid/budget 源: 从 brief_note 解析 OTA星级、评论数、JPY夜价
    正则: ★(\d\.\d)\((\d+)件\)  →  ota_rating, ota_review_count
    正则: 1泊(\d+)円〜  →  nightly_jpy_min
  酒店 luxury 源: 从 ranking_info 提取 Michelin Keys / Forbes stars
  餐厅 各源: tabelog_score 和 michelin 必须带过来，不可丢
```

**归一化步骤（合并后、选择模型前）:**

| 步骤 | 操作 | 关键规则 |
|------|------|---------|
| N1 | cuisine_type 归一化 | 所有原始值映射到标准菜系码（见 DATA_SCHEMA 菜系枚举），维护 `cuisine_mapping.json` |
| N2 | area → corridor 映射 | 用 corridor_definitions.json 做文本匹配，输出 `area_corridor_mapping.json` |
| N3 | budget_tier 细化 | 加 premium 层。**budget_tier 是价格层不是质量层**（见下方铁律） |
| N4 | 酒店 price_level 修正 | 用回溯的 JPY 价格重新分层，不用合并时的默认值 |
| N5 | 酒店 hotel_type 补全 | 从 name_ja 推断缺失值 |

**N3 铁律: budget_tier ≠ quality_score**

```
错误: Tabelog 3.8+ 且非快餐类 → premium
正确: 按已知价格/菜系场景推断

budget_tier 推断优先级:
  1. 已有 JPY 价格 → 直接按阈值分层
  2. Michelin 非空 → luxury
  3. 菜系场景推断（弱信号）:
     怀石/kaiseki/割烹/铁板烧/河豚 → premium
     拉面/乌冬/咖喱/丼/takoyaki → mid/budget
  4. 无法判断 → 保留原值，标 tier_confidence: "inferred"

原因: Tabelog 评分体系以 3.0 为基准、0.5 为刻度，反映口碑强弱不反映消费层级。
3.8 的拉面店可能人均 1000 日元（mid），3.5 的怀石可能人均 15000（premium）。
```

**N4 酒店 price_level 修正规则:**

```
JPY >= 30000/晚 → luxury
JPY 15000-30000 → expensive
JPY 8000-15000 → moderate
JPY < 8000 → budget
无价格时: Michelin Keys → luxury; ryokan+onsen → expensive; business_hotel → moderate
```

---

## 四、数据源与三轴判断模型

### 4.1 源注册表(P0/P1/P2/P3)

P0/P1分级用于**源管理**(抓取优先级、维护优先级、人工信任基线)，不直接用于终选逻辑。

| 级别 | 数据源 | 适用品类 | 获取方式 |
|------|--------|---------|---------|
| P0 | Tabelog (含百名店) | 餐厅 | WebFetch/OpenCLI |
| P0 | 米其林指南 | 餐厅 | WebFetch |
| P0 | MICHELIN Keys | 酒店 | WebFetch |
| P0 | 一休.com | 酒店 | WebFetch/OpenCLI |
| P0 | 楽天Travel | 酒店 | Travel API |
| P0 | 携程Trip.com | 全品类 | WebFetch/API |
| P0 | Google Maps | 全品类 | Places API |
| P0 | japan-guide.com | 景点 | WebFetch |
| P0 | JNTO | 景点 | WebFetch |
| P1 | Booking.com | 酒店 | Affiliate API |
| P1 | じゃらん | 酒店 | WebFetch |
| P1 | Agoda | 酒店 | WebFetch |
| P1 | TripAdvisor | 景点 | WebFetch |
| P1 | Retty | 餐厅 | WebFetch |
| P1 | GURUNAVI | 餐厅 | WebFetch |
| P1 | SAVOR JAPAN | 餐厅 | WebFetch |
| P1 | Relux | 酒店(高端) | WebFetch |
| P2 | 小红书 | 全品类 | OpenCLI |
| P2 | 马蜂窝 | 全品类 | WebFetch |
| P2 | 独立攻略站 | 全品类 | WebFetch/OpenCLI |
| P2 | 知乎 | 全品类 | WebFetch |
| P3 | AI知识 | -- | 必须标ai_generated，不可用于生产 |

### 4.2 三轴判断模型(终选逻辑核心)

**终选不靠"几个P0源确认"，靠三个判断轴:**

| 判断轴 | 回答的问题 | 说明 |
|--------|-----------|------|
| **quality** | 在该类中是否足够强 | 品质/专业性/口碑 |
| **traveler_fit** | 中国游客去了大概率满意吗 | 目标用户实际满意度 |
| **execution** | 现在可执行、现场风险可控吗 | 营业状态/交通/预约/排队 |

各品类各轴的权威来源:

**quality轴:**

| 品类 | 主评分源 | 辅助确认源 |
|------|---------|-----------|
| 餐厅 | Tabelog品类排名 | 米其林/百名店/Google |
| 酒店 体验型(ryokan/luxury_ryokan/shukubo) | 一休 + MICHELIN Keys | 楽天/Booking |
| 酒店 功能型(business/city/hostel) | 楽天 + **携程**(见下方说明) | 一休/Booking |
| 景点 | JNTO/japan-guide编辑等级 | Google评分(城市内相对) |
| 店铺 | 该类型专业源 | 独立攻略站原创推荐 |

**traveler_fit轴:**

| 数据源 | 价值 |
|--------|------|
| 携程Trip.com | 中国游客评分+评论+人民币价格。对本产品极重要(目标用户是中国游客) |
| 小红书 | 中国游客高频体验+避坑 |
| 马蜂窝/知乎 | 深度讨论+攻略补充 |

**execution轴:**

| 数据源 | 验证内容 |
|--------|---------|
| Google Maps | 坐标、营业状态、排队信息 |
| 官方网站 | 营业时间、预约方式、价格、定休日 |
| 独立攻略站 | 实地执行细节(排队、交通、语言) |

### 4.3 携程在不同品类的角色

携程对本产品极重要，但它在不同品类的判断轴上角色不同:

| 品类 | 携程的角色 | 原因 |
|------|-----------|------|
| 餐厅 | traveler_fit轴 | 品质判断以Tabelog/米其林为主，携程反映的是"中国游客是否满意" |
| 酒店 功能型 | quality轴 + traveler_fit轴 | 功能型酒店的"品质"就是"住得顺不顺"，携程中国用户评价直接反映这一点 |
| 酒店 体验型 | traveler_fit轴 + quality修正项 | 体验型的"品质"由MICHELIN Keys/一休定义，但携程可作为否决信号(如多人反映服务差) |
| 景点 | traveler_fit轴 | 品质由JNTO/japan-guide定义，携程反映游客满意度 |
| 店铺 | traveler_fit轴 | 品质由专业源定义 |

---

## 四b、评分解释系统

**不做跨平台线性换算，做"解释+翻译"。**

各平台评分机制不同(Tabelog基准3.0、Google裸平均、大众点评带治理加权、携程分垂类分制不同)，
硬换算成同一个数是伪精确。正确做法是三层:

```
第一层: 保留原始平台分(不丢)
第二层: 平台解释层(这个分在这个平台上是什么意思)
第三层: 内部基准分(我们自己的统一排序标准)
```

### 双解释层: 日本源 vs 国内源

**日本源解释层** — 回答"它在本地标准里强不强"

| 品类 | 主quality源 | 补充源 |
|------|-----------|--------|
| 餐厅 | Tabelog / Michelin | Google(执行性+热度) |
| 酒店 体验型 | 一休 / MICHELIN Keys | 楽天 |
| 酒店 功能型 | 楽天 | 一休 |
| 景点 | JNTO / japan-guide | Google(热度) |

**国内源解释层** — 回答"中国游客会不会满意/踩雷"

| 数据源 | 角色 | 注意 |
|--------|------|------|
| 携程/Trip.com | traveler_fit主信号; 功能型酒店也可入quality | 酒店/景点分制不同，不可混比 |
| 大众点评 | 中国用户满意度/消费感知 | 必须结合评论量看，平台持续治理促评/AIGC |
| 小红书 | 体验细节、排队避雷、近期波动 | 热度信号强但需去营销内容 |

两层分开解释，最后汇入同一个内部基准分。

### 平台读分卡

#### Tabelog

- 角色: 日本本地餐厅quality主骨架
- 机制: 基准分3.0，以0.5为评价刻度展开; 非裸平均分，按用户影响力加权动态计算
- 读法: **只看城市 x 菜系 x 预算层内的相对位置**，不跨品类/跨平台比较
- 额外看: 百名店/award/品类排名位置
- 注意: 3.5在高端怀石是中等，在甜品咖啡已经很强

#### Google Maps

- 角色: 执行性 + 大众热度(全品类)
- 机制: 所有已发布评分的简单平均值，1-5星
- 读法: 分数 + 评论量 + 最近评论时间
- 注意: 不做主quality源; 评论量用城市内相对值，不用绝对阈值

#### 一休.com

- 角色: 日本体验型酒店quality主源
- 机制: 多维度评分(服务/设施/餐食/风吕等)
- 读法: 综合分 + 各维度分 + 区域内排名
- 注意: 高端旅馆覆盖最强，商务酒店覆盖弱

#### 楽天Travel

- 角色: 日本功能型酒店quality主源
- 机制: 多维度评分 + 评论量
- 读法: 综合分 + 评论量 + 区域排名
- 注意: 覆盖面最广，从商务到旅馆都有

#### 携程/Trip.com

- 角色: traveler_fit主信号; 功能型酒店部分进quality
- 机制: 酒店常用10分制，景点常用5分制; Trip.Best是多因子算法排名(评分+评论+销量+搜索数据)
- 读法: 先分垂类再看raw score + 评论量 + 榜单位置
- 注意: 酒店9.2和景点4.7不是同一条尺度; 对本产品极重要但不替代日本骨架源

#### 大众点评

- 角色: 中国用户满意度/餐饮消费感知
- 机制: 用户按0-4打分，平台平均后乘10，再按点评数/时间/会员级别调整; 4条以下不出分
- 读法: 分数必须结合评论量和时间分布; 警惕高频促评型异常
- 注意: 平台2025年起升级星级规则并持续治理AIGC/促评，高分不等于高quality

#### MICHELIN (餐厅星级 / 酒店Keys)

- 角色: 餐厅和体验型酒店的最高quality权威
- 机制: 专家匿名评审
- 读法: 星级/Key级别直接映射grade; Bib Gourmand = 高性价比信号
- 注意: 覆盖面有限，未入选不等于不好

#### 小红书

- 角色: 中国游客体验细节、排队实况、近期波动
- 机制: 非评分平台，看笔记数量+互动量+内容细节
- 读法: 高频出现 = traveler_hot信号; 具体避坑内容 = risk信号
- 注意: 需区分原创体验和营销推广

### 内部基准分

平台解释后，转化为内部统一的粗粒度基准分，**只用0.5档位**:

#### Base Quality Score (主骨架)

| 分值 | 含义 | 对应参考 |
|------|------|---------|
| 5.0 | 该组顶级/标杆 | Tabelog百名店top / 米其林二三星 / MICHELIN Three Keys |
| 4.5 | 明显强 | Tabelog品类前5% / 米其林一星/Bib / MICHELIN Two Keys |
| 4.0 | 稳定强 | Tabelog品类前15% / japan-guide Top Attraction |
| 3.5 | 有竞争力 | Tabelog品类前30% / japan-guide Recommended |
| 3.0 | 中位可选 | 品类中位数水平 |
| 2.5以下 | 不应靠后续加分硬救 | 不进入终选 |

注意: 以上对应仅为参考锚点，实际由品类内相对位置决定，不硬套。

#### Base Quality Score 计算铁律

> 关西教训: 全局 min-max 归一化 (tabelog-3.39)/(4.65-3.39) 太脆弱，
> 补一轮 mid/budget 数据后上下界就漂了。

**组内 percentile 为主，raw score 只做辅助排序:**

```
餐厅:
  分组: city × cuisine_normalized × budget_tier
  有 tabelog_score: 组内 percentile rank (0-1)，映射到 2.5-5.0
  有 michelin: 组内 percentile + bonus (+0.25/+0.5/+0.75 for 1/2/3star)，cap 5.0
  无 tabelog 无 michelin: 取同组 median percentile，标 score_basis: "group_median"
  raw tabelog_score 保留为辅助字段，不作为 score 本身

酒店 — OTA/Keys 评分做主轴，hotel_type/features 只做修正:
  主信号:
    Michelin Keys: 3Keys→5.0, 2Keys→4.5, 1Key→4.0
    OTA 星级 (★4.5等): (rating / 5.0) 映射到 2.5-5.0
    Forbes stars: 5star→4.75, 4star→4.25
  修正信号（不做主评分）:
    hotel_type: ryokan/boutique → +0.1
    key_features 3+个 → +0.05
    source 多源 2+ → +0.05
  无任何评分: 按 city × hotel_type × price_level 组内 median

景点:
  japan_guide_level: top→4.0, recommended→3.5, featured→3.0
  城市特色加成: history_religion 在京都/奈良 +0.25

不做全局归一化。不做跨平台线性换算。只在组内比较。
```

#### Traveler Fit Modifier

范围: **-0.5 ~ +0.5**

| 值 | 含义 |
|----|------|
| +0.5 | 中国游客特别满意(携程高分+小红书高频好评) |
| +0.25 | 中国游客正面(携程评价不错) |
| 0 | 无明显信号或中性 |
| -0.25 | 有轻微不适配(语言障碍/口味差异) |
| -0.5 | 明显不适配(多人反映服务差/体验与预期不符) |

#### Indie Support Score

范围: **0 ~ +0.5**

单条权重:
- 强烈推荐(详细原创体验): 0.15
- 普通推荐(列表中有描述): 0.10
- 仅提及(一笔带过): 0.03
- 转载/PR: 0

递减规则: 前2条满权重，第3条起乘0.5。封顶0.5。

只允许影响: 帮助入围 / 同组内tie-break / 边界升级半档。
不允许: 单独把低quality条目抬成高等级 / 跨越主源上限。

#### Risk Penalty

范围: **-1.0 ~ 0**

| 值 | 触发条件 |
|----|---------|
| 0 | 无执行风险 |
| -0.25 | 轻微执行摩擦(步行稍远/偶尔排队) |
| -0.5 | 中度风险(排队常>60min/预约有难度/定休日多) |
| -1.0 | 严重风险(需提前数月预约且常约不到/交通极不便/近期大量差评) |

-1.0极少触发，大多数执行问题在-0.5以内。

#### 组内排序公式

```
HouseScore = BaseQuality + TravelerFit + IndieSupport + RiskPenalty
```

**只在同一决策位内排序用，不跨组比较，不展示给用户。**

示例:
- 菊乃井: Base 5.0 + Traveler +0.25 + Indie 0.15 + Risk -0.25(预约难) = 5.15
- 某网红拉面: Base 3.5 + Traveler +0.5 + Indie 0.3 + Risk -0.5(排队90min) = 3.8
- 同组内菊乃井排在前面，即使网红拉面traveler_fit更高

### 避雷触发机制

**不全量扫差评，只在特定条件下触发:**

触发条件(满足任一):
- S/A候选(终选的骨架，必须审)
- 边界升级候选(B->A或C->B)
- 中国游客高热条目(traveler_hot标签)
- 主源强但traveler源明显偏弱(反差信号)

触发后只看3类风险:

| 风险类型 | 示例 |
|---------|------|
| 执行性风险 | 排队、预约难、营业不稳定、定位难、交通摩擦 |
| 体验落差风险 | 照骗、过度商业化、单一爆品、性价比差 |
| 人群不匹配风险 | 语言不友好、亲子不友好、箱子不友好 |

证据门槛(满足任一才标避雷):
- 近6个月，2个以上平台重复出现同类负面
- 同一平台，3条以上具体负面指向同一问题
- 官方/商家明确承认的执行性问题

输出字段:
```json
"risk_watch": {
  "level": "none / mild / medium / high",
  "triggers": ["queue", "value_gap", "language_barrier"],
  "evidence": "近6个月携程+小红书均多次提到排队90分钟以上",
  "action": "建议非高峰时段去; 如时间紧改选替代店"
}
```

---

## 五、三条标签线

每条入选数据标记入选逻辑(可多选):

| 标签 | 含义 | 判断来源 | 手账本用途 |
|------|------|---------|-----------|
| city_icon | 城市身份/文化名片 | 编辑+权威源 | 行程骨架"必须体验" |
| traveler_hot | 游客高热度 | 携程/小红书/评论量 | "大家都在去"(标排队风险) |
| local_benchmark | 本地口碑标杆 | Tabelog/Retty/日文源 | "本地人推荐"(差异化价值) |

三者经常重叠(如菊乃井三条都满足)，但不应混为一类。
**手账本的付费价值在于local_benchmark -- 区别于免费攻略。**

---

## 六、品类内相对排名

不用固定阈值(3.2/3.5/3.7)做终选，用品类内相对位置:

```
终选标准:
"在这个城市、这个品类/类型、这个价位中，是否属于前列？"

操作:
1. 按 city x category x price_tier 分组
2. 每组内按主评分源排序(每组只认一个主评分源，不做跨平台综合分)
3. 按样本量决定取法(见下)
4. 编辑判断做最终取舍
```

### 主评分源(每组只认一个，其余来源只做交叉确认/风险提示)

| 品类 | 主评分源 | 辅助确认源 |
|------|---------|-----------|
| 餐厅 luxury/premium/mid/budget | Tabelog品类排名 | 米其林/百名店/Google |
| 餐厅 street | Google评分+评论 | Retty/小红书 |
| 酒店 体验型(ryokan/luxury) | 一休评分 + MICHELIN Keys | 楽天/Booking |
| 酒店 功能型(business/city) | 楽天评分 | 一休/Booking |
| 景点 | JNTO/japan-guide编辑等级 | Google评分(城市内相对) |
| 店铺 | 该类型专业源 | 独立攻略站原创推荐 |

**不做跨平台归一化。** Tabelog 3.5和Google 4.0不是同一件事，硬拉到同一刻度是伪精确。
其他来源只用于: 交叉确认、游客满意度修正、负面风险提示、执行可行性校验。

### 样本量门槛

分组后，按样本量决定取法:

| 组内样本量 | 取法 | 原因 |
|-----------|------|------|
| >= 15 | 取前10-20% | 样本够，百分位有意义 |
| 6-14 | 不用百分位，取最好的N家 + 编辑判断 | 样本不足，百分位会人为造出"冠军" |
| < 6 | 仅在存在明确代表项时收录1-2家，否则留空 | 样本太小，不硬做精选 |

### 同一决策位封顶3家

```
决策位 = corridor x category x price_tier
(酒店: area x hotel_type x price_level)

终选在每个决策位最多保留3家:
  首推: 综合最强，最能代表这一类
  稳妥替代: 质量接近，但排队/预约/价格/位置更友好
  机动备选: 风格略不同，或营业窗口更互补

规则:
  - 3家差异不够大 -> 只留2家
  - 没有真好选项 -> 留0家(允许稀疏)
  - 绝不为凑数放入"还行"的选项
```

手账本是纸质产品，用户要的是"帮我做过取舍"，不是"给我一个列表"。
3家 = 用户翻开就能决策，不需要再比较。

---

## 七、负向编辑规则

### 负向证据门槛(跨品类统一)

负向信号只有在满足以下条件时才可触发降级/排除:
- **官方明确信号**: 已关闭、维修中、安全警告等
- **多源重复提及**: 同一问题被 >= 3个独立来源提及(如"排队久""服务差""游客陷阱")
- **单源但证据确凿**: 如官方定休日与推荐冲突、Google Maps标记permanently closed

单一个人差评、单篇博文吐槽、或仅1-2条评论提及的问题，**不足以触发降级**，最多标注为risk_flag供编辑参考。

这条规则防止不同agent/编辑对负向信号使用不同尺度，导致精选风格漂移。

### 负向信号清单

精选的价值在"明明很多人写，我却不收":

| 负向信号 | 适用品类 | 处理 |
|----------|---------|------|
| 排队成本远超体验 | 餐厅/景点 | 不收或降级+标注 |
| 只靠单一爆品支撑 | 餐厅/景点 | 降级 |
| 体验波动大(好评差评极端) | 餐厅/酒店 | 标风险 |
| 营业不稳定 | 餐厅/店铺 | 标"建议出发前确认" |
| 高价但缺乏记忆点 | 餐厅/酒店 | 标value_perception:below |
| 和周边走廊搭配差 | 所有品类 | 降低推荐优先级 |
| 过度商业化(游客陷阱) | 餐厅/景点/店铺 | 降级或不收 |
| 替代品更优 | 所有品类 | 不收，记录替代推荐 |

负向淘汰必须记录理由:
```json
"editorial_exclusion": {
  "excluded": true,
  "reason": "排队2小时，同区域有3家同品质免排队替代",
  "better_alternatives": ["xxx_id", "yyy_id"]
}
```

---

## 八、独立攻略站管理

### 统一独立站池(不按品类拆)

每个城市圈维护一个独立站池:
- 先从已验证核心站检查是否覆盖该城市(乐吃购/BringYou/Mimi韩等)
- 搜索补充到20-30个
- 筛选出10-15个核心站(部分全覆盖，部分专精)
- 保存为 `data/{城市圈}_spots/indie_sites_evaluation.json`

### 筛选标准

| 维度 | 高分(3) | 中分(1-2) | 低分(0) |
|------|---------|----------|---------|
| 原创性 | 实拍+详细体验 | 部分原创 | 纯转载 |
| 覆盖深度 | 每家有价格/排队/评价 | 基本描述 | 只有名字 |
| 时效性 | 2024-2026更新 | 1-2年前 | 3年+ |
| 数量+专业+独立 | 各1分 | | |

总分>=7为核心站。

### 去重计票与grade加分

独立站对精选有两层价值: **grade微调** + **精选评价素材**。

#### grade加分规则

每条独立站推荐按深度计分:

| 推荐深度 | 权重 | 判断标准 |
|---------|------|---------|
| 强烈推荐 | 0.15 | 有专门段落/篇幅，实拍照片，具体体验描述 |
| 普通推荐 | 0.10 | 在推荐列表中出现，有简短描述 |
| 仅提及 | 0.03 | 一笔带过，无具体评价 |
| 转载/PR | 0 | 不计 |

累计规则:
- 前2条满权重，**第3条起乘0.5**（递减，防堆量）
- **封顶0.5**
- 加分只在同组内提升排位，不可跨组跳级
- 只允许影响: 帮助入围 / 同组内tie-break / 边界升级半档
- 不允许: 单独把低quality条目抬成高等级 / 跨越主源上限
- 多个差评 -> 标risk_flag，不机械降级

示例(含递减):
- 2个强烈+1个普通 = 0.15+0.15+(0.10x0.5) = 0.35
- 1个强烈+2个普通 = 0.15+0.10+(0.10x0.5) = 0.30
- 3个强烈 = 0.15+0.15+(0.15x0.5) = 0.375
- 1个强烈 = 0.15（单人强推也有价值）
- 5个普通 = 0.10+0.10+(0.10+0.10+0.10)x0.5 = 0.35

详细定义见第四b章"内部基准分 - Indie Support Score"。

#### 精选评价提取

独立站最大的产出不只是grade加分，更是**真实体验评价素材**。
博主的原创描述比我们自己写的why_selected有说服力得多。

```
每条终选数据最多保留3条精选评价(indie_quotes):
- 优先选: 有具体细节的(味道/氛围/服务)
- 优先选: 有实拍照片佐证的
- 优先选: 不同角度的(一个说味道好，一个说氛围好)
- 标注来源站名和文章URL
```

数据结构:
```json
"indie_quotes": [
  {
    "source": "Inside Kyoto",
    "url": "https://...",
    "quote": "The eel here has a perfectly crispy skin...",
    "aspect": "味道"
  },
  {
    "source": "Mimi韩",
    "url": "https://...",
    "quote": "排队大概20分钟，但完全值得...",
    "aspect": "排队/体验"
  }
]
```

---

## 九、搜索方法

### 语言分层

| 阶段 | 语言 |
|------|------|
| 发现池 | 简中+繁体台+繁体港+日文+英文 全开 |
| 入围池 | 日文+官方(JNTO/japan-guide)+简中 |
| 终选池 | 不搜索，做编辑判断 |

### 搜索词模板(发现阶段)

餐厅: "{城市}美食推荐" / "{城市}{菜系}推荐" / "tabelog {城市} ランキング" / "best {cuisine} in {city}"
酒店: "{城市}住宿推荐" / "{城市} ホテル おすすめ" / "best hotels {city}"
景点: "{城市}景点必去" / "japan-guide {city}" / "{城市} 観光 おすすめ"
店铺: "{城市}宝藏店铺" / "{城市} 古着屋 おすすめ" / "{city} vintage shops"

详细搜索词列表见各品类子文档(GUIDE_*.md)。

### OpenCLI 用于被 WebFetch 阻止的网站

被阻止的: livejapan.com, kaikk.tw, bring-you.info, mimigo.tw, ufood.com.hk
用OpenCLI替代。工具详情见 TOOLS_SETUP.md。

---

## 十、data_confidence 标记

每条数据必须携带(详见DATA_SCHEMA.md):

```json
"data_confidence": {
  "level": "verified/cross_checked/single_source/ai_generated",
  "sources": ["tabelog", "google_maps", "trip_com"],
  "axes_verified": {
    "quality": true,
    "traveler_fit": true,
    "execution": false
  },
  "verified_fields": ["grade", "pricing"],
  "unverified_fields": ["coord"],
  "last_verified_at": "2026-04"
}
```

| 等级 | 条件 | 可否用于生产 |
|------|------|-------------|
| verified | 三轴(quality+traveler_fit+execution)均有真实来源 | 可以 |
| cross_checked | 至少2个轴有真实来源 | 可以(标来源) |
| single_source | 仅1个轴有真实来源 | 标注使用 |
| ai_generated | 无任何轴有真实来源 | 不可用于生产 |

---

## 十一、已知问题与待修(关西数据)

### 数据真实性

现有关西数据(景点171+餐厅380+酒店250)全部为 ai_generated。
评分/价格/坐标/营业时间全是AI估算，未经真实数据源验证。

### 结构问题

| 问题 | 影响 | 状态 |
|------|------|------|
| 坐标反转(55条) | 地图错 | 待修 |
| 景点缺 reservation_required | 171条 | 待修 |
| 奈良 open_hours 空 | 22条 | 待修 |
| 餐厅时间含括号 | 44条 | 待修 |
| 餐厅 A+/B+ 非标准 | 51条 | 待修 |
| 酒店 grade null | 79条 | 待修 |
| 酒店缺 check_in/meals | 全部 | 待修 |
| best_season 语义混淆 | 全部景点 | 需迁移到 seasonality 三层模型 |
| 缺 seasonality.open_seasons | 全部景点 | 需补充 |
| 缺 corridor_adjacency | 全部景点 | 需补充(边际成本纳入模型依赖) |
| arima跨圈关联未建立 | taxonomy配置 | 需加 cross_region_access |

### 系统设计修复(非补丁)

**1. 季节性模型: best_season -> seasonality 对象**

旧: 单一字段 best_season 混淆"最佳季节"和"能不能去"
新: seasonality 三层语义(open_seasons/best_season/avoid_season)
详见: GUIDE_SPOTS.md 第四章

系统筛选逻辑变更:
- 硬约束用 open_seasons (排除不可去的)
- 软推荐用 best_season (排序加分)
- 软警告用 avoid_season (提示但不排除)

**2. 景点纳入: duration x grade 硬编码 -> 边际成本模型**

旧: 3天只纳入S+A，5天纳入S+A+B
新: 按边际时间成本决定 -- B级景点如果在走廊动线上(边际成本=0)也纳入
详见: GUIDE_SPOTS.md 第四b章

需要新字段: corridor_adjacency (每个景点的走廊位置+边际绕路时间)

**3. 跨区域可达性: taxonomy cross_region_access**

有马温泉属于hyogo但从大阪30分钟可达。
需要在taxonomy.json增加:
```json
"cross_region_access": {
  "arima": {
    "reachable_from": ["osaka", "kobe"],
    "transit_minutes": {"osaka": 50, "kobe": 30}
  }
}
```

---

## 十二、数据时效性管理

手账本是纸质产品，印完不能改。时效策略:

### 采集时

- 所有评分标注 last_verified_at
- 价格标注"仅供参考，以OTA实际价格为准"
- 营业时间标注来源和检查时间

### 出发前(SYSTEM_DESIGN_V2已设计)

- 出发前3天: 检查行程中所有餐厅/景点的当周营业状态
- 如有临时休业 -> 发消息给用户，附替代方案(贴纸覆盖)
- 极端天气预警 -> 建议调整行程

### 数据刷新周期

| 数据类型 | 刷新周期 | 原因 |
|----------|---------|------|
| 营业状态 | 每月 | 关店率10-15%/年 |
| 评分 | 每季度 | 缓慢变化 |
| 价格 | 每季度 | 季节波动大 |
| 坐标/地址 | 每年 | 极少变化 |

### 过期判定

- last_verified_at > 6个月 -> 标记"待刷新"
- last_verified_at > 12个月 -> 降级为 unverified
- 关键字段(营业状态)出发前必须再验证

---

## 十三、MVP路径(单人可执行)

**完整路径是团队级工作量。以下是单人可执行的最小可行路径:**

### MVP目标

一个城市(如大阪)的一个区域(如难波)，完整跑通:
- 20家餐厅(各预算层)
- 10家酒店(各价位)
- 10个景点
- 5家店铺

### MVP步骤(约2-3天工作量)

```
Day 1: 城市级资产 + 发现
  0. 建立大阪research pack(一次性):
     - taxonomy子区域定义、走廊定义 (30分钟)
     - 旺季日历、城市菜系特色概览 (30分钟)
  1. 发现层搜索(日文+中文，成熟类目不开五语):
     - Tabelog搜索难波各菜系排名(批量，只取name+score+award) (1小时)
     - 携程搜索难波餐厅/酒店排名(列表级) (30分钟)
     - 小红书搜索"大阪难波美食"(OpenCLI) (30分钟)
     - japan-guide大阪景点页 (30分钟)
  2. 停机判断: 各组候选是否足够? 不足的补搜，够了就停

Day 2: 入围 + 终选(模型只做判断)
  1. 脚本合并去重，建立候选池CSV (30分钟)
  2. 脚本批量抽取evidence block(8-12行/条) (30分钟)
     - API分层: 入围候选补评分+区域+价格带(不查full detail)
  3. 模型做选品判断: 喂evidence block，产出:
     - grade + selection_tags + why_selected + skip_if (1小时)
     - 同一决策位封顶3家
  4. 终选候选才查full detail:
     - Google Places完整信息(用field mask) (30分钟)
     - 官网确认营业时间/预约方式 (30分钟)

Day 3: 结构化 + 分层审核
  1. 种子CSV -> 脚本生成完整JSON (脚本，不消耗token)
  2. validate_data.py校验 (脚本)
  3. S/A级: 完整三轴审查，逐条审核 (1小时)
  4. B/C级: 只确认真实性+执行性 (30分钟)
  5. 扩展到更多区域...
```

### MVP之后的扩展

```
难波跑通后:
  -> 心斋桥/道顿堀(相邻区域，很多数据可复用)
  -> 梅田/天王寺(新区域)
  -> 全大阪
  -> 京都/神户/奈良
  -> 温泉地
```

**关键: 先在一个区域验证整个流程，再扩展。不要一开始就铺全城市。**

---

## 十四、自动化工具状态

| 工具 | 状态 | 说明 |
|------|------|------|
| validate_data.py | **待实现** | JSON校验、坐标检查、格式检查 |
| build_json.py | **待实现** | 候选池CSV + AI增强CSV -> 完整JSON |
| OpenCLI | 已安装+已连接 | 小红书/台湾站/日文站抓取 |
| WebFetch/WebSearch | 可用 | 部分站被阻止用OpenCLI替代 |
| Google Maps API | 需配置API Key | 坐标/评分/营业时间 |
| Rakuten Travel API | 需注册 | 酒店数据 |

**脚本实现优先级: validate_data.py > build_json.py > 其他**

---

## 十五、待补充主题(标注未来完善)

| 主题 | 重要度 | 说明 |
|------|--------|------|
| 图片/照片采集策略 | 高 | 纸质手账视觉呈现核心 |
| 季节活动采集指南 | 中 | Schema已定义结构，缺采集方法 |
| 走廊间交通时间 | 中 | corridor transit_minutes行程编排必需 |
| 汇率更新机制 | 低 | 当前硬编码0.05，需更新策略 |

---

## 十六、文档结构

```
docs/data-engineering/
  MASTER_GUIDE.md          -- 本文档(唯一权威执行文档)
  DATA_SCHEMA.md           -- 字段定义规范(含 Selection Ledger schema)
  PHASE2_PLAN.md           -- Phase 2 选择模型执行计划(v2.0)
  GUIDE_RESTAURANTS.md     -- 餐厅精选子文档
  GUIDE_HOTELS.md          -- 酒店精选子文档
  GUIDE_SPOTS.md           -- 景点精选子文档
  GUIDE_SHOPS.md           -- 店铺精选子文档
  TOOLS_SETUP.md           -- 工具安装与使用
  CITY_CIRCLE_TEMPLATE.md  -- 新城市圈开城模板(含 Phase 1→2 归一化步骤)
  KANSAI_LESSONS.md        -- 关西踩坑总结 → 下个城市圈防坑清单
```

已归档(内容已合并入MASTER_GUIDE):
- DATA_COLLECTION_GUIDE.md -> 合并
- DATA_SELECTION_METHODOLOGY.md -> 合并
- SELECTION_PHILOSOPHY.md -> 合并
- DATA_SOURCES_DIRECTORY.md -> 合并
- DATA_QUALITY_CHECKLIST.md -> 合并(校验规则见附录A)
- SEARCH_METHODOLOGY.md -> 合并(搜索词见附录B)

---

## 附录A: 自动校验规则

以下规则应写入 `scripts/validate_data.py`，每次数据变更后运行。

### 通用

```
RULE-001: JSON文件必须能正确解析
RULE-002: 所有ID在同类数据中唯一(跨文件检查)
RULE-003: coord[0](纬度) 在 24.0-46.0
RULE-004: coord[1](经度) 在 122.0-154.0
RULE-005: coord[0] > 100 则标记"经纬度反转"
RULE-006: grade 只允许 S/A/B/C，不允许 null/A+/B+
```

### 景点

```
RULE-101: when.open_hours 非空时匹配 /^\d{2}:\d{2}-\d{2}:\d{2}$/
RULE-102: when.reservation_required 必须是 boolean
RULE-103: cost.admission_jpy >= 0
RULE-104: visit_minutes > 0
RULE-105: main_type 必须是 fixed_spot/area_dest/experience
RULE-106: sub_type 必须在 taxonomy.json 中定义
```

### 餐厅

```
RULE-201: when.lunch_hours 非空时匹配 HH:MM-HH:MM(无括号)
RULE-202: when.dinner_hours 同上
RULE-203: cost._cny == cost._jpy * 0.05 (允许+-1误差)
RULE-204: budget_tier 必须是 luxury/premium/mid/budget/street
RULE-205: cuisine 必须在 DATA_SCHEMA.md 菜系码枚举中
RULE-206: wagyu_grade 非null时必须在枚举中
RULE-207: is_city_must_eat=true 时 must_eat_reason 不能为空
```

### 酒店

```
RULE-301: experience.grade 不允许 null(功能性住宿标C)
RULE-302: hotel_type 必须在枚举中
RULE-303: pricing.*_jpy 必须是长度2数组且 [0] <= [1]
RULE-304: check_in 匹配 /^\d{2}:\d{2}$/
RULE-305: check_out 同上
RULE-306: meals_included 必须含 breakfast + dinner boolean
RULE-307: price_level 必须是 luxury/expensive/moderate/budget/backpacker
```

### 修复操作速查

```python
# 坐标反转
if coord[0] > 100: coord = [coord[1], coord[0]]
# Grade标准化: A+->A, B+->B, null->C(酒店)
# 时间格式: re.sub(r'[(][^)]*[)]', '', raw).strip()
# check_in默认'15:00', check_out默认'11:00'(旅馆'10:00')
# meals_included从price_note推断('早'/'朝食'->breakfast=True)
```

---

## 附录B: 搜索词速查

| 品类 | 语言 | 搜索词 |
|------|------|--------|
| 餐厅 | 日文 | "{城市} {菜系} ランキング tabelog" / "tabelog {城市} 百名店" |
| 餐厅 | 简中 | "{城市}美食推荐" / "{城市}必吃" |
| 餐厅 | 繁体台 | "{城市}美食 推薦 部落格" |
| 餐厅 | 英文 | "best {cuisine} in {city} japan" |
| 酒店 | 日文 | "一休.com {城市} ランキング" / "楽天トラベル {城市} 口コミ" |
| 酒店 | 简中 | "{城市}住宿推荐 攻略" / "{城市}住哪里方便" |
| 酒店 | 繁体台 | "{城市}住宿 推薦 飯店" |
| 景点 | 英文 | "japan-guide {city}" |
| 景点 | 日文 | "{城市} 観光 おすすめ スポット" / "{城市} 穴場 スポット" |
| 景点 | 简中 | "{城市}景点 必去 推荐" / "{城市}小众景点" |
| 店铺 | 日文 | "{城市} 古着屋 おすすめ" / "{城市} 雑貨屋 おすすめ ブログ" |
| 店铺 | 简中 | "{城市}宝藏店铺 小众" / "{城市}中古店 推荐" |

搜索策略: 城市级(广) -> 区域级(深) -> 菜系/主题级(精)。每次记录搜索词+独立站URL+高频店名。

WebFetch可用: tabelog.com, trip.com, letsgojp.cn, matcha-jp.com, japan-guide.com, savorjapan.com
WebFetch被阻止(用OpenCLI): livejapan.com, bring-you.info, mimigo.tw, kaikk.tw
