# 当前状态

> 最后更新: 2026-03-30

---

## 系统成熟度

| 模块 | 状态 | 说明 |
|------|------|------|
| 表单采集 (Intake) | **可用** | DetailForm + submissions 完整 |
| 归一化 (Normalize) | **可用** | layer2_contract + profile tags |
| 城市圈决策链 | **可用** | 10 步管线跑通，北海道端到端验证通过 |
| 页面生成 | **可用** | planning_output 直通，17 种页型 |
| PDF 渲染 | **基本可用** | 能生成 PDF，但内容不够饱满（每天只 1-3 个活动） |
| 质量门控 | **可用** | 规则引擎 + 离线评测 + 多模型评审 |
| 管理后台 | **可用** | 订单/实体 CRUD/配置/trace/review + 侧边栏/仪表板/trust_status |
| 数据采集 | **基本可用** | Google Places + Tabelog + 携程/大众点评爬虫已建 |
| 用户前端 | **暂停** | 骨架在，前期不上线，抖音表单为主入口 |

---

## 当前聚焦：V1.0 北海道

**目标：** 生成一本内容饱满的北海道 5 天手账本 PDF，全部使用真实数据。

**执行策略：** 3 个检查点，每个做完审视再继续。详见 [IMPLEMENTATION_TASKS.md](IMPLEMENTATION_TASKS.md)。

### 检查点 1：数据地基 ← 当前阶段

| 任务 | 状态 | 负责 |
|------|------|------|
| A1 数据源注册中心 | 进行中 | Sonnet |
| A2 清除 AI 数据 | 进行中 | Sonnet |
| A3 前置约束数据表 | 待开始 | Sonnet |
| B1 Tabelog 全量拉取 | 进行中 | Opus |
| B2 Google Places 批量 | 待开始 | Sonnet |
| B3 Japan Guide 爬虫 | 待开始 | Sonnet |
| B4 攻略扫描 | 待开始 | Sonnet |
| B5 城市特色菜系 | 待开始 | Sonnet |

### 检查点 2：内容加工 + 片段（检查点 1 完成后）

评价维度提取、day_fragment 编排、距离矩阵

### 检查点 3：模板 + PDF（检查点 2 完成后）

行程模板组装、PDF 渲染完善、端到端验证

---

## 数据现状

| 指标 | 数值 |
|------|------|
| 实体总数 | 481 |
| 真实数据 (unverified) | 258 |
| AI 生成 (ai_generated) | 208（待标记 inactive） |
| 存疑 (suspicious) | 15 |
| 活动簇 | 35 |
| 角色绑定 | 89 |
| 北海道城市覆盖 | 10/10 |

**目标：** 札幌 300+ 真实实体 → 北海道总计 1500-2000

---

## 已修复的关键问题（本次会话）

- generate_trip 端到端跑通（修 12+ 个 Sonnet 遗留 bug）
- 事务管理根因修复（live_risk_monitor SQL 列名错误）
- 爬虫体系建立（Google Places / 携程 / 大众点评）
- 去重引擎（Levenshtein + 地理距离）
- trust_status 数据可信度标记
- 管理后台升级（侧边栏/仪表板/审核）

---

## 核心设计文档

所有架构设计整合在 [SYSTEM_DESIGN_V2.md](SYSTEM_DESIGN_V2.md) 中。
旧文档已归档到 `_archive/`。
