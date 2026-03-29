# AI API 供应商配置

> 最后更新: 2026-03-29

## 切换方法

修改 `.env` 文件中对应的变量，重启 Python 进程生效。

---

## 1. 阿里云百炼 DashScope ✅ 当前使用

```env
OPENAI_API_KEY=sk-df19f2a1b7e94841a968063ea047117f
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL=qwen-plus
AI_MODEL_STRONG=qwen-max
AI_MODEL_LIGHT=qwen-turbo
AI_MODEL_STANDARD=deepseek-v3.2
```

**推荐模型组合**（2026-03-29 更新）：

| 用途 | 推荐模型 | 原因 |
|------|---------|------|
| 数据采集（当前） | `deepseek-v3.2` | 官方标注"价格最低"，JSON 输出稳定，能力强 |
| 快速任务 | `qwen-turbo` | 最便宜，简单任务够用 |
| 高质量推理 | `qwen3-max` | Qwen 最强，但比 deepseek 贵 |

| 项目 | 说明 |
|------|------|
| 稳定性 | 高，国内直连，不封 IP |
| 可用模型 | qwen 全系列 + deepseek-v3.2 + kimi-k2.5 + deepseek-r1 |
| 适用场景 | 批量数据采集、文案生成 |
| 限速 | 宽松（RPM 约 60） |

---

## 2. saiai.top — OpenAI 系列

```env
# Key A（主力）
OPENAI_API_KEY=sk-45fc4ed0d618a7482adf9a75f7723ca5bfac3d30eac049e5a9d7c9991a685279
# Key B（备用）
OPENAI_API_KEY=sk-570d3d98543a0dd1c1dadad5a4497527684fbaf5bcee06f6d6b2cfad03c4bf7f
# Key C
OPENAI_API_KEY=sk-7b5389fc092b32e8c31b5747108d103dddfd164b4d8ba156beb68d38c9c62413

OPENAI_BASE_URL=https://api.saiai.top/v1
AI_BASE_URL=https://api.saiai.top/v1
AI_MODEL=gpt-4o
AI_MODEL_STRONG=gpt-4.1
AI_MODEL_LIGHT=gpt-4o-mini
AI_MODEL_STANDARD=gpt-4o
```

| 项目 | 说明 |
|------|------|
| 可用模型 | gpt-4o, gpt-4o-mini, gpt-4.1, gpt-4.1-mini, gpt-4.5-preview, o1, o3, o3-pro, o4-mini |
| 适用场景 | 高质量生成（review pipeline、文案润色、评审） |
| 限速 | 严格，并发过高会封 IP |
| 注意 | 封的是出口 IP，换 key 无用，需等解封或换网络 |

**⚠️ 踩坑记录（2026-03-29）**：连续快速调用 20+ 次/分钟导致 IP 被封 503，已改为批量模式（一个城市 3 次调用）+ 间隔 10-15 秒。

---

## 3. saiai.top — Claude 系列（仅 Claude Code 客户端）

```env
# 仅供 Claude Code 使用，Python 脚本调不了
ANTHROPIC_AUTH_TOKEN=sk-ce0d98a9e1be1646d50a4fef8f2e9c798565a5966603e816098eb9487d606092
ANTHROPIC_BASE_URL=https://api.saiai.top
```

| 项目 | 说明 |
|------|------|
| 可用模型 | claude-sonnet-4-6, claude-opus-4-6, claude-haiku-4-5-20251001 |
| 限制 | 只能被 Claude Code 客户端使用 |
| 报错 | 普通脚本调会报 `"Claude OAuth accounts only accept real Claude Code requests"` |

---

## 推荐策略

| 场景 | 推荐 |
|------|------|
| 批量数据采集（跑 seed 脚本） | DashScope（稳定不封） |
| 高质量文案/评审 | saiai GPT-4o（质量高但要限速） |
| 开发调试 | DashScope qwen-turbo（便宜快） |
| Claude Code 对话 | saiai Claude（自动配置） |
