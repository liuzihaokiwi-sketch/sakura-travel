# Spec: route-matrix

## 概述

Google Routes 交通矩阵模块获取行程内实体之间的步行/公交时间，写入 route_matrix_cache，供装配引擎和渲染层使用。

---

## 查询策略

### v1 实现（静态缓存优先）

1. 按城市预计算常用实体对的距离矩阵（city batch query）
2. 写入 route_matrix_cache，TTL 30 天
3. 装配时查缓存，命中直接用
4. 未命中：调用 Google Routes API，写缓存后返回
5. API 调用失败：返回 fallback 估算（步行 15 分钟 / 公交 30 分钟）

### Google Routes API 调用规格

```
POST https://routes.googleapis.com/directions/v2:computeRoutes
{
  "origin": {"location": {"latLng": {...}}},
  "destination": {"location": {"latLng": {...}}},
  "travelMode": "TRANSIT",  // or WALK
  "languageCode": "zh-CN"
}
X-Goog-FieldMask: routes.duration,routes.distanceMeters
```

---

## 数据模型

### route_matrix_cache（已有）

```sql
cache_id          UUID PK
origin_entity_id  UUID FK
dest_entity_id    UUID FK
travel_mode       VARCHAR(16)   -- walk/transit
duration_seconds  INTEGER
distance_meters   INTEGER
fetched_at        TIMESTAMPTZ
expires_at        TIMESTAMPTZ   -- fetched_at + 30天
```

---

## 渲染层使用

每日行程卡片中的「景点间交通」展示：
- 步行 < 10 分钟 → 显示"步行约 X 分钟"
- 步行 >= 10 分钟 → 显示"地铁/公交约 X 分钟"
- 无数据 → 不显示交通信息（静默降级）

---

## 验收标准

- [ ] `get_travel_time(origin_id, dest_id, mode)` 函数实现
- [ ] 缓存命中正常，miss 时调用 API
- [ ] fallback 返回估算值（不抛异常）
- [ ] 城市批量预计算脚本 `scripts/prebuild_route_matrix.py` 可运行
