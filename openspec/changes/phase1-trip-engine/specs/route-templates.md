# Spec: route-templates

## 概述

路线模板系统定义了 Phase 1 行程编排的骨架。每条模板代表一条经典日本旅行路线，内置每日时间块和实体槽位，装配引擎用评分排序填充槽位得到具体行程。

---

## 数据模型

### route_templates 表（已有）

```sql
route_template_id  UUID PK
template_code      VARCHAR(64) UNIQUE  -- 如 "tokyo_classic_5d"
template_name_zh   VARCHAR(128)
city_codes         TEXT[]              -- 覆盖城市，如 ["tokyo"]
total_days         INTEGER
scenes             TEXT[]              -- 适配场景：couple/family/solo/luxury
status             VARCHAR(16)         -- active / draft
template_json      JSONB               -- 完整模板结构（见下）
created_at         TIMESTAMPTZ
updated_at         TIMESTAMPTZ
```

### template_json 结构

```json
{
  "meta": {
    "template_code": "tokyo_classic_5d",
    "name_zh": "东京经典5日",
    "tagline_zh": "浅草·新宿·渋谷·秋叶原·汐留",
    "cover_image_query": "tokyo skyline",
    "total_days": 5,
    "city_codes": ["tokyo"],
    "scenes": ["couple", "solo", "group"],
    "intensity": "moderate"
  },
  "days": [
    {
      "day_num": 1,
      "theme_zh": "浅草历史文化",
      "area_zh": "浅草・上野",
      "time_blocks": [
        {
          "time_slot": "morning",
          "slot_type": "poi",
          "duration_minutes": 120,
          "tags_required": {"culture_history": 4},
          "area_hint": "asakusa",
          "fallback_entity_id": null
        },
        {
          "time_slot": "lunch",
          "slot_type": "restaurant",
          "duration_minutes": 60,
          "tags_required": {"food": 3},
          "area_hint": "asakusa",
          "fallback_entity_id": null
        },
        {
          "time_slot": "afternoon",
          "slot_type": "poi",
          "duration_minutes": 150,
          "tags_required": {"culture_history": 3},
          "area_hint": "ueno",
          "fallback_entity_id": null
        },
        {
          "time_slot": "evening",
          "slot_type": "poi",
          "duration_minutes": 90,
          "tags_required": {"photography_scenic": 3},
          "area_hint": "asakusa",
          "fallback_entity_id": null
        }
      ],
      "hotel_area_zh": "浅草・上野周边",
      "transport_notes_zh": "地铁銀座線、都営浅草線，JR 山手線"
    }
  ],
  "scene_variants": {
    "couple": {
      "tag_weight_overrides": {"photography_scenic": 1.3, "onsen_relaxation": 1.2},
      "tagline_suffix_zh": "情侣专属"
    },
    "family": {
      "tag_weight_overrides": {"family_kids": 1.5},
      "filter_exclude_tags": {"nightlife_entertainment": 3}
    }
  }
}
```

---

## 初期路线模板清单（5 条）

| 代码 | 名称 | 天数 | 城市 | 场景 |
|------|------|------|------|------|
| `tokyo_classic_5d` | 东京经典5日 | 5 | tokyo | couple/solo/group |
| `tokyo_classic_3d` | 东京精华3日 | 3 | tokyo | couple/solo |
| `kansai_classic_6d` | 关西经典6日（大阪+京都+奈良） | 6 | osaka/kyoto | couple/family |
| `kansai_classic_4d` | 关西精华4日 | 4 | osaka/kyoto | couple/solo |
| `tokyo_kansai_8d` | 东京+关西黄金8日 | 8 | tokyo/osaka/kyoto | couple/group |

---

## 槽位填充规则

1. 按 `tags_required` 条件从 entity_tags 过滤候选实体
2. 过滤 `area_hint` 匹配的实体（city_area 字段模糊匹配）
3. 按 entity_scores.final_score 降序取 Top 1
4. 若候选不足：扩大到全城市召回（去掉 area_hint 限制）
5. 若仍无候选：使用 `fallback_entity_id`（种子数据保底）
6. 同一实体不重复出现在同一行程中

---

## 场景变体规则

- `tag_weight_overrides`：调整标签权重，重新排序候选
- `filter_exclude_tags`：排除超过阈值的标签的实体（如家庭游排除夜生活场所）
- `tagline_suffix_zh`：在攻略标题后追加场景标签

---

## 验收标准

- [ ] 5 条路线模板种子数据写入 route_templates 表
- [ ] 每条模板至少覆盖 3 个场景变体
- [ ] 所有槽位的 tags_required 条件在现有实体标签中有足够覆盖（每槽位至少 3 个候选）
- [ ] `scripts/load_route_templates.py` 可重复执行（幂等）
