# Japan Travel AI — 产品定价与功能矩阵
> 最后更新: 2026-03-19 23:35
> 项目路径: /Users/yanghailin/projects/travel-ai

## 当前代码实现状态

| 层级 | 定义位置 | 状态 |
|---|---|---|
| API 层 | `app/api/products.py` | ✅ 仅上线 ¥19.9 基础版 (hardcoded) |
| DB 模型 | `app/db/models/business.py` → `product_sku` 表 | ✅ 支持多 SKU (features JSONB) |
| DB migration | `a1b2c3d4e5f6_initial_schema.py` | ✅ product_sku 表已建 |
| 种子数据 | 未找到 | ❌ 尚未写入 DB |

## 已设计的 SKU 体系 (从代码推断)

> 来源: `product_sku` 表注释 `"如 basic_20 / standard_128"` + `sku_type: template / personalized / themed`

### 💰 ¥19.9 引流款 — `basic_v1`

**SKU 类型**: `template` (模板型)

**已实现的功能** (在 `products.py` 中明确定义):
- ✅ AI 智能行程规划（基于评分引擎 + 实体库）
- ✅ 杂志级 PDF 攻略（WeasyPrint 渲染，可打印）
- ✅ H5 在线预览（手机可访问）
- ✅ 每日行程时间轴（含开闭时间、交通建议）
- ✅ AI 文案润色（景点一句话描述 + 旅行 Tips）

**路线模板**: 5 条
| 模板代码 | 说明 |
|---|---|
| `tokyo_classic_3d` | 东京经典 3 日 |
| `tokyo_classic_5d` | 东京经典 5 日 |
| `kansai_classic_4d` | 关西经典 4 日 |
| `kansai_classic_6d` | 关西经典 6 日 |
| `tokyo_kansai_8d` | 东京+关西 8 日 |

**支持场景**: couple / family / solo / senior (4种)

**限制** (推断自 features JSONB 设计):
- ❌ 无餐厅推荐 (has_restaurant = false)
- ❌ 无酒店筛选 (has_hotel_filter = false)
- ❌ 无自定义输入 (custom_input = false)
- ❌ 无人工审核 (无 review_jobs)
- ❌ 固定模板，不可修改路线

---

### 💎 ¥128 标准个性化 — `standard_128` (待实现)

**SKU 类型**: `personalized` (个性化)

**预期功能** (推断自 DB 模型 + features 字段设计):
- ✅ 基础版全部功能
- ✅ **餐厅推荐** (has_restaurant = true) — 利用 Tabelog 评分数据
- ✅ **酒店筛选** (has_hotel_filter = true) — 按预算/区域/类型筛选
- ✅ **自定义输入** (custom_input = true) — 用户可指定必去/避免的地点
- ✅ **偏好问卷** — 6 维度主题权重 (文化/美食/自然/购物/亲子/夜生活)
- ✅ **交通时间** — 景点间公共交通时间 (route_matrix)
- ✅ **预算估算** — 每日花费明细 (门票+餐饮+交通)
- ⚠️ **多版本对比** — trip_versions 表支持 (逻辑待实现)

**预期路线模板**: 基础版 5 条 + 额外深度模板

---

### 🏆 ¥298 主题深度游 — `themed_298` (待实现)

**SKU 类型**: `themed` (主题型)

**预期功能** (推断自代码架构设计):
- ✅ 标准版全部功能
- ✅ **人工审核** — review_jobs + review_actions 表 (编辑审核行程质量)
- ✅ **编辑加权** — entity_editor_notes (人工 boost + 内行秘诀)
- ✅ **酒店区域导览** — hotel_area_guide (编辑撰写周边介绍)
- ✅ **机票特价监控** — flight_offer_snapshots (持续追踪价格)
- ✅ **体验活动** — VELTRA/KKday 精选体验
- ✅ **季节专属** — 樱花/红叶/祭典 特别路线
- ✅ **实时天气** — Open-Meteo 天气预报注入行程

---

## features JSONB 字段设计

```json
// basic_v1 (¥19.9)
{
    "has_restaurant": false,
    "has_hotel_filter": false,
    "custom_input": false,
    "has_review": false,
    "has_transport_time": false,
    "has_budget_detail": false,
    "has_flight_monitor": false,
    "has_experience": false,
    "max_regenerate": 1
}

// standard_128 (¥128)
{
    "has_restaurant": true,
    "has_hotel_filter": true,
    "custom_input": true,
    "has_review": false,
    "has_transport_time": true,
    "has_budget_detail": true,
    "has_flight_monitor": false,
    "has_experience": false,
    "max_regenerate": 3
}

// themed_298 (¥298)
{
    "has_restaurant": true,
    "has_hotel_filter": true,
    "custom_input": true,
    "has_review": true,
    "has_transport_time": true,
    "has_budget_detail": true,
    "has_flight_monitor": true,
    "has_experience": true,
    "max_regenerate": 5
}
```

## 预算级别 (已实现)

代码中已有 4 档预算概念 (在 intent_parser, renderer, ai_generator 中使用):

| 级别 | 英文 | 中文 | 适用 |
|---|---|---|---|
| budget | 经济 | ¥300-500/天 | 背包客/学生 |
| mid | 中档 | ¥500-1000/天 | 大多数游客 |
| premium | 高档 | ¥1000-2000/天 | 商务/高端 |
| luxury | 奢华 | ¥2000+/天 | 蜜月/庆祝 |

## 支付渠道 (DB 已设计)

`orders` 表支持:
- 微信支付 (wechat)
- 支付宝 (alipay)
- Stripe (stripe)

状态流转: `pending → paid → processing → delivered → refunded`

---

## 总结

| 价位 | 已实现 | 说明 |
|---|---|---|
| **¥19.9 基础版** | ⚠️ 80% | API + 规划引擎 + 渲染 已有, 缺数据入库和端到端验证 |
| **¥128 标准版** | ❌ 30% | DB 模型已设计, features 控制逻辑待实现 |
| **¥298 主题版** | ❌ 20% | DB 模型已设计, 人工审核流程待实现 |

**⚠️ 注意**: 以上 ¥128 和 ¥298 的功能定义是根据代码架构推断的，具体功能和定价需要你确认。
