# 模板渲染引擎 (Template Renderer)

## 概述
把结构化行程数据变成"可卖"的成品攻略。
核心原则：**杂志级渲染是所有价位的基础线**，不是高价位的升级卖点。

## 设计原则（第一性原理）
- 规划与渲染必须分离
- 输入是 structured_plan.json，不是自由文本
- 模板分三层：layout / component / theme
- 内容与模板分离，支持多格式导出

## 渲染管线
```
structured_plan.json
  → template context builder（填充数据）
  → HTML/CSS（模板引擎）
  → PDF / H5 / 长图 / 微信摘要
```

---

## 杂志级渲染 = 基础线

### 为什么 ¥20 必须杂志级
- 渲染质量是引流款"秀肌肉"的核心手段
- 用户拿到 ¥20 的第一感受必须是"这 20 块花得太值了"
- 渲染品质本身驱动从 ¥20 → ¥128 的转化

### 各价位渲染差异（不在风格，在内容组件）
| 维度 | 引流款 | 利润款 | 高客单 |
|---|---|---|---|
| 渲染质量 | 杂志级 | 杂志级 | 杂志级 |
| 排版精度 | 相同 | 相同 | 相同 |
| 差异来源 | 内容组件不同 | 内容组件不同 | 内容组件+主题深度 |

---

## 模板三层架构

### Layer 1: Layout（页结构）
- 封面布局
- 每日时间轴布局
- 卡片网格布局
- 全出血大图布局
- 分栏信息布局

### Layer 2: Component（内容组件）
| 组件 | 引流款 | 利润款 | 高客单 |
|---|---|---|---|
| 封面（行程标题+封面图） | ✅ | ✅ | ✅ |
| 行程总览 | ✅ | ✅ | ✅ |
| 每日时间轴 | ✅ | ✅ | ✅ |
| 景点详情卡片 | ✅ | ✅ | ✅ |
| 酒店推荐卡片 | 区域指南版 | 具体酒店版 | 精选+对比版 |
| 餐饮推荐卡片 | ❌ | ✅ | ✅+菜品 |
| 区域地图 | ✅ | ✅ | ✅+标注 |
| 预算汇总 | 粗估 | 分项明细 | 分项+对比 |
| 交通指南 | 基础 | 详细 | 详细+卡券 |
| 避坑指南 | ❌ | ✅ | ✅+深度 |
| 主题深度板块 | ❌ | ❌ | ✅（茶道/温泉/动漫专属内容） |
| 注意事项 | 基础 | 完整 | 完整+个性化 |
| 签证/安全提醒 | ✅ | ✅ | ✅ |
| 免责声明 | ✅ | ✅ | ✅ |
| 升级引导 | ✅ | ❌ | ❌ |

### Layer 3: Theme（视觉主题）
| 主题 | 说明 | 用途 |
|---|---|---|
| magazine_clean | 杂志感 + 信息清晰 | 所有价位默认 |
| magazine_warm | 暖色调杂志感 | 亲子/温泉主题 |
| magazine_cool | 冷色调杂志感 | 都市/购物主题 |
| social_card | 社交媒体卡片风格 | 小红书/朋友圈分享版 |

---

## 输出格式
| 格式 | 用途 | 优先级 |
|---|---|---|
| H5 页面 | 在线阅读/分享/预览 | P0 |
| PDF | 下载/打印/离线查看 | P0 |
| 精简摘要 | 微信成交用 | P0 |
| 小红书长图 | 种草传播 | P1 |
| 微信长图 | 朋友圈分享 | P1 |

---

## 数据结构

### render_templates（模板配置）
| 字段 | 类型 | 说明 |
|---|---|---|
| template_id | UUID | 主键 |
| name | VARCHAR | 模板名 |
| layout_config | JSONB | 页结构配置 |
| component_config | JSONB | 组件开关与配置 |
| theme | VARCHAR | 视觉主题 |
| format | VARCHAR | h5 / pdf / wechat_image / xhs_image / summary |
| css_assets | JSONB | 样式资源 |
| version | INT | 版本号 |

### export_jobs（导出任务）
| 字段 | 类型 | 说明 |
|---|---|---|
| job_id | UUID | 主键 |
| plan_id | UUID | 关联行程 |
| template_id | UUID | 使用模板 |
| format | VARCHAR | 输出格式 |
| status | VARCHAR | pending / rendering / completed / failed |
| output_url | VARCHAR | 输出文件 URL |
| created_at | TIMESTAMP | 创建时间 |
| completed_at | TIMESTAMP | 完成时间 |

### export_assets（导出产物）
| 字段 | 类型 | 说明 |
|---|---|---|
| asset_id | UUID | 主键 |
| job_id | UUID | 关联导出任务 |
| format | VARCHAR | pdf / h5 / image |
| file_url | VARCHAR | S3 URL |
| file_size_bytes | INT | 文件大小 |
| page_count | INT | 页数（PDF） |
| created_at | TIMESTAMP | 创建时间 |

### plan_artifacts（全链路追溯表 — 最关键的表之一）
| 字段 | 类型 | 说明 |
|---|---|---|
| artifact_id | UUID | 主键 |
| trip_version_id | UUID | 关联行程版本 |
| planner_run_id | UUID | 关联编排运行 ID |
| score_version | VARCHAR | 评分引擎版本 |
| template_version | VARCHAR | 模板版本 |
| source_snapshot_ids | UUID[] | 使用的快照 ID 列表 |
| export_asset_id | UUID | 关联导出产物 |
| exported_at | TIMESTAMP | 导出时间 |

> 这张表能回答："这份 PDF 是基于哪次快照、哪版评分、哪版模板生成的？"

---

## 技术方案
- HTML/CSS → WeasyPrint 生成 PDF
- HTML → Next.js SSR 生成 H5 页面
- HTML → Puppeteer 截图生成长图
- 模板引擎：Jinja2（Python 侧）