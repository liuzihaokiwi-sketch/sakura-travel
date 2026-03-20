# 贡献指南 (CONTRIBUTING)

感谢你对 Japan Travel AI 项目的贡献！请遵循以下规范。

## 🔀 Git 工作流

### 分支命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 功能 | `feat/<short-name>` | `feat/admin-dashboard` |
| 修复 | `fix/<short-name>` | `fix/pdf-font-rendering` |
| 重构 | `refactor/<short-name>` | `refactor/scoring-engine` |
| 文档 | `docs/<short-name>` | `docs/api-endpoints` |
| 热修复 | `hotfix/<short-name>` | `hotfix/env-leak` |

### Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <subject>

[optional body]
```

**类型**：`feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `ci`

**作用域**：`api` / `web` / `catalog` / `ranking` / `planning` / `rendering` / `worker` / `scripts` / `config`

**示例**：

```
feat(api): add order modification endpoint
fix(rendering): correct CJK font fallback in PDF
refactor(catalog): extract tagger into separate module
docs(readme): update deployment instructions
chore(deps): bump fastapi to 0.115.5
```

### PR 流程

1. 从 `main` 创建功能分支
2. 完成开发 + 本地测试通过
3. 推送分支并创建 Pull Request
4. PR 标题遵循 commit 规范
5. 至少 1 人 Review + CI 通过后合并
6. 合并方式：**Squash and merge**

## 🎨 代码风格

### Python（后端）

- **Linter**: [Ruff](https://docs.astral.sh/ruff/) — 行宽 100，目标 Python 3.12
- **格式化**: `ruff format app/ scripts/ tests/`
- **检查**: `ruff check app/ scripts/ tests/`
- **类型标注**: 鼓励使用，新代码必须添加
- **Import 排序**: 由 Ruff 自动处理（isort 兼容）

```bash
# 一键检查 + 修复
ruff check --fix app/ scripts/
ruff format app/ scripts/
```

### TypeScript / React（前端）

- **Linter**: ESLint (Next.js 默认配置)
- **格式化**: Prettier（如有配置）
- **组件**: 函数组件 + hooks，不使用 class 组件
- **样式**: Tailwind CSS utility-first，避免自定义 CSS

```bash
cd web
pnpm lint        # ESLint 检查
pnpm lint --fix  # 自动修复
```

### SQL / 数据库

- **表名**: snake_case 复数（`entity_base`, `pois`, `hotels`）
- **列名**: snake_case（`city_code`, `entity_type`）
- **迁移**: 使用 Alembic `autogenerate`，每次迁移必须带描述性 message

```bash
alembic revision --autogenerate -m "add_name_local_column"
alembic upgrade head
```

## 🧪 测试

- 新功能必须附带测试
- 测试框架：`pytest` + `pytest-asyncio`
- 单元测试使用 SQLite in-memory，集成测试使用 PostgreSQL

```bash
# 运行全部测试
pytest -v

# 运行特定测试
pytest tests/test_scoring.py -v -k "test_context_score"

# 覆盖率报告
pytest --cov=app --cov-report=html
```

## 📁 文件组织

- 后端新模块放 `app/domains/<domain>/`
- API 路由放 `app/api/`
- 前端页面放 `web/app/<route>/`
- 共享组件放 `web/components/`
- 脚本放 `scripts/`
- 种子数据放 `data/seed/`

## ⚠️ 注意事项

1. **永远不要提交 `.env` 文件** — 已有 pre-commit hook 防护
2. **新增环境变量** → 同步更新 `.env.example` + `app/core/config.py`
3. **修改数据库模型** → 生成 Alembic 迁移脚本
4. **修改高风险文件**（评分引擎 / 行程装配器）→ 必须有测试覆盖