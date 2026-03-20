# 安全重构与双文档体系建设 — 任务清单

> 目标：项目体检 → 废弃识别 → 结构优化 → 双文档体系 → Git治理 → 安全上传
> 原则：先识别 → 再归档 → 验证后删除。绝不盲删。

---

## 任务总览

| # | 任务 | 产出文件 | 依赖 | 状态 |
|---|---|---|---|---|
| R1 | 全项目体检（文件盘点+分类+标签） | `r1-inventory.md` | 无 | [x] |
| R2 | 废弃代码与文档识别（引用扫描） | `r2-deprecation-candidates.md` | R1 | [x] |
| R3 | 项目结构优化方案 | `r3-structure-proposal.md` | R1+R2 | [x] |
| R4 | 双文档体系设计 | `r4-docs-design.md` | R3 | [x] |
| R5 | README/CONTRIBUTING/CODEOWNERS/.gitignore | `r5-repo-files.md` | R3 | [x] |
| R6 | Git上传前安全检查 | `r6-security-checklist.md` | R1 | [x] |
| R7 | 变更执行策略（分支/提交/回滚） | `r7-execution-plan.md` | R2+R3 | [x] |
| R8 | 最终交付物汇总 | `r8-summary.md` | 全部 | [x] |

---

## 执行顺序

```
R1 全项目体检（必须先做，是一切的基础）
  ↓
R2 废弃识别 + R6 安全检查（可并行，都依赖R1）
  ↓
R3 结构优化（需要R1+R2的结论）
  ↓
R4 双文档设计 + R5 仓库文件（可并行，都依赖R3）
  ↓
R7 执行策略（需要R2+R3）
  ↓
R8 最终汇总
```

---

## R1. 全项目体检

**产出**：`r1-inventory.md`

**范围**：项目根目录下所有文件和目录

**对每个文件/目录输出**：
- 路径
- 类型（代码/文档/配置/模板/静态资源/脚本/数据/测试/构建产物/临时文件）
- 最近作用判断
- 是否被引用（import/require/配置/路由/模板）
- 是否有明显重复
- 是否疑似废弃
- 推荐动作：keep / refactor / archive / delete_candidate / unsafe_to_touch

**方法**：
1. 递归列出所有文件
2. 按目录分组扫描
3. 对每个目录判断用途
4. 对可疑文件做引用扫描（grep import/require/include）

---

## R2. 废弃代码与文档识别

**产出**：`r2-deprecation-candidates.md`

**识别方法**：
- import/require/include 扫描
- CLI/脚本入口扫描
- 配置引用扫描
- 路由/页面引用扫描（Next.js app router）
- 文档互链扫描
- 模板/静态资源引用扫描

**输出 4 张表**：
1. 删除候选清单（确认无引用）
2. 归档候选清单（疑似废弃但有不确定性）
3. 高风险不可动清单（核心文件/有复杂引用）
4. 重复内容合并建议

---

## R3. 项目结构优化方案

**产出**：`r3-structure-proposal.md`

**输出**：
- 建议的新目录结构
- 每个目录的职责说明
- 从当前结构到新结构的迁移映射
- 哪些文件不动/哪些需要移动/哪些需要合并

---

## R4. 双文档体系设计

**产出**：`r4-docs-design.md`

**两套文档**：
- docs-human/（给人看：关键路径、快速上手、架构、风险）
- docs-ai/（给AI看：索引、模块注册、依赖图、入口点、schema）

**每个文档输出**：目标/目标读者/内容大纲/格式建议

---

## R5. 仓库治理文件

**产出**：`r5-repo-files.md`

**内容**：
- README.md 建议内容
- CONTRIBUTING.md 建议内容
- CODEOWNERS 建议内容
- .gitignore 建议内容
- .env.example 建议内容

---

## R6. Git上传前安全检查

**产出**：`r6-security-checklist.md`

**检查项**：
- secrets/API key/token 扫描
- .env 文件检查
- 大文件检查（>10MB）
- 无效/临时文件检查
- 历史中疑似敏感信息
- 提交信息规范

---

## R7. 变更执行策略

**产出**：`r7-execution-plan.md`

**内容**：
- 推荐分支名
- 提交粒度和顺序
- PR 结构
- 每步验证方式
- 回滚策略

---

## R8. 最终交付物汇总

**产出**：`r8-summary.md`

**汇总所有产出的核心结论**