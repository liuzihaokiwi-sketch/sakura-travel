# 实施任务分配表 V2

> 基于 SYSTEM_DESIGN_V2 第八章设计取舍决策，精简后的任务。
> 三个检查点，每个做完审视再继续。

---

## 检查点 1 完成情况审视

### 已完成
- A1 数据源注册中心 ✅ — 10 个源注册
- A2 清除 AI 数据 ✅ — 678 条活跃实体
- A3 气候+假日数据 ✅ — 120 条气候 + 35 条假日
- B1 Tabelog 札幌全量 ✅ — 240 家餐厅
- B2 Google Places 札幌 ✅ — 356 POI + 82 酒店
- B3 Japan Guide ✅ — 16 个景点评级
- B4 攻略扫描 ✅
- B5 城市特色菜系 ✅ — 札幌 8 个

### 需要修复的问题
1. city_data_coverage.current_count 未更新（全是 0）
2. 214 条 suspicious 需要检查原因
3. entity_source_scores 只有 Japan Guide 的 16 条，Tabelog/Google 评分没存
4. 其他北海道城市数据量太少（14-31 个 vs 札幌 449）

---

## 检查点 2：内容加工 + 片段编排

> 目标：札幌有饱满的 day_fragments，核心实体有评价维度和摘要。
> 验证：能手动组出一个内容充实的札幌 3 天行程。

### 修复任务（先做）

#### FIX-1. 更新 city_data_coverage 计数 [Sonnet · 普通]
```
写脚本从 entity_base 统计各 city_code × entity_type 的实际数量
更新 city_data_coverage.current_count
验证：SELECT city_code, entity_type, target_count, current_count FROM city_data_coverage WHERE city_code='sapporo'
      → current_count 不再全是 0
```

#### FIX-2. 检查 214 条 suspicious 原因 [Sonnet · 普通]
```
查 suspicious 实体的共同特征：是坐标问题还是名称去重问题？
合理的 → 改为 unverified
确实有问题的 → 保持 suspicious 或改为 rejected
验证：suspicious 数量降到合理范围（< 50）
```

#### FIX-3. Tabelog/Google 评分存入 entity_source_scores [Sonnet · 普通]
```
从 restaurants.tabelog_score 和 pois.google_rating 回填到 entity_source_scores
这样每个实体有独立的各源评分，手账本可以展示 "Tabelog 3.65 ★"
验证：SELECT source_name, COUNT(*) FROM entity_source_scores GROUP BY source_name
      → tabelog 200+, google 300+, japan_guide 16
```

#### FIX-4. 扩展到北海道其他城市 [Sonnet · 普通]
```
B1/B2 只跑了札幌。用同样的脚本跑其他 9 个城市：
  otaru/hakodate/asahikawa/furano/biei/noboribetsu/niseko/abashiri/kushiro/toya
每个城市按规模调整数量（大城市 100+，小城市 30-50）
验证：SELECT city_code, COUNT(*) FROM entity_base WHERE is_active=true GROUP BY city_code
      → 每个城市至少 30+
      → 北海道总计 1000+
```

### 新任务

#### C1. 评论采集 — 札幌 top 100 [Opus · 深度思考]
```
目标：为评分最高的 100 个实体采集评论原文
来源（按可行性排序）：
  1. Google Places Reviews（Place Details API，每实体 5 条）
  2. TripAdvisor 评论页（HTML 爬取）
  3. 攻略网站中提到该实体的段落（B4 已爬的文本二次利用）
存入 source_snapshots（type='review_batch'）
验证：SELECT COUNT(DISTINCT object_id) FROM source_snapshots WHERE object_type='review_batch' → 80+
```

#### C2. 维度提取 + 摘要生成 [Sonnet · 普通]
```
读取 C1 的评论原文
AI（Sonnet）按维度提取：
  餐厅：signature_dish_clarity/queue_risk/reservation_difficulty/language_friendliness/payment_method/value_perception
  景点：best_timing/weather_sensitivity/physical_demand/photo_value/crowd_pattern/duration_flexibility/child_friendly/season_dependency
  酒店：location_convenience/room_condition/bath_quality/breakfast_quality/soundproofing/value_perception/best_for
AI（Sonnet）生成一句话摘要：why_go/practical_tip/skip_if
过滤：跳过 <5 字评论、纯情绪评价、负面需 3+ 人提到才采信
存入 entity_review_signals.dimension_scores + entity_descriptions
验证：抽样 10 个实体人工看维度和摘要质量
```

#### C3. 标签生成 [Haiku/DeepSeek · 普通]
```
从维度自动推断标签：
  queue_risk=high → long_queue
  payment_method=cash_only → cash_only
  child_friendly=great → family_friendly
存入 entity_tags
验证：SELECT tag_value, COUNT(*) FROM entity_tags GROUP BY tag_value ORDER BY count DESC LIMIT 20
```

#### D1. day_fragments 表 + 札幌片段 [Opus · 深度思考]
```
新建 day_fragments 表（schema 见 SYSTEM_DESIGN_V2 附录 C）
为札幌编排 8-10 个片段，每个片段：
  - 从 entity_base 中选真实实体（trust_status != rejected）
  - 排时间顺序
  - 填 closed_days + alternatives + rain_alternative（方案 A 条件替代）
  - 配 title_zh + summary_zh

示例片段：
  "札幌市区经典半日" — 大通公园→时计台→电视塔→狸小路
  "札幌美食巡游" — 二条市场朝食→拉面横丁→汤咖喱
  "白色恋人+圆山动物园" — 亲子半日
  "藻岩山夜景" — 晚间半日
  "定山溪温泉日归" — 全日

验证：
  SELECT fragment_id, theme, city_code, total_duration FROM day_fragments WHERE city_code='sapporo'
  → 8-10 个片段
  每个片段 items 中的 entity_id 在 entity_base 中存在且 is_active=true
  至少 3 个片段有 alternatives 数据
```

#### D2. 其他城市片段 [Sonnet · 普通]
```
小樽：港町漫步半日、寿司美食
函馆：夜景全日、五棱郭+朝市
富良野/美瑛：花田自驾（夏）
旭川：旭山动物园+拉面村
登别：温泉一日
洞爷湖：火山温泉
总共 15-20 个片段
验证：SELECT city_code, COUNT(*) FROM day_fragments GROUP BY city_code → 每城市 2-3 个
```

### 检查点 2 验证

```
做完后人工验证：
1. 打开管理后台，看札幌的实体是否有维度评分和一句话摘要
2. 查看 day_fragments，每个片段时间是否连贯、实体是否真实
3. 手动把 3-4 个札幌片段拼成一个 3 天行程，看内容是否饱满
4. 如果饱满 → 进检查点 3
5. 如果不饱满 → 哪里不够就补哪里
```

---

## 检查点 3：模板 + PDF + 端到端验证

> 目标：一本可以卖的北海道 5 天手账本 PDF。
> 验证：你拿着 PDF 模拟一天行程，信息全部准确。

#### D3. 片段文案生成 [GPT Creative · 普通]
```
每个片段生成：
  title_zh（"小樽 · 港町漫步半日"）
  summary_zh（一段话描述这半天的体验）
  每个活动项的过渡文案（"从运河步行 5 分钟到音乐盒堂"）
GPT 生成后人工审核修改
验证：每个片段有 title_zh 和 summary_zh
```

#### D4. 行程模板组装 [Opus · 深度思考]
```
组装 3-5 个北海道完整模板：
  北海道经典5天（couple/moderate/summer）
  北海道经典5天（family/moderate/summer）
  北海道经典5天（couple/moderate/winter）
  北海道深度7天（couple/relaxed/summer）
  北海道紧凑4天（couple/packed/any）

每个模板引用 day_fragments + 指定酒店 + 城市间交通
新建 itinerary_templates 表
Opus 审核每个模板：路线连贯性、节奏感、值不值 298 元
验证：Opus 审核打分 > 80/100
```

#### D5. 定休日约束检查 [Sonnet · 普通]
```
用户下单指定日期后，自动检查模板中的 closed_days
触发 alternatives 替换
验证：构造一个周一出发的行程 → 周一定休的店被自动换掉
```

#### E1. 图片关联 [Sonnet · 普通]
```
assets/hokkaido/ 有 195 张图片
按文件名匹配到 entity_base
Google Places Photo API 补充缺失的
存入 entity_media
验证：核心实体（片段中用到的）80% 有图
```

#### E2. PDF 渲染完善 [Sonnet · 普通]
```
改进 export_plan_pdf.py：
  每天 5-6 个活动 + 餐厅 + 交通
  实体图片
  实用提醒（practical_tip）
  每日预算
  Tabelog/Google 评分展示
验证：5 天 PDF，人工检查每页内容是否饱满
```

#### E3. 预制页面 [Sonnet · 普通]
```
北海道美食图鉴（特色菜系介绍）
行前准备 checklist
交通指南（JR Pass）
实用信息（紧急电话/退税）
天气穿衣建议
验证：PDF 含这些页面
```

#### F1. 端到端验证 [人工 + Opus]
```
用模板生成一个 5 天北海道行程 PDF
人工逐项验证：
  每个地名 Google Maps 能找到 ✓
  营业时间和定休日正确 ✓
  价格大致准确 ✓
  交通时间合理 ✓
  评分来自权威源 ✓
  无 AI 编造内容 ✓
  图片真实 ✓
  拿着 PDF 感觉值 298 元 ✓
```

---

## 任务分配汇总

### 检查点 2

**Opus（设计+质量）：**
| ID | 任务 | Thinking |
|----|------|----------|
| C1 | 评论采集系统 | 开 |
| D1 | day_fragments + 札幌片段 | 开 |

**Sonnet（实现）：**
| ID | 任务 | Thinking |
|----|------|----------|
| FIX-1 | 更新覆盖计数 | 否 |
| FIX-2 | 检查 suspicious | 否 |
| FIX-3 | 评分存入 source_scores | 否 |
| FIX-4 | 扩展其他城市 | 否 |
| C2 | 维度提取+摘要 | 否 |
| C3 | 标签生成 | 否 |
| D2 | 其他城市片段 | 否 |

### 检查点 3

**Opus：** D4（模板组装+审核）+ F1（最终验证）
**Sonnet：** D3 + D5 + E1 + E2 + E3

### 并行策略

```
检查点 2：
  Opus: C1（评论采集）→ D1（片段编排，依赖 C2 的维度数据）
  Sonnet: FIX-1~4（先修复）→ C2+C3（依赖 C1）→ D2

  注意：D1 依赖 C2 的维度数据来选更好的替代方案
  但 D1 也可以先编排主活动，替代方案后补
  → Opus 和 Sonnet 可以大部分并行

检查点 3：
  Opus: D4（等 D1+D2+D3 都完成）→ F1
  Sonnet: D3+D5+E1+E2+E3（大部分可并行）
```
