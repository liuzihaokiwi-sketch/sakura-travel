# 新城市圈开城模板

> 版本: 2.0
> 更新: 2026-04-01
> 用途: 开始采集新城市圈时，复制此模板填写

---

## 使用方式

1. 复制本文件为 `{CITY_CIRCLE}_COLLECTION_PLAN.md`（如 `TOKYO_COLLECTION_PLAN.md`）
2. 按顺序填写每个章节
3. 完成调研后确认数量分配
4. 按 DATA_COLLECTION_GUIDE.md 的流程执行采集

---

## 一、城市圈基本信息

| 项目 | 填写 |
|------|------|
| 城市圈名称 | |
| 覆盖府县 | |
| 核心城市 | |
| 城市前缀 | |
| 数据目录 | `data/{}_spots/` |

### 子区域列表

| 府县 | 子区域 | 定位 |
|------|--------|------|
| | | |

---

## 二、区域调研结果

> 此章节必须在采集前完成。用agent搜索实际数据填写。

### 景点分布

| 区域 | 估计景点数 | S级候选 | 游客热度 |
|------|----------|---------|---------|
| | | | |

### 餐厅分布

| 区域 | 估计餐厅数 | 城市必吃菜系 | 游客热度 |
|------|----------|-------------|---------|
| | | | |

### 酒店分布

| 区域 | 估计酒店数 | 价位主体 | 游客热度 | 特色体验 |
|------|----------|---------|---------|---------|
| | | | | |

---

## 三、采集目标数量（按调研比例分配）

### 景点

| 区域 | S | A | B | C | 合计 |
|------|---|---|---|---|------|
| | | | | | |
| **合计** | | | | | |

### 餐厅

| 区域 | luxury | premium | mid | budget | street | 合计 |
|------|--------|---------|-----|--------|--------|------|
| | | | | | | |
| **合计** | | | | | | |

### 酒店

| 区域 | luxury | expensive | moderate | budget | backpacker | 合计 |
|------|--------|-----------|----------|--------|------------|------|
| | | | | | | |
| **合计** | | | | | | |

---

## 四、城市特有分类

> 该城市圈是否需要新增分类/标签？

### 新增 sub_type（如需要）

| 值 | 中文 | 说明 | 所属城市圈 |
|----|------|------|-----------|
| | | | |

### 新增 cuisine（如需要）

| 码 | 日文 | 中文 | 所属城市圈 |
|----|------|------|-----------|
| | | | |

### 新增 hotel_type（如需要）

| 码 | 中文 | 说明 |
|----|------|------|
| | | |

### 新增 experience.types（如需要）

| 类型 | 说明 |
|------|------|
| | |

### 新增画像维度（如需要）

| 维度码 | 中文 | 说明 |
|--------|------|------|
| | | |

---

## 五、走廊定义

> 每个城市定义步行可达区域

| 走廊ID | 名称 | 中心坐标 | 半径km | 典型游览h | 连接走廊 |
|--------|------|---------|--------|----------|---------|
| | | | | | |

---

## 六、旺季日历

| 时段 | 级别 | 价格倍率 | 影响范围 |
|------|------|---------|---------|
| | | | |

---

## 七、数据源

| 数据源 | URL | 用途 | 优先级 |
|--------|-----|------|--------|
| | | | |

---

## 八、采集执行流程

> 遵循 MASTER_GUIDE 第二b章"效率规则"

### Phase 0: 城市级资产(一次性)

- [ ] taxonomy.json
- [ ] corridor_definitions.json
- [ ] indie_sites_evaluation.json (10-15个核心独立站)
- [ ] seasonal_calendar (旺季日历)
- [ ] city_cuisine_map (城市特有菜系概览)
- [ ] city_hotel_landscape (各区域酒店价位分布)

### Phase 1: 发现(脚本+API批量，低成本)

```
搜索语言: 成熟类目用日文+中文，不熟悉类目五语全开
API层级: 只查ranking/keyword/list级别，不查detail
停机规则: 连续10个新候选无1入围则停

每批最多3个并发agent，每agent最多35条
```

| 批次 | 品类 | Agent 1 | Agent 2 | Agent 3 |
|------|------|---------|---------|---------|
| 1 | 景点 | | | |
| 2 | 餐厅 | | | |
| 3 | 酒店 | | | |

### Phase 1.5→2 衔接: 数据归一化（必做，不可跳过）

> 关西教训: 跳过归一化直接进 Phase 2 会导致 cuisine 混乱、price_level 被默认值覆盖、
> 强信号在合并时丢失，Phase 2 无法跑选择模型。

```
归一化步骤（详见 MASTER_GUIDE 3.1 节）:
  N1. cuisine_type 归一化 — 映射到标准菜系码，维护 cuisine_mapping.json
  N2. area → corridor 映射 — 输出 area_corridor_mapping.json
  N3. budget_tier 细化 — 加 premium 层（价格层≠质量层，不用评分推价格）
  N4. 酒店 price_level 修正 — 用回溯的 JPY 价格重新分层
  N5. 酒店 hotel_type 补全 — 从 name_ja 推断

合并脚本必须保留的字段（不可丢弃）:
  餐厅: tabelog_score, michelin, source（不可在合并时丢掉）
  酒店: ranking_info, brief_note(含OTA评分/JPY价格), key_features
  景点: japan_guide_level, japan_guide_url

检查点: 归一化后 cuisine 唯一值<40, price_level 分布合理(不是85%同一值)
```

### Phase 2: 入围+终选（Sonnet 批量证据 + Opus 审关键条目）

> 详见 PHASE2_PLAN.md v2.0

```
关键约束:
  - budget_tier 是价格层，不是质量层（不用 Tabelog 分数推价格）
  - base_quality_score 用组内 percentile，不做全局 min-max 归一化
  - 酒店 quality 用 OTA/Keys 评分做主轴，hotel_type/features 只做修正
  - editorial_exclusion 纳入选择主流程，不是后处理
  - JSON ledger 为主输出，Markdown 为审稿层

流程:
  2A. 纯 Python 预处理（不调 API）
      - base_quality_score（组内 percentile）
      - indie_support_score
      - slot 分组 + city-relative percentile + same-slot cap 3
      - 标记候选: selected / borderline / excluded / needs_editorial
  2B. Sonnet 批量结构化短证据（仅对 selected + borderline 调 API）
      - 每条 120-220 字 + JSON 字段
      - 分批串行，每批 15-20 条
  2C. Opus 审核（仅四类关键条目）
      - S/A 候选、边界升级项、risk_watch>=medium、slot 超载组
  2D. 生成 selection_ledger.json
  2E. 编译 GUIDE_*.md（审稿层）
```

### Phase 3: 结构化+分层审核

```
1. 种子CSV -> 脚本生成完整JSON(不消耗token)
2. validate_data.py校验
3. S/A级: 完整三轴审查，逐条人工审核
4. B/C级: 只确认真实性+执行性
5. 导入DB + 端到端测试
```

---

## 九、Token预算估算

### 效率流程下的token分布

| 阶段 | 消耗token的工作 | 不消耗token的工作 |
|------|----------------|-----------------|
| Phase 0 城市级资产 | 调研agent(~5万) | taxonomy/corridor JSON手动或脚本 |
| Phase 1 发现 | 搜索agent(~10万) | API批量查询(外部成本，非token) |
| Phase 2 选品判断 | 模型读evidence block做判断(~15万) | 脚本合并CSV、抽摘要、API补字段 |
| Phase 3 结构化 | -- | 种子CSV->JSON(脚本) |
| Phase 3 S/A审核 | opus逐条审核(~10万) | -- |
| Phase 3 B/C审核 | sonnet轻审(~5万) | validate_data.py(脚本) |
| **合计** | **~45万** | 脚本+API |

### 对比：关西实际消耗(旧流程 vs 新流程)

| | 旧流程(模型生成全量JSON) | 新流程(种子+脚本+分层审核) |
|---|----------------------|------------------------|
| 景点 212条 | ~40万 | ~12万 |
| 餐厅 380条 | ~65万 | ~18万 |
| 酒店 300条 | ~50万 | ~15万 |
| 调研+审核 | ~15万 | ~10万(审核更聚焦) |
| **合计** | **~170万** | **~55万** |

关键节约点:
1. 模型不再生成坐标/价格/营业时间等机械字段 -> 省~50%
2. 模型吃evidence摘要不吃原始网页 -> 省~30%input
3. B/C轻审不写编辑辩护 -> 省~20%审核token

---

## 十、种子数据格式

> 新城市圈推荐使用种子CSV + 脚本扩展方式

### 景点种子CSV

```csv
id,name_zh,name_ja,name_en,main_type,sub_type,grade,city_code,corridor,visit_min,admission_jpy,best_for,grade_reason,why_selected,skip_if
```

### 餐厅种子CSV

```csv
id,name_zh,name_ja,name_en,cuisine,budget_tier,grade,city_code,corridor,is_must_eat,lunch_jpy_range,dinner_jpy_range,signature,why_selected,skip_if
```

### 酒店种子CSV

```csv
id,name_zh,name_ja,name_en,hotel_type,district,price_level,exp_grade,exp_types,best_for,not_for,check_in,check_out,meals,why_selected,skip_if
```

种子数据由opus生成（需要选品判断力），脚本自动扩展为完整JSON。

---

## 十一、完成检查清单

- [ ] taxonomy.json 创建
- [ ] corridor_definitions.json 创建
- [ ] 景点数据完成 + 校验通过
- [ ] 餐厅数据完成 + 校验通过
- [ ] 酒店数据完成 + 校验通过
- [ ] S/A级条目逐条审核
- [ ] 价格抽查（对比OTA实际价格）
- [ ] 坐标抽查（在地图上验证）
- [ ] 导入DB
- [ ] 端到端测试（行程编排是否正常）
