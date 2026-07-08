---
name: travel-ai-land-the-plane
description: Session-close / wrap-up checklist for the travel-ai repo. Use at the END of any work session, BEFORE claiming a task is done — run the harness and paste its full output, delta-update the handoff four fields, sink learnings to the right layer, and emit the next-session prompt. A forced anti-shortcut loop for unreliable models. Triggers - 收尾, 交付, land the plane, wrap up, finish, 结束会话, 完成, close session.
---

# Travel AI · 收尾交付（Land the Plane）

一条**防偷懒的强制闭环**。模型不稳时，收尾最容易被跳过或造假（不跑就声称跑过、报喜不报忧、假装修了没修）。逐条过，每条留下可检查的证明，不许跳、不许口头带过。

## 何时用

任何工作会话的**最后一件事**，在你准备说「做完了 / 已完成」之前。切片没做完也走一遍（在阻塞字段如实写卡点）。

## 硬闸（逐条执行，每条留证明）

### 1. Harness 闸——跑，并贴完整输出

- 按 `AGENTS.md` 验证速查表 / `docs/agents/harness.md` 选对应 harness：`check_workflow.ps1`（工作流健康），或 `python scripts/validate_{entity,restaurants,hotels,template}.py <file_or_dir>`（数据/模板）。研究类走 evidence ledger。
- **把命令完整输出贴进汇报**，含 `Summary: N failed` 那行。
- 🚫 口头声称「跑过了/应该没问题」而不贴输出；改 validator 白名单或砍字段来「过检」；`--force` / `--no-verify` 静默跳过。
- FAIL 就如实报，并判断是实现 / 输入 / harness / 需求哪类问题。

### 2. Handoff delta——只改四字段 + 盖日期

- 打开当前 `_tmp/handoff/CURRENT_*`，只更新：仓库状态 / 进度 / 阻塞 / 下一步，盖当天日期。
- 🚫 整篇重写；漏盖日期；把描述性过程灌进去。

### 3. 沉淀分层——经验归到正确的层

- two-strikes：同一教训第二次出现才升格为规则；第一次只修不记。
- 去向：跨 AI 规则 → 仓库 `AGENTS.md` / skill / SOP；状态 → handoff；单边操作习惯/用户偏好 → memory；证据 → `research/`。
- 🚫 把跨 AI 规则只写进单边 memory（正本必须进仓库）；顺手重写整份规则文档（只 delta 单条）。

### 4. 外化副产品扫描

- 本会话有没有挖到可发社媒的干货（冷知识 / 避坑 / 反直觉 / 幕后严谨）？有就沉淀到 `marketing/{region}/素材库.md`，标可发形式。见 `AGENTS.md`「沉淀去向」。

### 5. 下一会话启动 prompt

- 一段话：接哪条线、卡在哪、下一步做什么，让下个会话零翻找开工。

### 6. 三行汇报——只报需拍板的

- 做了什么 / 怎么验证（引用第 1 步输出）/ 留下什么可复用经验。结论 + 关键数字 + 卡点，不复述推导。

## 写入验证（本项目特有·血泪教训）

Write/Edit 偶发「回执成功但文件没落地」（工具降级 / malformed 调用）。**收尾前必须 ls / grep 抽验关键交付物真在磁盘上**，别信回执就声称完成。

## 偷懒信号（自查镜子）

- 想写「validator 应该没问题」→ 停，去真跑，贴输出。
- 想整篇重写 handoff → 停，只 delta 四字段。
- 某步失败 / 被限速 / 中断，想略过不提 → 停，如实写进阻塞。
- 想说「已修复」但无 harness 证明 → 停，要么补证明，要么改说「待验证」。

## 范例：一次合格的收尾

```markdown
## 验证（第 1 闸·贴完整输出）
$ powershell ./scripts/agent/check_workflow.ps1
  Summary: 0 failed, 6 warnings
$ python scripts/validate_entity.py japan/kansai/entities
  合计: 155 entities, 0 errors  -> exit 0

## Handoff delta（第 2 闸·四字段 + 日期）
- 仓库状态：land-the-plane 重建、pre-commit hook 落地
- 进度：check_workflow 0 failed
- 阻塞：无
- 下一步：skill examples 分层
更新时间：2026-07-09

## 三行汇报（第 6 闸）
- 做了什么：修复 dangling ref + 建强制闸
- 怎么验证：check_workflow 0 failed（已贴）
- 可复用经验：Write 回执≠落地，收尾必须 ls 抽验
```

## 完成判据

六闸都留下可检查痕迹（贴了输出、handoff 有当天 delta、该沉淀的进了对应文件、关键交付物已 ls 抽验、有启动 prompt、三行汇报），才算落地。缺一条就是还在滑行。
