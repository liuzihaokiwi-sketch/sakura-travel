# S3. 图片资产治理系统
> 产品：日本旅行定制规划
> 作者：AI-3
> 更新：2026-03-21
> 依赖：entity_media 表、city_defaults 默认图、html_renderer._get_entity_image()

---

## 一、现状诊断

### 已有
| 组件 | 位置 | 能力 |
|---|---|---|
| `entity_media` 表 | `app/db/models/catalog.py` | 存图片 URL、media_type、sort_order、is_cover、source、caption |
| `_get_entity_image()` | `html_renderer.py:66` | entity_media 有图 → 用；无图 → city_defaults fallback；都无 → None |
| `_CITY_DEFAULT_IMAGES` | `html_renderer.py:36` | 10 个城市硬编码兜底图 |

### 缺失（按影响排序）

| # | 缺失项 | 影响 | 严重度 |
|---|---|---|---|
| 1 | **无候选→精选流程** | 爬到什么用什么，质量不可控 | 🔴 |
| 2 | **无横竖图分类** | 交付页用竖图、商品页用横图时拉伸/裁切 | 🔴 |
| 3 | **无失效检测** | 外链 404 → 交付页白框，用户信任崩塌 | 🔴 |
| 4 | **无 attribution 管理** | Google Places 图片需署名，违规可被停 API | 🟡 |
| 5 | **无图片自有化** | 全依赖外链，速度/稳定不可控 | 🟡 |
| 6 | **无多用途裁切** | 同一张图无法适配交付页/小红书/分享卡片 | 🟡 |
| 7 | **无人工抽检机制** | 图里有水印/低质/不相关内容无法发现 | 🟡 |
| 8 | **无季节/时段匹配** | 冬天推樱花图、夜景配白天场景 | 🟠 |

---

## 二、目标架构

### 图片生命周期

```
                    ┌──────────────────────────────────────────┐
                    │           图片生命周期                      │
                    └──────────────────────────────────────────┘

  ① 采集入池          ② 自动处理           ③ 精选标记           ④ 分发使用
  ──────────       ──────────────       ──────────────       ──────────────
  Google Places     尺寸检测               自动评分              交付页封面
  Unsplash          横竖比判定             人工抽检              交付页景点卡
  爬虫抓取           去重（pHash）          精选标记 ✓            商品页展示
  编辑上传           外链→自有化           季节/时段标签          小红书配图
  用户投稿(未来)      缩略图生成            attribution记录        分享卡片
                    失效检测(定期)                              PDF 导出
```

### 数据模型升级

#### entity_media 表扩展字段

| 新字段 | 类型 | 说明 |
|---|---|---|
| `status` | VARCHAR(20) | `candidate` → `approved` → `rejected` → `expired` |
| `orientation` | VARCHAR(10) | `landscape` / `portrait` / `square` |
| `width` | INT | 原始宽度 px |
| `height` | INT | 原始高度 px |
| `aspect_ratio` | VARCHAR(10) | `16:9` / `4:3` / `3:2` / `1:1` / `9:16` / `other` |
| `quality_score` | SMALLINT | 0-100 自动评分（分辨率+清晰度+构图） |
| `season_tag` | VARCHAR(20) | `spring` / `summer` / `autumn` / `winter` / `all` |
| `time_of_day` | VARCHAR(20) | `day` / `golden_hour` / `night` / `all` |
| `usage_flags` | JSONB | `{"cover": true, "card": true, "xhs": false, "share": true}` |
| `self_hosted_url` | TEXT | 自有 CDN URL（外链转存后填入） |
| `thumbnail_url` | TEXT | 缩略图 URL（300px 宽） |
| `attribution_text` | VARCHAR(500) | 版权署名文字 |
| `attribution_url` | TEXT | 版权来源链接 |
| `license_type` | VARCHAR(30) | `google_places` / `unsplash` / `cc0` / `editorial` / `unknown` |
| `phash` | VARCHAR(64) | 感知哈希，用于去重 |
| `last_checked_at` | TIMESTAMP | 最近一次可用性检查时间 |
| `reviewed_by` | VARCHAR(100) | 人工审核人（为空=未审核） |
| `reviewed_at` | TIMESTAMP | 审核时间 |

#### 新表：`media_usage_log`（图片使用记录）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT | 主键 |
| media_id | BIGINT | 关联 entity_media.id |
| usage_scene | VARCHAR(30) | `delivery_cover` / `delivery_card` / `product_page` / `xhs_post` / `share_card` / `pdf` |
| plan_id | UUID | 关联行程（可空） |
| render_config | JSONB | `{"crop": "center", "size": "720x405", "overlay": "gradient"}` |
| created_at | TIMESTAMP | 使用时间 |

---

## 三、候选图池 → 精选图集流程

### 3.1 入池（采集）

| 来源 | 入池方式 | 默认 status | 默认 license_type |
|---|---|---|---|
| Google Places Photos | 爬虫 `google_places.py` 采集 | `candidate` | `google_places` |
| Unsplash API | 城市/景点关键词搜索 | `candidate` | `unsplash` |
| 爬虫抓取（JNTO/Matcha等） | 各爬虫采集 | `candidate` | `unknown` |
| 编辑手动上传 | 工作台上传 | `approved`（跳过自动评审） | `editorial` |

### 3.2 自动处理管线

```python
# 每张新入池图片自动执行：
async def process_candidate_image(media_id: int):
    """
    1. 下载 → 检测尺寸 → 填 width/height/orientation/aspect_ratio
    2. 计算 pHash → 去重（汉明距离 < 8 视为重复，标记 rejected）
    3. 自动质量评分 → quality_score
       - 分辨率 ≥ 1080px 宽: +30
       - 无明显水印（OCR 检测）: +20
       - 清晰度（拉普拉斯方差）: +20
       - 构图合理（主体居中/三分法）: +15
       - 色彩饱和度适中: +15
    4. 转存到自有 CDN → 填 self_hosted_url
    5. 生成缩略图（300px 宽）→ 填 thumbnail_url
    6. quality_score ≥ 60 → status 保持 candidate
       quality_score < 60 → status = rejected
    """
```

### 3.3 精选标记规则

| 条件 | 操作 | 说明 |
|---|---|---|
| quality_score ≥ 80 且 orientation=landscape | 自动标记 `approved` + `usage_flags.card=true` | 高质量横图自动入选卡片用途 |
| quality_score ≥ 80 且 orientation=portrait | 自动标记 `approved` + `usage_flags.xhs=true` | 高质量竖图自动入选小红书用途 |
| quality_score 60-79 | 保持 `candidate`，等人工抽检 | 中等质量需人工判断 |
| quality_score < 60 | 自动 `rejected` | 低质量直接拒绝 |
| 编辑上传 | 直接 `approved`，手动设 usage_flags | 编辑图片最高优先级 |

### 3.4 人工抽检

| 抽检范围 | 抽检比例 | 触发条件 |
|---|---|---|
| S 级实体（data_tier='S'）图片 | **100%** | 必须人工确认 |
| A 级实体图片 | **50%** | 随机抽检 |
| B 级实体图片 | **20%** | 随机抽检 |
| 封面用途图片 | **100%** | is_cover=true 的必须人工过 |
| 自动 approved 的 | **30%** | 抽检自动决策的准确性 |

**人工审核清单：**
- [ ] 图片内容与实体匹配（不是别的景点的图）
- [ ] 无明显水印/LOGO
- [ ] 无低俗/不雅内容
- [ ] 色调和谐，适合杂志感渲染
- [ ] 季节标签正确（有樱花=spring，有红叶=autumn）
- [ ] attribution 信息完整

---

## 四、横竖图分类与用途映射

### 4.1 图片分类体系

| 分类维度 | 值 | 判定规则 |
|---|---|---|
| **方向** landscape | 宽 > 高 × 1.1 | 适合卡片、封面、PDF |
| **方向** portrait | 高 > 宽 × 1.1 | 适合小红书、手机全屏 |
| **方向** square | 其他 | 适合头像、缩略图 |
| **用途** cover | 宽≥1080px + landscape + quality≥80 | 封面/大图 |
| **用途** card | 宽≥720px + landscape + quality≥60 | 景点/餐厅/酒店卡片 |
| **用途** xhs | 高≥1280px + portrait + quality≥70 | 小红书配图 |
| **用途** share | 宽≥600px + quality≥60 | 分享卡片 |
| **用途** thumbnail | 任意 | 自动生成 300px 宽缩略图 |

### 4.2 各终端图片需求

| 使用场景 | 所需方向 | 所需比例 | 最小尺寸 | 裁切方式 |
|---|---|---|---|---|
| **交付页封面（M1）** | landscape | 16:9 → 全屏 | 1080×608 | center-crop + 底部渐变遮罩 |
| **交付页景点卡片（M3）** | landscape | 16:9 | 720×405 | center-crop |
| **交付页餐厅卡片（M4）** | landscape | 4:3 | 480×360 | center-crop |
| **交付页酒店卡片（M5）** | landscape | 3:2 | 600×400 | center-crop |
| **商品页展示图** | landscape | 16:9 | 800×450 | center-crop |
| **小红书图文** | portrait | 3:4 | 1080×1440 | center-crop / 原图 |
| **分享卡片** | landscape | 5:4 | 600×480 | center-crop + 文字叠层 |
| **PDF 内页** | landscape | 16:9 | 1080×608 | center-crop |
| **微信缩略图** | square | 1:1 | 300×300 | center-crop |

### 4.3 图片选取优先级

```python
def select_image_for_scene(entity_id, scene: str) -> Optional[str]:
    """
    按优先级选图：
    1. editorial 来源 + approved + usage_flags[scene]=true → 编辑精选
    2. approved + usage_flags[scene]=true + quality_score DESC → 自动精选
    3. approved + orientation 匹配 + quality_score DESC → 方向匹配
    4. candidate + orientation 匹配 + quality_score DESC → 候选池（未审核）
    5. city_defaults[city_code] → 城市兜底图
    6. None → CSS 占位
    """
```

---

## 五、失效/错误/Attribution 处理

### 5.1 失效图片检测

**定时任务：`check_image_availability`**
| 配置 | 值 |
|---|---|
| 频率 | 每周一次（全量）；每天一次（最近7天使用过的） |
| 方式 | HEAD 请求检测 HTTP 状态码 |
| 超时 | 5秒 |

```python
async def check_image_availability(media_id: int):
    """
    HEAD 请求图片 URL：
    - 200 → 正常，更新 last_checked_at
    - 403/404/410 → status='expired'，触发替补选图
    - 超时/5xx → 标记 soft_fail，3次连续失败 → expired
    """
```

**失效后自动替补：**
1. 同实体的其他 approved 图片自动顶上（按 quality_score DESC）
2. 无替补 → fallback 到 city_defaults
3. 运营通知：S/A 级实体图片失效时，发告警到工作台

### 5.2 错误图片处理

| 错误类型 | 检测方式 | 处理 |
|---|---|---|
| **内容不匹配** | 人工抽检发现 | 标记 `rejected` + 备注原因 |
| **水印/LOGO** | OCR 自动检测 + 人工复核 | 标记 `rejected` |
| **色情/暴力** | 云端内容安全 API | 自动 `rejected` + 告警 |
| **极低分辨率** | width < 400 或 height < 300 | 自动 `rejected` |
| **重复图片** | pHash 汉明距离 < 8 | 保留质量高的，其余 `rejected` |

### 5.3 Attribution（版权署名）管理

| 来源 | 是否需要署名 | 处理方式 |
|---|---|---|
| Google Places Photos | **是**（API Terms 要求） | 在图片下方小字显示 `attribution_text` |
| Unsplash | **推荐**（非强制） | 在图片下方小字显示 "Photo by X on Unsplash" |
| CC0 / 公共领域 | 否 | 不显示 |
| 编辑自有 | 否 | 不显示 |
| 来源不明 | **风险** | 标记 `license_type=unknown`，优先替换为有明确来源的图 |

**交付页 Attribution 展示规范：**
- 不在图片上叠加，不破坏杂志感
- 在页面最底部统一展示"图片来源"区域
- 格式：`浅草寺图片 © Google Maps 用户 XXX`
- 字号 10px，颜色 `#B0A89A`，视觉上弱化

---

## 六、图片服务于各终端的具体规范

### 6.1 交付页（核心场景）

| 位置 | 图片要求 | 缺图处理 | 备注 |
|---|---|---|---|
| M1 封面 | 1080px+ 横图，城市氛围 | city_defaults 必有 | 底部60%渐变遮罩 `rgba(0,0,0,0.4→0)` |
| M3 景点卡 | 720px+ 横图，16:9 | 同城市默认图 + 灰色半透明叠层 | 圆角 12px |
| M4 餐厅卡 | 480px+ 横图，4:3，食物特写优先 | 通用日式料理图 | 圆角 12px |
| M5 酒店卡 | 600px+ 横图，3:2，外观/大堂/房间 | 通用酒店外观图 | 圆角 12px |

### 6.2 商品页（售前展示）

| 位置 | 图片要求 | 说明 |
|---|---|---|
| 主图 | 城市标志性景点，1080px+，暖色调 | 吸引点击 |
| 示例行程截图 | 交付页截图（自动生成） | 展示交付物品质 |
| 用户评价配图 | 用户授权的交付页截图 | 社会证明 |

### 6.3 小红书配图

| 内容类型 | 图片要求 | 图片来源 |
|---|---|---|
| 景点推荐 | 竖图 3:4，高饱和度，有人物更好 | entity_media (portrait + xhs=true) |
| 路线汇总 | 横图拼接为九宫格 | 自动拼接脚本 |
| 避坑指南 | 对比图（好 vs 坑） | 编辑制作 |
| 餐厅推荐 | 食物特写，竖图 | entity_media + 菜品标签 |

### 6.4 分享卡片（微信/朋友圈）

| 元素 | 规范 |
|---|---|
| 尺寸 | 600×480（5:4） |
| 构成 | 背景图（模糊）+ 行程摘要文字叠层 |
| 背景图 | 城市封面图，高斯模糊 radius=20 |
| 文字 | 白色，标题 24px Bold + 正文 14px |
| 底部 | 品牌 LOGO + 二维码 |

---

## 七、_get_entity_image() 升级方案

### 现有代码（待替换）

```python
# 当前：只取第一张 photo，无质量/用途筛选
async def _get_entity_image(session, entity_id, city_code) -> Optional[str]:
    result = await session.execute(
        select(EntityMedia).where(
            EntityMedia.entity_id == entity_id,
            EntityMedia.media_type == "photo",
        ).limit(1)
    )
    media = result.scalar_one_or_none()
    if media and media.url:
        return media.url
    return _CITY_DEFAULT_IMAGES.get(city_code)
```

### 升级后

```python
async def get_entity_image(
    session: AsyncSession,
    entity_id: uuid.UUID,
    city_code: str,
    scene: str = "card",  # cover / card / xhs / share / thumbnail
    season: str | None = None,  # spring / summer / autumn / winter
) -> ImageResult:
    """
    按场景+季节选图，多级 fallback。
    返回 ImageResult(url, attribution_text, attribution_url)
    """
    # 1. 编辑精选（source=editorial, approved, usage_flags[scene]=true）
    # 2. 自动精选（approved, usage_flags[scene]=true, quality DESC）
    # 3. 季节匹配（approved, season_tag 匹配, quality DESC）
    # 4. 候选池（candidate, orientation 匹配, quality DESC）
    # 5. 城市兜底（city_defaults）
    # 6. None
```

---

## 八、自动化任务清单

| 任务 | 频率 | 方式 | 人工兜底 |
|---|---|---|---|
| 新图入池自动处理 | 实时（入库触发） | 异步 Job | 否 |
| 图片可用性检查 | 周一次全量 + 日一次热图 | 定时任务 | S/A 级失效时告警 |
| pHash 去重扫描 | 周一次 | 定时任务 | 否 |
| 低分图清理 | 月一次 | 定时任务 | 否（质量 < 40 自动清理） |
| S 级实体图片审核 | 持续 | 人工审核队列 | 必须 |
| 季节标签更新 | 季度一次 | 半自动（AI 标注 + 人工复核） | 是 |
| attribution 合规检查 | 月一次 | 定时扫描 license_type=unknown | 是 |
| CDN 转存积压处理 | 日一次 | 定时任务 | 否 |

---

## 九、实施优先级

| 阶段 | 任务 | 工时估算 | 价值 |
|---|---|---|---|
| **P0（必须）** | 横竖图字段 + orientation 自动检测 | 2h | 交付页不变形 |
| **P0** | status 字段 + 基础 approved/rejected 流程 | 3h | 质量可控 |
| **P0** | 升级 _get_entity_image → 按用途选图 | 3h | 各终端图片适配 |
| **P0** | 图片可用性定期检查 + 失效替补 | 4h | 不出现白框 |
| **P1** | 外链转存自有 CDN | 6h | 稳定性+速度 |
| **P1** | pHash 去重 | 3h | 避免重复图 |
| **P1** | 自动质量评分 | 6h | 减少人工审核量 |
| **P1** | attribution 管理 + 交付页展示 | 3h | 合规 |
| **P2** | 小红书配图自动裁切/拼接 | 4h | 内容运营效率 |
| **P2** | 分享卡片自动生成 | 4h | 传播 |
| **P2** | 季节/时段智能匹配 | 4h | 体验细节 |

---

## 变更日志

| 日期 | 变更 |
|---|---|
| 2026-03-21 | 初版，完成 S3 全部设计 |
