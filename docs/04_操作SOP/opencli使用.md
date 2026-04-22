# opencli 使用 SOP(AI 复用指南)

> 最后更新:2026-04-21
> 适用:Claude Code / 其他 AI 需要用 opencli 查小红书、下载图/视频、扒笔记正文时

---

## 一、opencli 是什么

本地 CLI 工具(Node.js),走本机 Chrome 浏览器(cookie + session 已登录)调小红书等站点的公开页面,把结果用表格/JSON/Markdown 输出。

**位置**:`D:/projects/projects/travel-ai/opencli-main/`

**前置条件**:
- 本机 Chrome 已登录过小红书账号(cookie 生效)
- opencli 已 `npm run build`(改过代码必须重 build)
- 运行在 **git bash** 下(Windows 原生 CMD 有些路径拼接坑)

---

## 二、能做什么 · 按任务类型查命令

### 2.1 搜索笔记(最常用)

```bash
cd D:/projects/projects/travel-ai/opencli-main
node dist/main.js xiaohongshu search "关键词" --limit 10 --format md
```

**返回**:rank / title / author / likes / published_at / **url(带 xsec_token)**

- `--limit` 默认 10,最多可 20
- `--format` 可选 `md` / `json` / `table` / `csv`
- 判断爆款优先看 `collects`(需进 note 命令)而不是 likes;search 只给 likes,足够粗筛

**经验**:
- 关键词越具体越准(例:"TN旅行手账 日本" 比 "手账" 好)
- 想找某博主作品直接搜 "博主名 + 地区"

### 2.2 读笔记正文(标题/正文/作者/互动数)

```bash
node dist/main.js xiaohongshu note "完整 URL(带 xsec_token)" --format md
```

**必须传完整 URL**,带 `xsec_token` 才能访问。光传 note-id 经常 404。

**返回字段**:title / author / content / likes / collects / comments / tags

**技巧**:`content` 含完整 caption(~1000 字左右,含 hashtag),是判断"值不值得下图"的关键。collects 高说明有长期参考价值。

### 2.3 下载笔记全部图片和视频

```bash
node dist/main.js xiaohongshu download "完整 URL" --output "D:/tmp/xhs_refs/某个命名文件夹"
```

**输出结构**:
```
--output/
  └─ {note-id}/
       ├─ {note-id}_1.jpg
       ├─ {note-id}_2.jpg
       ├─ {note-id}_1.mp4   # 视频笔记会下多个流(不同清晰度),一般第一个最清晰
       └─ ...
```

**图片清晰度**:自动取 WB_DFT(高清默认渲染),比 WB_PRV 预览大 3-5 倍。

### 2.4 其它常用命令(按需)

```bash
# 开发用:dump __INITIAL_STATE__ 结构(适配器坏掉时排查)
node dist/main.js xiaohongshu dump-state "URL" --output ./xhs-dump

# 创作者自己的数据(需登录 creator.xiaohongshu.com)
node dist/main.js xiaohongshu creator-profile
node dist/main.js xiaohongshu creator-notes
node dist/main.js xiaohongshu creator-stats

# 笔记评论
node dist/main.js xiaohongshu comments "note-id"
```

看全部:`node dist/main.js xiaohongshu --help`

---

## 三、核心约束(不守规矩就踩坑)

### 3.1 ⚠️ 不要并发调用

browser 实例是复用的,并发跑 download/note 会**串数据**:A 笔记的输出里可能出现 B 笔记的图。

**规矩**:search 可以并发(纯 API),但 note/download/dump-state **一次只跑一条**。

### 3.2 URL 必须带 xsec_token

正确:
```
https://www.xiaohongshu.com/search_result/671cb9bb000000001402f0aa?xsec_token=ABrPP-li...&xsec_source=
```

错误(容易 404):
```
https://www.xiaohongshu.com/explore/671cb9bb000000001402f0aa
671cb9bb000000001402f0aa
```

**获取 URL 的办法**:从 search 结果里复制整行 url。

### 3.3 笔记 404 = 作者删了 / 小红书下架

dump 出来看 url 重定向到 `xiaohongshu.com/404?...&error_msg=当前笔记暂时无法浏览` 就是这种情况。换一条笔记就行。

### 3.4 环境变量

长笔记/视频要加超时:

```bash
OPENCLI_BROWSER_COMMAND_TIMEOUT=240 node dist/main.js xiaohongshu download "URL" ...
```

数字单位是秒,默认 60,图多视频多调到 180~240。

---

## 四、完整工作流示例

### 场景:找某主题的爆款手账,下载图用于设计参考

```bash
# Step 1: 搜
cd D:/projects/projects/travel-ai/opencli-main
node dist/main.js xiaohongshu search "TN旅行手账 日本" --limit 15 --format md

# Step 2: 挑 likes/collects 高的 3-5 条,**串行**下载
# (注意每条之间用 && 串起来,或一条跑完再跑下一条)
OPENCLI_BROWSER_COMMAND_TIMEOUT=240 node dist/main.js xiaohongshu download \
  "https://www.xiaohongshu.com/search_result/xxx?xsec_token=yyy&xsec_source=" \
  --output "D:/tmp/xhs_refs/作者名_主题"

# Step 3: 想知道 caption(判断哪些图值得保留)再跑 note
node dist/main.js xiaohongshu note "https://..." --format md
```

---

## 五、失效排查

### 症状 A:`No media found`

可能原因:
1. 笔记真的没有图/视频 → 正常
2. 笔记 404 了 → dump-state 看看 url 是不是跳 404
3. 适配器挂了(小红书改了页面)→ dump-state 看 `__INITIAL_STATE__` 里 `imageList` / `video` 字段名变没变

**修复路径**:改 `opencli-main/src/clis/xiaohongshu/download.ts`,然后 `cd opencli-main && npm run build`。

历史背景:2026-04-21 大修过一次,把原来基于 CSS 选择器的提取改成扫 `<script>` 里 `window.__INITIAL_STATE__=...` 的原始文本,用正则抽 `imageList.infoList[].url`(优先 `WB_DFT`)和 `video.media.stream.h264[].masterUrl`。详见 git 记录。

### 症状 B:`Detached while handling command` / 超时

浏览器 session 断了。关掉所有 Chrome,重开一次并登录小红书,再跑。

### 症状 C:search 正常但 note/download 403/登录墙

cookie 过期,浏览器重新登录小红书。

### 症状 D:`initialStateError: Converting circular structure`

**不是 bug**,是预期行为。`window.__INITIAL_STATE__` 是 Vue 响应式对象有循环引用不能 `JSON.stringify`。适配器读的是 `<script>` 原始文本,不受影响。

---

## 六、对这个项目的具体用法

### 做模板调研时

搜"地区 + 核心关键词",挑 likes > 1000 的看标题,想要的 download 下来。图存到 `marketing/{地区}/design_refs/` 或 `marketing/{地区}/爆款参考.md` 对应目录。

### 做素材沉淀时

note 命令拉 caption → 有传播性的冷知识/避坑/本地视角句子摘录到 `marketing/{地区}/素材库.md`,附原笔记 URL 和 collects 数。

### 开发工具链时

`dump-state` 是排查其它站点适配器坏掉的通用套路:加个 dump 命令 → 跑一次 → 看数据在哪个字段 → 改提取逻辑。小红书/B 站/抖音/微博的 Next.js 或 Nuxt 站点几乎都有 `__INITIAL_STATE__` 或 `__NEXT_DATA__`。

---

## 七、把工具链当专家来养

opencli 本身是开源 fork(位置:`opencli-main/`,不是 npm 全局装的),改了就是我们自己的分支。发现坏了自己修,用法积累写回这份文档。
