# 工程师 B 开工提示词（D40 动线说明 md 全面改造 + 引用路径全局修复）

> 复制以下内容到新 Claude Code 窗口（opus·判断量大）启动。
> 工作范围：`templates/**/*.md` + `assembly/**/*.md` + `japan/kansai/产品原则.md` + 引用路径全局修复·**不动任何 JSON 文件**。
> 预计工作量：一个窗口跑满。和工程师 A 并行·零文件冲突。

---

## 开工前必读

按顺序读这 5 份：
1. [CLAUDE.md](../../CLAUDE.md)
2. [docs/02_历史决策/DECISIONS.md](../02_历史决策/DECISIONS.md) D39 + D40
3. [docs/03_数据契约/SCHEMA.md](../03_数据契约/SCHEMA.md) §1.1-§1.3
4. [japan/kansai/plans/写作规范.md](../../japan/kansai/plans/写作规范.md) 完整
5. [japan/kansai/assembly/engine.md](../../japan/kansai/assembly/engine.md) 完整
6. [japan/kansai/_archive/templates_花名册_pre_d40.md](../../japan/kansai/_archive/templates_花名册_pre_d40.md)（老花名册·1400 行·做参考不用全读）

**目标**：按 D40 新架构把动线层的 md 文档整理干净·方案作者能用·引用路径全通。

---

## 任务清单（7 项·全部完成才交付）

### 1. 25 个子目录 index.md 重命名为「动线说明.md」+ 瘦身

**清单**（25 个）：
- `templates/kyoto/arashiyama/index.md`
- `templates/kyoto/higashiyama/index.md`
- `templates/kyoto/fushimi/index.md`
- `templates/kyoto/kitayama/index.md`
- `templates/kyoto/okazaki_tetsugaku/index.md`
- `templates/kyoto/nijo/index.md`
- `templates/kyoto/kurama_kibune/index.md`
- `templates/kyoto/takao/index.md`
- `templates/kyoto/uji/index.md`
- `templates/kyoto/half_day/index.md`
- `templates/osaka/namba/index.md`
- `templates/osaka/osakajo/index.md`
- `templates/osaka/kaiyukan/index.md`
- `templates/osaka/tennoji/index.md`
- `templates/osaka/nakazakicho/index.md`
- `templates/osaka/expo/index.md`
- `templates/osaka/usj/index.md`
- `templates/osaka/half_day/index.md`
- `templates/other/nara/index.md`
- `templates/other/kobe/index.md`
- `templates/other/arima/index.md`
- `templates/other/koyasan/index.md`
- `templates/other/kinosaki/index.md`
- `templates/other/yoshino/index.md`
- `templates/other/half_day/index.md`

**操作**：
- 每个 `index.md` 重命名为 `动线说明.md`（`git mv` 保留历史·不是删旧建新）
- 瘦身到**动线层必要信息**·复杂动线 30-50 行·简单动线 15-25 行·按实际需要不硬凑

**动线说明.md 新模板**（参考结构·可按动线特点调整）：

```markdown
# {动线名} 动线说明

## 定位
（一句话·这条动线是什么·比其他动线独特在哪）

## 精髓 / 灵魂
（3-5 行·核心体验逻辑·情绪弧线·peak-end 在哪）

## 适合谁
（文字化描述·不用数字公式）
- 情侣：很合适 / 一般 / 不推荐（一句话说原因）
- 朋友：...
- 家庭：...

## 变体差异（给方案作者挑候选用·不重复 JSON 字段）
（一张 5-10 行的表·列 5-10 个变体·每行 2-3 词说核心差异）

## fixed_early / deep_stay 候选（如适用）
（本动线相关的 pace_type 候选·复用 plans/写作规范.md 总库·只列本动线的 1-3 个）

## 跨动线规则（可选·只写本动线相关的）
（如「与 kyoto/higashiyama 地理对称·常一天岚山+一天东山」「与 kyoto/okazaki_tetsugaku 红叶季不同日」）

## 硬约束
（交通时效/班次/预约等动线层硬性限制·旅馆难约/班次少/冬季停运 等）
```

**删除内容**（原 index.md 有但不该留）：
- ❌ 变体清单逐条枚举（变体内容在 JSON·方案作者读 JSON 不读 index）
- ❌ 装配打分公式（已删·D40）
- ❌ 同动线互斥规则（方案作者在候选列表里写）
- ❌ night_options / 夜模块挂载字段（方案作者在方案骨架里写）
- ❌ min_days / selectable_tag（方案层决定）
- ❌ 「day_type 枚举表」这种引用老字段的内容

**保留 / 精简**：
- ✅ 动线定位叙事
- ✅ 变体之间的灵魂差异（不是字段清单·是精简叙事）
- ✅ 跨动线规则（属于本动线的部分·关西 7 条的展开）
- ✅ 硬约束（班次/预约/冬季停运）

### 2. 每个动线说明.md 加 pace_type 候选信息（如适用）

参考 `plans/写作规范.md §四` 候选总库·各动线有本动线相关的 1-3 个候选·加到动线说明.md。

**有内容加的动线**：
- `arashiyama` → fixed_early: [岚山 5 出片]·deep_stay onsen: [岚山 8]·deep_stay deep_local: [岚山 9·岚山 10]
- `higashiyama` → fixed_early: [清水独享·樱花/红叶/常年 3 个待建]
- `fushimi` → fixed_early: [无人千本鸟居 1 个待建]
- `arima` → deep_stay onsen: [有马 1·有马 3]
- `kinosaki` → deep_stay onsen: [城崎 1]
- `koyasan` → deep_stay deep_local: [高野山 1]
- `takao` → deep_stay onsen: [高雄 2 候选]

**其他动线不加这一段**（无候选）。

### 3. arashiyama/transport.md 去 fixed_early 标签

- 扫 `templates/kyoto/arashiyama/transport.md`·去掉所有「fixed_early」关键字
- 保留 5 号模板的「首班 JR 5:55·门到门 35 分钟」这类**实际交通数据**（不是标签）
- 按 D39/D40 改写说明：岚山 5 是「愿意为出片早起一次」的用户用·不是强制

### 4. higashiyama / fushimi 动线说明.md 加「fixed_early 候选待建」段

plans/写作规范.md 列了 4 个待建候选（清水独享樱花/红叶/常年 + 伏见稻荷无人千本鸟居）。

- `higashiyama/动线说明.md` 加一段：「fixed_early 候选待建：清水独享樱花版（3/28-4/5）/ 红叶版（11/15-12/5）/ 常年版。四要素齐全·下轮窗口按 plans/写作规范.md §四 建」
- `fushimi/动线说明.md` 加一段：「fixed_early 候选待建：伏见稻荷无人千本鸟居（常年）。7:00 前千本鸟居独走 vs 10:00 每 2 米一人」

### 5. 删除 assembly/templates/index.md 老花名册

**动作**：
- 确认老花名册里**有价值的内容已迁移**到对应的动线说明.md（变体 variant 灵魂描述·跨动线规则）
- 迁移完后·删除 `japan/kansai/assembly/templates/index.md`
- 老文件副本已归档到 `japan/kansai/_archive/templates_花名册_pre_d40.md`·无需再保留原位

**迁移判断**：
- **迁移**：每个 variant 的「灵魂一句话」（如果动线说明.md 的变体差异段需要参考）·跨动线规则（关西 7 条在哪个动线展开）
- **丢弃**：打分数字（已删字段）·互斥字段（方案层管）·night_options（方案层管）·selectable_tag（方案层管）

### 6. 更新 japan/kansai/产品原则.md

- 删除「关西 7 条」详细条款（已搬 plans/写作规范.md §三·避免两处维护）
- 替换为引用指针：「关西 7 条化学反应详见 [plans/写作规范.md §三](plans/写作规范.md)·本文不重复」
- 产品原则.md 保留价值观/哲学/质量标准（不搬·那不是规则是价值观）

### 7. 引用路径全局修复

全仓库扫所有 md 文档里对**过时路径**的引用·改成新路径：

| 旧路径 | 新路径 |
|---|---|
| `assembly/templates/index.md` | `assembly/engine.md`（装配引擎行为）或 `plans/写作规范.md`（方案层/跨动线规则）·按上下文选 |
| `assembly/templates/data/*` | 不变（data 子目录的 JSON 还用） |
| `templates_old_d36/` | `_archive/templates_old_d36/` |
| `_deprecated/` | `_archive/deprecated_pre_d40/` |
| `_deferred/` | `_archive/deferred_pre_d40/` |
| `_legacy/` | `_archive/legacy_pre_d40/` |
| `D36_D37_落地工作计划.md` | `_archive/D36_D37_落地工作计划.md` |
| 各子目录的 `index.md` | `动线说明.md` |

**扫描范围**：
- `CLAUDE.md`
- `docs/**/*.md`
- `japan/kansai/**/*.md`（排除 `_archive/`·归档不管）
- `marketing/**/*.md`

**方法**：grep 每个旧路径·找到所有引用·逐个改新路径。**不要**用批量 sed 替换·要判断上下文（引用装配引擎还是方案层写作规范）。

---

## 硬规·必守

1. **不动 JSON**（工程师 A 的工作）
2. **不动模板的 slots / note 正文内容**（那也是 A 的工作·日文中文化属 A）
3. **动线说明.md 不硬凑字数**（简单动线 15 行·复杂动线 50 行·按需）
4. **引用路径改动必须 grep 验证**（改完再扫一遍·确保无漏改）
5. **产品原则.md 不过度砍**（价值观保留·只砍与 plans/写作规范.md 重复的规则）
6. **不编造跨动线规则**（原 index.md 没写的跨动线关系·不自己瞎补）

---

## 交付消息格式

```
D40 动线说明 md 改造完成

1. 25 个动线说明.md 重命名+瘦身完成（平均 X 行·最长 arashiyama Y 行·最短 kinosaki Z 行）
2. pace_type 候选段加：7 个动线（岚山/东山/伏见/有马/城崎/高野山/高雄）
3. arashiyama/transport.md：去 fixed_early 标签 ✓
4. higashiyama + fushimi 待建 fixed_early 段加 ✓
5. assembly/templates/index.md 删除·有价值内容迁移清单贴上
6. 产品原则.md 精简：关西 7 条改引用指针 ✓
7. 引用路径全局修复：扫 X 个 md 文件·改 Y 处引用·grep 验证 0 残留

附：每个动线说明.md 的行数列表
```

---

## 开工

准备好读文档 → 执行 7 项 → 贴完成汇报。有疑问先问。
