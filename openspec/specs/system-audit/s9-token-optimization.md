# S9. 最省 Token 设计 — 固定方案 + 差异补丁 + 模板库

> 产品：日本旅行定制规划（30-40页杂志级攻略）
> 更新：2026-03-21
> 目标：通过"固定方案 + 差异补丁 + 内容模板库"最大化省 token，只在真正需要个性化的地方调用 AI

---

## 一、当前 AI 调用现状审计

### 现有 AI 调用点

| 调用点 | 文件 | 模型 | 触发频率 | 每次token(估) | 说明 |
|---|---|---|---|---|---|
| **文案生成** | `copywriter.py` | GPT-4o-mini | 每个实体×每个场景 | ~400 tok/次 | 生成 copy_zh + tips_zh |
| **方案润色** | `assembler.enrich_itinerary_with_copy()` | 同上(批量) | 每个方案所有实体 | ~6,000-10,000 tok/方案 | 一个7天方案约20-28个实体 |

### 当前缓存策略

```python
# copywriter.py 现有缓存
Redis key: "copywriter:{entity_id}:{scene}"
TTL: 7天
```

### 当前问题

| 问题 | 严重度 | 说明 |
|---|---|---|
| **相同实体重复生成** | 🔴 高 | 同一个浅草寺，couple场景和family场景分别生成。但"浅草寺的一句话描述"在多数场景下几乎一样 |
| **事实信息重复传入prompt** | 🔴 高 | 每次调用都传入 name_zh/entity_type/city/area/tags/rating/review_count，这些都是固定信息 |
| **通用内容用AI生成** | 🟡 中 | "建议提前查看官方开放时间"这类tips完全可以规则生成，不需要AI |
| **交通/时间/门票走AI** | 🟡 中 | "09:00出发，地铁银座线，15分钟，¥170"这类纯事实内容不应走AI |
| **每日概要用AI** | 🟡 中 | "浅草→晴空塔→秋叶原"这类概要可以规则拼接 |
| **缓存命中率不够** | 🟡 中 | 7天TTL太短，热门实体的文案应该持久化到DB |

---

## 二、内容分层：什么该静态 / 规则 / 模板 / AI

### 30-40页攻略的内容构成（按token消耗分类）

```
完整攻略 ≈ 15,000-20,000 中文字

  ┌─ 静态内容块 ────── ~40% ─── 0 token ──┐
  │  封面/目录/交通卡指南/行前准备/         │
  │  安全须知/紧急联系/封底                  │
  ├─ 规则生成 ────── ~30% ─── 0 token ──┤
  │  时间轴骨架/交通指引/门票价格/          │
  │  每日概要/路线逻辑/天气提示             │
  ├─ 模板+变量填充 ─── ~15% ─── 0 token ──┤
  │  酒店推荐卡片/餐厅推荐卡片/             │
  │  Plan B 备选/区域简介                   │
  ├─ AI润色 ───────── ~10% ─── 少量token ──┤
  │  推荐理由(朋友口吻)/每日小贴士/         │
  │  路线设计理由                           │
  └─ AI原创 ───────── ~5% ─── 核心token ──┘
     个性化开头语/特殊场景适配文案/
     用户特殊需求回应
```

### 逐块详细分析

---

### 🟢 Tier 0：纯静态内容块（0 token，预写入模板库）

**占比：~40%页面内容**

| 内容块 | 当前状态 | 改造方案 |
|---|---|---|
| **行前准备清单** | 未实现 | 按城市预写：签证/行李/APP/货币/保险。Jinja2模板 `pre_trip_{city}.html.j2` |
| **安全须知** | 未实现 | 全日本通用1份 + 城市补充。模板 `safety_guide.html.j2` |
| **交通卡购买指南** | 未实现 | 按城市组合预写：东京=Suica，关西=ICOCA，跨区=JR Pass。模板 `transport_pass_{region}.html.j2` |
| **紧急联系卡片** | 未实现 | 全日本通用：110/119/大使馆。模板 `emergency_card.html.j2` |
| **封面** | ✅ 已有模板 | 变量：城市名/天数/人数/日期。0 token |
| **目录页** | 未实现 | 从方案结构自动生成。0 token |
| **封底** | 未实现 | 固定文案 + 可选祝福语。0 token |

**实现方式**：建立 `content_blocks/` 目录，每个静态块一个 `.md` 或 `.html.j2` 文件

```
templates/content_blocks/
├── pre_trip/
│   ├── visa.html.j2           # 签证（按签证类型分支）
│   ├── packing.html.j2        # 行李清单（按季节分支）
│   ├── apps.html.j2           # 必装APP（固定）
│   ├── currency.html.j2       # 货币支付（固定）
│   └── insurance.html.j2      # 保险（固定）
├── safety/
│   ├── general.html.j2        # 通用安全
│   └── earthquake.html.j2     # 地震应对
├── transport/
│   ├── suica_guide.html.j2    # Suica购买使用
│   ├── icoca_guide.html.j2    # ICOCA购买使用
│   └── jr_pass_calc.html.j2   # JR Pass值不值（变量：行程城市列表）
└── common/
    ├── cover.html.j2          # 封面
    ├── toc.html.j2            # 目录
    ├── emergency.html.j2      # 紧急联系
    └── back_cover.html.j2     # 封底
```

**Token节省**：这40%内容从"可能走AI"变成"确定0 token"

---

### 🟡 Tier 1：规则生成（0 token，纯代码逻辑）

**占比：~30%页面内容**

| 内容块 | 当前状态 | 规则化方案 |
|---|---|---|
| **时间轴骨架** | ✅ 已有(assembler) | 从 route_template → itinerary_days/items 结构化数据直出。已是0 token |
| **交通指引** | ⚠️ 基础实现 | `route_matrix_cache`查时间+距离 → 模板填充："🚇 银座线 浅草→上野 3分钟 ¥170" |
| **门票/开放时间** | ✅ 数据已有 | `pois.admission_fee_jpy` + `opening_hours_json` 直接渲染 |
| **每日概要** | ⚠️ 可改进 | 规则拼接：`"{Day1景点1名}→{景点2名}→{景点3名}"` 不需AI |
| **路线逻辑说明** | 未实现 | 规则生成："浅草和晴空塔同一天，因为步行{distance}分钟" → 从route_matrix数据推导 |
| **天气提示** | ⚠️ 可改进 | `weather_snapshots`数据 → 规则："Day3可能有雨，建议带伞" |
| **预算估算** | 未实现 | 门票+交通+餐费(按budget_level预设)逐天累加 |
| **JR Pass计算** | 未实现 | 规则：新干线段数×单价 vs JR Pass价格 → 简单比较 |

**关键规则生成器设计**：

```python
# 新增文件: app/domains/planning/content_rules.py

def generate_daily_summary(day: ItineraryDay) -> str:
    """规则生成每日一句话概要"""
    poi_names = [item.entity_name for item in day.items if item.item_type == "poi"]
    return "→".join(poi_names[:4])  # 最多4个

def generate_transit_description(origin, dest, route_cache) -> str:
    """规则生成交通指引"""
    data = route_cache.get((origin.entity_id, dest.entity_id))
    if not data:
        return f"🚶 步行前往"
    mode_icon = {"transit": "🚇", "walking": "🚶", "driving": "🚗"}
    return f"{mode_icon.get(data['mode'], '🚇')} {data.get('line_name', '')} {data['duration_min']}分钟 ¥{data.get('fare', '—')}"

def generate_route_reason(day_items, route_cache) -> str:
    """规则生成路线编排理由"""
    reasons = []
    for i in range(len(day_items) - 1):
        a, b = day_items[i], day_items[i+1]
        dist = route_cache.get((a.entity_id, b.entity_id), {})
        if dist.get('duration_min', 999) <= 15:
            reasons.append(f"{a.name_zh}和{b.name_zh}放在一起，因为步行{dist['duration_min']}分钟就到")
    return "。".join(reasons) if reasons else ""

def generate_budget_estimate(day, budget_level) -> dict:
    """规则生成每日预算估算"""
    meal_cost = {"budget": 2000, "mid": 4000, "premium": 8000, "luxury": 15000}
    transport = sum(item.estimated_cost_jpy or 0 for item in day.items if item.item_type == "transit")
    admission = sum(item.estimated_cost_jpy or 0 for item in day.items if item.item_type == "poi")
    meals = meal_cost.get(budget_level, 4000)
    return {"transport": transport, "admission": admission, "meals": meals, "total": transport + admission + meals}
```

**Token节省**：这30%内容全部规则化，0 token

---

### 🔵 Tier 2：模板 + 变量填充（0 token，结构化数据直插）

**占比：~15%页面内容**

| 内容块 | 当前状态 | 模板化方案 |
|---|---|---|
| **酒店推荐卡片** | 未实现 | 模板：名称/价格/评分/距车站/设施标签 全从DB字段直插。无需AI |
| **餐厅推荐卡片** | 未实现 | 模板：名称/评分/人均/菜系/营业时间/预约难度 全从DB字段直插 |
| **区域简介** | ⚠️ hotel_area_guide已有 | `hotel_area_guide.area_summary_zh` 预写入DB（人工撰写，非AI实时生成） |
| **Plan B 备选** | 未实现 | 每个POI预关联1-2个备选（同区域/室内/低体力），模板卡片展示 |
| **景点信息卡** | ✅ 基本实现 | 从entity_base+pois字段直出：开放时间/门票/预约提示/建议时长 |

**酒店推荐卡片模板示例**：

```html
<!-- templates/content_blocks/hotel_card.html.j2 -->
<div class="hotel-card">
  <img src="{{ hotel.cover_image_url }}" />
  <h3>{{ hotel.name_zh }} <span class="ja">{{ hotel.name_ja }}</span></h3>
  <div class="meta">
    <span class="price">¥{{ hotel.typical_price_min_jpy }}/晚起</span>
    <span class="rating">⭐ {{ hotel.google_rating }}</span>
    <span class="distance">🚶 {{ hotel.walking_distance_station_min }}分钟到{{ hotel.nearest_station }}</span>
  </div>
  <div class="amenities">
    {% for a in hotel.amenities %}
    <span class="tag">{{ amenity_labels[a] }}</span>
    {% endfor %}
  </div>
  <!-- 推荐理由：从 entity_editor_notes 或 预写文案库取，不是AI实时生成 -->
  <p class="reason">{{ hotel.recommendation_reason }}</p>
  {% if hotel.caveat %}
  <p class="caveat">⚠️ {{ hotel.caveat }}</p>
  {% endif %}
</div>
```

**Token节省**：这15%内容全部模板化，0 token。酒店/餐厅的推荐理由来自预写文案库(entity_editor_notes)而非AI实时生成

---

### 🟠 Tier 3：AI润色（少量token，仅润色不原创）

**占比：~10%页面内容**
**目标 token：~1,500-2,500/方案（对比当前6,000-10,000）**

| 内容块 | AI做什么 | AI不做什么 | token/次 |
|---|---|---|---|
| **推荐理由** | 将DB中的结构化数据+editor_notes润色成朋友口吻 | 不查数据、不编事实 | ~200 |
| **每日小贴士** | 根据当天行程特点+天气生成1句话建议 | 不重复通用建议 | ~80 |
| **路线设计理由** | 将规则生成的路线逻辑说明润色成自然语言 | 不编造逻辑 | ~150 |

**关键优化：批量润色替代逐条生成**

```python
# 当前方式（浪费token）：每个实体单独调用
for entity in entities:  # 28次调用
    copy = await generate_copy(entity, scene)  # 每次 ~400 token

# 优化方式：批量润色（1次调用）
batch_prompt = """
以下是7天行程中的关键景点，请为每个写一句话推荐理由（朋友口吻，25-40字）。

数据：
1. 浅草寺 | 寺庙 | 浅草 | 免费 | ⭐4.5 | 编辑备注：早上7点前人少
2. 晴空塔 | 展望台 | 押上 | ¥3100 | ⭐4.3 | 编辑备注：晴天能看到富士山
3. 上野公园 | 公园 | 上野 | 免费 | ⭐4.4 | 编辑备注：春天樱花最佳
...（最多30个实体，1次调用）

请输出JSON数组，每项: {"entity_name": "...", "copy_zh": "...", "tips_zh": "..."}
"""
# 1次调用 ~1,500 token，替代28次×400 = 11,200 token
```

**Token节省：从 ~10,000 降到 ~2,000/方案（-80%）**

---

### 🔴 Tier 4：AI原创（核心token，不可省）

**占比：~5%页面内容**
**目标 token：~500-1,000/方案**

| 内容块 | 必须AI的原因 | token/次 |
|---|---|---|
| **个性化开头语** | 需融合用户画像(party_type/style/budget)生成定制感 | ~200 |
| **特殊场景适配** | 蜜月/亲子/老人等特殊建议无法模板穷举 | ~300 |
| **用户特殊需求回应** | 用户自由输入的must_visit/special_needs需要解读 | ~300 |

**这些是AI的"最后一公里"价值，不能省。**

---

## 三、Token优化架构设计

### 新架构：三级内容管道

```
Level 0: 静态内容块 ─── content_blocks/*.html.j2 ────→ 0 token
         (行前准备/安全/交通卡/紧急联系/封面/封底)

Level 1: 规则+模板 ──── content_rules.py + 模板 ────→ 0 token
         (时间轴/交通/门票/概要/预算/JR计算/
          酒店卡片/餐厅卡片/Plan B/区域简介)

Level 2: 批量AI润色 ─── batch_polish() ────→ ~2,000 tok/方案
         (推荐理由/小贴士/路线理由)

Level 3: AI个性化 ──── personalize() ────→ ~800 tok/方案
         (开头语/特殊场景/特殊需求)
```

### 缓存策略升级

| 缓存层 | 当前 | 优化后 |
|---|---|---|
| **实体文案** | Redis TTL=7天，按entity+scene | PostgreSQL持久化 + Redis热缓存。key改为`{entity_id}:{copy_version}`，不按scene分（文案场景差异<5%） |
| **批量润色结果** | 无 | Redis TTL=30天，key=`polish:{template_code}:{scene}:{entity_ids_hash}` |
| **静态内容块** | 无 | 文件系统缓存（编译后的Jinja2模板），无限期 |
| **个性化文案** | 无 | 不缓存（每次都是个性化的） |

### 文案版本控制

```sql
-- 新增表：entity_copy_cache（替代纯Redis缓存）
CREATE TABLE entity_copy_cache (
    entity_id UUID REFERENCES entity_base(entity_id),
    copy_version INT DEFAULT 1,         -- 文案版本（实体数据变更时+1）
    copy_zh TEXT NOT NULL,               -- 一句话描述
    tips_zh TEXT NOT NULL,               -- 旅行Tips
    generated_by VARCHAR(20) NOT NULL,   -- 'ai' / 'editor' / 'rule'
    model_version VARCHAR(50),           -- 'gpt-4o-mini-2024-07-18'
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (entity_id, copy_version)
);
-- 好处：AI只需为新实体/更新实体生成文案，老实体直接查DB
```

---

## 四、逐场景Token消耗对比

### 场景1：¥19.9 基础版（7天经典东京，模板直出）

| 步骤 | 当前token | 优化后token | 方法 |
|---|---|---|---|
| 28个实体文案 | 11,200 | 0 | 全部从 entity_copy_cache 读取（预生成） |
| 时间轴骨架 | 0 | 0 | assembler 已是规则生成 |
| 交通/门票/时间 | 0 | 0 | DB字段直出 |
| **总计** | **~11,200** | **~0** | **基础版 = 0 token！** |

> 基础版是固定模板 + 预缓存文案，完全不需要实时AI调用

### 场景2：¥128 标准版（个性化7天，含酒店餐厅）

| 步骤 | 当前token | 优化后token | 方法 |
|---|---|---|---|
| 28个POI文案 | 11,200 | 0 | entity_copy_cache |
| 5家酒店推荐理由 | N/A(未实现) | 0 | entity_editor_notes（预写） |
| 14家餐厅推荐理由 | N/A(未实现) | 0 | entity_editor_notes（预写） |
| 批量润色（个性化措辞调整） | N/A | 1,500 | 1次batch_polish调用 |
| 个性化开头语 | N/A | 200 | 1次personalize调用 |
| 行前准备/安全/交通 | 0 | 0 | 静态内容块 |
| **总计** | **~11,200+** | **~1,700** | **-85%** |

### 场景3：¥298 深度版（深度个性化+拍照攻略）

| 步骤 | 当前token | 优化后token | 方法 |
|---|---|---|---|
| POI+酒店+餐厅文案 | ~15,000 | 0 | 预缓存 |
| 批量润色 | N/A | 2,000 | 1次调用，含拍照点描述 |
| 个性化开头+场景适配 | N/A | 500 | 1次调用 |
| 特殊需求回应 | N/A | 300 | 根据special_needs生成 |
| 路线设计理由润色 | N/A | 200 | 规则生成→AI润色 |
| **总计** | **~15,000+** | **~3,000** | **-80%** |

---

## 五、预生成策略（offline batch）

### 核心思想：把AI调用从"用户请求时"移到"后台空闲时"

```
用户请求时 (latency-critical):
  只做：模板装配 + DB查询 + 缓存读取 + 少量个性化AI(~3秒)

后台空闲时 (batch job):
  做：新实体文案生成 + 热门路线预渲染 + 季节性内容更新
```

### 预生成任务清单

| 任务 | 频率 | 触发条件 | token预算/次 |
|---|---|---|---|
| **新实体文案** | 实时 | entity_base 新增记录 | ~400/实体 |
| **实体文案更新** | 周级 | entity_base 字段变更 | ~400/实体 |
| **热门路线预渲染** | 日级 | 8个模板 × 4个场景 = 32个组合 | 0（纯模板渲染） |
| **editor_notes预写** | 周级 | S/A级实体变更 | ~200/实体 |
| **季节性内容块** | 月级 | 季节切换 | ~1,000/季 |

### Cron调度

```python
# 新增: scripts/batch_precache.py

async def precache_entity_copy():
    """批量预生成所有活跃实体的文案"""
    # 1. 查找缺少 entity_copy_cache 的实体
    # 2. 按城市分批，每批50个实体
    # 3. 1次batch调用生成50个实体的copy_zh + tips_zh
    # 4. 写入 entity_copy_cache 表
    # 预算：500个活跃实体 × 80tok/个 = 40,000 tok（一次性投入，约$0.006）
    pass

async def precache_hot_routes():
    """预渲染热门路线（纯模板，0 token）"""
    # 8个模板 × 4个场景 = 32个HTML
    # 存入 Redis，key: "prerender:{template}:{scene}"
    pass
```

---

## 六、实施优先级

| 阶段 | 任务 | 预期节省 | 工时(估) |
|---|---|---|---|
| **P0 立即做** | 基础版改为0-token纯模板直出 | 基础版100%省token | 1天 |
| **P0 立即做** | 批量AI调用替代逐条调用 | -70% token/方案 | 0.5天 |
| **P0 立即做** | entity_copy_cache表 + 预生成脚本 | 热门实体0实时token | 1天 |
| **P1 本周** | 静态内容块目录 + 6类模板 | 40%内容0 token | 2天 |
| **P1 本周** | content_rules.py（交通/预算/概要规则化） | 30%内容0 token | 1.5天 |
| **P2 下周** | 酒店/餐厅卡片模板化 + editor_notes预写 | 推荐内容0实时token | 2天 |
| **P2 下周** | 缓存策略升级（Redis→DB持久化） | 长期省重复调用 | 1天 |

### Token 预算总结

| SKU | 当前估算 | 优化后 | 节省比 | 成本/方案 |
|---|---|---|---|---|
| ¥19.9 基础版 | ~11,000 tok | **0 tok** | -100% | $0.000 |
| ¥128 标准版 | ~15,000 tok | **~1,700 tok** | -89% | ~$0.0003 |
| ¥298 深度版 | ~20,000 tok | **~3,000 tok** | -85% | ~$0.0005 |

> 按 GPT-4o-mini 定价 $0.15/1M input + $0.60/1M output 计算
> 即使日均100个方案，月AI成本 < $2

---

## 七、决策树：这块内容该怎么生成？

```
这块内容会因用户不同而变化吗？
├── 不会 → 静态内容块（Level 0）
│         例：行前准备、安全须知、紧急联系
│
└── 会 → 变化的部分是事实数据还是表达方式？
    │
    ├── 事实数据（价格/时间/距离）→ 规则生成（Level 1）
    │   例：门票¥3100、步行15分钟、JR Pass值不值
    │
    └── 表达方式 → 数据库里有预写文案吗？
        │
        ├── 有（entity_editor_notes）→ 模板填充（Level 2-静态端）
        │   例：酒店推荐理由（预写）
        │
        └── 没有 → 需要个性化口吻吗？
            │
            ├── 不需要 → 批量AI预生成 + 缓存（Level 2）
            │   例：景点一句话描述（通用，缓存7天+）
            │
            └── 需要 → AI实时生成（Level 3）
                例：个性化开头语、特殊需求回应
```
