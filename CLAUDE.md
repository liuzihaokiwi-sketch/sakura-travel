# 项目总入口(每次会话必读)

> AI 进入这个项目第一份读的文档。2026-04-20 更新,瘦身到入口+导航,详情引用 docs/。

## 一、5 秒理解

- **做什么**:付费旅行手账本,¥298 国内/¥348 国外,纸质本 + 贴纸 DIY 包
- **核心价值**:专家策展(AI 辅助) → 中国游客"照着走就对了"
- **当前阶段**:关西样板间,早春京都模板精修中
- **产品精髓**:一本日记 ≠ 攻略;像懂当地的朋友在耳边讲

**质量标准**:真实日本旅行顾问看到会不会点头。不点头就重做。

---

## 二、工作类型导航(按你要做什么查入口)

### 🟢 做关西模板(当前主线)

**必读**:
- `docs/04_操作SOP/模板写作.md` — Part 0 策展 + Part 1 搜索 + Part 2 字段 + Part B 自检
- `japan/kansai/产品原则.md` — 关西餐饮/酒店/密度/退化/7 条化学反应
- `japan/kansai/research/insights.md` — 关西城市洞察

**真实模板样板**:`japan/kansai/templates/common/kyo_arashiyama_core_full.json`（D36 改造前的版本，改造后的 demo 待 P0 工作产出）

**🔗 联动**:挖到小众视角/10% 惊喜/本地冷知识 → `marketing/japan/kansai/素材库.md`

### 🟢 做调研

**必读**:`docs/04_操作SOP/研究方法.md` — 5 阶段 + 7 问 + MTE 框架

**🔗 联动**:opencli 搜到爆款 → `marketing/{地区}/爆款参考.md`;本地视角/痛点 → 素材库

### 🟢 做数据采集

**必读**:`docs/04_操作SOP/数据采集.md` — AI 不写事实 + 三轴判断 + 可信度分级

**🔗 联动**:带传播性的冷知识/避坑 → 素材库

### 🟡 做运营内容

**必读**:`marketing/strategy.md` + `marketing/japan/kansai/素材库.md` + `爆款参考.md`

### 🟡 改架构 / 字段变更

**必读**:`docs/02_历史决策/DECISIONS.md` + `DEFERRED.md` + `docs/03_数据契约/SCHEMA.md`

**硬规**:字段变更**先改 SCHEMA.md**,再改其他(SCHEMA 是入口不是出口)

### 🟡 改代码

**必读**:`docs/03_数据契约/数据流.md` + `docs/02_历史决策/DECISIONS.md`

**注意**:2026-04-20 仓库重构后,app/ 里 import 路径对老 `content/kansai/` `data/events/` 失效,当前代码跑不起来。改代码时要同步路径。

### 🟡 客服/业务流程

**必读**:`docs/03_数据契约/业务流.md` + `docs/05_情境手册/客服应对.md`

---

## 三、6 条绝对红线(任何工作都不能破)

### 1. 数据真实性(第一红线)

适用:所有事实性内容——JSON 字段、文档元数据、素材库条目。

**可信度分级**:`verified`(2+ P0/P1 交叉) / `cross_checked`(1 P0/P1+其他) / `single_source`(仅 P2) / `ai_generated`(**不可上生产**)

**自检**:写"事实"前问"真搜过的还是推断?"——推断的去真搜 / 或标"未核实",**绝不把推断写成事实**。

**反例**:给餐厅填 `rating=4.3` 没搜过 Tabelog;写博主站"coverage=关西"没访问过;写"WebFetch 可用"没试过。

### 2. 不许打补丁绕过问题

修根因,不要 workaround。
- DB 连接失败 → 修连接,不加 `force_ai=True` 跳过
- 测试失败 → `xfail(strict=True)` 追踪,不改断言放水
- party_type 不识别 → 在定义本身携带属性,不在消费端列举

### 3. 不许硬编码业务数据

配置数据(城市圈映射/阈值/价格上限/人群分类)必须从配置文件或 DB 读。
**判断**:将来可能变的,不该在代码里。

### 4. 字段变更必须先改 SCHEMA.md

唯一权威源是 `docs/03_数据契约/SCHEMA.md`。顺序:SCHEMA → 写作指引 → DECISIONS。
**禁止反向**(先加字段再改 SCHEMA)。

### 5. 不许假装修了实际没修

S/A 和 B/C 两分支写不同注释但做相同事(都 continue) → 逻辑相同写一个分支,不用注释掩盖。

### 6. 不许在函数体内重复 import

所有 import 放模块顶部。

---

## 四、产品第一性原理(灰色判断时的锚)

### 模板精髓(用户视角)

> **① 这不是一本攻略,是为我量身准备的一本日记。**
>
> **② 每翻一页,像有个懂当地的朋友在耳边跟我讲这段旅行。**

### 数据精髓

> **① 用户照着这条去现场,一切和本子一样。**
>
> **② 用户觉得"这家只有懂当地的人才会挑出来"。**

### 研究精髓

> **① 用户翻开觉得"懂这个地方"。**
>
> **② 走一趟回来觉得"我好像真的懂了这个国家"。**

所有 SOP 都是这些精髓的展开。灰色判断回到这几句。

---

## 五、关键目录速查

```
travel-ai/
├── japan/kansai/       ← 关西工作区(主战场,2026-04-22 D36 重构)
│   ├── templates/{common,early_spring,sakura,...}/  ← 98 个模板按 8 季节分子目录
│   ├── facts/          ← entities + restaurants + hotels + live_facts
│   ├── assembly/       ← 装配规则 markdown(模板装配/餐厅装配/酒店装配)
│   ├── events/         ← 事件数据(待迁 markdown)
│   ├── 当前状态.md     ← 换窗口先读这个
│   ├── 产品原则.md     ← 关西哲学
│   └── 这是什么.md     ← 关西定位
├── china/ europe/
├── marketing/          ← 运营(素材库/爆款参考在这)
├── docs/
│   ├── 01_项目定位/    ← 判断标准
│   ├── 02_历史决策/    ← D36 (2026-04-22 字段大瘦身)
│   ├── 03_数据契约/    ← SCHEMA(字段定稿)
│   ├── 04_操作SOP/     ← 模板/数据/研究 SOP
│   └── 05_情境手册/    ← 客服等
├── app/ web/ data/
└── _deprecated/        ← 废弃兜底
```

---

## 六、工作方式(精简速记)

- **质量优先,简洁高效**:宁可少覆盖,不降低质量
- **信息整合 + 好的思考**:参考市面最佳(小红书/Black Tomato/Tabelog/BRUTUS),不自己发明
- **当专家自主判断**:小事直接做,动产品形态时才问
- **有问题一次性提 3 个**,不逐个确认
- **Agent ≤2 并发**,简单用 haiku/sonnet,质量判断用 opus
- **Anthropic API 不高并发**(会限速),高并发用阿里云 qwen-max
- **边做边沉淀素材** → marketing/ 素材库(产品护城河)

详细工作方式见 `MEMORY.md` 的 feedback 类笔记。

---

## 七、当前状态

关西进展 + 下一窗口接什么 → **读 `japan/kansai/当前状态.md`**。

**最近重要决策**(详见 DECISIONS.md):
- D32 关西 v2 四层架构
- D33 季节目录 10→7 档
- D34 仓库按"大洲/圈"聚合
- D35 docs/ 5 类重构

---

## 八、工具速查

- **opencli**(小红书搜索/下载/正文):完整用法见 `docs/04_操作SOP/opencli使用.md`
  - 搜索:`cd D:/projects/projects/travel-ai/opencli-main && node dist/main.js xiaohongshu search "xxx" --limit 10 --format md`
  - 下载图/视频:`node dist/main.js xiaohongshu download "完整URL带xsec_token" --output "D:/tmp/xhs_refs/..."`
  - 读正文:`node dist/main.js xiaohongshu note "完整URL" --format md`
  - ⚠️ note/download **串行跑**(并发会串数据);URL 必须带 `xsec_token`;judging 爆款看 **collects > likes**
- **xhs 防盗链**:Referer `xiaohongshu.com` + iPhone UA(见 memory)
- **数据源优先级**:P0 官方/权威 → P1 中国用户源(小红书/携程)→ P2 参考 → P3 AI 兜底(不用于事实)

---

## 九、Git / 代码规范(要改代码时看)

- 不主动 commit/push/force push/amend,除非用户明确要求
- commit message 写"为什么改"而不是"改了什么"
- 不加用户没要求的功能、重构、文档注释
- Bug 修复不"顺便"清理周围代码
- 不留死代码 / 注释掉的代码 / `# removed`

格式化:`ruff check --fix app/ scripts/ && ruff format app/ scripts/`

---

## 十、获取帮助

- `/help`(Claude Code)
- 反馈:https://github.com/anthropics/claude-code/issues
