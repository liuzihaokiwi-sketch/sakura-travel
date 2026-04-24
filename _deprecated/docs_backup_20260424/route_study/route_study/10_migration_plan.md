# 21 个早春京都模板 — 迁移计划

> 本文档定义：如何把今晚写的 21 个模板（旧架构）迁移到新架构（08 文档）下。
> 核心原则：**保留策展价值，删掉冗余和违规**。

---

## 一、21 模板现状盘点

全部位于 `content/kansai_v2/early_spring/kyoto/`：

| # | 文件 | 当前类型 | 分数预估 | 新架构处置 |
|---|------|---------|---------|----------|
| 1 | kyo_kiyomizudera__higashiyama_core | full_day | 56 | 保留（main 池王牌）|
| 2 | kyo_arashiyama__early_spring | full_day | 48 | 保留但**降为 core + early_spring_notes**（与樱花/红叶独立版共存）|
| 3 | kyo_kinkakuji__northwest_early_spring | full_day | 50 | 保留但**降为 northwest_core + 早春加成**|
| 4 | kyo_nintendo_museum__main | full_day | 55 | 保留（main 池，selectable_tag）|
| 5 | kyo_teamlab_biovortex__main | full_day | 57 | 保留（main 池，selectable_tag）|
| 6 | kyo_fushimi_sake__brewery_tour | full_day | 48 | 保留但**拆 3 个版本**：常规 / 3/14 酒祭 special_date / 十石舟 3/20 后版本 |
| 7 | kyo_higashiyama__couple_ritual | full_day | 46 | **重构动线**：改成哲学之道/鸭川情侣日，避开东山精华已占用的景点 |
| 8 | kyo_higashiyama__friends_kimono | full_day | 47 | **重构动线**：改成锦市场+河原町闺蜜日（可合并东山一部分但不和 1 号重合）|
| 9 | kyo_kitano_tenmangu__ume_deep | full_day | 47 | 保留（early_spring 限定，无 core 对应）|
| 10 | kyo_jonangu__shidare_ume | full_day | 40 | **降为半日**（城南宫半日），去掉伏见稻荷部分 |
| 11 | kyo_zuishinin__ono_ume | full_day | 35 | **降为半日**（随心院+小野梅半日）|
| 12 | kyo_railway_aquarium__family | full_day | 43 | 保留（main 池亲子专属）|
| 13 | kyo_nijo_castle__power_leisure | full_day | 46 | 保留（main 池）|
| 14 | kyo_craft__experience | full_day | 41 | **拆 2-3 个半日**：京友禅半日 / 和菓子半日 / 陶艺半日 |
| 15 | kyo_sagano_torokko__scenic_train | full_day | 45 | 保留，拆"含漂流版" vs "只小火车版" |
| 16 | kyo_gear_theatre__night_show | night_day | 44 | **转为 night_module**（2-3 小时，不占一天）|
| 17 | kyo_ohara__deep_retreat | full_day | 27 | 保留（deep 池）|
| 18 | kyo_sagano__deep_moss | full_day | 32 | 保留（deep 池）|
| 19 | kyo_okazaki__philosophers_path | full_day | 39 | **重构**：简化成"银阁+哲学之道+南禅"主线，去掉冈崎美术馆分支 |
| 20 | kyo_recovery__slow_day | full_day | 27 | 保留但**暂缓系统化**（08 文档 §13）|
| 21 | kyo_arashiyama_onsen__1n_stay | multi_day | 40 | 保留（deep 池，特殊多日结构）|

---

## 二、迁移分组

### 组 A：保留 + 按新架构重写（12 个）
直接迁移的 full_day / multi_day / 亲子专属模板：
1. kiyomizudera（东山精华）
2. arashiyama（加 early_spring_notes）
3. kinkakuji（加早春加成）
4. nintendo
5. teamlab
6. kitano_ume
7. railway_aquarium
8. nijo_castle
9. ohara
10. sagano_deep_moss
11. recovery（保留不改）
12. arashiyama_onsen_1n（保留作多日样本）

### 组 B：降级为半日（3 个）
- `kyo_jonangu__half_pm`（下午城南宫半日）
- `kyo_zuishinin__half_pm`（下午随心院半日）
- `kyo_fushimi_inari__half_am`（上午伏见稻荷半日）—— 新增，拆出城南宫模板里的伏见部分

### 组 C：拆成多个半日（1 个）
`kyo_craft__experience` 拆为：
- `kyo_yuzen_nishijin__half_am`（京友禅上午半日 + 西阵扩展）
- `kyo_wagashi_gion__half_pm`（和菓子下午半日 + 祇园）
- `kyo_kiyomizu_pottery__half_am`（清水烧上午半日 + 清水坂）

### 组 D：转为 night_module（1 个）
`kyo_gear__night` 只保留 19:00-21:30 的 2.5 小时，白天段删除。

### 组 E：重构动线（3 个）
- `kyo_higashiyama__couple_ritual` → `kyo_philosophers__couple`（哲学之道情侣日）或 `kyo_kamogawa__couple`（鸭川情侣日）
- `kyo_higashiyama__friends_kimono` → `kyo_nishiki_kawaramachi__friends`（锦市场+河原町闺蜜日）
- `kyo_okazaki__philosophers_path` → 简化为单一主线

### 组 F：拆多版本（2 个）
- `kyo_fushimi_sake__brewery_tour` 拆为：
  - `kyo_fushimi_sake__regular`（常规版，all days）
  - `kyo_fushimi_sake_fes__special_date_20260314`（3/14 特供）
  - 十石舟段进 availability，不单独拆模板
- `kyo_sagano_torokko__scenic_train` 拆为：
  - `kyo_sagano_torokko__only`（只小火车 + 岚山主线）
  - `kyo_sagano_torokko_hozugawa__full`（含保津川漂流）

---

## 三、单个模板迁移步骤

### Step 1：字段结构改写
- 目录按新分层（`full_day/main/` / `full_day/deep/` / `half_day/morning/` 等）
- 字段按 08 文档结构
- 删除 `tags` / `fit_audience` / `condition` / `assembly`（旧字段）
- 补齐 `applies_when` / `excludes_when` / `pool` / `critical_entities`

### Step 2：事实抽离
- `note` 里的**所有票价 / 开放时间 / 闭馆日 / 电话网址**删掉
- 对应事实填入 `live_facts/kyoto.json`
- `note` 只保留**设计思路**

### Step 3：用户决策删除
- 扫 `note` / `design` 里的"三个方向任选""(1)A (2)B"等
- 改成**单一最佳方向**（按默认人群选）
- 真需要人群差异的，用 `_variants` 覆盖

### Step 4：景点避让检查
按分从高到低重排：
- 东山精华日占用：清水/三年坂/八坂/花见小路/白川/建仁寺
- 情侣日/闺蜜日**不能**再用这些 critical entities
- 重构情侣日/闺蜜日的动线

### Step 5：校验
- `critical_entities` 每个 ID 必须在 entities 层
- `meal_area` 每个值必须在合法区域枚举
- `pool` 是合法值（main/deep/modules/special_date）
- 无禁用词（方向任选/都不会错）

---

## 四、迁移优先级

### P0：样板验证（1 个）
`kyo_arashiyama__early_spring` 按新架构完整重写，跑通规则装配。

### P1：main 池核心（8 个）
- kiyomizudera（东山精华）
- kinkakuji（北山）
- nintendo
- teamlab
- nijo_castle
- railway_aquarium
- kitano_ume
- recovery

### P2：deep 池（4 个）
- ohara / sagano_deep_moss / arashiyama_onsen_1n / okazaki_simplified

### P3：半日 + 夜间模块（5 个）
- jonangu_half / zuishinin_half / fushimi_inari_half
- craft 3 个拆出来的半日
- gear_night_module

### P4：重构型（3 个）
- philosophers_couple（替代 higashiyama_couple）
- nishiki_kawaramachi_friends（替代 higashiyama_friends）
- fushimi_sake 拆 2 版

### P5：special_date（1 个）
- fushimi_sake_fes_20260314

---

## 五、工作量估算

按单个模板 15-30 分钟（已有原稿，只做字段重构+事实抽离）：
- 组 A 保留类 12 个 × 20 min = 4 小时
- 组 B 降级半日 3 个 × 15 min = 45 min
- 组 C 拆半日 3 个 × 30 min = 1.5 小时（需要针对性设计不同工艺日）
- 组 D 夜间模块 1 个 × 15 min = 15 min
- 组 E 重构动线 3 个 × 60 min = 3 小时（需要重新设计动线）
- 组 F 拆多版本 2 个 × 30 min = 1 小时

**合计约 10-12 小时**，分多次 session 完成。

---

## 六、依赖

**前置条件（必须先完成）**：
1. 09_facts_to_collect.md 里的 P0 entities + live_facts 先填完（至少样板用到的）
2. entities/kyoto.json 初始版本（至少 P0-P1 约 20 个 entity）
3. 目录结构建立（`full_day/main/` 等）

**并行可做**：
- 餐厅池迁移（从旧 restaurants.json）
- 酒店池初始化（从温泉一泊模板抽）
- 校验脚本（scripts/validate_templates.py）

---

## 七、不做的事（明确）

- **不推倒重写**：原 21 模板的策展思路（`design` 字段核心内容）保留
- **不立即建 overlay**：岚山/北山的 core + overlay 合并等做樱花/红叶季时再做
- **不修 recovery 日的装配规则**：恢复日暂缓系统化
- **不深度处理"预约失败"场景**：交给客服流程

---

## 八、下次 session 启动顺序

1. 读 08 文档（架构共识）
2. 读 09 文档（事实采集清单）
3. 读本文档（迁移计划）
4. 采集 P0 事实（岚山 3 + 清水寺 1 + 天龙寺已在）
5. 按新架构重写 Arashiyama 样板 → 验证
6. 通过后按 P1 顺序批量迁移
