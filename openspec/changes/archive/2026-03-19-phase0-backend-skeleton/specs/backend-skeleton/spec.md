## ADDED Requirements

### Requirement: 项目结构按领域划分
系统 SHALL 采用模块化单体结构，按六大领域划分目录（trip_core / catalog / live_inventory / ranking / rendering / review_ops），每个领域包含自己的 service、schema、router。

#### Scenario: 新增领域功能不影响其他领域
- **WHEN** 开发者在 `app/domains/catalog/` 下新增文件
- **THEN** 其他领域（如 trip_core）的测试不受影响，不需要修改其他领域的 `__init__.py`

### Requirement: 健康检查端点
系统 SHALL 提供 `GET /health` 端点，返回服务状态和数据库连接状态。

#### Scenario: 服务正常时健康检查通过
- **WHEN** 调用 `GET /health`，数据库和 Redis 均可连接
- **THEN** 返回 HTTP 200，body 为 `{"status": "ok", "db": "ok", "redis": "ok"}`

#### Scenario: 数据库不可用时健康检查返回降级状态
- **WHEN** 调用 `GET /health`，PostgreSQL 连接超时
- **THEN** 返回 HTTP 200，body 为 `{"status": "degraded", "db": "error", "redis": "ok"}`

### Requirement: 配置管理
系统 SHALL 通过 `pydantic-settings` 读取环境变量，不在代码中硬编码任何连接字符串、API Key 或密钥。

#### Scenario: 从环境变量加载配置
- **WHEN** 服务启动时，环境变量 `DATABASE_URL` 已设置
- **THEN** `Settings.database_url` 返回该值，数据库连接成功建立

#### Scenario: 缺少必填环境变量时启动失败
- **WHEN** 服务启动时，必填环境变量 `DATABASE_URL` 未设置
- **THEN** 服务启动抛出 `ValidationError`，进程退出，日志输出缺失字段名
