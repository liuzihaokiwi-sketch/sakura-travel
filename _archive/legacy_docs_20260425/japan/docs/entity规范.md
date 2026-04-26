# 日本 entity（景点）规范

> 日本各圈通用规范。entity = 景点·动线锚点·文化地标，是模板/餐厅/酒店挂载的基础设施。
> 跟餐厅 / stops / 酒店三类规范并列。
> 字段权威 → [docs/SCHEMA.md §2.1](../../docs/SCHEMA.md)（D43 三块结构）

---

## 一、6 条铁律（违反任何一条 = 全部不通过）

### 1. entity 不为挂店服务（核心铁律）

entity 必须**自己有意义**才加：
- 用户必去 / 模板动线锚点 / 文化地标
- 不是为了"店挂不上"而凑

**店挂不上就挂最近合理 entity，walk_min 大一点没关系**。挂不上任何合理 entity 的店 → 降 skeleton 或不收，**不为它加新 entity**。

历史教训：D40 时期为了让店家"挂得近"凑了 4 个大阪 entity（堀江/日本桥/美国村/心斋桥筋），每个用户用到都正好是动线锚点 → 这种该加；但若是为了挂某家路边咖啡而加 → 拒绝。

### 2. 字段不准膨胀

字段定稿见 §二。**不准私自加任何字段**。

D43 已禁字段：name_zh/name_ja/name_en（合并 note.店名）/ coordinates / official_url / short_desc / admission / opening_hours / closed_days / access / photo_ok / tripod_allowed / reservation_required / seasonal_notes / notes / is_public_path / unesco / address_ja / phone / reservation_url / _alias / 8 个一次性字段。

发现需要新字段 → **停下问用户**，不要先加再说。

### 3. 数据不准造假

- 推断 ≠ 事实（米其林星级年份不猜·营业时段不编）
- 查不到 → 模糊化 / 标"待核实" / 字段留空
- 不写跨景点比较句（"全京都最美的红叶"）
- 数据来源必须真访问过，不是 AI 推断

### 4. area 必须从白名单选

跟餐厅/stops/酒店共用同一 `area_registry.json`。entity 的 area 是**该景点所在区域**（动线粒度），不是城市级粗粒度。

不在 registry → 停下报告。

### 5. depth 必须真实

- skeleton：基础信息（id / city / area / category / note 简介）
- verified：note 全填 + 元数据完整
- full：verified + templates_meta 至少 3 个 key（拍照位置/冷知识/避坑 优先）

**templates_meta 全空也能 verified·但不能 full**。

### 6. 主次分明

- **A 类**（装配跑不动 / 字段缺失） → 停下报告
- **B 类**（用户体验硬伤：地址错 / 季节标错 / 模板用不到） → 停下报告
- **小事**（templates_meta 不全 / 文笔粗糙 / 数据来源单一） → 标 verified 或留空，**继续做不停**

---

## 二、字段定稿（D43 三块结构）

详见 [docs/SCHEMA.md §2.1](../../docs/SCHEMA.md)。本段只做摘要+示例。

```json
{
  "entity_id": "kyo_kiyomizudera",
  "city": "京都",
  "area": "higashiyama",
  "category": "unesco_temple",
  "depth": "full",
  "season_months": [11, 12],
  "note": {
    "店名": "清水寺（清水寺 / Kiyomizu-dera）",
    "简介": "1200 年木造大舞台，京都最具代表的世界遗产寺院。可拍照禁三脚架，无需预约。建议清晨 7 点前到避开人流。官网 kiyomizudera.or.jp。",
    "票价": "成人 ¥500 / 学生 ¥400",
    "营业": "06:00-18:00（夏季到 19:00）；无定休",
    "怎么去": "市バス『五条坂』下车步行 10 分；京阪『清水五条』步行 25 分"
  },
  "templates_meta": {
    "亮点": ["木造大舞台", "1200 年历史", "世界遗产"],
    "拍照位置": [
      {"位置": "西门石阶", "角度": "回望京都市区", "时段": "黄昏"}
    ],
    "冷知识": "1633 年重建，舞台 139 根榉木立柱无钉接合",
    "衔接": "出南门下二三年坂步行 8 分到八坂通",
    "季节看点": {"红叶": "11 月中-12 月上三重塔周边", "樱花": "3 月下染井吉野西门通"},
    "顺路小店": ["七味家本铺（参道入口）"],
    "避坑": "10 点后参道挤建议 7 点前到"
  },
  "可信度": "verified",
  "数据来源": ["https://www.kiyomizudera.or.jp/"],
  "最后核实": "2026-04-25"
}
```

### 系统字段（6 个）

| 字段 | 必填 | 说明 |
|---|---|---|
| `entity_id` | ✅ | `{城市拼音简写}_{景点名}` |
| `city` | ✅ | 中文城市名（京都/大阪/神户） |
| `area` | ✅ | 动线粒度·与 area_registry 对齐 |
| `category` | ✅ | 类型枚举（temple/shrine/castle/bridge/park/garden/market/commercial_street/museum/onsen/view_spot/natural_path/riverside/theme_park/district/aquarium/observation_deck/amusement_park/shopping_street/boulevard/ferris_wheel/experience/historic_area/viewpoint/neighborhood） |
| `depth` | 选填，缺省 `skeleton` | `skeleton` / `verified` / `full` |
| `season_months` | 选填 | 季节独家月份数字数组（红叶=[11,12]）·常年=null 或省略 |

### note 块（5 个 key·给用户最终看）

| key | 必填 | 说明 |
|---|---|---|
| `店名` | ✅ | 中文（日文 / 英文）。中日一致省括号；缺英文省 `/ Eng` |
| `简介` | full 必填 | 80-200 字，"懂当地的朋友讲口吻"。吸收原 short_desc + 拍照规则 + 预约要求 + 季节亮点 + 避坑 tip |
| `票价` | 选填（免费景点省略） | 自然语言。"成人 ¥500 / 学生 ¥400" 或"免费" |
| `营业` | full 必填 | 自然语言一句：开门时段 + 定休 + 季节限定。24h 通行型写"24h"；商店街类写"各店不同" |
| `怎么去` | full 必填 | 含最近交通+步行分钟 |

### templates_meta 块（7 个 key·模板/AI 写文案时用·全选填）

| key | 说明 |
|---|---|
| `亮点` | 3-5 个短词标签，模板挂载时拉来 |
| `拍照位置` | 结构化机位（位置/角度/时段对象数组）·或 markdown 列表自由文本 |
| `冷知识` | curators_notes 渲染时引用的 fun_fact 素材 |
| `衔接` | 跟其他 entity 的动线衔接（"步行 N 分到 X"） |
| `季节看点` | 按季节 key 分（樱花/红叶/夏夜/雪）·装配按季节挑 entity 时配套消费 |
| `顺路小店` | 自由漫游段引用 |
| `避坑` | 模板/AI 写文案时引用 |

整块可空。但 depth=full 必须至少 3 个 key（**拍照位置/冷知识/避坑** 优先）。

### 元数据块（3 个）

| 字段 | 必填 | 说明 |
|---|---|---|
| `可信度` | ✅ | `verified`（2+ P0/P1 交叉）/ `cross_checked`（1 P0/P1+其他）/ `single_source`（仅 P2）/ `ai_generated`（不可上生产） |
| `数据来源` | ✅（≥1 URL） | 数组 |
| `最后核实` | ✅ | YYYY-MM-DD |

---

## 三、分类标准

### 3.1 category 枚举（约 24 项）

按物理类型分（决定动线放置/装配类型去重）：

| 类型 | 例子 |
|---|---|
| `temple` / `unesco_temple` | 清水寺/金阁寺/天龙寺 |
| `shrine` | 伏见稻荷/八坂神社 |
| `castle` | 大阪城/姬路城/二条城 |
| `bridge` | 渡月桥 |
| `park` / `garden` | 奈良公园/曹源池 |
| `market` / `shopping_street` / `commercial_street` | 锦市场/心斋桥筋/道顿堀 |
| `museum` / `experience` | 任天堂博物馆/食品模型体验 |
| `onsen` | 有马/城崎 |
| `view_spot` / `observation_deck` / `viewpoint` | 通天阁/六甲山顶 |
| `natural_path` / `riverside` / `boulevard` | 哲学之道/鸭川/御堂筋 |
| `theme_park` / `amusement_park` / `aquarium` / `ferris_wheel` | USJ/海游馆/HEP FIVE |
| `district` / `historic_area` / `neighborhood` | 嵯峨鸟居本/堀江/美国村 |

新类型不进枚举的 → 停下问用户。

### 3.2 季节独家 vs 常年

`season_months` 字段决定：
- 常年（多数 entity）→ null 或省略
- 季节独家（红叶名所/樱花夜枫/川床）→ `[11, 12]` 等月份数组

装配按用户行程日期 filter 季节独家 entity·常年 entity 不受季节影响。

---

## 四、数据准入

> **核心原则**：3 套递进判断——**价值判断 → 证据判断 → 角色判断**。

### 4.1 价值判断（要不要这条 entity）—— MTE 七维度

Kim et al. (2012) 学术锚（279 篇文献综述）：

| 维度 | 含义 |
|---|---|
| **享乐 Hedonism** | 感官愉悦 |
| **刷新 Refreshment** | 脱离日常 |
| **本地文化 Local culture** | 接触地方 |
| **意义感 Meaningfulness** | 与自我/他人联结 |
| **知识 Knowledge** | 学到东西 |
| **参与 Involvement** | 亲身动手 |
| **新奇 Novelty** | 第一次体验 |

**判断标准**：一个 entity 能同时打中 **2-3 个维度 = 好**；只打中 1 个 = 平庸；一个都打不中 = 不收。

### 4.2 证据判断（够不够格入池）—— 三轴模型 + 三层池

#### 三轴

| 轴 | 信号源 | 通过标准 |
|---|---|---|
| **quality** | 官方观光局 / Japan-guide / MATCHA / 米其林绿星 / japan_guide_level | 该类型中是否足够强 |
| **traveler_fit** | 携程评分+评论 / 小红书 collects > likes / 知乎长文 / 马蜂窝 | 中国游客实际去了不会后悔（不只"好玩"） |
| **execution** | 营业稳定 / 票价清晰 / 交通可达 / 人流可控 | 用户照行程能去到 |

**三轴规则**（4 档可信度）：
- **三轴全过** → `verified` 入 full
- **两轴过** → `cross_checked` 入 full
- **一轴过** → `single_source`，标注后入 full（高优先升级）
- **无任何真实证据** → `ai_generated`，禁止上生产

#### 三层池漏斗

```
发现池（5-10× 终选量）
   ↓ 任一可信源提及即入
入围池（2-3× 终选量）
   ↓ 三轴中至少两轴覆盖
终选池
   ↓ "朋友第一次去，我会专门推荐这个吗？"
   ↓ 同一决策位最多 3 家
   ↓ 允许稀疏（某区某档没合格的就空着）
```

### 4.3 角色判断（怎么用 / Tier 分层）

#### Tier 决定投入精力

| Tier | 投入 | 字段完整度 |
|---|---|---|
| **S 级**（城市代表·不去会遗憾） | 30-40 分钟/个 | depth=full + templates_meta 全填 |
| **A 级**（重要搭配·值得专程） | 15-20 分钟/个 | depth=full + templates_meta 至少 3 key |
| **B 级**（顺路可以·不必专程） | 10 分钟/个 | depth=verified + 拍照位置 1-2 |
| **C 级**（补充选项·时间富余） | 5 分钟/个 | depth=skeleton 即可 |

#### B/C 级小众入池 4 步（任一不通过则不入）

1. **内容质量**：能否一句话说清"为什么值得去"，说不清不入
2. **顺路+时间成本**：< 1.5h 顺路 → 候选进次要 slot；不顺路 → 候选作为"小众专题日"
3. **同区比较**：跟同区其他 B/C 候选比，**更独特/难替代才进**（不是"也不错"就入）
4. **人群标注**：明确适合 party_type（酒造适合 couple 不适合 family_with_children）·无明确人群 → 默认不进常规行程

### 4.4 数据源

完整 60+ 站清单见 [独立站清单.md](独立站清单.md)。entity 重点用：

- **P0**：JNTO（japan.travel）/ 京都市公式（kyoto.travel）/ 大阪観光局（osaka-info.jp）/ 米其林指南绿星 / Google Maps
- **P1**：Japan-guide.com（英文景点权威）/ MATCHA / 小红书（traveler_fit 主信号）/ 携程 / 知乎长文 / 马蜂窝
- **P2**：Inside Kyoto / Inside Osaka / icotto / aumo / co-trip / Hanako Web / 关西おでかけ手帖（季节专题）/ reddit r/JapanTravel

### 4.5 负向信号（任一触发即降 skeleton 或不收）

| 信号 | 处理 |
|---|---|
| 公认游客陷阱 | 不收 |
| 商业化网红打卡墙（无文化深度） | 归 stops 不归 entity |
| 装修中 / 永久闭馆 | 立即降 skeleton 标注·不删 |
| 小红书爆火但无官方/Google 背书 | 进 skeleton 观察 1-2 个月 |
| 体验维度只打中 1 个 | 不收 |

### 4.6 使用优先级（实操）

1. 现有 entity 库（`entities/{city}.json`）— 首选，不重复建
2. 模板已引用但 entity 不存在 → 优先补
3. P0 官方观光局 → 列发现池
4. P1 小红书 opencli + 知乎 → 补 traveler_fit
5. P2 季节专题 → 补 templates_meta.季节看点

**不自己编**。

### 4.7 搜索词模板

| 语言 | 词 |
|---|---|
| 日文 | `"{城市} {景点} 公式"` / `"{城市} 観光 おすすめ"` |
| 简中 | `"{城市}必去景点"` / `"{城市}小众"` / `"{城市}{季节}"` |
| 英文 | `"{city} hidden gems locals"` / `"{city} second visit"` |

---

## 五、校验

校验脚本：`scripts/validate_entity.py`

校验规则：
- 系统字段白名单（6 个）+ note 字段白名单（5 个）+ templates_meta 白名单（7 个）+ 元数据白名单（3 个） → 未知字段 FAIL
- area 字段必须在 `{圈}/area_registry.json` → 不在 FAIL
- category 必须在枚举内 → 不在 FAIL
- 必填字段缺 → FAIL
- depth=full 但 templates_meta < 3 个 key → 自动建议降 verified
- 可信度=ai_generated → FAIL（不可上生产）

跑法：`python scripts/validate_entity.py`，粘**完整输出**到交付消息。

---

## 六、历史教训

### 6.1 字段大瘦身（D43·已解决）

D40 时期 entity 字段达 36 个，包括 unesco/phone/address_ja/bridge_length_m 等单一 case 字段，且 SCHEMA 跟数据双向脱节（107 errors）。
**对策**：D43 重写为三块结构（系统 6 + note 5 + templates_meta 7 + 元数据 3 = 21 字段），单一 case 字段合并到 templates_meta 自由文本。

### 6.2 entity 为挂店凑数（已禁）

D40 时期为让店家"挂得近"加 entity（如某餐厅没有合理景点 → 加一个新 entity 仅给它挂）。
**对策**：铁律 1——entity 必须自己有意义，店挂不上就降 skeleton 不补 entity。

### 6.3 ID 重复混用（已合并）

`kyo_nijo_castle` vs `kyo_nijojo` / `nar_kasuga_taisha` vs `nar_kasugataisha` 等并存。
**对策**：ID 选规范命名（英文优先·snake_case·城市前缀统一），D43 时旧 ID 全部合并清理。

### 6.4 category 枚举跟现实脱节（已解决）

D40 SCHEMA 枚举写漏 13 项（aquarium/observation_deck/amusement_park/shopping_street/boulevard/ferris_wheel/experience/unesco_temple/street/historic_area/natural/viewpoint/neighborhood）。
**对策**：D43 扩枚举到约 24 项+ validator 校验，新类型不进枚举的停下问用户。

### 6.5 opening_hours 24h 通行型空缺（已解决）

街道/河岸/桥这种 24h 通行型 opening_hours 大量空缺。
**对策**：合并到 note.营业 自然语言一句话·24h 通行写"24h"·商店街写"各店不同"。

### 6.6 templates_meta 全空但标 full（注意点）

depth=full 但 templates_meta 7 个 key 全没填，无法支撑模板拉来用。
**对策**：full 必须至少 3 个 key（拍照位置/冷知识/避坑 优先），否则降 verified。
