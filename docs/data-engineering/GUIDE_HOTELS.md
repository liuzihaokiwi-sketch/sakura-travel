# 酒店精选指南

> 版本: 2.0
> 更新: 2026-04-01
> 上位文档: SELECTION_PHILOSOPHY.md
> 定位: 编辑型酒店推荐库，不是订房系统
> 核心逻辑: hotel_type x district x price_level 分轨比较

---

## 一、分轨比较原则

**不把商务酒店和顶级旅馆放一起比。**

精选标准是"在同类型同区域同价位中，是否属于前列？"

```
比较单元 = hotel_type x district x price_level

示例:
- 京都祇园 luxury_ryokan 中: 俵屋 vs 柊家 vs 虹夕诺雅 -> 哪2-3家最值得写？
- 大阪难波 business_hotel 中: Dormy Inn vs APA vs 东横INN -> 哪家性价比最高？
- 有马温泉 ryokan 中: 全区35家取最值得的8-10家
```

每个比较单元内按主评分源排序，不跨单元比较，不做跨平台归一化综合分。
按样本量决定取法(见MASTER_GUIDE第六章): >=15用百分位, 6-14用fixed N, <6仅收明确代表项。
同一决策位(area x hotel_type x price_level)最多保留3家: 首推/稳妥替代/机动备选。

---

## 二、数据源(按三轴模型)

酒店的数据源角色**按hotel_type不同而不同**，不是统一的优先级排序。
详见MASTER_GUIDE第四章"三轴判断模型"。

### 体验型酒店(ryokan/luxury_ryokan/shukubo/machiya)

| 判断轴 | 主评分源 | 辅助源 |
|--------|---------|--------|
| quality | 一休评分 + MICHELIN Keys | 楽天/Booking/Relux |
| traveler_fit | 携程 + 小红书 | 马蜂窝/独立站 |
| execution | Google Maps + 官方网站 | 独立站实地体验 |

携程在体验型酒店主要作为traveler_fit信号，但可作为quality的**修正项/否决项**
(如: 多位中国游客反映服务态度差 -> 即使一休高分也要标风险)

### 功能型酒店(business_hotel/city_hotel/hostel/boutique)

| 判断轴 | 主评分源 | 辅助源 |
|--------|---------|--------|
| quality | 楽天 + **携程** | 一休/Booking |
| traveler_fit | 携程 + 小红书 | 马蜂窝/独立站 |
| execution | Google Maps + 官方网站 | 独立站实地体验 |

功能型酒店的"品质"就是"住得顺不顺"，携程中国用户评价直接反映目标用户感知到的品质。

### 所有酒店通用

| 数据源 | 得到什么 |
|--------|---------|
| 一休.com | 评分排名、价格、设施、含餐 |
| 楽天Travel | 评分、价格、评论、空房 |
| 携程Trip.com | 中国游客评分、人民币价格、中文评论 |
| Booking.com | 国际评分(1-10)、价格 |
| じゃらん | 日本家庭客评分 |
| Google Maps | 评分、坐标、营业状态 |
| 小红书 | 中国游客住宿体验 |
| 独立攻略站 | 入住体验、区域选择建议 |
| MICHELIN Keys | 体验型酒店最高权威 |

---

## 三、MICHELIN Keys 体系

替代旧的"米其林推荐酒店":

| 等级 | 含义 | 对应我们的grade |
|------|------|----------------|
| Three Keys | 住宿体验最高荣誉 | S级 |
| Two Keys | 杰出住宿 | A级 |
| One Key | 值得特别关注 | A-B级 |

MICHELIN Keys 是体验型酒店(experience.grade S/A)的权威信号。
在日本已覆盖东京、京都、大阪等主要城市。

---

## 四、三层池执行

### 发现池

```
Step 1: OTA批量搜索
  - 一休/楽天/携程/Booking 按区域搜索
  - 每区域取前20-30家(各平台)
  - 合并去重(日文名为主键)

Step 2: MICHELIN Keys名单
  - 提取该城市所有Key酒店

Step 3: 独立攻略站
  - 从核心站(乐吃购/BringYou/Mimi韩等)获取推荐
  - 搜索补充到20-30个独立站

Step 4: 小红书
  - "{城市}住宿" "{区域}酒店"
  - 记录高频推荐和避坑信息
```

### 入围池

```
按 hotel_type x district x price_level 分组后:

进入条件:
- 同组内 一休/楽天 评分前30%
- 或 携程评分前20%(中国游客认可)
- 或 MICHELIN Keys 入选
- 或 2个P0+P1来源交叉高分

不进入:
- 仅1个来源且非P0
- Google < 3.3
- 携程 < 3.5 且评论 > 50(确认差)
```

### 终选池

```
每个分组内:
1. 按主评分源排序(体验型用一休+MICHELIN Keys，功能型用楽天)
2. 按样本量决定取法(>=15取前10-20%，6-14取best N，<6仅收代表项)
3. 编辑判断:
   - "如果朋友去这个区域，这个预算，我会推荐住这家吗？"
   - 检查负向信号
   - 确认体验标签
4. 某个分组没有好选项就空着

终选数量参考(不是硬指标):
  luxury_ryokan: 每温泉地3-5家
  city_hotel: 每核心区域3-5家
  business_hotel: 每核心区域2-3家(只选性价比最高的)
  hostel: 每城市2-3家(只选口碑最好的)
```

---

## 五、体验等级

| 等级 | 含义 | 判断来源 | 行程影响 |
|------|------|---------|---------|
| S | 住宿本身是此行目的 | MICHELIN Three Keys/编辑判断 | check-in后算活动 |
| A | 住宿明显加分 | MICHELIN Keys/一休高分体验旅馆 | 预留泡汤/赏景时间 |
| B | 有小惊喜 | 有温泉大浴场/特色设计 | 不影响行程但更好 |
| C | 纯功能性住宿 | 普通商务酒店 | 纯睡觉 |

体验类型: onsen / view / heritage / shukubo / machiya / design / meal

**experience.grade从OTA评论+独立站体验描述+MICHELIN Keys判断，不是AI凭空标注。**

---

## 六、三条标签(酒店版)

| 标签 | 含义 | 示例 |
|------|------|------|
| city_icon | 住在这里本身就是体验 | 俵屋旅馆、虹夕诺雅、高野山宿坊 |
| traveler_hot | 中国游客高频推荐 | Dormy Inn(温泉+夜宵)、大阪万豪(夜景) |
| local_benchmark | 日本本地口碑最好 | 一休评分top、西村屋本馆(城崎) |

---

## 七、价格采集

**价格必须来自OTA真实数据，绝不可AI估算。**

```
采集方法:
  一休/楽天/携程各搜索3个时段:
  - 淡季(1月平日)
  - 平季(5月平日)
  - 旺季(11月周末/3月下旬樱花季)

记录:
  - 最低和最高价格
  - 是否含餐、含税
  - 多平台取中位数作为参考价

输出:
  pricing.off_season_jpy: [min, max]
  pricing.regular_season_jpy: [min, max]
  pricing.peak_season_jpy: [min, max]
  pricing.price_note: "含早晚餐 / 旺季翻3倍 / ..."
```

---

## 八、负向编辑规则(酒店)

| 信号 | 处理 |
|------|------|
| 隔音差(3+人提及) | 标注，轻度降级 |
| 设施老旧+价格不低 | 标 value_perception: below |
| "步行5分钟"但实际爬坡/绕路 | 调整access_friction |
| 房间极小(连箱子都打不开) | 标注，budget层可接受 |
| check-in排队30分钟+ | 标注practical_tip |
| 旺季价格翻3倍以上 | 标注，建议替代时段 |
| 装修好但位置极不便 | 不降级但标access_friction: high |

---

## 九、评价维度(从真实评论提取)

| 维度 | 字段名 | 类型 |
|------|--------|------|
| 位置便利度 | location_convenience | remote/ok/convenient/excellent |
| 房间状况 | room_condition | dated/acceptable/good/excellent |
| 温泉/浴场 | bath_quality | none/basic/good/exceptional |
| 早餐评价 | breakfast_quality | none/basic/good/highlight |
| 隔音情况 | soundproofing | poor/acceptable/good |
| 性价比 | value_perception | below/fair/above |
| 适合人群 | best_for | string[] |

**从携程中文评论+小红书+Booking评论提取。评论没提到的不填。**

---

## 十、温泉旅馆特殊处理

- 价格通常含早晚餐 -> price_note 标明
- 城崎11-3月蟹季 +50-100% -> 标明
- experience.grade 通常 >= B(有温泉)
- bath_quality 和 breakfast_quality(含晚餐) 特别重要
- 城崎七汤巡り / 有马金泉银泉 -> 在descriptions中说明

---

## 十一、交通摩擦度

```
access_friction:
  level: low/medium/high
  summary: 具体描述
  luggage_friendly: true/false

判断标准(必须查实际交通路线，不凭AI印象):
  low: 车站直结或步行5分钟内平路
  medium: 步行10-15分钟或需换乘一次
  high: 需坐船/爬坡/换接驳车/末班车早
```
