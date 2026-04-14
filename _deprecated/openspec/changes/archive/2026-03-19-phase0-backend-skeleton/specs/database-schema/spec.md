## ADDED Requirements

### Requirement: 全量 DDL 三层分离建表
系统 SHALL 在 Phase 0 一次性建好全部 35 张表，按 Layer A（Catalog）/ Layer B（Snapshots）/ Layer C（Derived）+ 业务表四组组织 SQLAlchemy models，通过 Alembic 生成首个 migration。

#### Scenario: Alembic 首次迁移成功
- **WHEN** 在干净的 PostgreSQL 实例上运行 `alembic upgrade head`
- **THEN** 全部 35 张表创建成功，无外键约束错误，`alembic_version` 表记录当前版本

#### Scenario: pgvector 扩展就绪
- **WHEN** migration 运行时，PostgreSQL 已安装 pgvector 扩展
- **THEN** `CREATE EXTENSION IF NOT EXISTS vector` 成功执行，`entity_base` 的 embedding 列可用

### Requirement: 实体基表 entity_base 统一主键
所有实体（poi / hotel / restaurant）MUST 通过 `entity_id`（UUID）关联到 `entity_base`，`entity_type` 字段区分类型，扩展表（`pois` / `hotels` / `restaurants`）以 `entity_id` 为主键且同时为外键。

#### Scenario: 创建 POI 实体
- **WHEN** 向 `entity_base` 插入一条 `entity_type='poi'` 的记录，同时向 `pois` 插入对应的扩展字段
- **THEN** 两张表通过 `entity_id` JOIN 可查到完整 POI 信息

#### Scenario: 查询同城景点列表
- **WHEN** 查询 `entity_base WHERE city='Tokyo' AND entity_type='poi' AND status='active'`
- **THEN** 返回该城市所有有效景点，可与 `pois` JOIN 获取停留时长等专属字段

### Requirement: plan_artifacts 全链路追溯
系统 SHALL 在 `plan_artifacts` 表中记录每次行程生成所使用的 `score_version`、`template_version`、`source_snapshot_ids`，确保可以完整复现任何一次生成结果。

#### Scenario: 行程生成后追溯其快照版本
- **WHEN** 查询某份已生成的行程计划对应的 `plan_artifacts`
- **THEN** 能取到 `source_snapshot_ids` 数组，通过关联 `source_snapshots` 表还原当时的外部数据状态
