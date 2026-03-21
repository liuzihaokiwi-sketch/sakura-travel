# Spec: magazine-renderer

## 概述

杂志级渲染系统将结构化行程 JSON 转换为精美 HTML，再导出为 PDF 和 H5 预览。定位是"用户拿到手觉得值一两百"的排版质量。

---

## 模板架构

```
templates/magazine/
├── base.html.j2          # 基础布局（head / fonts / CSS 变量）
├── cover.html.j2         # 封面页（全屏图 + 路线标题 + 标签）
├── day_card.html.j2      # 每日行程卡片（时间轴 + 实体卡片列表）
├── entity_card.html.j2   # 实体卡片（图片 + 名称 + 描述 + 实用信息）
├── hotel_area.html.j2    # 住宿区域指南卡片
├── transport.html.j2     # 交通指引页
├── tips_page.html.j2     # 实用信息汇总页
└── css/
    ├── magazine_clean.css  # 主主题
    └── variables.css       # CSS 变量（颜色/字体/间距）
```

---

## 设计规范

### 颜色体系

```css
--color-bg:          #FAFAF8;   /* 暖白底色 */
--color-text:        #2C2C2C;   /* 深灰正文 */
--color-accent:      #C0392B;   /* 朱红强调（日式） */
--color-accent-2:    #2C6E49;   /* 深绿次要强调 */
--color-muted:       #8C8C8C;   /* 浅灰辅助文字 */
--color-border:      #E8E4DC;   /* 边框/分割线 */
```

### 字体

- 标题：Noto Serif SC（衬线，有质感）
- 正文：Noto Sans SC（无衬线，清晰）
- 数字/时间：Tabular Numbers

### 排版原则

- 高留白（页边距 >= 24px）
- 封面：全出血大图 + 白色标题叠加 + 路线天数/城市标签
- 每日卡片：左侧时间轴 + 右侧实体卡片流
- 实体卡片：图片（16:9）+ 名称（加粗）+ 一句话描述 + 标签徽章 + 实用信息（营业时间/交通）
- 实用信息页：图标列表（签证/天气/货币/交通/紧急电话）

---

## 渲染引擎

### PDF 渲染（WeasyPrint）

```python
# app/domains/rendering/magazine/pdf_renderer.py
async def render_pdf(plan_id: UUID) -> bytes:
    html = await render_html(plan_id)
    pdf = weasyprint.HTML(string=html).write_pdf(
        stylesheets=[weasyprint.CSS(filename="magazine_clean.css")]
    )
    return pdf
```

WeasyPrint 配置要点：
- `@page { size: A4; margin: 20mm; }`
- `@page :first { margin: 0; }` — 封面无边距
- 字体通过系统安装（Dockerfile 预装 fonts-noto-cjk）

### H5 渲染（Jinja2 静态 HTML）

- 同一套模板，CSS 中 `@media print` 控制 PDF 差异
- 移动端优化：`viewport` + 弹性布局
- 无 JS 依赖（纯静态，CDN 可部署）

---

## 图片处理

| 情况 | 处理方式 |
|------|---------|
| entity_media 有图 | 直接使用图片 URL |
| entity_media 无图 | 使用城市默认图片（data/city_defaults/{city}.jpg） |
| 图片加载失败 | CSS 占位背景色 + 图标 |

---

## 验收标准

- [ ] 模板文件结构创建完整
- [ ] `render_html(plan_id)` 函数输出有效 HTML
- [ ] PDF 渲染正常，中文不乱码
- [ ] H5 预览在手机端正常显示
- [ ] 封面、每日卡片、实体卡片样式达到设计规范
- [ ] 无图片时 fallback 正常
