# 工程师 A 开工提示词（D40 JSON 全面改造）

> 复制以下内容到新 Claude Code 窗口（sonnet 即可）启动。
> 工作范围：`templates/**/*.json` + `scripts/validate_template.py`·**不动任何 md 文件**。
> 预计工作量：一个窗口跑满。和工程师 B 并行·零文件冲突。

---

## 开工前必读

按顺序读这 4 份：
1. [CLAUDE.md](../../CLAUDE.md)
2. [docs/02_历史决策/DECISIONS.md](../02_历史决策/DECISIONS.md) D39 + D40
3. [docs/03_数据契约/SCHEMA.md](../03_数据契约/SCHEMA.md) §1.1-§1.3
4. [japan/kansai/plans/写作规范.md](../../japan/kansai/plans/写作规范.md) 四要素/候选库
5. [japan/kansai/assembly/engine.md](../../japan/kansai/assembly/engine.md) 装配引擎行为

**目标**：把 88 个模板 JSON 按 D40 新字段契约批量改造·跑 validate 全过。

---

## 任务清单（10 项·全部完成才交付）

### 1. 删除 14 个冗余字段

每个 JSON 顶层必须删除（如存在）：
- `label`
- `description`
- `curators_notes`
- `hotel_area_note`
- `min_days`
- `selectable_tag`
- `day_type`
- `exclusive_with`
- `night_options`
- `template_kind`
- `downgrade_target`
- `core_experience`
- `audience_bonus`
- `execution_risk`

**方法**：批量脚本扫 JSON·键存在则删。

### 2. 加 pace_type 字段（仅非 adaptive 模板）

**adaptive 模板（绝大多数）**：`pace_type` 字段**不写**（默认即 adaptive）。

**必须显式写 pace_type 的模板**：
- `kyoto_arashiyama_5` → `pace_type: "fixed_early"`
- `kyoto_arashiyama_8` → `pace_type: "deep_stay"`·`pace_type_sub: "onsen"`
- `kyoto_arashiyama_9` → `pace_type: "deep_stay"`·`pace_type_sub: "deep_local"`
- `kyoto_arashiyama_10` → `pace_type: "deep_stay"`·`pace_type_sub: "deep_local"`
- `arima_1` → `pace_type: "deep_stay"`·`pace_type_sub: "onsen"`
- `arima_3` → `pace_type: "deep_stay"`·`pace_type_sub: "onsen"`
- `kinosaki_1` → `pace_type: "deep_stay"`·`pace_type_sub: "onsen"`
- `koyasan_1` → `pace_type: "deep_stay"`·`pace_type_sub: "deep_local"`
- `takao_2`（如保留 onsen 语义）→ 保持 `day_type=onsen_2day` 的语义·改写为 `pace_type: "deep_stay"`·`pace_type_sub: "onsen"`（注：该模板 onsen ≤1 资源由方案作者把关）

### 3. 岚山 7 个模板回滚标签

| 模板 | 操作 |
|---|---|
| `kyoto_arashiyama_2` 早春一日 | 删除 fixed_early 相关·归默认 adaptive（不显式写 pace_type） |
| `kyoto_arashiyama_3` 樱花开门即进 | 同上·归 adaptive·`time_sensitivity: "soft"` + note 说明「樱花季 10:00 后人满·早到抢空景」 |
| `kyoto_arashiyama_5` 出片一日 | **保留 fixed_early**（D39/D40 明文唯一远郊例外）·`time_sensitivity: "hard"`·contingencies.late_start 必写 |
| `kyoto_arashiyama_6` 红叶一日 | 删除 fixed_early·归 adaptive·`time_sensitivity: "soft"` + note 说明「红叶季早到抢空景」 |
| `kyoto_arashiyama_7` 小火车+漂流 | 归 adaptive + `time_sensitivity: "soft"` + `time_sensitivity_note: "嵯峨野小火车 1 小时一班·出门提前 20 分钟赶最近班次"` |
| `kyoto_arashiyama_9` 红叶深度两日 | 归 deep_stay + deep_local |
| `kyoto_arashiyama_10` 樱花深度两日 | 归 deep_stay + deep_local |
| `kyoto_okazaki_tetsugaku_2` 瑠璃光院 | 归 adaptive + `time_sensitivity: "soft"` + `time_sensitivity_note: "瑠璃光院抽签全天多场次每 20 分钟一场·按指定时刻反推出发"` |

### 4. contingencies 规范化（late_start 键）

**fixed_early + time_sensitivity=hard 模板必须写 `contingencies.late_start`**·自然语言 Plan B·告诉用户「起晚了/错过班次怎么办」。

示例（岚山 5）：
```json
"contingencies": {
  "rain_light": "...",
  "rain_heavy": "...",
  "crowd": "...",
  "late_start": "若 7:00 之后才出门——渡月桥晨光+竹林光柱两个机位已错过·不追了·直接去 % ARABICA 渡月桥店排队看桥·9:00 再走天龙寺曹源池（无开门即进的水面倒影但大方丈+法堂云龙图仍值得）。下午按原计划嵯峨野民居樱漫步→奥嵯峨三寺→17:00 渡月桥 peak-end。出片体验打 6 折但岚山一日不崩。"
}
```

**写作硬规**：
- 不引用其他模板 ID（不写"切换到 arashiyama_1"）
- 用自然语言·具体到"去哪喝咖啡·先走哪个"
- 策展人视角·有温度·不是系统机械降级

**原有 contingencies.crowd 里**关于 "fixed_early 触发失败降级为 arashiyama_1" 的文字删除·改写成 late_start。

### 5. variant_label 大幅精简

**绝大多数 JSON 的 variant_label 字段删除**（让渲染层自动用「动线名 + 季节标注」生成）。

**只保留/重写灵魂特别的 10-20 个**·按**诗意标题**风格：
- 10-14 字
- 不含 `fixed_early` / `adaptive` / `9 点档` / `·标准日基准` 等内部术语
- 像日记标题/诗句·有美感

**示范**（岚山 10 变体）：

| 旧 variant_label | 新 variant_label |
|---|---|
| 岚山核心一日（9 点档基准）| **删除**（渲染层用"岚山·一日"生成）|
| 岚山早春一日（fixed_early·7:30 前到竹林...）| **删除** |
| 岚山樱花一日·开门即进 | **删除** |
| 岚山樱花一日·氛围 | **删除** |
| 岚山出片一日（fixed_early·三机位晨光轮转...）| `晨光岚山·追光三站` |
| 岚山红叶一日（fixed_early·奥嵯峨）| **删除** |
| 嵯峨野小火车+保津川漂流一日（fixed_early·班次锚定）| `上山坐火车·下山坐船` |
| 岚山温泉一泊·两日 | `岚山温泉·住一夜` |
| 岚山红叶深度一泊两日（fixed_early·D1 夜枫+D2 清晨独享红叶竹林+奥嵯峨三寺完整）| `岚山·夜枫与清晨` |
| 岚山樱花深度一泊两日（fixed_early·D1 夜樱+D2 清晨独享曹源池 2h+三寺山樱）| `岚山·夜樱与清晨` |

**判准**：
- 动线标准日 / 季节常规版 / 氛围版·**都删 variant_label**
- 独特叙事（晨光轨迹 / 火车+漂流反差 / 夜枫+清晨 / 夜樱+清晨 / 宿坊早朝勤行）·**重写诗意**
- 不确定的·删（渲染层兜底·不会丢信息）

### 6. 日文批量中文化（按白名单）

**保留（无需翻译）**：温泉 / 怀石 / 割烹 / 茶寮 / 町家 / 宿坊 / 锦市场 / 葛切 / 抹茶 / 和菓子 / 鳗丼 / 炸豚排 / 一泊二食 / 素泊 / 女将 / 朝食 / 一休 / 楽天 / Tabelog / 祇园祭 / 天神祭 / 大文字 / 五山送火 / 御手洗祭 / 节分祭 / 初詣 / MICHELIN / Keys / きらら（首次加括号「展望车厢きらら」）/ トロッコ（首次加「小火车（トロッコ）」）

**必翻译**：
- コース → 套餐
- ホットケーキ → 厚松饼
- きんし丼 → 金丝鳗鱼丼
- まぶしご飯 → 撒酱拌饭
- テーブル紅葉 → 桌面红叶
- キモノフォレスト → 和服柱林
- 特別拝観 → 特别参拝
- 上り/下り → 上行/下行
- 紅葉 → 红叶
- 庭園 → 庭园
- 本殿 → 本殿（保留·汉字同义）
- 境内 → 境内（保留）

**扫描范围**：每个 JSON 的 `note` / `slots[*].main[*].note` / `slots[*].optional[*].note` / `slots[*].main[*].options_note` / `contingencies.*` 所有用户可能看到的字符串字段。

**自检**：改完 grep 每个 JSON 检查是否还有纯假名裸写（如 コース / の / が 等片假名/平假名助词单独成词）。

### 7. 清理过时文字

`note` 里的过时引用全部删除（已不符合 D39/D40 语义）：
- `本模板 fixed_early·出门档无效（D38 §9.5）`
- 引用 `assembly/templates/index.md` 的句子（该文件已归档）
- 引用 `D36/D37/D38` 的章节号（改成自然语言描述·或删）

替换为自然语言说明·如岚山 5 note 开头：
> 岚山晨光三机位轮转·不按用户出门档平移·起晚了看 contingencies.late_start。核心判断：...

### 8. 删除 arm_arima_4

- 删除 `japan/kansai/templates/other/arima/4.json`
- 不用管装配层的引用（那是工程师 B 的范围）
- 在 commit 说明里写「跨城组合归方案层·D40 决议」

### 9. 更新 validate_template.py

`scripts/validate_template.py` 的白名单字段清单（参考 SCHEMA §1.1 新定义）：

**必填**：`template_id` / `applicable_dates` / `note` / `slots`

**可选**：`variant_label` / `pace_type` / `pace_type_sub` / `time_sensitivity` / `time_sensitivity_note` / `contingencies`

**拒绝**：`label` / `description` / `curators_notes` / `hotel_area_note` / `min_days` / `selectable_tag` / `day_type` / `exclusive_with` / `night_options` / `template_kind` / `downgrade_target` / `core_experience` / `audience_bonus` / `execution_risk`

**扩展校验**：
- `pace_type=fixed_early` 或 `time_sensitivity=hard` 时·`contingencies.late_start` 必须存在
- `pace_type=deep_stay` 时·`pace_type_sub` 必须是 `onsen` 或 `deep_local`
- `time_sensitivity in (soft, hard)` 时·`time_sensitivity_note` 必须存在
- variant_label 如存在·长度 ≤ 20 字符·不含 `fixed_early` / `adaptive` / `deep_stay` / `9 点档` 子串

### 10. 全量跑 validate · 粘完整输出

```bash
cd d:/projects/projects/travel-ai
python scripts/validate_template.py japan/kansai/templates/
```

**粘完整输出到交付消息**（不是口头声称「全过」·memory: feedback_validate_before_deliver）。

---

## 硬规·必守

1. **不擅自修改 validator 放行错误字段**（memory: feedback_never_modify_validator）
2. **不编造数据**·改文字化中文时不确定就保留日文并标「待核实」
3. **写作质量不下降**：删字段不影响 note 和 slots 的叙事完整性
4. **岚山 5 绝对不能回滚 adaptive**·D39/D40 双重例外·看到任何试图改的都停下来问
5. **报数字必须脚本核验**（88 JSON 完成进度 = 脚本数·不估算）
6. **不批量补丁掩盖错误**：validate FAIL 找根因修·不改 validator 白名单放行

---

## 交付消息格式（要简洁）

```
D40 JSON 改造完成

1. 字段删除：88 JSON·删除 14 冗余字段·脚本核验 0 残留
2. pace_type 加：10 个（岚山 5/8/9/10 + 有马 1/3 + 城崎 1 + 高野山 1 + 高雄 2·如保留）
3. 岚山 7 回滚：2/3/6 → adaptive·7 → adaptive+soft·9/10 → deep_stay·5 保留 fixed_early
4. contingencies.late_start：8 个 hard 模板全写·岚山 5 样板
5. variant_label：删除 X 个·重写 Y 个（贴新旧对照表·10 条左右）
6. 日文中文化：扫描 X 处·改动 Y 处
7. 过时文字清理：扫到 X 处·全删
8. arm_arima_4 删除 ✓
9. validator 更新：新白名单 10 字段·扩展校验 4 项
10. validate 全量跑：粘完整输出（88/88 PASS）
```

---

## 开工

准备好读文档 → 执行 10 项 → 粘 validate 输出。有疑问先问不要瞎改。
