# 大阪城上午 + 难波下午晚上｜固定生成命令

给接手模型看的执行口径：

- 不要直接调 `/v1/images/generations`。
- 不要自己拼 Responses API JSON。
- 只运行 `scripts/generate_handbook_image_saiai.py`。
- `--model` 是宿主对话模型，默认 `gpt-5`；真正图像模型由 `image_generation` tool 在 saiai 平台后端决定。
- 每张图只传一张场景参考 A + 一张画风参考 B。
- prompt 固定读 `prompts/*.txt`，不要临时把整份 brief 复制进命令。
- 参考图用途先看 [reference_index.md](./reference_index.md)。
- 脚本读取 `.env` 的 `SAIAI_BASE_URL` / `SAIAI_API_KEY`，不读取 saiai-cli 配置。当前已验证成功的 base url 是 `https://api.saiai.top`；key 只保存在 `.env`，不要写进本文档。
- 若返回 `503 no_available_account`，先换回 `.env` 中已验证成功的 saiai key；不要先改 prompt、尺寸或参考图。

## 已验证成功记录

2026-04-28 已用本文件方法成功生成：

```text
generated/osakajo_morning_hero_v1.png
status=200
size=1024x1536
bytes=3498820
```

2026-04-28 风格修正后，`osakajo_morning_hero_v2.png` 更接近目标：水墨毛边、纸感、速写线更明显。后续同类图优先沿用 v2 的短 prompt 与 `hozenji_namba_afternoon_v3.png` 风格 B 图。

## 必需图

### 大阪城主视觉

当前推荐版本：`generated\osakajo_morning_hero_v2.png`。v1 偏干净水彩，不作为目标风格参考。

如果后续同类图太干净、没有水墨毛边，优先用已验证风格图 `generated\hozenji_namba_afternoon_v3.png` 作为 B 图复跑。它的纸感、墨线和自然毛边是当前目标风格。

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --prompt-file japan\kansai\assets\routes\osaka\osakajo_namba\prompts\osakajo_morning_hero.txt `
  --image A=japan\kansai\assets\routes\osaka\osakajo_namba\references\scene\osakajo_morning_hero_photo_a.jpg `
  --image B=japan\kansai\assets\routes\osaka\osakajo_namba\generated\hozenji_namba_afternoon_v3.png `
  --size 1024x1536 `
  --quality medium `
  --out japan\kansai\assets\routes\osaka\osakajo_namba\generated\osakajo_morning_hero_v2.png
```

### 道顿堀夜景气氛

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --prompt-file japan\kansai\assets\routes\osaka\osakajo_namba\prompts\dotonbori_night_mood.txt `
  --image A=japan\kansai\assets\routes\osaka\osakajo_namba\references\scene\dotonbori_canal_photo_b.jpg `
  --image B=japan\kansai\assets\routes\osaka\osakajo_namba\references\style\style_inkwash_sketch_paris_a.jpg `
  --size 1536x1024 `
  --quality medium `
  --out japan\kansai\assets\routes\osaka\osakajo_namba\generated\dotonbori_night_mood_v1.png
```

## 已有可复跑图

### 大阪城到难波路线图

当前已有 `generated\osakajo_to_namba_route_map_v1.png`，但它更像路线插画，不是可读地图。正式地图先按单张素材处理，给 D7 半页到整页使用：图像只做底图、线路、编号点和空白，中文地名/站名由排版层叠加。

只有补齐 `references\scene\osaka_route_map_photo_a.png` 这类真实路线截图参考后才复跑；不要拿景点照片代替地图参考。地图生成优先一张过，先把真实参考图和本 prompt 固定好，再出 v2。

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --prompt-file japan\kansai\assets\routes\osaka\osakajo_namba\prompts\osakajo_to_namba_route_map.txt `
  --image A=japan\kansai\assets\routes\osaka\osakajo_namba\references\scene\osaka_route_map_photo_a.png `
  --image B=japan\kansai\assets\routes\osaka\osakajo_namba\generated\hozenji_namba_afternoon_v3.png `
  --size 1024x1536 `
  --quality medium `
  --out japan\kansai\assets\routes\osaka\osakajo_namba\generated\osakajo_to_namba_route_map_v2.png
```

### 法善寺 / 难波小巷

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --prompt-file japan\kansai\assets\routes\osaka\osakajo_namba\prompts\hozenji_namba_afternoon.txt `
  --image A=japan\kansai\assets\routes\osaka\osakajo_namba\references\scene\hozenji_alley_details_photo_a.jpg `
  --image B=japan\kansai\assets\routes\osaka\osakajo_namba\references\style\style_inkwash_sketch_paris_a.jpg `
  --size 1024x1536 `
  --quality medium `
  --out japan\kansai\assets\routes\osaka\osakajo_namba\generated\hozenji_namba_afternoon_v4.png
```

## 可选补图

### 大阪城纹理 / 石垣小品

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --prompt-file japan\kansai\assets\routes\osaka\osakajo_namba\prompts\osakajo_texture_stickers.txt `
  --image A=japan\kansai\assets\routes\osaka\osakajo_namba\references\scene\osakajo_texture_photo_a.jpg `
  --image B=japan\kansai\assets\routes\osaka\osakajo_namba\references\style\style_watercolor_soft_garden_a.jpg `
  --size 1024x1024 `
  --quality medium `
  --out japan\kansai\assets\routes\osaka\osakajo_namba\generated\osakajo_texture_stickers_v1.png
```

### 难波小店 / 橱窗小品

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --prompt-file japan\kansai\assets\routes\osaka\osakajo_namba\prompts\namba_shopfront_stickers.txt `
  --image A=japan\kansai\assets\routes\osaka\osakajo_namba\references\scene\namba_shopfront_details_photo_a.jpg `
  --image B=japan\kansai\assets\routes\osaka\osakajo_namba\references\style\style_inkwash_sketch_paris_a.jpg `
  --size 1024x1024 `
  --quality medium `
  --out japan\kansai\assets\routes\osaka\osakajo_namba\generated\namba_shopfront_stickers_v1.png
```

### 道顿堀招牌局部

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --prompt-file japan\kansai\assets\routes\osaka\osakajo_namba\prompts\dotonbori_sign_detail.txt `
  --image A=japan\kansai\assets\routes\osaka\osakajo_namba\references\scene\dotonbori_sign_photo_a.png `
  --image B=japan\kansai\assets\routes\osaka\osakajo_namba\references\style\style_inkwash_sketch_paris_a.jpg `
  --size 1536x1024 `
  --quality medium `
  --out japan\kansai\assets\routes\osaka\osakajo_namba\generated\dotonbori_sign_detail_v1.png
```
