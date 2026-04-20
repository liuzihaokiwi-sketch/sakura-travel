# 旅行手账本产品原则（西班牙 348 元）

> 本文档是西班牙手账本产品的**唯一原则文档**。
> 与关西 brief.md 并列，共享"策展产品 / 70-20-10 / A-B 推荐 / 信息分层"的通用骨架，差异化在节奏、餐饮、区域文化。
> AI 生成行程时只需读这一份。

---

## 1. 产品定位

**我们卖的是策展产品，不是定制工具。**

和关西一致：用户付费买"专家替你做好决策的确定性"。**一套主线模板 × 微调参数 = 覆盖所有用户**。

质量标准：**一个真实的西班牙本地顾问 + 一个懂中国用户视角的旅行博主，联合打磨出的攻略。** 不是"AI 生成看起来还行"。

---

## 2. 西班牙 ≠ 一个国家

**核心认知：Spain is many countries wearing one coat.**

西班牙内部的分裂比关西深得多。关西是大阪→京都→神户的**连续**情绪变化；西班牙是**并列**的 5 个文化区：

| 文化区 | 代表城市 | 情绪基调 | 感官主导 | 身份 |
|--------|---------|---------|---------|------|
| **Andalucía** | Sevilla / Granada / Córdoba | 慢热、melodic、festivo | 听觉(flamenco) + 嗅觉(橙花) + 味觉(炸鱼) | español |
| **Cataluña** | Barcelona / Girona | 设计、企业家气、欧洲感 | 视觉(Gaudí) + 海 | **不自认 Spanish，用 català** |
| **Basque** | San Sebastián / Bilbao | 骄傲、内敛、工业底蕴 | 味觉(pintxos 密度) + 海岸 | **不自认 Spanish，用 vasco** |
| **Madrid / Castilla** | Madrid / Toledo / Segovia | 快、城市夜、正统 | 视觉(博物馆) + 夜色 | español |
| **Galicia** | Santiago / 北岸 | 雾、内省、慢 | 听觉(海雾) + 味觉(海鲜) | **用 gallego** |

### 文案红线（硬）

- 在巴斯克 / 加泰 / 加利西亚区域，**禁用"西班牙人"**；用 "vasco / català / gallego" 或"本地人 / 这里的人"
- 不说"西班牙的 Barcelona"，说"加泰罗尼亚首府 Barcelona"
- 不把"晚饭 10 点"当猎奇卖点；用"按他们的生物钟，这就是傍晚 8 点"的 framing（Franco 时区错位导致）

### 情绪转折节点

类比关西"大阪→京都"模型，西班牙的多城主线按文化区切：

- Madrid(快) → Sevilla/Andalucía(慢热)：7 天行程最强对比
- Barcelona(设计) → San Sebastián(味觉)：北方轴
- Granada(摩尔余韵) → Sevilla(flamenco)：南方慢轴

---

## 3. 节奏灵魂（西班牙专属）

### 3.1 时区错位认知

Franco 1940 年把时钟从 GMT 挪到 CET，至今未改。**西班牙人的生物钟对伦敦，钟面写柏林。** 一切"晚"不是晚，是时钟骗人。这是整套节奏设计的底层解释。

### 3.2 一天 7 段节奏（不是 3 餐 + 景点）

| 时段 | 内容 | 是否可砍 |
|------|------|---------|
| 08-10h | 轻早餐（tostada + café con leche） | 可替代 |
| 09-13h | 主景点（最佳效率时段，不能浪费） | 不可砍 |
| 14-16h | **午餐 + sobremesa**（主餐，2-2.5h） | **sobremesa 不可砍** |
| 16-18h | **Siesta / 室内博物馆 / 慢逛**（夏季 40°C+ 避暑） | 可替代 |
| 17-18:30h | **Merienda**（咖啡+小甜点，必排） | **不可砍** |
| 19-21h | **Paseo**（换装慢走，ver y ser visto） | 不可砍 |
| 21:30-23h | 晚餐 / tapeo | 不可砍 |
| 22:00+ | Flamenco / 夜酒（可选） | 可选 |

### 3.3 北南时间差（硬参数）

| 区域 | 午餐 | 晚餐 |
|------|------|------|
| 北部（巴斯克、加利西亚、加泰北部） | 13:30 | 21:00 |
| 中部（马德里、卡斯蒂利亚） | 14:00 | 21:30 |
| 南部（安达露西亚） | 14:30 | 22:00 |

区域模板的默认 slot 时间按 region 分层，不用全国统一。

### 3.4 周日 = 硬约束日

除 Madrid / Barcelona 市中心外，**大多数商店、超市、银行周日关门**。周日模板：
- 砍所有 shopping slot
- 拉满博物馆 / 教堂 / paseo / 家庭午餐
- 标注免费博物馆时段（Prado 周日 17-19h 等）

### 3.5 8 月马德里空城（日历硬约束）

Madrileños 8 月去海边，大量餐厅商店关门。8 月马德里模板必须提示，建议用户挪到 9 月或年初；或反向做"热浪中的博物馆 + 避暑习惯"。

---

## 4. meal_role（西班牙扩展）

继承关西的 `arrival_recovery / core_local_experience / everyday_good / affordable_local`，**新增 / 细化**：

| 角色 | 含义 | 时段 | 适用约束 |
|------|------|------|---------|
| `merienda` | 下午茶（咖啡+churros/小甜点） | 17-18:30h | 每天必排，非可选 |
| `menu_del_dia` | 工作日午间套餐（€8-17 三道菜） | 14-16h | **周一-周五午餐限定**，周末晚餐不可推 |
| `sobremesa_extended` | 午餐延时 slot（饭后 45-60min 咖啡/甜酒） | 接午餐后 | 不可砍，**packed 密度也保留** |
| `vermut_ritual` | 中午餐前仪式（zinc 吧台 dry vermouth + olives） | 12-15h | 周末特有，某些城市（Triana/Madrid Castizo）更典型 |
| `tapeo_crawl` | 多家 tapas 串 | 21h+ | tapas 文化区（安达露西亚/巴斯克）核心体验 |
| `pintxos_crawl` | 巴斯克版 tapeo（Donostia / Bilbao 独有） | 20h+ | 巴斯克专用，不用 tapeo |

### meal_role 使用规则

- **Merienda 每天排 1 次**（密度=packed 也不砍；relaxed 可并入"自由漫步+咖啡" slot 不显式标注）
- **Menu del día 仅周一-周五午餐推**；周六日午餐不推，晚餐任何时候不推
- **Sobremesa 强制 2-2.5h 午餐 slot**；不是"吃 1h 走人"
- **Tapeo/pintxos 至少 1 晚做成显式 slot**（不是"晚餐吃 tapas"，而是"3 家 tapas 串"，每家 1-2 杯 + 1-2 份）

### 餐饮硬约束（西班牙）

- **不点 Sangría**（游客饮料），夏天点 tinto de verano；文案里给这条"点对了"的线索
- 点啤酒说 "una caña"（小杯）或 "una doble"，不说 cerveza（游客用词）
- 5-6 PM 不点啤酒（社交错位），这时段是 merienda 咖啡
- 西文菜单有 **ración / media ración / tapa** 三档价，英文菜单只有整份价——提示用户要西文菜单点半份最划算
- **"挂满 flamenco + 斗牛装饰的餐厅" = 游客陷阱**（中文源红线），直接避开

---

## 5. 新 slot 类型

在关西 `poi / meal / walk / transport / shop_info` 基础上新增：

| slot.type | 含义 | 时长 | 备注 |
|-----------|------|------|------|
| `paseo` | 傍晚社会仪式散步 | 60-90min | 必含 dress code 提示（换装、不带大相机） |
| `sobremesa` | 午餐延时谈话时段 | 45-60min | 与前一个 `meal` slot 绑定，不独立砍 |
| `siesta_indoor` | 午后室内替代（博物馆/教堂/慢逛） | 90-120min | 夏季必排；冬季可替代为 paseo 前置 |
| `flamenco_show` | 弗拉门戈观赏 | 60-90min | 仅 Andalucía / Madrid；订票严格度高 |
| `pintxos_crawl` | 巴斯克小吃巡游 | 2-3h | 巴斯克专用 |

---

## 6. 订票严格度（硬约束）

西班牙有 4 级订票窗口，超过窗口 = 产品失败：

| 级别 | 场所 | 提前窗口 | 手账本处理 |
|------|------|---------|-----------|
| **L1 最严** | Alhambra Nasrid Palaces | **3 个月前** | 下单前硬提示；订不到则行程改结构 |
| **L2 严** | Sagrada Família 塔楼 / Casa Vicens | 2 个月前 | 订不到降级为只看立面 |
| **L3 中** | Alcázar Sevilla / Catedral Sevilla + Giralda / La Pedrera / Casa Batlló / Prado 特展 | 2 周前 | 订不到则换其他博物馆 |
| **L4 松** | Bernabéu / Camp Nou 导览 / 一般博物馆 | 1 周前 | 订不到下调优先级 |
| **L5 Flamenco** | Casa de la Memoria / La Casa del Flamenco | **春秋 5-7 天前** 就卖完 | 提前订 A 场；B 轨用不订票的 Peña / Casa Anselma |

**手账本必须写清楚每个景点的订票窗口 + 官网链接**，这是"给确定性"的核心体现。

**票记名制**（Alcázar / Catedral / Alhambra）= 带护照核对，必须在旅行手册开头强调。

---

## 7. 着装硬约束

- **宗教场所**（大教堂 / 修道院）：过膝 + 不无袖 + 不吊带（硬要求，被拒案例多）
- **Paseo 时段**：换一套像样的衣服，不要运动装 / 沙滩装 / 大相机（会被标记 outsider）
- **Feria de Abril 参与**：女生传统 traje de flamenca（可租）

手账本在相关 slot 的 note 里一句话提示，不做列表，不做长篇。

---

## 8. Paradores（独家武器）

**Paradores de Turismo** 是西班牙国营古迹酒店网（97 家），把古城堡/修道院/宫殿改造成酒店。**中文攻略零覆盖**，是我们的信息差武器。

### 使用场景

- 历史名城 + 用户预算允许（中档+）→ 优先推 Parador
- 经典组合：
  - Parador de Granada（Alhambra 内部！）
  - Parador de Toledo（俯瞰全城）
  - Parador de Santiago（Reyes Católicos 酒店）
  - Parador de Ronda（悬崖边）

### 酒店层处理

- Parador 优先于同档 chain hotel
- 手账本推荐 Parador 时用"住在古迹里"的叙事（不是"四星酒店"）
- 具体可用的 15 家在事实层（live_facts / hotel_pools）维护，不写死在模板里

---

## 9. 体验设计原则（与关西共享 + 西班牙特化）

### 9.1 70/20/10 内容比例（同关西）

- 70% S 级景点（Alcázar / 大教堂 / Sagrada / Prado / Alhambra）
- 20% 氛围搭配（paseo / merienda / sobremesa / 街区漫步）
- 10% 惊喜 moment（Triana 的 Casa Anselma / Metropol Parasol 日落 / Peña flamenca）

### 9.2 B 选项要真的"惊"（同关西）

西班牙特供 B 方向：
- A：Casa de la Memoria flamenco 纯场 → B：Casa Anselma 免费酒馆听
- A：老城 tapas 餐厅 → B：Triana 后巷 Puratasca 炒饭 + 天妇罗 chorizo
- A：标准雪莉杯 → B：Bar Santa Ana 全年圣周圣母像

### 9.3 峰值稀缺（同关西）

- 6-8 天 1 大峰值 + 1 小峰值
- 9-13 天 2 大峰值 + 1-2 小峰值

西班牙大峰值候选：Alhambra 全景夕照 / Sagrada 黄昏光线 / Flamenco 心灵相通时刻 / Feria de Abril（4 月限定）/ Semana Santa 凌晨游行（3-4 月限定）

### 9.4 人味（西班牙比关西更浓）

西班牙人味是"被动接收"的——你坐在 paseo 的长椅上，5 分钟内会有人跟你说话。每 2 天必须有一个"和本地人同框" moment：市场吃 tapa、zinc 吧台 vermut、peña 听歌、paseo 长椅、merienda 老咖啡馆。

### 9.5 降档也是体验（西班牙特有）

- Menu del día（€8-17 三道菜 + 酒）本身是高档用户不该错过的"本地人正餐制度"
- Triana 站吧台 vermut + olives 比五星酒店早餐更值得写

### 9.6 文案有温度 / 给线索不给结论（同关西）

- 错："Alcázar 是塞维利亚必看景点"
- 对："开门就进——9 点的 Alcázar 后花园没人，爬山虎从墙头垂下来，茉莉香是这里的早餐"

---

## 10. A/B 推荐策略（同关西，全品类适用）

| | A（安全牌） | B（惊喜牌） |
|---|---|---|
| 定位 | 系统默认 | "想试试不一样的？" |
| 知名度 | 高 | 小众 |
| 体验角色 | 主流 | 与 A 不同 |

A/B 必须体验角色不同；西班牙 B 轨常见方向：**商业演出 vs 非商业场所 / 游客区 vs 本地街区 / 标准餐厅 vs 市场站着吃**。

---

## 11. 餐饮策略

### 11.1 核心理念（同关西）

普通餐压低，高光餐拉高。西班牙特有：**menu del día 和 vermut 是"被设计的平价体验"**，高档用户也该安排。

### 11.2 预算基线（约 7 顿正餐 + 每天 merienda）

| 档位 | 分布 |
|------|------|
| 经济 | 4-5 经济 + 2 中档 + 1 showcase tapas / flamenco 夜 |
| 中档 | 2 经济 + 3-4 中档 + 1-2 中高档 + 0-1 showcase |
| 高档 | 1 经济(menu del día) + 2-3 中档 + 3-4 高档 + 0-1 顶级（Quique Dacosta / Disfrutar / Arzak） |

### 11.3 跨城市菜系去重（类关西）

- A 轨去重，B 不算
- 城市代表菜系优先：
  - Sevilla → pescado frito / rabo de toro / sherry
  - Granada → tapas gratis（点酒送 tapa 独有制度）
  - San Sebastián → pintxos
  - Madrid → cocido / callos / churros
  - Barcelona → pa amb tomàquet / seafood paella / cava
  - Valencia → **正宗 paella**（paella 全程最多 1 次，归 Valencia；其他城市不上 paella）

### 11.4 showcase 上限

- 每城最多 1 顿 showcase
- 全程最多 2 顿（7-8 天）或 3 顿（13+ 天）
- Top tier（米其林 2★+）：family 永不触发；couple/friends 最多 1 次

---

## 12. 酒店策略（同关西 + Parador 优先）

### 呈现方式

- 推荐 1 家 + 备选 1 家（主备差异化）
- 历史名城优先推 Parador（如可用）
- 手账本中 Parador 用"住在古迹里"的叙事

### 修饰器（同关西）

`quality_first / resort_vibe / value_for_money / balanced`

西班牙扩展：`historic_lodging`（Parador 优先触发）

---

## 13. 模块拼装原则（同关西 + 西班牙特化）

### 13.1 基本结构（同关西）

核心基座 + 用户勾选模块 + 人群日 + 季节活动

### 13.2 排序原则（同关西）

Sleep first, play second.

### 13.3 换城日规则（同关西 + 西班牙交通特化）

- 上午 = 出发城市，下午 = 目的地
- AVE 高铁干线（Madrid-Sevilla / Madrid-Barcelona）：2.5-3h，是首选
- **提前 60 天订 AVE Promo 票可便宜 60%**
- 小城之间（Granada-Sevilla / Córdoba-Sevilla）用 ALSA 大巴 2-3h，比火车便宜

### 13.4 季节模块（西班牙独有）

| 季节活动 | 日期 | 城市 | 模块影响 |
|---------|------|------|---------|
| Semana Santa（圣周） | 3 月底-4 月初（2026: 3.29-4.5） | Sevilla / Málaga / Granada | 整周改模板，住宿翻 2-3 倍 |
| Feria de Abril | 4 月中下旬 | Sevilla | 独立模块，traje de flamenca 体验 |
| La Mercè | 9.24 前后 | Barcelona | Barcelona 季节模块 |
| San Fermín（奔牛） | 7.6-14 | Pamplona | Pamplona 专属模块 |
| Las Fallas | 3.15-19 | Valencia | Valencia 专属模块 |
| Reyes（三王节） | 1.6 | 全国 | 当天游行，大多数店关 |

---

## 14. 密度策略（同关西）

| 密度 | 砍减 |
|------|------|
| packed | 不砍（但 sobremesa / merienda / paseo 三个"灵魂 slot"永远不砍） |
| balanced | 砍 P4-P5 |
| relaxed | 砍 P3-P5，只保留 P1-P2 + 一个亮点 |

**西班牙特殊保护**：
- 任何密度都保留 sobremesa（砍了就不是西班牙）
- 任何密度都排 merienda（可不显式标注，但必须在时段里）
- Paseo 任何密度都保留（夏季 40°C+ 时可挪到 20h 后）

---

## 15. 天气 Plan B（西班牙扩展）

- 夏季 40°C+ 不是"天气问题"，是**常态**：14-18h 必须室内
- 雨天（北部多）：博物馆 / 教堂 / Mercado / flamenco 博物馆
- 冬季 11-2 月是 **Alcázar / Alhambra / Catedral 最松时段**，对怕晒+排队的用户反而是甜蜜点

---

## 16. 退化路径（同关西）

1. 天数不够 → 保留核心锚点 → 保留 1 亮点模块 → 保留人群记忆点 → 砍外围
2. 模块过多 → 明确勾选优先 → 时间稀缺性排序 → 被挤压模块给解释文字
3. 餐厅池不足 → 扩大半径 → 放宽预算半档 → 放宽 B → 允许只有 A
4. 人群+预算冲突 → 安全/适配优先于预算升级

---

## 17. 信息分层（同关西）

| 层级 | 内容 | 呈现 |
|------|------|------|
| 主线 | 核心景点 + 正餐 + 酒店 + flamenco 一场 | 大字 |
| 次级 | paseo 路线 + merienda + siesta 替代 + 次级景点 | 中字 |
| 附录 | peña / 小市场 / 街区 wild card / 购物 / 实用技巧 | 小字 |

---

## 18. 与关西 brief.md 的差异总结（给 AI 快速索引）

| 维度 | 关西 | 西班牙 |
|------|------|-------|
| 情绪结构 | 连续（大阪→京都→神户） | 并列（5 个文化区，选 2-3 区串） |
| 一天结构 | 早-午-下-晚 4 段 | 7 段（多出 sobremesa / merienda / paseo） |
| 晚餐时间 | 18-19h | 21-22h（南部更晚） |
| 午餐时长 | 1h | 2-2.5h（含 sobremesa） |
| 文化红线 | 无 | 加泰/巴斯克/加利西亚不是 Spanish |
| 订票严格度 | 基本不预约（除 USJ / teamLab） | 5 级严格度，Alhambra 3 月前 |
| 酒店武器 | 温泉旅馆 | Parador 国营古迹 |
| 季节模块 | 樱花/红叶 | Semana Santa / Feria / La Mercè / San Fermín |
| 餐饮去重 | 同天不重菜系 | 同 + menu del día 周末不推 + paella 归 Valencia |
