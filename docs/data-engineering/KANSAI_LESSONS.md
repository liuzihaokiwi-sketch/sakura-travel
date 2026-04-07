# 关西城市圈踩坑总结 — 下个城市圈防坑清单

> 日期: 2026-04-01
> 城市圈: 关西（京都/大阪/神户/奈良 + 温泉地 + 小城市）
> 用途: 下个城市圈（如广府/东京/北海道）采集时，对照此清单避免重复踩坑

---

## 一、Phase 1 发现池采集

### 坑1: 合并脚本丢强信号

**现象:** 5个来源合并成 merged_final.csv 时，酒店的 OTA 评分（★4.5(4702件)）、
JPY 价格（1泊9300円〜）、Michelin Keys、Forbes stars 等强信号全部被丢弃。
合并后只剩 7 个基础列。

**原因:** 合并脚本只定义了最小公共 schema，来源特有的强信号字段被排除在 fieldnames 之外。

**防坑:**
- 合并脚本的 schema 必须包含所有来源的强信号字段（见 MASTER_GUIDE 3.1 节）
- 不同来源的强信号在不同列名下 → 合并时标准化列名，但不丢数据
- 来源特有字段宁可多带不可丢，后续归一化步骤再处理

### 坑2: cuisine_type 75+ 种混乱

**现象:** 5个来源各用不同语言/粒度的菜系分类。合并后有 75+ 种 cuisine_type，
日文（"ラーメン"）、英文（"ramen"）、中文（"拉面"）混用，同一菜系多个编码。

**原因:** 各来源抓取时直接用了原始平台的分类标签，没有在入库前归一化。

**防坑:**
- **采集时**就映射到标准菜系码，不要等合并时再处理
- 维护 `cuisine_mapping.json`：原始值 → 标准码
- 标准菜系码定义在 DATA_SCHEMA.md，新城市圈先审菜系枚举，缺的先加

### 坑3: 酒店 price_level 被默认值覆盖

**现象:** 380家酒店中 326家（85.8%）标记为 moderate，几乎没有分层。

**原因:** 合并脚本对缺少 price_level 的酒店统一填了默认值 "moderate"，
而多数来源的酒店数据本身没有 price_level 列。

**防坑:**
- 缺少 price_level 时标 null，不填默认值
- 归一化步骤(N4)用回溯的 JPY 价格重新分层
- 如果原始来源有价格嵌在文本里（如 brief_note），合并时正则提取出来

### 坑4: Agent 输出文件在错误目录

**现象:** 所有 Agent 输出的 CSV 文件都落在项目根目录，而不是 `data/kansai_spots/`。

**原因:** Agent prompt 没有指定输出路径，Agent 默认写到 CWD。

**防坑:**
- Agent prompt 中明确指定输出文件的完整路径
- Agent 完成后立即检查文件是否在正确位置
- 在 CITY_CIRCLE_TEMPLATE 的 Phase 1 批次表中写明每个 Agent 的输出路径

### 坑5: Windows GBK 编码与 emoji 冲突

**现象:** Python 脚本中的 emoji（✅, ⚠️, 📊 等）在 Windows 控制台输出时报
`UnicodeEncodeError: 'gbk' codec can't encode character`。

**原因:** Windows 默认 stdout 编码是 GBK，无法显示 emoji。

**防坑:**
- 脚本中不用 emoji，用 ASCII 文本替代: `[ok]` `[warn]` `[pending]` `[NO]`
- 或者在脚本开头设置 `sys.stdout.reconfigure(encoding='utf-8')`
- CSV 文件始终用 `encoding='utf-8'`

---

## 二、Phase 1→2 衔接（数据归一化）

### 坑6: 跳过归一化直接进 Phase 2

**现象:** Phase 1 完成后直接试图跑 selection model，发现 cuisine 混乱、
price_level 没分层、缺 corridor 映射，无法分组排序。

**原因:** 文档中 Phase 1→2 之间没有明确的归一化步骤。

**防坑:**
- **必须执行 MASTER_GUIDE 3.1 节的 N1-N5 归一化步骤**
- 归一化后检查: cuisine 唯一值<40、price_level 分布合理、corridor 非空率>80%
- 这一步是文档化的必经步骤，不是可选的

### 坑7: budget_tier 用 Tabelog 分数推断

**现象:** 计划中用 "tabelog 3.8+ 且非快餐类 → premium" 推断价格层。

**问题:** Tabelog 评分以 3.0 为基准、0.5 为刻度，反映口碑强弱不反映消费层级。
3.8 的拉面店可能人均 1000 日元（mid），3.5 的怀石可能人均 15000（premium）。

**防坑:**
- **budget_tier 是价格层，不是质量层**
- 推断优先级: 已知价格 > Michelin非空→luxury > 菜系场景弱推断 > 保留原值
- 绝不用评分推价格

### 坑8: base_quality_score 做全局 min-max 归一化

**现象:** 用 `(tabelog - 3.39) / (4.65 - 3.39)` 做全局线性归一化。

**问题:** 上下界是数据集依赖的，补一轮 mid/budget 数据后 3.39 就不是最小值了。
而且 Tabelog 3.5 在高端怀石是中等，在甜品咖啡已经很强，全局归一化抹掉了品类差异。

**防坑:**
- **组内 percentile 为主**：在 city × cuisine × budget_tier 分组内算 percentile rank
- raw tabelog_score 保留为辅助字段，不作为 score 本身
- 不做全局归一化，不做跨平台线性换算

### 坑9: 酒店 base_quality 用弱代理变量

**现象:** 酒店 base_quality_score 计划用 "source 数量 + key_features 丰富度" 为主。

**问题:** 来源多不多、字段丰富不丰富是弱信号，而原始数据中已有 OTA 星级、
Michelin Keys、Forbes stars 等强信号，只是在合并时被丢了。

**防坑:**
- 先回溯原始来源文件提取强信号（坑1的修复）
- 酒店 quality: OTA/Keys 评分做主轴，hotel_type/features 只做修正
- 无任何评分的才回退到组内 median

---

## 三、多源采集效率

### 坑10: Tabelog Agent 跑了 6+ 小时

**现象:** Tabelog by-cuisine Agent 从 10+ 个菜系 × 4 个城市逐页抓取，耗时 6+ 小时。

**原因:** Agent 没有超时机制，逐条处理太慢，遇到反爬不会自动跳过。

**防坑:**
- Agent 设 2 小时超时（CITY_CIRCLE_TEMPLATE 已写）
- 超时后有 fallback plan（用已有数据继续，或换小规模抓取策略）
- 成熟类目只取 top N 页不做穷举

### 坑11: 等一个 Agent 阻塞了全流程

**现象:** Tabelog Agent 长时间未完成，其他工作被阻塞。
后来决定不等它，先用已有 4 个来源合并 + 启动补充 Agent。

**防坑:**
- Phase 1 各 Agent 独立运行，不互相依赖
- 每个 Agent 完成后立即合并到候选池
- 合并后立即跑 go/no-go 检查（餐厅>=500、酒店>=350）
- 某个 Agent 超时 → 用已有数据跑 Phase 1.5.5 决策框架

### 坑12: 多源重叠率低于预期

**现象:** 6 个来源中只有 14% 的餐厅出现在 2+ 个来源中（目标 40%）。

**原因:** 不同来源覆盖不同品类（Tabelog 偏中高端、Trip.com 偏游客热门、
Retty 偏本地人），交叉少是正常的。

**防坑:**
- 多源置信度目标从 40% 下调到 20-25% 更现实
- indie_support_score 的价值不在多源重叠，在于补充视角
- Phase 2 的 editorial judgment 比机械计算多源重叠更靠谱

---

## 四、数据质量

### 坑13: CSV schema 不一致导致 DictWriter 报错

**现象:** 酒店数据含 `ranking_info` 和 `hotel_type_guess` 列，不在 DictWriter 的
fieldnames 列表中，报 `ValueError: dict contains fields not in fieldnames`。

**原因:** 不同来源 CSV 的列名不同，合并脚本的 fieldnames 是硬编码的。

**防坑:**
- 合并脚本先扫描所有来源的列名，取并集作为 fieldnames
- 或者用 `extrasaction='ignore'`（但不推荐，可能丢数据）
- 更好: 采集时就统一列名（在 Agent prompt 中指定）

### 坑14: 餐厅数据前后不一致（816 vs 720）

**现象:** 文档说 816 家，实际 merged_final.csv 只有 720 行。

**原因:** 816 是加上 Retty/GURUNAVI 补充后的数字，但补充数据可能没被最终合并脚本纳入，
或者去重后数量下降。

**防坑:**
- 每次合并后立即统计并更新文档
- 合并脚本应输出每个来源的新增/重复计数
- 最终数字以 merged_final.csv 的实际行数为准，不以文档为准

---

## 五、下个城市圈开城前检查清单

在开始新城市圈采集前，逐项确认:

- [ ] 标准菜系码枚举已更新（新菜系先加到 DATA_SCHEMA）
- [ ] cuisine_mapping.json 模板已准备（预填常见日文→标准码映射）
- [ ] 合并脚本 schema 包含所有强信号字段（不丢 OTA 评分/JPY 价格/Keys）
- [ ] Agent prompt 指定了输出文件完整路径和列名规范
- [ ] Agent 有 2 小时超时 + fallback plan
- [ ] 归一化步骤(N1-N5)写入了执行清单，不可跳过
- [ ] budget_tier 推断规则不依赖评分（价格层≠质量层）
- [ ] base_quality_score 用组内 percentile，不做全局 min-max
- [ ] 酒店 price_level 不用默认值覆盖，缺数据标 null
- [ ] Python 脚本不用 emoji（Windows GBK 兼容）
- [ ] go/no-go 检查阈值已定义（每品类最低数量）
- [ ] Phase 1→2 归一化是文档化的必经步骤

---

## 六、关键数字（关西实际值，供下个城市圈参考）

| 指标 | 关西实际值 | 备注 |
|------|-----------|------|
| 发现池-餐厅 | 720 | 目标 700-800，实际 96% |
| 发现池-酒店 | 380 | 目标 500-600，实际 69%（可接受） |
| 发现池-景点 | 143 | 目标 100+，实际 143% |
| 来源数-餐厅 | 6 | 高端/2×mid/Trip-XHS/Tabelog/Retty-GURUNAVI |
| 来源数-酒店 | 4 | 高端/2×mid/Onsen |
| 多源重叠率 | 14% | 远低于 40% 目标，属正常 |
| Tabelog 覆盖率 | 51% | 368/720 有 tabelog_score |
| Michelin 覆盖率 | 5% | 36/720 有 michelin |
| 酒店 OTA 评分覆盖 | ~28% | 仅 mid/budget 来源的 brief_note 中有 |
| Agent 总耗时 | ~17 小时 | 6个 Agent，Tabelog 一个就占 6+ 小时 |
| cuisine_type 归一化前 | 75+ | 归一化后目标 <40 |
| hotel price_level 归一化前 | 85.8% moderate | 归一化后应合理分布 |

---

## 七、改进后的理想流程（对照 CITY_CIRCLE_TEMPLATE）

```
Phase 0: 城市级资产（一次性）
  taxonomy.json / corridor_definitions.json / cuisine_mapping.json
  ↓
Phase 1: 发现（Agent 批量，每 Agent 有超时+指定输出路径+列名规范）
  每个 Agent 完成后立即合并 + go/no-go 检查
  ↓
Phase 1→2 归一化（N1-N5，纯 Python，必做不可跳过）
  检查点: cuisine <40 种, price_level 分布合理, corridor 非空 >80%
  ↓
Phase 2A: 纯 Python 预处理（base_quality 组内 percentile + slot 分组）
  ↓
Phase 2B: Sonnet 批量结构化短证据（仅对 selected + borderline）
  ↓
Phase 2C: Opus 审关键条目（S/A + 边界 + risk + slot冲突）
  ↓
Phase 2D: selection_ledger.json
  ↓
Phase 2E: GUIDE_*.md（审稿层）
  ↓
Phase 3: 结构化 + 导入 DB + 端到端测试
```
