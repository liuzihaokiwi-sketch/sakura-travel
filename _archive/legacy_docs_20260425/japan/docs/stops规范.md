# 日本停留池规范

> 日本各圈通用规范。停留池 = 动线插件（顺路歇脚 / 顺路逛），不强制，走 near_attractions 就近匹配。
> 跟餐厅（必去）/ entity（景点）/ 酒店（住宿）三类规范并列。
> 关西特定的区域基因 → `japan/kansai/这是什么.md`

---

## 一、6 条铁律（违反任何一条 = 全部不通过）

### 1. 字段不准膨胀

字段定稿见 §二。**不准私自加任何字段**：
- `walk_min_estimated` ❌（已禁用）
- `drive_only` / `tags` / `vibe` 等 sonnet 自创 ❌
- 发现需要新字段 → **停下问用户**，不要先加再说

校验脚本对字段做严格白名单，未知字段 = FAIL。

### 2. 数据不准造假

**查不到 ≠ 写假的**。三种处理：
- 模糊化（"小店"替"30 平米"）
- 标"营业时段以官网为准"
- 字段留空或 null

**禁止行为**：
- 全部停留点写"通常 11:00-21:00"凑营业 ❌
- 步行分钟全标 estimated ❌
- 跨店比较句"全京都最好的咖啡" ❌

### 3. area 必须从白名单选

`area` 字段是全局事实（跨餐厅/停留点/酒店/模板/装配），**禁止自由命名**。

写 area 前必 grep `{圈}/area_registry.json`：
- 在白名单里 → 用 registry 标准名
- 不在 → **停下报告**，由用户决定加 registry 还是改用现有 area

校验脚本对 area 做严格白名单，不在 registry = FAIL。

### 4. entity 不为挂店服务

entity 必须**自己有意义**才加：
- 用户必去 / 模板动线锚点 / 文化地标
- 不是为了"店挂不上"而凑

**店挂不上就挂最近合理 entity，walk_min 大一点没关系**。挂不上任何合理 entity 的店 → 降 skeleton 或不收，**不为它加新 entity**。

### 5. depth 必须真实

- 地址查不到 / 营业全靠类目均值 = 自动降 skeleton
- full 必须三段式完整（系统字段 + note 全填 + 准 entity 挂载）
- 不强凑 full 撑数量

### 6. 主次分明（避免反复纠结）

- **A 类**（装配跑不动 / 字段缺失） → 停下报告
- **B 类**（用户体验硬伤：地址错 / 类型错 / 与餐厅混淆） → 停下报告
- **小事**（营业不全 / 文笔粗糙 / 招牌品类细节） → 标 verified 或留空，**继续做不停**

---

## 二、字段定稿

```json
{
  "id": "kyo_arashiyama_arabica",
  "area": "岚山",
  "near_attractions": [{"entity_id": "togetsukyo_bridge", "walk_min": 2}],
  "type": "咖啡",
  "depth": "full",
  "note": {
    "店名": "% Arabica 京都 嵐山",
    "简介": "渡月桥北詰的爆款拍照咖啡店，世界各地分店里中国游客密度最高的一家。京都拿铁是招牌——浓缩奶泡上点抹茶粉，杯子上是樱花季限定花纹。20 平米小店，外带为主，店外渡月桥背景天然出片。",
    "亮点": ["京都拿铁", "渡月桥拍照机位"],
    "地址": "京都市右京区嵯峨天龙寺芒之马场町 3-47（渡月桥北詰即到）",
    "营业": "9:00-18:00；无定休；周末高峰排队 30-40 分钟"
  }
}
```

### 系统字段（5 个）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | ✅ | `{城市拼音简写}_{区域简写}_{店名拼音}` |
| `area` | string | ✅ | 动线级粒度，跟 area_registry.json 对齐（禁城市级粗粒度） |
| `near_attractions` | array | ✅（≥1） | `[{entity_id, walk_min}]`。entity 必须真实存在 |
| `type` | string | ✅ | 开放枚举（见 §三） |
| `depth` | string | 选填，缺省 `skeleton` | `skeleton` / `verified` / `full` |

### note 字段（5 个）

| key | 必填 | 说明 |
|---|---|---|
| `店名` | ✅ | 中文（日文/英文）。如 `% Arabica 京都 嵐山`、`鍵善良房（かぎぜん）` |
| `简介` | full 必填 | 60-120 字，"懂当地的朋友讲口吻"。讲招牌+氛围+独特点 |
| `亮点` | full 必填 | 2-4 个短词标签 |
| `地址` | full 必填 | 含最近交通+步行分钟 |
| `营业` | full 必填 | 一句话含开门+定休+排队/季节/特殊提醒。所有时间敏感信息都在这一句 |

---

## 三、分类标准

### 3.1 跟餐厅的边界

判断进 stops 还是 restaurants：
- **能解决一顿正餐** → restaurants（即使便宜也算）
- **纯咖啡甜品/购物/手作** → stops

边界 case：
- 伏見夢百衆（咖啡+品酒+酒馒头·无正餐）→ stops
- 鳥せい本店（酒藏居酒屋·能正餐）→ restaurants
- STANDARD BOOKSTORE（书+咖啡+杂货复合）→ stops（type=书店咖啡）
- Smart Coffee 2F 洋食午市（能正餐）→ restaurants

### 3.2 type 开放枚举

**吃喝类**：咖啡 / 甜品 / 抹茶 / 和菓子 / 茶寮 / 喫茶店 / 刨冰 / 日本酒
**购物类**：古着 / 古书 / 书店 / 书店咖啡 / 杂货 / 设计杂货 / 文具 / 当地土特产
**体验类**：古道具 / 工艺品 / 手工艺 / 唱片 / 御宅店 / 道具屋

**不强求枚举**——sonnet 写到合适词就行（如新品类"文房具"/"陶器")，但同一品类必须用同一词避免漂移。

---

## 四、数据准入

> **总原则**：准入靠**三轴模型 + 三层池**。详见 [docs/04_操作SOP/数据采集.md §三 §五](../../docs/04_操作SOP/数据采集.md)。

### 4.1 三轴模型

每家 Full 必须**三轴中至少两轴有真实证据**：

| 轴 | 信号源 | 通过标准 |
|---|---|---|
| **quality** | 媒体推荐 / 行业奖 / 老铺背书 | "懂当地的朋友会专门带去"的店 |
| **traveler_fit** | 携程评分+评论 / 小红书 collects > likes | 中国游客实际去了不会后悔 |
| **execution** | 营业稳定 / 排队 ≤90 分钟 / 不需预约 | 用户照行程能去到 |

**三轴规则**：
- 三轴全过 → `verified` 入 full
- 两轴过 → `cross_checked` 入 full
- 一轴过 → `single_source`，标注后入 full
- 无任何真实证据 → `ai_generated`，禁止上生产

### 4.2 数据源

完整数据源清单见 [独立站清单.md](独立站清单.md)。停留点重点用：

- **P0**：Google Maps 4.3+ + 官网（execution）
- **P1**：小红书 collects > likes（traveler_fit 主信号）/ 携程 / 大众点评
- **P2**：thisismedia（古着）/ icotto / Hanako / cottrip / Recoya（唱片）/ JAM TRADING（古着）/ ELLE HK（中古店）等品类专题站

### 4.3 负向信号（任一触发即降 skeleton 或不收）

| 信号 | 处理 |
|---|---|
| 公认游客陷阱（本地人避开） | 不收 |
| 连锁化无特色（如全国连锁咖啡店） | 不收 |
| 排队 >90 分钟且同区有替代 | 降 skeleton |
| 小红书爆火但 Google <3.8 / 评价两极 | 降 skeleton |
| 价格与体验不匹配 | 降 skeleton |
| 关店/搬迁/装修中 | 立即降 skeleton 标注 |

---

## 五、校验

校验脚本：`scripts/validate_restaurants.py`（同时校验 restaurants + stops）

校验规则：
- 系统字段白名单（5 个）+ note 字段白名单（5 个）→ 未知字段 FAIL
- area 字段必须在 `{圈}/area_registry.json` → 不在 FAIL
- near_attractions.entity_id 必须在 `{圈}/entities/*.json` → 不在 FAIL
- 必填字段缺 → FAIL
- depth=full 但 note 字段缺 → FAIL（自动建议降 skeleton）

跑法：`python scripts/validate_restaurants.py`，粘**完整输出**到交付消息。

---

## 六、历史教训

### 6.1 area 命名漂移（已解决）

D43 前 area 自由字符串，导致同一动线区有"三宮"/"旧居留地"/"神户三宮-旧居留地"三个桶。
**对策**：area_registry.json 白名单 + validator 强制校验。

### 6.2 walk_min_estimated 字段膨胀（已禁用）

之前为标"步行分钟估算"加了 `walk_min_estimated: bool`，结果 sonnet 全部标 true 等于没标。
**对策**：字段删除，停留点 walk_min 一律按真实查得填，查不到 → 写真实估算值（不强求精度）。

### 6.3 营业类目均值漂移（已解决）

之前 sonnet 把不同店都写"通常 11:00-21:00"凑营业。
**对策**：营业查不到必须写"营业时段以官网为准"或具体真实时段，禁用类目均值。

### 6.4 跟餐厅混淆（注意点）

边界 case 如"咖啡+正餐"复合店容易塞错池。
**对策**：判断按"能否解决一顿正餐"，能 → restaurants，不能 → stops。
