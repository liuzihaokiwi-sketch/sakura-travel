# 关西归档目录（2026-04-24 D40 整理）

> 本目录集中存放历史版本 / 过时计划 / 废弃模板·不再维护·只为追溯。
> 归档自 D40 架构重构（装配四层化 + 字段大瘦身）。

## 子目录清单

| 子目录 | 来源 | 说明 |
|---|---|---|
| `deprecated_pre_d40/` | 原 `japan/kansai/_deprecated/` | D36 前遗留的废弃模板 JSON（核心/半日/一日老格式） |
| `deferred_pre_d40/` | 原 `japan/kansai/_deferred/` | 推迟但保留追溯（abandoned + v1_archive） |
| `legacy_pre_d40/` | 原 `japan/kansai/_legacy/` | D36 前的 circles / route_templates / v1_content / 2026-04-22 misc |
| `templates_old_d36/` | 原 `japan/kansai/templates_old_d36/` | D36 重构前的老模板目录（按主题非按动线） |
| `D36_D37_落地工作计划.md` | 原 `docs/04_操作SOP/` | D36/D37 窗口级工作计划·架构已落·计划过时 |

## 归档准则

以下情况可以进归档·**不要删**（保留追溯价值）：
- 被某个 Dxx 决策废弃的设计·对应的文档/模板
- 某版本的草稿·被后续版本完全取代
- 过时窗口计划（某窗口专用·该窗口已完成）

## 查看时注意

- 归档内容**不反映当前系统状态**
- 任何架构疑问以 [DECISIONS.md](../../../docs/02_历史决策/DECISIONS.md) 最新条目为准
- 不要从归档文件恢复内容到当前系统·先确认没被新架构替代
