## ADDED Requirements

### Requirement: 区域种子数据启动加载

系统 SHALL 在 FastAPI 应用启动时（startup 事件）从 `data/` 目录加载以下种子 JSON 到内存全局字典：
- `japan_region_usertype_matrix_v1.json` — 区域×用户类型推荐矩阵
- `route_region_binding_v1.json` — 线路与区域绑定关系
- `p0_route_skeleton_templates_v1.json` — P0 线路骨架模板

#### Scenario: 启动加载成功
- **WHEN** FastAPI 应用启动（lifespan startup）
- **THEN** 全局字典 `REGION_DATA`、`ROUTE_BINDINGS`、`ROUTE_TEMPLATES` 被填充，日志输出 "Loaded X regions, Y routes"

#### Scenario: 种子文件缺失时警告不崩溃
- **WHEN** `data/` 目录下某个 JSON 文件不存在
- **THEN** 日志输出 WARNING 但应用正常启动，对应字典为空

### Requirement: 按区域筛选实体

系统 SHALL 提供 `get_entities_by_region(region_id, entity_type)` 函数，通过区域的 core_cities + extended_cities 映射到 entity_base.city_code，返回该区域内的实体列表。

#### Scenario: 查询东京都市圈景点
- **WHEN** 调用 `get_entities_by_region("R01", "poi")`（R01 = 东京都市圈，core_cities=["tokyo"]）
- **THEN** 返回 city_code="tokyo" 的所有 POI 实体

#### Scenario: 查询包含扩展城市的区域
- **WHEN** 调用 `get_entities_by_region("R01", "poi")`（R01 的 extended_cities=["yokohama", "kamakura"]）
- **THEN** 返回 city_code 为 tokyo、yokohama、kamakura 的所有 POI 实体

### Requirement: 按线路筛选城市组合

系统 SHALL 提供 `get_cities_for_route(route_id)` 函数，返回指定线路覆盖的城市列表。

#### Scenario: 查询经典东京大阪线路
- **WHEN** 调用 `get_cities_for_route("RT01")`（经典东京-大阪线路）
- **THEN** 返回 `["tokyo", "osaka", "kyoto"]` 城市列表
