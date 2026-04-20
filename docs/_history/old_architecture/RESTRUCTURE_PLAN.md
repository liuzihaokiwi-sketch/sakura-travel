# 项目结构重构方案

> 状态:**设计稿,待执行**
> 日期:2026-04-18
> 目的:当前仓库经历过一次大迭代(16步管线 → 模板+Opus装配),旧代码/旧文档/新资产混杂,AI 读仓库容易误入老代码。本方案定义一个清晰的终态结构,一次性搬迁到位。

---

## 一、设计目标

不是"目录越少越好",也不是"层次越多越对称"。目标是:

1. **职责全覆盖**:每一类资产/代码都有明确的家(客服流程、外部客户端、装配阶段、跨地区共享资产都不能没地方放)
2. **扩展有位**:新地区、新阶段、新交付形态到来时,目录已经预留空间,不需要再次重构
3. **唯一归属**:任何一个文件,能一眼说出它该在哪
4. **AI 读仓库不走偏**:目录结构 + CLAUDE.md 只有一套活跃架构叙事,老代码彻底隔离

---

## 二、现状问题

- `app/domains/planning_v2/` 只剩 2 个文件,但和 `app/domains/rendering/` `app/domains/templates/` 平级散落
- 客服/发货业务逻辑散落在 `docs/ops/`,代码层无家
- Anthropic/Qwen/Google Routes 客户端封装散在多处
- `content/kansai/` 只有日本一个地区,未来国内/欧洲进来时层次不够
- `research_europe/` `research_iberia/` `research_methodology/` 三个根目录研究笔记平铺
- `data/` 混着静态配置(circle_registry)和运行时产物
- `docs/` 有 10+ 子目录,一半是指南类内容(应就近放),权威源反而不突出
- `CLAUDE.md` 同时描述 v2 架构和 16 步 Legacy 两套,AI 读到后者会误认为仍在用

---

## 三、终态目录结构

```
travel-ai/
├── content/                      # 地区资产(所有内容,按大洲分层)
│   ├── japan/
│   │   ├── kansai/
│   │   │   ├── brief.md
│   │   │   ├── policy.json
│   │   │   ├── assembly_rules.json
│   │   │   ├── tag_vocab.json
│   │   │   ├── transport.json
│   │   │   ├── live_facts/
│   │   │   ├── cities/                       # kyoto/osaka/nara/kobe/uji/koyasan/kinosaki
│   │   │   │   └── {city}/{days,restaurants,hotels,shops}.json
│   │   │   └── assets/                       ← assets/kansai/
│   │   └── _research/                        # 日本圈调研笔记(未来)
│   ├── china/
│   │   ├── guangfu/
│   │   └── _raw/                             # 爬虫原始数据(中间态)
│   ├── europe/
│   │   ├── iberia/
│   │   │   └── _research/                    ← research_iberia/
│   │   └── _research/                        ← research_europe/
│   └── _shared/                              # 跨地区共享资产(四类)
│       ├── schema/                           # 字段定义+校验器 ← docs/SCHEMA.md
│       ├── personas/                         # 人群画像规则
│       ├── writing_guides/                   # 模板写作 SOP ← docs/templates/
│       └── methodology/                      # 研究方法论 ← research_methodology/
│
├── app/                          # 代码主体(保留传统命名,不折腾)
│   ├── planning/                 # 装配引擎(原 planning_v2,去掉 v2 赘余)
│   │   ├── intake/               # 4屏表单 → 硬约束
│   │   ├── pool/                 # 候选池硬筛(规则)
│   │   ├── assembly/             # Opus 两步装配(核心)
│   │   │   ├── opus_assembler.py
│   │   │   └── prompts/          # Opus 提示词模板
│   │   ├── budget/               # 预算计算
│   │   │   └── budget_calculator.py
│   │   ├── templates/            # 模板加载器 ← app/domains/templates
│   │   └── contracts.py          # 步骤间数据契约
│   │
│   ├── rendering/                # 手账本渲染(独立于装配)
│   │   ├── handbook/             # HTML 手账本 ← app/domains/rendering/magazine
│   │   ├── pdf/                  # 未来 PDF 导出
│   │   └── templates/            # Jinja 模板
│   │
│   ├── fulfillment/              # 客服/发货业务逻辑(新增,之前无家)
│   │
│   ├── api/                      # FastAPI 路由(薄层转发)
│   ├── workers/                  # arq jobs
│   ├── db/                       # models + migrations
│   └── clients/                  # 外部服务封装(统一)
│       ├── anthropic.py
│       ├── qwen.py
│       └── google_routes.py
│
├── web/                          # 前端(保持不动)
│
├── docs/                         # 只放决策+流图+导航
│   ├── README.md                 # 内部导航:去哪找什么
│   ├── DECISIONS.md              # 架构决策日志
│   ├── FLOWS.md                  # 数据流+运行时流(合一)
│   └── DEFERRED.md               # 推迟事项
│
├── scripts/                      # 一次性脚本
├── tests/                        # 集成测试(单元测试贴代码)
├── deploy/                       # Docker 配置
├── ops/                          # 运维脚本(部署/监控/日志迁移)
├── var/                          # .gitignore,运行时产物(日志/缓存/快照)
│
├── CLAUDE.md                     # 重写,只讲新结构
├── AGENTS.md / CODEOWNERS / README.md
├── pyproject.toml / alembic.ini / docker-compose*.yml / .env*
└── _deprecated/                  # .gitignore,本地考古(已有)
```

---

## 四、设计决策详解

### 保留的分层(每一层都有实质内容)

| 分层 | 理由 |
|------|------|
| `app/planning/{intake,pool,assembly,budget,templates}` | 业务本来就有 5 个装配阶段,提前分好,每个子目录起步 1-2 文件,长大有地方长 |
| `content/_shared/{schema,personas,writing_guides,methodology}` | 跨地区公共资产本来就有 4 类,塞单文件装不下 |
| `app/fulfillment/` | 客服发货是核心业务动作(CLAUDE.md 反复提到),之前没家散在 docs/ops |
| `app/clients/` | Anthropic/Qwen/Google Routes 现在散落 3 处,换 provider 要全局搜 |
| `app/rendering/` 独立于 `app/planning/` | 两者生命周期彻底解耦(渲染吃装配输出),不能合并 |
| `var/` | 运行时产物不进 git,和 content/ 静态资产物理分离 |
| `content/_shared/_research/` vs `content/{region}/_research/` | 大洲级研究笔记 vs 次区域研究笔记,层级区分 |

### 砍掉的分层(对称但无信息量)

| 砍掉 | 理由 |
|------|------|
| `platform/` 包装 api/db/workers | Python 项目传统 `app/` 就够,再加一层是装饰 |
| `regions/` 包装 content/ | 同上,空壳层 |
| `delivery/` 包装 rendering+fulfillment | 两者职责已足够独立,不需要共同父目录 |
| `japan/_shared` / `europe/_shared` | 大洲内部共享还未出现,出现时再开,不预留空目录 |
| `engine/kanto/ stickers/ pdf/` 等空目录 | YAGNI,新地区/新交付形态到来时再建 |

---

## 五、唯一归属检验

拿任意文件,能一眼说出它该在哪:

| 文件/资产 | 归属 |
|----------|------|
| Anthropic SDK 封装 | `app/clients/anthropic.py` |
| 关西京都餐厅池 | `content/japan/kansai/cities/kyoto/restaurants.json` |
| 关西地区整体 brief | `content/japan/kansai/brief.md` |
| 客服发货前核查逻辑 | `app/fulfillment/pre_ship_check.py` |
| 模板写作 SOP | `content/_shared/writing_guides/template_sop.md` |
| 字段权威定义 | `content/_shared/schema/` |
| 人群画像规则(情侣mid不推USJ) | `content/_shared/personas/` |
| 研究方法论(怎么评估数据源) | `content/_shared/methodology/` |
| 为什么砍 16 步管线 | `docs/DECISIONS.md` |
| 数据流+运行时流 | `docs/FLOWS.md` |
| 运行时快照/日志 | `var/` |
| Opus prompt 模板 | `app/planning/assembly/prompts/` |
| 西班牙调研笔记 | `content/europe/iberia/_research/` |
| 欧洲大洲框架笔记 | `content/europe/_research/` |
| 跨地区研究方法论 | `content/_shared/methodology/` |

---

## 六、现状 → 终态 迁移映射

### 代码层

| 现状 | 终态 |
|------|------|
| `app/domains/planning_v2/opus_assembler.py` | `app/planning/assembly/opus_assembler.py` |
| `app/domains/planning_v2/budget_calculator.py` | `app/planning/budget/budget_calculator.py` |
| `app/domains/planning_v2/__init__.py` + `models.py` | `app/planning/contracts.py` |
| `app/domains/templates/` | `app/planning/templates/` |
| `app/domains/rendering/magazine/` | `app/rendering/handbook/` |
| `app/api/trips_v2.py` + `app/main.py` | `app/api/` |
| `app/workers/jobs/*` | `app/workers/jobs/*`(路径不变) |
| `app/db/*` | `app/db/*`(路径不变) |
| (新建) | `app/clients/` + `app/fulfillment/` |

### 内容/数据层

| 现状 | 终态 |
|------|------|
| `content/kansai/*` | `content/japan/kansai/*` |
| `assets/kansai/` | `content/japan/kansai/assets/` |
| `data/circle_registry.json` + `data/city_circles/` | `content/_shared/schema/` |
| `data/events/` | `content/_shared/` 或各地区下 |
| `data/{guangfu_spots,...}/*.json` | `content/china/{region}/_raw/` |
| `research_europe/` | `content/europe/_research/` |
| `research_iberia/` | `content/europe/iberia/_research/` |
| `research_methodology/` | `content/_shared/methodology/` |

### 文档层

| 现状 | 终态 |
|------|------|
| `docs/SCHEMA.md` | `content/_shared/schema/README.md` |
| `docs/templates/*.md` | `content/_shared/writing_guides/` |
| `docs/intake/` | `app/planning/intake/README.md` |
| `docs/ops/` | `app/fulfillment/README.md` 或 `ops/` |
| `docs/rendering/` | `app/rendering/README.md` |
| `docs/data-engineering/` | `content/_shared/methodology/data-engineering/` |
| `docs/facts/` | `content/_shared/methodology/facts/` |
| `docs/research/` | `content/_shared/methodology/research/` |
| `docs/DECISIONS.md` | `docs/DECISIONS.md`(保留) |
| `docs/FLOW_DATA.md` + `docs/FLOW_RUNTIME.md` | `docs/FLOWS.md`(合一) |
| `docs/DEFERRED.md` | `docs/DEFERRED.md`(保留) |
| `docs/README.md` | `docs/README.md`(重写为内部导航) |
| `docs/page_system/` `docs/product/` | 评估后下沉或保留 |

### 其他

| 现状 | 终态 |
|------|------|
| 根目录 `_deprecated/` | 保留,已 .gitignore |
| `opencli-main/` 第三方资源 | 评估:进 `var/` 或删除 |
| 根目录 `ERROR` 文件 | 删除 |
| 运行时日志/临时文件 | 新建 `var/`,.gitignore |

---

## 七、风险与注意事项

1. **import 路径大变**:`from app.domains.planning_v2 import ...` → `from app.planning.assembly import ...`。需全局搜索替换,配合类型检查验证。
2. **alembic migrations 路径**:`app/db/migrations` 位置未变,但 `alembic.ini` 里 `script_location` 若写绝对路径需同步更新。
3. **Docker 卷挂载**:`docker-compose*.yml` 里挂载 `./app` `./content` `./data` 等路径,需同步更新。
4. **CI 路径**:`.github/workflows/` 里 `pytest app/` `ruff check app/` 等命令如果锁定路径需更新。
5. **content/ 首次入库**:目前 `content/kansai/*` 不在 git,搬迁时一并 commit,这是本次最重要的"资产保护"动作。
6. **CLAUDE.md 同步重写**:搬完后 CLAUDE.md 的"关键配置文件"表、"核心文件"列表全部要更新;Legacy 16 步管线小节删光。
7. **WWW/API 公网调用**:如果有外部服务调用固定路径,搬迁不影响(都是内部代码)。

---

## 八、执行顺序建议

> 不要一次性全动。分阶段,每阶段一个可验证的停靠点。

1. **阶段 0:落 commit**(把 303 个未提交变更分 2-3 个 commit 提交,形成干净起点)
2. **阶段 1:搬 content/**(最危险的资产先入库并重组,不动代码,pytest 全绿)
3. **阶段 2:搬 app/**(按 planning/rendering/fulfillment/clients 重组,大规模 import 替换,pytest 全绿)
4. **阶段 3:搬 docs/**(指南下沉,docs/ 只剩 4 文件)
5. **阶段 4:重写 CLAUDE.md**(砍 Legacy,新职责地图)
6. **阶段 5:清理**(删 `ERROR` 文件,`opencli-main/` 评估,`.env.example` 更新路径示例)

每阶段完成 = 一个 commit,可独立回滚。

---

## 九、不在本次范围的事

- 前端 `web/` 结构不动
- `_deprecated/` 不动(本地考古用)
- 业务逻辑不改,只是搬位置
- 新功能不加
- 不引入新依赖

---

## 十、本文档的角色

这是**一次性重构方案**,执行完应:
- 移入 `docs/DECISIONS.md` 作为一条决策(D<编号>:大规模目录重构)
- 或移入 `_deprecated/` 作为历史记录
- 根目录删除本文件

不长期保留在根目录。
