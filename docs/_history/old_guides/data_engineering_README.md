# 数据工程文档

## 目录结构

```
docs/data-engineering/
├── README.md                   本文档
│
├── methodology/                方法论（怎么思考）
│   └── master-guide.md         选品方法论（三轴/三层池/评分解释/负向规则/效率规则）
│
├── sources/                    数据源目录（有什么源）
│   ├── README.md               索引
│   ├── japan/                  日本
│   │   ├── README.md
│   │   ├── restaurants.md      吃
│   │   ├── hotels.md           住
│   │   ├── spots.md             玩
│   │   ├── shops.md            买
│   │   └── transport.md        行
│   └── china/                  国内（占位，开城时填充）
│       └── README.md
│
├── guides/                     采集工作流（怎么做）
│   ├── restaurants.md          餐厅
│   ├── hotels.md               酒店
│   ├── spots.md                景点
│   └── shops.md                店铺
│
└── ops/                        工具+运维+经验
    ├── tools-setup.md          工具配置（OpenCLI/WebFetch/API）
    ├── city-circle-template.md 新城市圈开城模板
    └── kansai-lessons.md       关西踩坑总结
```

---

## 你要做什么？

| 场景 | 读这个 |
|------|--------|
| 找某品类的日本数据源 | [sources/japan/](sources/japan/) |
| 了解选品方法论（三轴模型/三层池/评分解释） | [methodology/master-guide.md](methodology/master-guide.md) |
| 数据字段规范 | [../../docs/SCHEMA.md](../SCHEMA.md) |
| 采集某品类的具体工作流 | [guides/](guides/) |
| 配置工具（OpenCLI/Google API/Rakuten API） | [ops/tools-setup.md](ops/tools-setup.md) |
| 开一个新城市圈 | [ops/city-circle-template.md](ops/city-circle-template.md) |
| 查看关西踩坑记录避免重犯 | [ops/kansai-lessons.md](ops/kansai-lessons.md) |

---

## 四个子目录的职责

| 目录 | 性质 | 变动频率 |
|------|------|---------|
| **methodology/** | 选品方法论，决策逻辑 | 很低（核心原则） |
| **sources/** | 数据源字典，按地域+品类 | 中等（发现新源时更新） |
| **guides/** | 品类采集工作流 | 中等（流程迭代时） |
| **ops/** | 工具配置+踩坑+开城模板 | 较高（开城经验沉淀） |

`methodology/` 告诉你**为什么这样做**。
`sources/` 告诉你**去哪里找数据**。
`guides/` 告诉你**采集时的具体步骤**。
`ops/` 告诉你**工具怎么用、踩过什么坑**。
