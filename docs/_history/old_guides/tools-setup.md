# 数据采集工具设置与使用

> 版本: 2.0
> 更新: 2026-04-01

---

## 一、防止乱码规则

**所有文档和数据文件必须遵守以下规则，防止乱码:**

1. 文件编码统一使用 UTF-8 (无BOM)
2. 不使用 Unicode 特殊字符: 不用 -> 和 ├── 和 └── 等树形符号，改用 - 和 * 和缩进
3. 不使用 emoji (包括 checkmark 等符号)
4. JSON 文件写入后用 python 验证编码: `python -c "import json; json.load(open('file.json', encoding='utf-8'))"`
5. Markdown 文件写入后检查是否有乱码: `python -c "open('file.md', encoding='utf-8').read()"`
6. Windows 环境下 python 输出中文需要注意 GBK 编码问题，用 `2>&1 | cat` 或设置 `PYTHONIOENCODING=utf-8`
7. 用 `python` 而不是 `python3` (Windows 下 python3 指向 Store 安装器会弹窗)

---

## 二、工具总览

| 工具 | 用途 | 状态 |
|------|------|------|
| OpenCLI | 抓取任意网页(小红书/台湾站/日文站) | 已安装+扩展已连接 |
| WebFetch | Claude Code内置网页抓取 | 可用，部分网站被阻止 |
| WebSearch | Claude Code内置搜索 | 可用，中日英文均可 |
| Google Maps Places API | 坐标/评分/营业时间 | 需API Key |
| Rakuten Travel API | 酒店信息 | 需注册开发者 |

---

## 三、OpenCLI

### 3.1 项目位置

`d:/projects/projects/travel-ai/opencli-main/`

### 3.2 当前状态 (2026-04-01 验证通过)

```
opencli v1.5.6
Node.js: v24.13.0
Daemon: 运行中 (port 19825)
Chrome 扩展: 已连接 (v1.5.5)
```

### 3.3 Chrome 扩展安装

```
1. Chrome 打开 chrome://extensions/
2. 开启"开发者模式"
3. "加载已解压的扩展程序"
4. 选择 d:/projects/projects/travel-ai/opencli-main/extension
5. 确认扩展已启用
```

检查连接:
```bash
cd d:/projects/projects/travel-ai/opencli-main
node dist/main.js doctor
```

### 3.4 已验证可用的内置CLI命令

#### 小红书 (需要Chrome已登录小红书)

搜索笔记:
```bash
node dist/main.js xiaohongshu search "大阪美食推荐" --limit 20 -f json
```
输出: rank, title, author, likes, published_at, url

抓取单篇笔记:
```bash
node dist/main.js xiaohongshu note "<note-url-or-id>" -f json
```
输出: title, author, content, likes, collects, comments, tags

注意: 很多小红书图文笔记的正文在图片上，content 字段可能只有标签。需要结合 download 命令获取图片。

#### 携程 (公开数据)

搜索:
```bash
node dist/main.js ctrip search "大阪酒店" -f json
```

#### 其他可用命令

查看所有命令:
```bash
node dist/main.js list
```

### 3.5 探索新网站

```bash
# 分析网站结构
node dist/main.js explore "https://example.com/" --goal "描述你要找什么"

# 一键生成CLI
node dist/main.js generate "https://example.com/"

# 录制浏览器操作
node dist/main.js record "https://example.com/page"
```

### 3.6 适用场景

- 小红书: 用 xiaohongshu search/note 命令
- 台湾独立站 (.tw): WebFetch 被阻止，用 OpenCLI explore/record
- 香港站: 同上
- 日文网站: 部分 WebFetch 可用，不行就用 OpenCLI
- Tabelog 详情页: 用 OpenCLI 抓取评分和评论

---

## 四、WebSearch (Claude Code 内置)

支持中日英文搜索。搜索词模板见 [sources/japan/](../sources/japan/) 各品类文件。

即使网站 WebFetch 被阻止，WebSearch 仍然能搜到该网站的摘要信息。

---

## 五、Google Maps Places API

### 用途
精确坐标、评分、评论数、营业时间、营业状态

### 费用
- Text Search: $17/1000 请求
- Place Details: $5/1000 请求
- 每城市建议控制 500 请求内 (约 $10)

### 省额度策略
- 优先用其他方式获取坐标 (官网/OSM/攻略站地图)
- 宝藏店铺类尽量不用 API
- Google API 主要用于: 批量坐标验证 + 营业状态确认

### 配置
```
环境变量: GOOGLE_MAPS_API_KEY
配置文件: .env
```

---

## 六、Rakuten Travel API

### 用途
酒店信息批量获取、评分、价格、空房

### 注册
开发者注册: https://webservice.rakuten.co.jp/

### API 文档
https://webservice.rakuten.co.jp/documentation/travel

---

## 七、工具选择决策

需要抓取网页内容:
- 网站需要登录 (小红书等) -> 用 OpenCLI
- WebFetch 能访问 -> 用 WebFetch (最方便)
- WebFetch 被阻止 -> 用 OpenCLI
- 只需要搜索摘要 -> 用 WebSearch

需要获取坐标/营业时间:
- 少量 (<20 条) -> Google Maps 手动搜索 (免费)
- 中量 (20-100 条) -> 先试官网/OSM，不够再用 API
- 大量 (>100 条) -> Google Maps Places API

需要获取酒店价格/评分:
- 日本酒店 -> Rakuten API + 一休 WebFetch/OpenCLI + 携程 WebFetch
- 国际酒店 -> Booking API + 携程 WebFetch

---

## 八、采集前检查清单

每次开始新城市圈采集前确认:

- [ ] OpenCLI daemon 运行中 (node dist/main.js doctor)
- [ ] Chrome 扩展已连接
- [ ] 小红书已在 Chrome 中登录
- [ ] Google Maps API Key 已配置 (如需使用)
- [ ] Rakuten Travel API 已注册 (如需使用)
- [ ] WebFetch/WebSearch 可正常使用
- [ ] python 命令可用 (不是 python3)
