# Seed 脚本说明

> 最后更新: 2026-03-29

所有 seed 脚本均为幂等操作（ON CONFLICT DO NOTHING），可重复执行。

---

## MVP 执行顺序（Kansai）

```bash
# 1. 基础配置
python -m scripts.seed_product_skus
python -m scripts.seed_product_config
python -m scripts.seed_templates

# 2. 城市圈定义
python -m scripts.seed_all_circles

# 3. 关西活动簇
python -m scripts.seed_kansai_circle              # 主源：100+ 基础簇
python -m scripts.seed_kansai_v2_clusters          # 权威源：含节奏三字段的完整簇

# 4. 关西实体
python -m scripts.seed_kansai_extended_entities    # 实体数据（POI/餐厅/酒店）
python -m scripts.seed_kansai_deep_data            # 深度数据（审核通过后执行）

# 5. 评分规则
python -m scripts.seed_all_soft_rules
```

---

## 脚本分类

### 基础配置

| 脚本 | 说明 |
|------|------|
| `seed_product_skus.py` | 产品 SKU 定义 |
| `seed_product_config.py` | 产品配置 |
| `seed_templates.py` | 路线模板 |
| `seed_all_soft_rules.py` | 评分软规则 |
| `seed_soft_rule_defaults.py` | 软规则默认值 |
| `seed_segment_weight_packs.py` | 客群权重包 |
| `seed_stage_weight_packs.py` | 阶段权重包 |

### 城市圈

| 脚本 | 说明 |
|------|------|
| `seed_all_circles.py` | 所有城市圈定义（6+ 个圈） |
| `seed_all_production.py` | 生产环境一键初始化 |

### 关西（Kansai）— MVP 目标

| 脚本 | 角色 | 说明 |
|------|------|------|
| `seed_kansai_circle.py` | 主源 | 基础圈定义 + 100+ 活动簇 |
| `seed_kansai_v2_clusters.py` | 权威源 | 完整 v2 簇定义（含节奏三字段） |
| `seed_kansai_entities.py` | 实体 | MVP 基础实体数据 |
| `seed_kansai_extended_entities.py` | 实体 | 扩展实体数据（110+ POI/65 餐厅/8 酒店） |
| `seed_kansai_deep_data.py` | 深度 | 20 景点 + 30 餐厅 + 10 住宿区域（待审核） |

### 其他区域

| 区域 | 主源 | 补充 | 实体 |
|------|------|------|------|
| 东京 | `seed_tokyo_clusters.py` | `seed_tokyo_supplemental_clusters.py` | - |
| 北海道 | `seed_hokkaido_clusters.py` | `seed_hokkaido_supplemental_clusters.py` | `seed_hokkaido_entities.py` |
| 九州 | `seed_kyushu_clusters.py` | `seed_kyushu_supplemental_clusters.py` | - |
| 广府 | `seed_guangfu_clusters.py` | `seed_guangfu_supplemental_clusters.py` | - |
| 华东 | `seed_huadong_clusters.py` | - | - |
| 新疆 | `seed_xinjiang_clusters.py` | - | - |
| 冲绳 | `seed_okinawa_clusters.py` | - | - |
| 中部 | `seed_chubu_clusters.py` | - | - |
| 潮汕 | `seed_chaoshan_clusters.py` | - | - |

### 跨圈

| 脚本 | 说明 |
|------|------|
| `seed_family_shopping_clusters.py` | 跨圈亲子/购物活动簇 |

### 工具脚本

| 脚本 | 说明 |
|------|------|
| `backfill_activity_cluster_fields.py` | 回填活动簇缺失字段 |
| `populate_anchor_entities.py` | AI 填充 anchor_entities 字段 |
| `sync_entity_gaps.py` | 分析实体缺口 + 定向生成 + 绑定 |
| `convert_mojor_to_seed.py` | 将 mojor/*.md 转换为 seed 脚本 |
| `demo_page_pipeline.py` | 页面渲染管线演示/验证 |
| `verify_api.py` | API 端点验证 |

---

## 已删除的脚本

| 脚本 | 删除日期 | 原因 |
|------|---------|------|
| `seed_complete_clusters.py` | 2026-03-29 | 早期全量合并，被各区域独立脚本取代 |
| `seed_phase2_real_circles.py` | 2026-03-29 | Phase 2 验证用最小数据，已过时 |
| `seed_kansai_mvp.py` | 2026-03-29 | 不完整的编排器，被 seed_all_clusters.sh 取代 |
| `seed_kansai_corridors.py` | 2026-03-29 | 走廊数据已合并入 v2_clusters |
| `seed_kansai_specialty_clusters.py` | 2026-03-29 | 特色簇已合并入 v2_clusters |
| `seed_kansai_extended_circles.py` | 2026-03-29 | 扩展簇已合并入 v2_clusters |
| `seed_kansai_supplemental_clusters.py` | 2026-03-29 | 季节簇已合并入 v2_clusters |
| `seed_kansai_unified_clusters.py` | 2026-03-29 | 去重逻辑已内化到 v2 |
| `_add_columns.py` | 2026-03-29 | 一次性 migration 辅助脚本 |
