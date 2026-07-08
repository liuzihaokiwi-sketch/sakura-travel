# 手账图片素材生成

> 适用范围：为实体手账生成动线图片、互动页素材、贴纸级素材  
> 推荐工具：GPT Image 2  
> 核心原则：先判断图片在手账页里占几分之几，再决定画幅、细节密度和提示词；每张图必须有独立 prompt，但不要为单张图反复堆补丁词

## 零、成品素材硬约束

这里生成的是“放进手账本里打印使用的单张素材图”，不是让模型画一本手账本、一本打开的书、一页排版稿或一张设计 mockup。

每张最终可用图必须满足：

- 只是一张完整画面或一组明确的贴纸素材，不出现手账本、书脊、装订线、翻页、圆角纸页、页面阴影、排版框、标题栏、文字说明。
- 除非明确生成贴纸组，否则一次只生成一张主体图，不要四宫格、拼贴板、contact sheet、before/after、多版本并排。
- 可直接裁切放入版面；画面边缘可以有水彩留白，但不能像一本已经装订好的本子。
- 没有可读文字、假字、品牌 logo、水印。
- 先看图再入库：没有美感、主体不清、像页面 mockup、像素材拼盘、风格不统一的图，不进入正式素材索引，只能放 `_review/` 或直接废弃。

提示词里可以写图片用途和页幅占比，但必须写成“for placement into a printed travel journal layout as an image asset”。不要写成“draw a printed handbook page / journal spread / page design”。

## 一、基本流程

每条动线需要生成图片时，先在对应素材目录建立图片生成说明：

```text
japan/kansai/assets/routes/{city}/{route_id}/image_generation_brief.md
```

每张图片都单独准备：

1. 图 A：具体景色实拍，用来锁定真实场景、构图元素、空间关系
2. 图 B：统一画风参考，用来控制手账插画质感、色彩、线条、纸感
3. 图片用途：放在哪个跨页、哪一侧、承担什么功能
4. 页幅占比：例如二分之一页、三分之一页、八分之一页
5. 画幅尺寸：例如竖图 `1*2`、竖图 `2*3`、横图 `3*2`、方图 `1*1`
6. 英文 GPT Image 2 prompt
7. 英文 negative prompt

不要用一条通用 prompt 生成整组图片。每张图都必须有自己的提示词。

## 二、页幅与细节密度

| 页幅占比 | 常见用途 | 画幅建议 | 细节密度 |
|---|---|---|---|
| 二分之一页到三分之二页 | 当天唯一主视觉、上午/下午主视觉 | 竖图 `1*2` 或 `2*3` | 高，主体和环境都要清楚 |
| 三分之一页到二分之一页 | 夜晚气氛块、街区中图、地图 | 横图 `3*2`、竖图 `2*3`、方图 `1*1` | 中高，构图集中 |
| 四分之一页 | 局部招牌、纹理、互动页辅助图 | 横图 `3*2` 或方图 `1*1` | 中等，一眼能辨认 |
| 八分之一页到六分之一页 | 食物贴纸、角色、纸胶带感小图 | 方图 `1*1` | 低到中，轮廓清楚优先 |

一天里不要堆太多大图。普通完整日建议：

- 最多 1 张二分之一页以上的大图
- 1-2 张三分之一页左右的中图
- 其余用贴纸、小图、色块和留白

## 三、目录规范

推荐结构（references 分两层，避免画风/实景混在一起）：

```text
japan/kansai/assets/routes/{city}/{route_id}/
  image_generation_brief.md
  references/
    style/
      style_reference_b.png                ← 主画风（每条动线只挑一张当主）
      style_{flavor}_{tag}_a.jpg           ← 备用风格池，按场景挑
    scene/
      {asset_name}_photo_a.jpg             ← 实景参考图 A（地点/构图）
      {asset_name}_photo_b.jpg             ← 同一对象不同角度补充
    _review/
      {whatever}.jpg                        ← 暂存待筛
  generated/
    {asset_name}_v{n}.png                  ← 生成结果按版本递增
```

命名约定：

- 实景参考统一带 `_photo_a` 后缀；同对象多张时第二张用 `_photo_b`
- 画风参考统一带 `style_` 前缀；主画风固定叫 `style_reference_b.png`
- 生成结果带 `_v1 / _v2` 版本号，方便对比；选定版去掉版本号正式入库
- 不入库的废图直接删，不保留 `_bad / _ng` 命名

## 四、提示词写法

优先使用“短规则 + 场景变量”的写法，不要把每张图都写成很长的修补清单。提示词目标是稳定复现图 A 的真实场景，并套用图 B 的手账画风。

通用规则：

- 图 A 是构图和地点真实性的主依据，默认保留图 A 里能帮助识别地点的元素。
- 图 B 只控制画风、纸感、线条和边界，不改变地点结构。
- 红灯笼、招牌、店灯、石板路、桥栏等真实现场元素，除非明显干扰画面，否则不要禁止。
- 可以减少遮挡主体的人、拥挤游客、过密电线、临时施工物、垃圾桶等影响阅读的小噪音。
- 不要把街景处理成完全无人；少量店员、远处行人、自然经过的人可以保留，让画面有生活感。
- 边缘可以做水墨晕染、纸张留白或松散笔触，让图片适合排进手账。
- prompt 尽量短，先写“保留什么”，再写“清理什么”，最后写“套用什么风格”。
- negative prompt 只写全局禁忌，不针对单张图不断补丁。
- 灯笼、招牌、菜单牌可以保留形状和氛围，但不要追求可读文字；生成结果里出现假字时，后续统一用“no readable text”约束。

### Kiwi 形象插入规则

Kiwi 是可选的手账陪伴角色，不是每张图都要出现。只有当画面有自然位置时才插入，避免破坏真实地点识别。

- 适合插入：地图、贴纸组、留白边角、互动页、小物件图、路线提示图、画面边缘的观察者位置。
- 谨慎插入：街巷、餐饮、交通小景，可以作为很小的店员旁观察者、角落贴纸、手账边注感小角色。
- 不建议插入：当天主视觉大图、需要强真实感的地标图、夜景主体、空间已经很满的照片转插画。
- Kiwi 应保持简单圆润的线稿形象：小圆身体、短翅膀、长喙、黑豆眼、头顶三撮毛，可拿地图、相机、手账或小旗。
- 风格必须跟图 B 统一：水彩/墨线/纸感；不要做成突兀贴纸、3D 吉祥物或彩色卡通头像。
- Kiwi 不能遮挡地标、店招、路线主体，也不要出现品牌字样或口号。

每张图的 prompt 至少包含：

- 使用图 A 保持真实地点结构
- 使用图 B 匹配手账画风
- 图片在手账中的用途和页幅占比
- 画幅方向，例如 vertical `1*2` / horizontal `3*2`
- 主体、背景、留白、细节密度
- 不允许牺牲地点识别度

示例结构：

```text
Create one standalone [vertical / horizontal / square] illustration asset based on reference image A for [real place / object], while matching the visual style, line quality, paper texture, and color mood of reference image B.

Preserve [key real elements]. The image is only an artwork asset for placement into a printed travel journal layout, not a page mockup. Keep the composition [simple / detailed enough], leave [negative space / margin] for layout, and make sure the subject remains readable at about [page fraction] page size.

Composition: [aspect ratio], [main subject placement], [detail density], [mood].
Output: exactly one complete image, not a book, not a journal page, not a four-panel grid, not a collage sheet.
```

Negative prompt 至少包含：

- 不要文字或假字
- 不要过度写实照片滤镜
- 不要赛博朋克/幻想化/过饱和，除非该动线本来需要
- 不要人群挤满主体
- 不要加入参考图没有的大型元素
- 不要手账本、打开的书、页面 mockup、四宫格、多版本拼贴

## 五、saiai / Responses API 生成方法

saiai 当前可用路径是 Responses API 的流式接口，不是旧的 `/v1/images/generations`。

固定执行口径：

- 只用项目脚本 `scripts/generate_handbook_image_saiai.py`，不要让接手模型直接拼 API JSON。
- 不使用旧接口 `/v1/images/generations`，本项目走 `/v1/responses` + `image_generation` tool。
- 每张图的完整提示词先落盘到动线目录 `prompts/{asset_name}.txt`，命令只读 `--prompt-file`。
- 每条动线建立 `generate_images.md`，里面放可直接复制执行的 PowerShell 命令；接手模型优先读这个文件。
- 脚本里 `--model` 是宿主对话模型（默认 `gpt-5`），真正画图的是 image_generation tool，对应平台后端的 GPT Image 2，不需要在命令里指定图像模型。
- 脚本只读取当前进程环境变量或项目 `.env` 里的 `SAIAI_BASE_URL` / `SAIAI_API_KEY`，不读取 `saiai-cli init` 或 `init-codex` 写入的 CLI 配置。
- `.env` 中已验证可用的配置口径是 `SAIAI_BASE_URL=https://api.saiai.top` + 当前可用的 `SAIAI_API_KEY`；不要把 key 写进 SOP、brief、命令文档或聊天记录。

推荐用项目脚本生成：

竖图主视觉（大阪城等，1*2 比例）：

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --prompt-file tmp\prompt.txt `
  --image A=japan\kansai\assets\routes\osaka\osakajo_namba\references\scene\osakajo_morning_hero_photo_a.jpg `
  --image B=japan\kansai\assets\routes\osaka\osakajo_namba\references\style\style_reference_b.png `
  --size 1024x1536 `
  --quality medium `
  --out japan\kansai\assets\routes\osaka\osakajo_namba\generated\osakajo_morning_hero_v1.png
```

横图夜景（道顿堀夜景，3*2 比例）：

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --prompt-file tmp\prompt.txt `
  --image A=japan\kansai\assets\routes\osaka\osakajo_namba\references\scene\dotonbori_canal_photo_b.jpg `
  --image B=japan\kansai\assets\routes\osaka\osakajo_namba\references\style\style_reference_b.png `
  --size 1536x1024 `
  --quality medium `
  --out japan\kansai\assets\routes\osaka\osakajo_namba\generated\dotonbori_night_mood_v1.png
```

方图贴纸/纹理（食物贴纸、石垣纹理，1*1 比例）：

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --prompt-file tmp\prompt.txt `
  --image A=japan\kansai\assets\routes\osaka\osakajo_namba\references\scene\osakajo_texture_photo_a.jpg `
  --image B=japan\kansai\assets\routes\osaka\osakajo_namba\references\style\style_reference_b.png `
  --size 1024x1024 `
  --quality medium `
  --out japan\kansai\assets\routes\osaka\osakajo_namba\generated\osakajo_texture_stickers_v1.png
```

`--size` 可选值：`1024x1024` / `1024x1536`（竖）/ `1536x1024`（横）；`--quality` 在 `low/medium/high` 之间选，medium 一般够手账打印（300dpi 下 11cm 单页只占 1300px 宽）。

脚本会做三件事来避免 `413 Payload Too Large`：

- 参考图先压缩到较小长边，再转 base64。
- 发送前计算 JSON payload 体积，默认超过约 `7 MB` 就本地中止。
- 如果仍然过大，自动降低参考图尺寸和 JPEG 质量；还过大时，改为少传参考图或缩短 prompt。

执行规则：

- token 只读环境变量或 `.env`，不要写进脚本、SOP、brief 或聊天记录。
- 只传必要参考图。通常一张图 A + 一张图 B 足够。
- prompt 不要整段复制整份 brief，只复制当前单图需要的短 prompt。
- `stream: true` 只解决返回图片的问题，不能降低上传体积；上传太大仍会 413。
- 如果出现 404，优先检查是否误用了 `/v1/images/generations`；本项目应走 `/v1/responses`。
- 如果出现 413，先减图、减 prompt、减参考图数量，不要反复重试同一个大请求。
- 如果出现 `503 no_available_account`，优先检查当前 `.env` 的 `SAIAI_API_KEY` 是否是已验证可用账号；这通常是 saiai 账号池 / key 问题，不是 prompt、图片尺寸或 `--quality` 问题。
- 验证通过的成功特征：命令输出 `status=200`，随后出现 `saved=... bytes=...`；生成文件应能用 PIL 打开并有非零尺寸。

## 六、素材归属

动线专属素材放：

```text
japan/kansai/assets/routes/{city}/{route_id}/
```

城市或圈层可复用素材放：

```text
japan/kansai/assets/finished/
japan/kansai/assets/raw/
```

模板 JSON 不直接承载图片文件路径。后续由通用渲染配置按 `route_id + page_role + asset_role` 读取素材索引。

## 七、和每日页型的关系

图片生成前先读：

- [每日手账页型设计.md](docs/操作SOP/上线前/手账/每日手账页型设计.md)

基础执行跨页和互动跨页都按“左页 / 右页”成组设计。图片只服务页面功能，不为了好看而挤占执行信息。
