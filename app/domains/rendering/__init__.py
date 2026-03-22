"""
app/domains/rendering — 渲染层（L3）

负责将 ReportPayloadV2 转换为 PagePlan → PageViewModel，
供 Web 组件和 PDF 导出使用。

模块：
  page_type_registry  — 17 种页型定义（L3-02）
  chapter_planner     — 章节规划器（L3-03）
  page_planner        — 页面规划器（L3-04）
  page_view_model     — 页面 ViewModel 构建器（L3-05）
  page_validator      — 页面级校验（L3-14）
"""
