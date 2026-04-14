# 待解决问题与执行方案

> 2026-04-01。最终目的：付费用户拿到值298元的手账本。
> 阻塞质量的两条线：数据不完整 + 管线缺体验结构。两线并行，人工不参与常规流程。

---

## 产品决策（已定，所有执行必须遵守）

| # | 决策 | 定义 |
|---|------|------|
| P1 | 偏好约束 | must_have_tags = 全程强覆盖 + 每日软倾斜，不是"每天至少一个" |
| P2 | 无偏好默认 | 各体验桶 top N 组合，不是全局 top N |
| P3 | 体验桶 | 7 桶：heritage_spiritual / nature_outdoor / market_citylife / art_culture_experience / entertainment_night / onsen_relax / urban_landmark_family。sub_type 保留做桶内排序 |
| P4 | 惊喜点 | local_benchmark + 质量达标 + 可执行 + 不与 canonical 重叠。池层 2-4 个，行程 6-8天1个、9-13天1+1 |
| P5 | 候选点状态 | core / niche / backup / dominated_candidate |
| P6 | 死库存 | 先标不删，等 12 case 跑完再处理 |
| P7 | 选品清单 | needs_editorial → selected_small_group + 两层自动 fallback，不依赖人工 |
| P8 | 景点评级 | top→S/A, recommended→A/B, featured→B/C，区间映射非硬绑 |
| P9 | 父子实体 | 数据层共存，候选池可共存，主选层互斥，父实体做 container |
| P10 | 标签三层 | 第一层：体验分类（sub_type 自动继承 shrine/temple/garden 等，Step 4/5 消费）；第二层：实用属性（reservation_required/cash_only 等，Step 4 过滤 + 手账本展示）；第三层：采集描述（仅数据侧内部用，不进 DB） |
| P11 | 不依赖人工 | 人工只做最终抽查，不参与生产链路常规流程。详见下方 |

### P11 详细规则

| 环节 | 原来依赖人工 | 改为 |
|------|-------------|------|
| trust_status 升级 | 人工确认才能 verified | 双源交叉自动升 cross_checked，单源保持 single_source，两者都可上生产 |
| 评价维度提取 | 抽样10个人工看 | AI 提取后自动进 DB，质量靠规则校验（非空、格式对、枚举内） |
| 模板质量审核 | Opus审核+人工看 | Opus 过就算过 |
| 最终验证 | 人工模拟走一遍 | 管线输出 Markdown 可读版，偶尔翻翻，不阻塞生产 |
| Opus 降级复核 | 标记需人工复核 | 自动标 review_confidence=degraded，不阻塞 |
| 质量门不过 | 人工介入 | 自动重写最多2轮，还不过显式失败，不进人工队列 |
| 选品小样本组 | needs_editorial 等人工判断 | 自动 fallback 到粗分组（P7） |
| 数据源调度 | 手动触发 | cron 自动按频率跑 |

### 架构决策

| 决策 | 定义 |
|------|------|
| 数据权威源 | DB 是唯一权威源，管线只读 DB |
| JSON 定位 | 导入中间产物，不被管线直接消费 |
| ledger 定位 | 选品决策记录，不是生产实体画像 |
| 测试路径 | JSON → importer → 测试 DB → pipeline |

---

## 数据侧任务

> 目标：让 DB 里有完整的、可被管线消费的关西实体数据。
> 负责方：数据工程师。管线程序员不碰数据内容。

### 阻断生产（DB 里没有可用数据）

| # | 问题 | 说明 |
|---|------|------|
| D1 | 景点缺 6 个核心字段 | 坐标/entity_id/name_zh/visit_minutes/cost/best_season 全缺，ledger 只是选品记录 |
| D2 | 酒店 88/89 是 AI 生成 | 无坐标/价格/含餐信息，整个池不可信 |
| D3 | 餐厅无坐标、无具体价格 | 35/152 是 AI 生成（8家标了A级） |
| D17 | 酒店 JSON 无法匹配进池 | city_code 和 circle.cities 不匹配或结构不对 |
| D25 | 景点缺 physical_demand | 设计文档定了 easy/moderate/demanding 三档，数据未填 |

### 数据质量（能跑但出错）

| # | 问题 | 说明 |
|---|------|------|
| D4 | S级酒店 price_level 全标 moderate | 丽思卡尔顿推给 budget 用户 |
| D5 | 西村屋本館 hotel_type=city_hotel | 实际是 ryokan |
| D6 | 天桥立/伊根 city_code=kyoto | 距京都 2.5 小时 |
| D7 | 高野山宿坊混入景点池 | 住宿体验产品 |
| D8 | 打分系统字段全 null/0 | fine-grain scoring 未执行 |
| D9 | 38/121 景点无 selection_tags | 画像匹配缺依据 |
| D10 | 景点全部 single_source | 仅 japan-guide |
| D11 | 餐厅 cuisine_type 日英混用 | cuisine_normalized 正常 |
| D12 | 6条B级景点 score=4.0+top 疑似应升A | 打分逻辑没跑 |
| D13 | Nintendo Museum/Ine 标A但 score=3.0 | 依据不足 |
| D15 | 酒店无奈良覆盖 | 0 家奈良酒店 |

### 标签与配置

| # | 问题 | 说明 |
|---|------|------|
| D14 | Selection Ledger needs_editorial 吞候选 | GPT 新窗口修，改 selected_small_group + 自动 fallback |
| D16 | 嵯峨野小火车缺季节标签 | 缺 cherry_blossom/autumn_leaves |
| D18 | tags 中英文不统一 | 表单传 shrine（英文），tags 是"拍照强"（中文），→ P10 三层分离 |
| D19 | 伏见稻荷缺 shrine 标签 | 日本最著名神社 |
| D20 | 春日大社缺 shrine 标签 | 同上 |
| D21 | 顶级庭园缺 garden 标签 | 桂离宫/修学院离宫 |
| D22 | 岚山地区与竹林重叠 | → P9 父子互斥 |
| D23 | 东山散步道与清水寺/祇园重叠 | → P9 父子互斥 |
| D24 | 有马温泉 city_code 待确认 | JSON 和 DB 是否一致 |

---

## 管线侧任务

> 目标：管线逻辑能保证"好数据进来 → 好攻略出去"。
> 负责方：程序员。不等数据就绪即可开始。

### 第一优先级：决定攻略质量上限

| # | 问题 | 改法 | 位置 |
|---|------|------|------|
| L1 | Step 3 不能降级 | API 不可用直接失败，不用 qwen-max 凑合 | step03_city_planner.py |
| L2 | Step 3 偏好只是背景不是约束 | prompt 里 must_have_tags 从信息列举改为显式约束：全程必须覆盖（P1） | step03 prompt |
| L15 | Step 3 偏好权重传递不够 | 偏好拆三层传：必须覆盖 / 强偏好 / 体验约束（避免单类堆叠） | step03 prompt |
| L13 | RegionSummary 缺季节信息 | Step 2 输出加当前季节和季节性事件 | step02_region_summary.py |

### 第二优先级：保证菜单质量（Step 4 改造）

| # | 问题 | 改法 | 位置 |
|---|------|------|------|
| L3 | 无 max_pool_size | 分桶配额后合并截断到 30-45 | step04 + PoolConfig |
| L4 | 无品类分桶 | 按 P3 的 7 个 experience_bucket 分桶取额 | step04 + taxonomy.json |
| L5 | 无偏好加权 | must_have_tags 命中的桶配额上调，must_visit 直接保入池（P1/P2） | step04 |
| L6 | 无惊喜点保留 | local_benchmark 过 4 条 gate 后保留 2-4 个（P4） | step04 |
| L14 | USJ 突破 admission_cap | 确认 must_visit 豁免逻辑是否正确，非 must_visit 的高价 POI 应被 cap 拦住 | step04 |
| P9落地 | 父子实体互斥 | 同一天主活动中父子实体不能同时出现 | step04/step05 |
| P10落地 | 标签映射 | taxonomy.json 加 sub_type → 体验分类标签的映射表 | taxonomy.json |

### 第三优先级：保证最终体验（Step 5 + Step 10）

| # | 问题 | 改法 | 位置 |
|---|------|------|------|
| L7 | Step 5 无品类覆盖约束 | prompt 加：全程必须覆盖足够数量的 distinct bucket（P2） | step05 prompt |
| L8 | Step 5 无连续品类惩罚 | prompt 加软引导：尽量避免连续2天同主桶 | step05 prompt |
| L9 | Step 5 无体验结构概念 | prompt 从"每天选1-2个"改为"先分体验槽再填实体" | step05 prompt |
| L8b | Step 10 缺连续同类硬检测 | 连续3天同 bucket 标 violation，Step 11 去修 | step10_feasibility.py |

### 后续（不阻塞当前）

| # | 问题 | 说明 | 触发条件 |
|---|------|------|---------|
| L10 | 死库存分析 | 用 12 case 跑完的使用率统计做判定（P5/P6） | 12 case 跑完后 |
| L11 | Step 9 commute_matrix 契约不匹配 | 期望 entity→entity，实际酒店级聚合 | 接入 Google Routes API 时 |
| L12 | Step 14 读 items 但 key 是 activities | **已修** | - |

---

## 执行顺序

```
并行线 A（管线侧，程序员，不等数据）：
  1. taxonomy.json 加 experience_buckets + 标签映射 + 父子互斥规则
  2. Step 3 不降级 + prompt 改约束式
  3. Step 4 分桶配额 + 偏好加权 + 惊喜保留
  4. Step 5 prompt 加体验结构约束
  5. Step 10 加连续同类检测

并行线 B（数据侧，数据工程师/GPT）：
  1. Selection Ledger 修 needs_editorial（GPT 新窗口）
  2. 关西实体数据补全（坐标/name_zh/价格/visit_minutes/best_season/physical_demand）
  3. 标签统一（P10 三层分离）
  4. 数据导入 DB（importer）

汇合：
  两线完成后跑 12 个关西真实表单 CP1-CP4
  → 产出候选点使用率统计
  → 死库存分析（P5/P6）
  → 质量评审
```
