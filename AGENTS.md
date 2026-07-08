# Travel AI · 项目层入口

> 通用工作流（开工/收尾仪式、切片纪律、Task Packet、沉淀规则）在全局层，两端自动加载（Codex: `~/.codex/AGENTS.md`；Claude Code: `~/.claude/CLAUDE.md` import 同一份）。
> 本文件只放 travel-ai 项目特有的事实和规则，预算 ≤120 行。流程细节住在 `.agents/skills/` 和 `docs/`，按需读取。

## 项目一句话

付费旅行手账本（¥298 国内 / ¥348 国外）：纸质本 + 贴纸 DIY 包。
口号：**一本为你写好的旅行手账——旅行时带着走·旅行后留作回忆。**（所有用户可见文字的语气基线）

## 判断锚（灰色判断回到这里）

用户付费买的是「**有人替我想过 + 敢对结果负责**」的确定感。我们卖品质 + 确定性 + 独立（不和商家合作、不收恰饭）。
质量标准：**真实旅行顾问看到会不会点头·不点头就重做。**

## Handoff 入口（开工仪式第 1 步读这里）

```text
_tmp/handoff/CURRENT_README.md
```

只进一条工作线，只读一个 `CURRENT_*` 中断点 + 它点名的 ≤5 份必读。

## 6 条红线

1. **数据真实性**：没搜过的不写成事实，推断必须标「未核实」。可信度分级：`verified` / `cross_checked` / `single_source` / `ai_generated`（不可上生产）。
2. **修根因**，不打补丁绕过问题（不加 force 跳过、不改断言放水）。
3. **业务数据不硬编码**：将来可能变的，从配置文件或 DB 读。
4. **字段变更先改 `docs/项目核心/字段权威.md`**，再改其他，禁止反向。
5. **不假装修了实际没修**。
6. **import 全部放模块顶部**。

## 路由

| 任务 | 入口 |
|---|---|
| 内容装配 / 路线研究 / 数据池 | `_tmp/handoff/CURRENT_1_*` + skill `travel-ai-{research,content-assembly,data-collection}` |
| 系统组合渲染（web/app/render） | `_tmp/handoff/CURRENT_2_*` + skill `handbook-system-rendering` |
| 复杂视觉生产（地图/大通页/AI图） | `_tmp/handoff/CURRENT_3_*` + skill `handbook-{visual-production,image-assets}` |
| 营销运营 | skill `travel-ai-marketing` + `marketing/` |
| 改架构 / 字段 | `docs/项目核心/当前生效决策.md` + `字段权威.md` |
| 改代码 | `docs/项目核心/数据流.md`（注意 app/ 部分旧 import 路径失效） |

项目 skills 在 `.agents/skills/`（Agent Skills 开放标准，Codex 与 Claude Code 共用同一份）。

## 验证（harness 速查）

| 对象 | 命令 |
|---|---|
| entity | `python scripts/validate_entity.py` |
| 餐厅 + stops | `python scripts/validate_restaurants.py` |
| 酒店 | `python scripts/validate_hotels.py` |
| 模板 | `python scripts/validate_template.py` |
| 工作流健康 | `./scripts/agent/check_workflow.ps1` |

详表见 `docs/agents/harness.md`；研究类按 `docs/agents/research.md` 做 evidence ledger（事实/体验/判断/偏好/未核实分开）。

## 沉淀去向（项目特有）

- 传播素材（冷知识/避坑/反直觉结论/幕后严谨过程）→ `marketing/{region}/素材库.md`。**任何工作线（研究/装配/采数/视觉）中发现即时沉淀，不等收尾**；顺手标一句可发形式（图文/口播/速查/客服答疑）；会话收尾兜底扫一遍有没有漏。原则：一次采集喂多出口（产品 + 社媒 + 答疑），研究/工作的强制副产品，不是事后另起炉灶。
- 研究证据/冲突/过程 → `research/`；正式结论回写对象目录（japan/ europe/ …）。
- 跨 AI 的项目规则 → 本文件或对应 skill/SOP；状态 → handoff。

## 项目工作方式

- 质量优先：宁可少覆盖，不降低质量。当专家自主判断，小事直接做，动产品形态才问。
- **极简姿态（ponytail）**：写代码前爬懒惰阶梯——①需要存在吗（YAGNI，不需要就不写）②标准库/平台原生/已装依赖能做就用③一行能写不写十行④才轮到最小可用实现。懒但不失职：信任边界校验、数据丢失、安全、无障碍永不砍。走捷径必须留痕标升级路径。
- 用户可见文案中文主写，日文必要时括号补充。
- Anthropic API 不做高并发（会限速）；高并发用阿里云 qwen-max。
- 批量看图先建缩略图 review board：`.\.venv\Scripts\python.exe .\scripts\build_image_review_board.py <dir> --out-dir _tmp\<task>-image-review --recursive --max-edge 420 --quality 72`，不直接开全尺寸 PNG。
- 格式化：`ruff check --fix app/ scripts/ && ruff format app/ scripts/`

## 工具

- **opencli**（小红书搜索/下载/正文）：用法见 `docs/操作SOP/opencli使用.md`。note/download 必须串行；URL 带 `xsec_token`；判断爆款看 collects > likes。
- **数据源优先级**：P0 官方/权威 → P1 中国用户源（小红书/携程）→ P2 参考 → P3 AI 兜底（不用于事实）。
