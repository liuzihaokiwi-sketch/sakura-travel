# Prompt Catalog（AI 版）

## 当前仍在使用的 prompt 场景
1. `catalog/tagger.py`：标签生成
2. `planning/copywriter.py`：一句话描述 + tips
3. `intake/intent_parser.py`：自然语言意图解析
4. `catalog/ai_generator.py`：离线生成实体

## 当前 prompt 使用原则
- Prompt 只负责少量高价值解释
- 不要用 prompt 代替结构、规则和配置
- 能模板化的不要交给 AI 从头写

## 新方向下 prompt 的角色
最值得交给 AI 的：
- 总设计思路
- 每日亮点解释
- 复杂取舍说明
- 少量个性化润色

不值得继续重写的：
- 通用出发前准备
- 通用安全提示
- 重复性酒店/餐厅理由
- 可以由规则直接给出的判断
