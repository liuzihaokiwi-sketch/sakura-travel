# Contributing

## Git 工作流

### 分支命名

| 类型 | 命名规范 | 示例 |
|------|----------|------|
| 功能开发 | `feature/<name>` | `feature/admin-dashboard` |
| Bug 修复 | `fix/<name>` | `fix/quiz-validation` |
| 重构 | `refactor/<name>` | `refactor/repo-cleanup` |
| 文档 | `docs/<name>` | `docs/api-guide` |

### Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/):
```
<type>(<scope>): <description>
```

Type: `feat` / `fix` / `chore` / `docs` / `refactor` / `test`
Scope: `admin` / `api` / `web` / `scripts` / `db` / `docs`

## 代码风格

### Python（后端）
- Formatter/Linter: [Ruff](https://docs.astral.sh/ruff/)
- 公共函数必须有类型标注

```bash
ruff check --fix app/ scripts/
ruff format app/ scripts/
```

### TypeScript（前端）
- Linter: ESLint (Next.js 默认)
- 样式: Tailwind CSS utility classes

```bash
cd web && pnpm lint
```

### 数据库
- 表名: snake_case 复数 (`entity_base`, `pois`)
- 迁移: Alembic autogenerate，每次带描述性 message

## 测试

```bash
pytest tests/ -v                    # 全量测试
pytest tests/test_scoring.py -v     # 单个文件
```

## 注意事项

1. 不要提交 `.env` 文件
2. 新增环境变量 → 同步更新 `.env.example` + `app/core/config.py`
3. 修改数据库模型 → 生成 Alembic 迁移
