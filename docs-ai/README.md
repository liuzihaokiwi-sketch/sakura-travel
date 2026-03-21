# docs-ai-v2

这套文档给 AI 与新开发者使用，目标不是重复产品脑暴，而是：
1. 让 AI 快速知道当前代码和当前目标之间的差距
2. 避免把旧架构当成单一真相源
3. 让修改尽量基于事实、少误改高风险文件

## 使用顺序
1. repo_index.md
2. do_not_break.md
3. runtime_entrypoints.md
4. config_inventory.md
5. data_models.md
6. dependency_map.md
7. pipeline_catalog.md
8. prompt_catalog.md

## 重要原则
- 这些文档描述的是“当前代码事实 + 明确的迁移提示”
- 如果代码与产品新方向冲突，优先把冲突标出来，不要假装代码已经完成迁移
- 当前产品单一真相源不在这些 AI 文档里，而应在产品文档中维护
