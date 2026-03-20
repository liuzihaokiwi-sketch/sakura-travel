# Contributing to Travel AI

## Git 工作流

### 分支命名

| 类型 | 命名规范 | 示例 |
|------|----------|------|
| 功能开发 | `feature/<name>` | `feature/admin-dashboard` |
| Bug 修复 | `fix/<name>` | `fix/quiz-validation` |
| 重构 | `refactor/<name>` | `refactor/repo-cleanup` |
| 文档 | `docs/<name>` | `docs/api-guide` |
| 紧急修复 | `hotfix/<name>` | `hotfix/payment-error` |

### Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <description>

[optional body]
```

**Type**:
- `feat` — 新功能
- `fix` — Bug 修复
- `chore` — 构建/工具/依赖
- `docs` — 文档
- `refactor` — 重构
- `test` — 测试
- `style` — 格式调整

**Scope**: `admin` / `api` / `web` / `scripts` / `db` / `docs`

**示例**:
```
feat(admin): add order kanban dashboard
fix(api): prevent duplicate quiz submissions
docs: update README with new API endpoints
chore: archive legacy HTML pages
```

### PR 流程

1. 从 `main` 拉分支
2. 开发 + 本地测试
3. 确保 `ruff check` 和 `pnpm lint` 通过
4. 提交 PR，描述清楚改了什么和为什么
5. Code review 后合并到 `main`

## 🎨 代码风格

### Python（后端）

- **Formatter**: [Ruff](https://docs.astral.sh/ruff/) (`ruff format app/ scripts/`)
- **Linter**: [Ruff](https://docs.astral.sh/ruff/) (`ruff check app/ scripts/`)
- 类型标注: 所有公共函数必须有类型标注
- Docstring: 使用 Google style

```bash
# 一键检查 + 修复
ruff check --fix app/ scripts/
ruff format app/ scripts/
```

### TypeScript / React（前端）

- **Linter**: ESLint (Next.js 默认配置)
- **格式化**: Prettier（如有配置）
- **组件**: 函数组件 + hooks，不使用 class 组件
- **样式**: Tailwind CSS utility classes，不写自定义 CSS

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