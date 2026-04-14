# 数据工程师任务：关西圈数据补全与质量修复

> 管线程序员已完成 16 步管线代码。管线只读 DB，不读 JSON。
> 你的任务：让 DB 里有完整的、可被管线消费的关西实体数据。

## 你必须先读的文件

- `CLAUDE.md` — 工程规范（不许用 AI 知识代替真实数据、数据可信度分级）
- `docs/PENDING_ISSUES.md` — 完整问题清单和产品决策
- `data/kansai_spots/config/taxonomy.json` — 分类体系（experience_buckets、tag_inheritance_rules、parent_child_entities 已定义）
- `data/circle_registry.json` — 圈配置（kansai 的 cities、budget_config）

## 管线期望的数据 Schema

管线从 DB 的 `entity_base` + `poi`/`restaurant`/`hotel` 表查询。每个实体必须有以下字段：

### 景点（entity_type=poi）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| entity_id | UUID | 是 | 稳定唯一标识 |
| name_zh | str | 是 | 中文名（手账本用） |
| name_en | str | 是 | 英文名 |
| name_ja | str | 否 | 日文名 |
| entity_type | str | 是 | 固定 "poi" |
| city_code | str | 是 | 必须在 circle_registry.json 的 kansai.cities 中，或在 taxonomy.json 的 sub_region_codes 中 |
| sub_type | str | 是 | 必须是 taxonomy.json main_types 下的合法 sub_type（如 history_religion、nature_scenery 等） |
| data_tier | str | 是 | S/A/B/C |
| lat | float | 是 | 纬度（关西范围：33.5-36.0） |
| lng | float | 是 | 经度（关西范围：134.0-137.0） |
| is_active | bool | 是 | true |
| typical_duration_min | int | 是 | 建议游览时长（分钟） |
| admission_fee_jpy | int | 否 | 门票价格（日元），免费填 0 |
| best_season | str | 否 | "all"/"spring"/"spring,autumn" 等 |
| physical_demand | str | 否 | "easy"/"moderate"/"demanding" |
| risk_flags | list | 否 | 施工/不稳定等风险标签 |

### 景点标签（entity_tags 表）

每个景点必须有英文结构化标签。标签来源规则见 taxonomy.json 的 `tag_inheritance_rules`：

**第一层（自动继承，必须有）：**
- 根据 sub_type 自动继承。如 `history_religion` → 自动加 `cultural`、`historical`
- 根据名称关键词自动继承。如名称含"神社" → 加 `shrine`；含"寺" → 加 `temple`；含"庭園" → 加 `garden`

**第二层（实用属性，有则加）：**
- `reservation_required` — 需预约
- `cash_only` — 只收现金
- `free_admission` — 免费
- `family_friendly` — 亲子友好
- `photo_spot` — 拍照点
- `rainy_day_ok` — 雨天可去

**第三层（采集描述，不进 DB）：**
- 中文描述标签（"拍照强"、"网红店"等）只留在 ledger/JSON 原始数据中
- `local_benchmark` — 本地人常去（这个标签进 DB，用于惊喜点机制）

### 餐厅（entity_type=restaurant）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| entity_id | UUID | 是 | |
| name_zh | str | 是 | |
| name_ja | str | 是 | |
| entity_type | str | 是 | 固定 "restaurant" |
| city_code | str | 是 | 同上 |
| data_tier | str | 是 | S/A/B/C |
| lat | float | 是 | |
| lng | float | 是 | |
| is_active | bool | 是 | |
| cuisine_normalized | str | 是 | 英文标准菜系（ramen/soba/kushiage/udon 等） |
| budget_tier | str | 是 | budget/mid/premium/luxury |
| budget_lunch_jpy | int | 否 | 午餐人均（日元） |
| budget_dinner_jpy | int | 否 | 晚餐人均（日元） |
| tabelog_score | float | 否 | Tabelog 评分 |
| opening_hours_json | dict | 否 | 营业时间 |

### 酒店（entity_type=hotel）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| entity_id | UUID | 是 | |
| name_zh | str | 是 | |
| name_ja | str | 是 | |
| entity_type | str | 是 | 固定 "hotel" |
| city_code | str | 是 | 同上 |
| data_tier | str | 是 | S/A/B/C |
| lat | float | 是 | |
| lng | float | 是 | |
| is_active | bool | 是 | |
| hotel_type | str | 是 | city_hotel/business_hotel/ryokan/minshuku/shukubo |
| price_level | str | 是 | budget/moderate/expensive/luxury |
| nightly_jpy_min | int | 是 | 每晚最低价（日元） |
| star_rating | int | 否 | 星级 |
| check_in_time | str | 否 | "HH:MM" |
| check_out_time | str | 否 | "HH:MM" |
| meals_included | str | 否 | "none"/"breakfast"/"dinner"/"breakfast_dinner" |

---

## 具体修复任务

### P0：阻断生产（不修管线跑不通）

**D1：景点补全 6 个核心字段**

当前 `spots_selection_ledger.json` 有 121 个选品记录，但缺坐标、entity_id、name_zh、visit_minutes、cost、best_season。

做法：
1. 用 ledger 中的 `name_en`/`name_ja` 去 Google Places API 查坐标和中文名
2. entity_id 生成 UUID
3. visit_minutes 从攻略/评论提取，搜不到用 sub_type 默认值（temple 60、museum 90、theme_park 240、district 120、park 60）
4. admission_fee_jpy 从 Google/官网查，免费填 0，搜不到填 null
5. best_season 从 japan-guide 页面提取，全年可去填 "all"
6. physical_demand 根据 sub_type + visit_minutes 推断（outdoor_sport+120min → demanding，shrine+60min → easy），有登山/长距离步行的标 "demanding"

**D2：酒店重建**

当前 88/89 是 AI 生成，不可信。

做法：
1. 用 ledger 中的酒店名去一休/楽天/Booking 查真实数据
2. 补全坐标、price_level、nightly_jpy_min、hotel_type、meals_included
3. 丽思卡尔顿/Capella/西村屋本館 等 S 级酒店的 price_level 必须标 expensive 或 luxury，不是 moderate
4. 西村屋本館 hotel_type 改 ryokan
5. 高野山宿坊 hotel_type 用 shukubo
6. ai_generated 的数据全部用真实数据源替换，无法验证的降级或删除

**D3：餐厅补坐标和价格**

做法：
1. 用 name_ja 去 Tabelog/Google Places 查坐标
2. budget_lunch_jpy/budget_dinner_jpy 从 Tabelog 价格区间推算
3. 35 家 ai_generated 中 8 家标了 A 级 — 必须用真实数据源验证，验不了就降到 C 或删除
4. cuisine_type 字段统一用 cuisine_normalized 的值，不保留日文原始值

**D17：酒店 city_code 对齐**

确保所有酒店的 city_code 在 `circle_registry.json` 的 kansai.cities 或 taxonomy.json 的 sub_region_codes 中。

**D25：景点 physical_demand**

每个景点填 easy/moderate/demanding：
- easy：平地步行，无楼梯，轮椅可达（大部分寺社、博物馆、购物区）
- moderate：有坡道/楼梯但不长，正常体力可完成（伏见稻荷全程、岚山散步）
- demanding：登山/长距离步行/大量楼梯（吉野山奥千本、熊野古道、比叡山）

### P1：数据质量修复

| # | 任务 | 做法 |
|---|------|------|
| D4 | S级酒店 price_level 修正 | 丽思卡尔顿→luxury，Capella→luxury，西村屋→expensive，本覚院→moderate |
| D5 | 西村屋 hotel_type | city_hotel → ryokan |
| D6 | 天桥立/伊根 city_code | kyoto → amanohashidate/ine（已在 sub_region_codes 中） |
| D7 | 高野山宿坊归池 | 从景点池移到酒店池，entity_type=hotel，hotel_type=shukubo |
| D8 | 打分系统字段 | 至少跑一遍 house_score 计算逻辑，填入真实的 base_quality_score |
| D9 | 补 selection_tags | 38 个无标签的景点至少标一个（traveler_hot/city_icon/local_benchmark） |
| D10 | 交叉验证 | 121 个景点目前只有 japan-guide 单源，至少用 Google Places 交叉验证坐标和评分 |
| D11 | cuisine_type 统一 | 全部用 cuisine_normalized 的英文值 |
| D12 | 6条B级疑似应升A | 重新评估 house_score=4.0+japan_guide=top 的景点 grade |
| D13 | Nintendo Museum/Ine grade | 重新评估 score=3.0 标 A 的依据 |
| D15 | 奈良酒店 | 确认是否需要（奈良通常日归），如需则补 2-3 家 |

### P2：标签标准化（P10 落地）

导入 DB 时必须执行 taxonomy.json 的 `tag_inheritance_rules`：

1. **by_sub_type 自动继承**：每个实体根据 sub_type 自动加对应英文标签
2. **by_name_keyword 自动继承**：扫描 name_zh/name_ja/name_en，匹配关键词加标签

示例：
- 伏见稻荷大社：sub_type=history_religion → 加 `cultural`、`historical`；名称含"神社" → 加 `shrine`
- 岚山竹林小径：sub_type=nature_scenery → 加 `nature`、`scenic`、`outdoor`
- 清水寺：sub_type=history_religion → 加 `cultural`、`historical`；名称含"寺" → 加 `temple`

现有中文标签（"拍照强"、"亲子"等）不进 entity_tags 表，留在原始 JSON 中。

### P3：父子实体标记（P9 落地）

taxonomy.json 已定义了两组父子关系。数据侧需要确保：
1. 父子实体都保留在 DB 中
2. 父实体的 entity_id 和子实体的 entity_id 都准确
3. 如果发现更多父子关系（如 "南禅寺区域" 包含 "南禅寺"+"哲学之道"），补进 taxonomy.json 的 parent_child_entities.groups

### P4：景点 grade 对齐（P8 落地）

japan-guide 的 top/recommended/featured 对应 grade 的默认区间：
- top → S 或 A（关西名片级默认 S，其他默认 A）
- recommended → A 或 B（目的地级默认 A）
- featured → B 或 C（行程增色默认 B）

不是硬绑定。可以根据以下因素微调：
- 圈内地位（姬路城虽然 top 但关西只去一天，可以 A 不一定 S）
- 体验稀缺性（城崎温泉是关西唯一温泉街目的地，虽然 recommended 可以给 A）
- 画像加成（USJ 对文化深度游用户降一级，对亲子用户升一级——这个在 taxonomy.json 的 profile_boost_rules 中配置）

---

## Selection Ledger 修复（D14/P7）

另开窗口用 GPT 修。核心改动：
- `needs_editorial` → `selected_small_group`
- 两层分组自动 fallback（fine_slot → coarse_slot）
- 不再依赖人工判断

详见 `docs/PENDING_ISSUES.md` 中 P7 的完整规则。

---

## 验收标准

完成后，以下条件必须满足：

1. **景点**：≥100 个实体有完整字段（坐标+name_zh+visit_minutes+sub_type+grade+tags），0 个 ai_generated
2. **餐厅**：≥120 个实体有完整字段（坐标+name_zh+cuisine_normalized+budget_tier），ai_generated ≤10 个且全部 grade=C
3. **酒店**：≥60 个实体有完整字段（坐标+name_zh+hotel_type+price_level+nightly_jpy_min），0 个 ai_generated
4. **标签**：每个实体至少有 2 个英文结构化标签（来自 tag_inheritance_rules）
5. **city_code**：所有实体的 city_code 在 circle_registry.json kansai.cities 或 taxonomy.json sub_region_codes 中
6. **grade**：无 ai_generated 实体标 A/S 级

---

## 不需要做的

- 不需要改管线代码（step04/step05 等）
- 不需要改 taxonomy.json（已经配好了 experience_buckets/tag_inheritance_rules/parent_child_entities）
- 不需要改 circle_registry.json
- 不需要写 importer（老板另外安排）
- 中文描述标签不需要翻译成英文，直接丢弃不进 DB
