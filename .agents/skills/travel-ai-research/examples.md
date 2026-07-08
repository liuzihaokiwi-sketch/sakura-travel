# Research · 真实范例

> 全部指向仓库真实研究产物（2026-07-09 核）。研究口径以 `docs/操作SOP/上线前/研究方法.md` 与各目录 `*_STANDARD.md` 为准。

## 证据落位：两种真实约定

| 区域 | 证据目录 | 索引 |
|---|---|---|
| 关西（成熟区） | `research/japan/kansai/routes/{route_id}/`、`seasonal/`、`region/` | 目录内 `ROUTE_RESEARCH_STANDARD.md` 定评分口径 |
| 意大利（新区） | `europe/italy/_research/` | `europe/italy/_research/_INDEX.md` |

原则不变：**证据/过程/冲突进 research 目录，最终结论回写正式对象**（`动线说明.md` / 数据池 / `marketing/`）。证据先落最窄可复用位置，别一上来写进产品层。

## 范例 1：研究沉淀（真实·关西首次 Top20）

`research/japan/kansai/routes/kansai_first_timer_top10_regular_20260504.md` 的开头就把三件事钉死：

```markdown
Date: 2026-05-04
Status: research deposit only. This is a ranked research conclusion,
        not a plan, template, or 动线说明.md change.

## 评分方法（总分 100）
| 维度 | 分值 |
| 核心体验好玩 / 记忆密度 | 35 |
| 首次关西代表性 | 25 |
| 7-9 天游程装配价值 | 15 |
| 常规季稳定性 | 15 |
| 中文游客反馈与踩坑风险 | 10 |

### Source rules
- Official/factual sources only support hours, access, ticketing, rules.
- Deep sources support route logic and comparative value.
```

可复制的动作：① 顶部标 `research deposit only`，防止研究被误当产品改动；② 先写显式评分维度再排序，判断可追溯；③ 事实源与体验源分开引用（研究方法铁律）。

## 范例 2：证据 → 可执行结论（真实·意大利硬预约总表）

`europe/italy/_research/italy_20260920_hard_reservation_master_20260708.md` 把「哪天放票」这类易腐事实做成**行动日历**（唯一执行入口）：

```markdown
> 可信度分级: verified（官方页面直接确认）/ cross_checked（≥2 独立源）/ single_source / 未核实

| 日期 | 动作 | 紧急度 |
| **7/31 罗马 00:00** | 梵蒂冈 9/29 早场抢票 tickets.museivaticani.va，60 天窗口分钟级售罄 | ⚡⚡ |
| **8/11** | 圣马可 9/25 放票（45 天窗口）tickets.basilicasanmarco.it | ⚡⚡ |
| **8/31** | 斗兽场 9/30 放票（提前 30 天）ticketing.colosseo.it | ⚡⚡ |
```

可复制的动作：① 每条带**官方 owner URL + 放票窗口机制 + 核查日**，口径注明「以当日官方页面为准」；② 用 `可信度分级` 标注每条证据强度（这是**研究散文里的 ledger**，不是数据池 per-record 字段）；③ 把结论压成一张「按日期做」的行动表，读者零推导执行。

## 范例 3：opencli 取小红书证据（真实命令·串行）

```powershell
cd D:/projects/projects/travel-ai/opencli-main
node dist/main.js xiaohongshu search "关西 红叶 避坑" --limit 10 --format md
node dist/main.js xiaohongshu note "完整URL含xsec_token" --format md
```

硬规则：`note`/`download`/`dump-state` **串行**（并发会串输出）；URL 必须带 `xsec_token`；判断爆款看 `collects > likes`（长期意向强于点赞）；小红书是**体验/趋势证据，不是权威事实源**。下载媒体归 `research/` 或 `references/`，绝不直接进 `web/public`。

## 收尾自检（研究线专用）

- [ ] 证据文件路径存在且以研究对象命名（`ls` 抽验，别信 Write 回执）。
- [ ] 当前事实有源标注或标「未核实」；事实源与体验源分开记。
- [ ] 最终结论已回写正式对象，不是只躺在 `research/`。
- [ ] 挖到的冷知识/避坑/反直觉 → `marketing/japan/kansai/素材库.md`（研究的强制副产品）。
