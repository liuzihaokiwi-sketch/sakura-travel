# 深度研究搜索方法论

> 记录：2026-04-12
> 用途：下次做城市圈或体验维度研究时复用

---

## 核心原则

**维度和规则都不能拍脑袋定，必须从文献或真实旅行者内容中提取。**

每条洞察必须能回答：
- 这是从哪里搜到的？（URL或平台+文章类型）
- 这是真实旅行者/研究者说的，还是AI从训练数据推断的？
- 如果是推断，停下来真搜，或标注"未验证/待核实"

---

## 搜索策略

### 一、维度框架先从综述文献入手

不要直接搜"体验有哪些维度"——AI会直接从知识库回答。
正确做法：搜系统综述（systematic review）论文，从真实文献提取框架。

**有效关键词：**
- `"memorable tourism experience" dimensions framework systematic review`
- `tourism experience quality psychology research 2023 2024`
- `travel experience [具体方向] research`

**关键发现：** Kim et al. (2012) MTE七维度（279篇文献综述确认）是目前最有学术共识的框架：享乐/刷新/本地文化/意义感/知识/参与/新奇。新维度研究要在这个基础上找补充，不是另起炉灶。

---

### 二、旅行者深度内容：找"去了才懂"而非攻略

**不要搜：**
- "关西旅游攻略"
- "京都必去景点"
- "大阪美食推荐"

**要搜：**
- `[城市] travel mistakes locals vs tourists`
- `[城市] second visit what I learned`
- `[城市] authentic experience beyond [著名景点]`
- `"后悔没早知道" [城市]`
- `[城市] 当地人视角`
- `[城市] 去了才知道`

**平台优先级：**
- 英文：旅行者个人博客 > reddit r/JapanTravel > japan-guide.com论坛 > Tripadvisor论坛
- 中文：知乎长文 > 马蜂窝游记 > 小红书深度帖（不是图片帖）
- 排除：旅游局官网、OTA推广内容、泛泛攻略清单

---

### 三、区分两类问题，用不同策略

| 问题类型 | 可以用AI知识 | 必须真搜 |
|---------|------------|---------|
| 逻辑性规则（为什么这样排） | 部分可以 | 需要真实旅行者验证 |
| 具体数据（班次/时间/价格） | 不可以 | 必须找一手来源 |
| 心理机制（体验为什么好） | 不可以 | 找学术文献 |
| 常识性建议（早起人少） | 不需要搜，直接排除 | — |

---

### 四、迭代搜索：每轮之间停下来判断

**第一轮：** 宽泛关键词，找方向
**停下来问：** 哪些是常识（删掉）？哪些是真盲区（保留）？哪些方向还没覆盖？
**第二轮：** 针对盲区缩小关键词，找具体内容
**停下来问：** 每条洞察有来源吗？逻辑自洽吗？能直接影响装配决策吗？
**第三轮（如需要）：** 针对需要验证的具体数据补搜

---

### 五、识别"AI生成冒充搜索结果"的信号

以下情况高度可疑，需要追问来源：

- 给了具体数字但没有URL（如"30-40%"、"14:40末班"）
- 逻辑太完整、太整齐，像是从常识直接推导的
- 洞察方向和搜索关键词高度重合（说明没有真正找到意外发现）
- "多位旅行者反馈"但没有具体链接

---

### 六、体验维度研究的有效关键词库

```
# 时间感知
"travel time perception" slow down psychology
"time dilation" travel novelty information processing

# 认知负荷
"cognitive load" travel itinerary decision fatigue vacation
"cognitive light" itinerary design travel

# 旅伴动态
"travel companion" relationship dynamics experience quality research
"travel companionship" memorable experience well-being

# 记忆编码
"memorable tourism experience" encoding mechanism
"peak end rule" travel application

# 感官体验
"multisensory" tourism experience memory
"sensory" travel experience cross-modal

# 期望管理
"expectation disconfirmation" tourism satisfaction
"over-marketing" tourism disappointment

# 地方依恋
"place attachment" tourist short-term bonding
host-guest interaction emotional connection revisit

# 身份认同
"narrative transportation" travel storytelling
"co-creation" tourist story experience
```

---

## 需要核实后才能用的内容类型

- 具体班次/时刻（如有马温泉大巴）→ 去官网或Google Maps查
- 酒店/餐厅具体接待政策 → 去官网或Tabelog/一休查
- 季节性开放时间 → 去景区官网查
- 价格 → 去OTA或官网查当前价

**原则：** 能搜到"结构性洞察"（大巴班次有限制）就进内容，具体数字必须标注"出发前确认"。

---

## 已完成的研究文件

| 文件 | 状态 | 可用度 |
|------|------|--------|
| `travel_experience_dimensions.md` | 第一版完成，有学术来源 | 可用，与MTE框架对照后补充 |
| `B1_kansai_insights.md` | 有问题，部分条目是推断 | 需逐条过滤后使用 |
| `B2-B6_*.md` | 浅层搜索，城市圈未开发时暂存 | 暂不使用 |
