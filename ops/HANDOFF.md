# AI 交接板

> 这个文件是两台电脑的 AI 之间传递信息用的。
> 老板这边的 AI 写完 push，小雅那边的 AI pull 后读这个文件获取最新上下文。
> 小雅那边有问题也可以写在这里 push 回来。

---

## 最新消息（2026-04-07）

### 给小雅的 AI：

**你的角色：** 运营助手，协助小雅做小红书和抖音内容。

**当前阶段：** 养号建信任，发专业旅行攻略内容，暂不卖产品。

**内容方向举例：**
- 关西必吃的美食
- 大阪烧 Top3 精选  
- 奈良小众游一天怎么玩
- 京都本地人才知道的5件事

**小雅的工作流：**
1. 从 `ops/content/xiaohongshu/drafts/` 和 `douyin/scripts/` 取内容草稿
2. 调整网感、排版后发布
3. 竞品好内容记到 `ops/content/competitor_notes.md`
4. 发布后归档到 `published/`

**当前状态：** 
- 草稿还没有，等老板定好方向后会生成
- 有 10 个待讨论的运营决策，见 `ops/content/OPEN_DECISIONS.md`
- 小雅可以先跟你讨论这些决策，讨论结果写到 OPEN_DECISIONS.md 里

**数据素材在哪：**
- 餐厅：`data/kansai_spots/restaurants/`（380+家）
- 景点：`data/kansai_spots/poi/`
- 酒店：`data/kansai_spots/hotels/`
- 大阪模板（含详细点评）：`data/kansai_spots/templates/osaka/`

**多账号策略：** 多个账号，国内和国外内容分开。具体待定。

---

## 小雅 → 老板（回复区）

（小雅的 AI 有问题或讨论结果写在这里）
