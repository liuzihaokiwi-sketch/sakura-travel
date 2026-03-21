# R7. 变更执行策略

> 确保重构过程安全、可回滚、可追溯。

---

## 一、分支策略

| 分支名 | 用途 | 生命周期 |
|---|---|---|
| `main` | 主分支，不直接操作 | 永久 |
| `refactor/repo-cleanup` | 重构主分支 | 合并后删除 |

所有操作在 `refactor/repo-cleanup` 上执行，完成后 PR 合并到 `main`。

---

## 二、提交顺序（7 个 commit，从低风险到高风险）

| 顺序 | Commit 信息 | 操作 | 风险 | 回滚方式 |
|---|---|---|---|---|
| 1 | `chore: delete debug screenshots and build artifacts` | 删除 R2表1 的 20 个文件 | 无 | `git revert` |
| 2 | `chore: archive legacy HTML pages` | 移动早期 HTML 到 `archive/legacy-html/` | 无 | `git revert` |
| 3 | `chore: archive deprecated web pages` | 移动废弃前端页面到 `archive/legacy-web-pages/` | 低 | `git revert` |
| 4 | `chore: archive legacy docs` | 移动旧文档到 `archive/legacy-docs/` | 低 | `git revert` |
| 5 | `chore: reorganize data directory` | 移动 seed 数据 + 爬虫数据 + 建软链接 | 中 | 软链接保证兼容 |
| 6 | `docs: create docs-human and docs-ai skeleton` | 新建双文档目录 + 占位文件 | 无 | `git revert` |
| 7 | `chore: update .gitignore, README, add CONTRIBUTING and CODEOWNERS` | 更新仓库治理文件 | 无 | `git revert` |

### 为什么这个顺序

- 先删无风险的调试文件（commit 1）→ 验证构建正常
- 再做归档（commit 2-4）→ 验证前后端都能跑
- 再做数据重组（commit 5）→ 这是唯一有代码引用风险的步骤
- 最后加文档和配置（commit 6-7）→ 纯新增，无风险

---

## 三、每步验证方式

| Commit | 验证方式 |
|---|---|
| 1 | `ls data/gf_*.png` 应返回空 |
| 2 | `ls archive/legacy-html/` 确认文件在 |
| 3 | `cd web && npx next build` 确认前端构建通过 |
| 4 | 无需验证（纯文档移动） |
| 5 | `python scripts/verify_api.py` 确认后端 API 正常；`ls -la data/events_raw` 确认软链接存在 |
| 6 | `ls docs-human/ docs-ai/` 确认目录存在 |
| 7 | `cat .gitignore` 确认覆盖完整 |

---

## 四、回滚策略

| 情况 | 做法 |
|---|---|
| 某个 commit 导致构建失败 | `git revert <commit-hash>` 回滚该步骤 |
| 数据重组导致后端报错 | 删除软链接 + `git revert` commit 5 |
| 需要整体回滚 | `git reset --hard main` 回到主分支状态 |
| 归档的文件后来发现还需要 | 从 `archive/` 目录移回原位 |

---

## 五、PR 结构

```
PR: refactor/repo-cleanup → main

标题：[Refactor] 项目重构：清理废弃文件 + 双文档体系 + Git治理

描述：
## 变更摘要
- 删除 20 个调试截图和构建产物
- 归档 31 个废弃文件（早期HTML/废弃前端页/旧文档）
- 重组 data/ 目录（seed/ + crawled/）
- 新建 docs-human/ 和 docs-ai/ 文档体系
- 更新 .gitignore、README、新增 CONTRIBUTING 和 CODEOWNERS

## 不影响的内容
- app/ 后端代码零修改
- web/ 核心页面零修改
- templates/ 渲染模板零修改
- openspec/ 零修改
- 数据库/迁移零修改

## 验证方式
- [ ] `cd web && npx next build` 通过
- [ ] `python scripts/verify_api.py` 通过
- [ ] 所有归档文件在 archive/ 中可找到
```

---

## 六、执行时间估算

| 步骤 | 预估时间 |
|---|---|
| Commit 1-2（删除+HTML归档） | 5 分钟 |
| Commit 3-4（前端页面+文档归档） | 10 分钟 |
| Commit 5（数据重组+软链接） | 15 分钟 |
| Commit 6（文档骨架） | 10 分钟 |
| Commit 7（仓库文件） | 10 分钟 |
| 验证 | 10 分钟 |
| **总计** | **约 1 小时** |