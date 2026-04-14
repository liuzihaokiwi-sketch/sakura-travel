# 实体数据层 — Catalog 主档 (entity_base + POI + Hotel + Restaurant)

## 概述
所有实体共享统一基类 `entity_base`，各类型扩展表存专属字段。
属于三层数据架构中的 **Layer A：主档事实层（Catalog）**，只存相对稳定的事实。

## 三层数据架构
```
Layer A：Catalog（主档事实）   ← 本 spec
Layer B：Live Snapshots（动态快照）  → data-pipeline/spec.md
Layer C：Derived（派生结果）   → scoring-engine + itinerary-planner
```

## 落表方式：共享基表 + 扩展表（CTI）
- `entity_base` 存公共字段
- `pois` / `hotels` / `restaurants` 存各自专属字段
- 通过 `entity_id` 关联
- `entity_tags` / `entity_media` / `entity_editor_notes` 通过 entity_id + entity_type 关联

---

## entity_base（公共基表）
| 字段 | 类型 | 说明 |
|---|---|---|
| entity_id | UUID | 内部统一主键 |
| entity_type | VARCHAR | poi / hotel / restaurant |
| source | VARCHAR | google_places / booking / tabelog / internal |
| source_id | VARCHAR | 外部主键 |
| name_local | VARCHAR | 本地名（日文） |
| name_zh | VARCHAR | 中文名 |
| name_en | VARCHAR | 英文名 |
| country | VARCHAR | 国家 |
| city | VARCHAR | 城市 |
| area | VARCHAR | 区域（浅草/新宿/祇園…） |
| lat | DECIMAL(10,7) | 纬度 |
| lng | DECIMAL(10,7) | 经度 |
| categories | JSONB | 类型分类 |
| media_assets | JSONB | 图片/封面 URL |
| description_zh | TEXT | 中文简介 |
| data_tier | VARCHAR | S / A / B 级 |
| status | VARCHAR | active / deprecated |
| region_scope | VARCHAR | mainstream / extended / niche（对应价位所需的地区覆盖） |
| updated_at | TIMESTAMP | 最近主档更新时间 |
| created_at | TIMESTAMP | 创建时间 |

## entity_tags（统一标签表）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| entity_id | UUID | 关联实体 |
| entity_type | VARCHAR | poi / hotel / restaurant |
| tag_name | VARCHAR | 标签名 |
| tag_score | INT | 标签强度 0-5 |
| source | VARCHAR | system / editor / gpt_assisted |
| updated_at | TIMESTAMP | 更新时间 |

### 标签库
family_friendly / pet_friendly / luxury / budget_friendly / anime / shopping / onsen / food / nature / photo_spot / museum / theme_park / culture / nightlife / skiing / tea_ceremony / rainy_day_friendly / transport_convenient / low_physical / couple_friendly / solo_friendly / elder_friendly

## entity_media（媒体资源表）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| entity_id | UUID | 关联实体 |
| entity_type | VARCHAR | poi / hotel / restaurant |
| media_type | VARCHAR | photo / video / cover |
| url | VARCHAR | 资源 URL |
| caption_zh | VARCHAR | 中文图说 |
| sort_order | INT | 排序 |

---

## pois（景点扩展表）
| 字段 | 类型 | 说明 |
|---|---|---|
| entity_id | UUID | 主键，关联 entity_base |
| opening_hours | JSONB | 营业时间结构 |
| typical_visit_duration | INT | 建议停留时长（分钟） |
| best_time_slot | VARCHAR[] | 适合时间段（AM/PM/EVENING） |
| ticket_level | VARCHAR | 免费/低/中/高 |
| ticket_price_ref | VARCHAR | 参考票价说明 |
| weather_sensitivity | VARCHAR | 高/中/低 |
| queue_risk | VARCHAR | 排队风险（低/中/高） |
| rain_backup_candidates | UUID[] | 雨天替代候选 entity_id |
| accessibility | VARCHAR | 无障碍等级 |
| tips_zh | TEXT | 中文游玩提示 |

## hotels（酒店扩展表）
| 字段 | 类型 | 说明 |
|---|---|---|
| entity_id | UUID | 主键，关联 entity_base |
| brand | VARCHAR | 品牌（APA/东横INN/星野…） |
| hotel_category | VARCHAR | 商务/度假/民宿/胶囊/温泉旅馆 |
| star_level | INT | 星级 1-5 |
| nearest_station | VARCHAR | 最近车站 |
| walk_to_station_min | INT | 步行到车站分钟数 |
| transport_score | INT | 交通便利度 1-10 |
| room_size_hint | VARCHAR | 房间大小提示 |
| checkin_time | VARCHAR | 入住时间 |
| checkout_time | VARCHAR | 退房时间 |
| checkin_notes_zh | TEXT | 中文办理须知 |
| neighborhood_profile | TEXT | 周边环境描述 |
| price_range_jpy | VARCHAR | 参考价格带（日元） |
| price_range_cny | VARCHAR | 参考价格带（人民币） |
| booking_url | VARCHAR | 预订链接 |

## restaurants（餐饮扩展表）
| 字段 | 类型 | 说明 |
|---|---|---|
| entity_id | UUID | 主键，关联 entity_base |
| cuisine | VARCHAR[] | 菜系 |
| price_range_level | VARCHAR | 低/中/高/奢华 |
| price_range_jpy | VARCHAR | 参考人均（日元） |
| price_range_cny | VARCHAR | 参考人均（人民币） |
| opening_hours | JSONB | 营业时间 |
| last_order_time | VARCHAR | 最后点单时间 |
| accepts_reservations | BOOLEAN | 是否可预约 |
| reservation_method | VARCHAR | 预约方式 |
| queue_risk | VARCHAR | 排队风险（低/中/高/极高） |
| avg_wait_min | INT | 平均等待时间（分钟） |
| signature_items | JSONB | 招牌菜列表 |
| meal_slots | VARCHAR[] | BREAKFAST/LUNCH/DINNER/LATE_NIGHT |
| suitable_for | VARCHAR[] | 独旅/情侣/亲子/多人/商务 |

---

## hotel_area_guide（区域住宿指南，引流款用）
| 字段 | 类型 | 说明 |
|---|---|---|
| guide_id | UUID | 主键 |
| city | VARCHAR | 城市 |
| area | VARCHAR | 区域名 |
| area_description_zh | TEXT | 区域住宿推荐理由 |
| price_range_ref | VARCHAR | 价格带参考 |
| suitable_for | JSONB | 适合人群标签 |
| nearby_attractions | JSONB | 附近主要景点 |
| transport_highlight | TEXT | 交通亮点 |

---

## 数据分级策略
| 级别 | 覆盖 | 数据要求 | 谁来做 |
|---|---|---|---|
| S 级 | 每城市 Top 20 景点 / Top 10 酒店 / Top 15 餐厅 | 全字段+editorial_notes+标签强度 | 你 + GPT 辅助 |
| A 级 | 每城市 Top 50-100 实体 | 主要字段+editorial_boost+关键标签 | GPT 预打 + 你校准 |
| B 级 | 长尾实体 | 仅 entity_base + 系统自动标签 | 全自动 |

## 约束
- 每个实体必须有 name_zh、city、area、lat/lng
- S 级实体必须有 entity_editor_notes
- entity_base.status = deprecated 的不参与召回
- region_scope = niche 的实体仅在高客单产品中使用
