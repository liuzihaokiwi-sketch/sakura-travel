## 1. 图片缓存基础设施

- [ ] 1.1 创建 `web/lib/photo-cache.ts` — 实现 `fetchPhoto(url, cacheDir) → base64 dataURI` 函数，支持本地文件缓存到 `output/.photo-cache/`
- [ ] 1.2 创建 `web/lib/card-colors.ts` — 统一配色常量（bg-primary, accent, bloom-full 等）和 bloom stage 判断函数，供所有模板复用

## 2. 共享模板组件

- [ ] 2.1 创建 `web/lib/card-components.ts` — 公共 React.createElement 组件：FooterCTA、BrandMark、ScoreBadge、BloomBadge、SpotRow（依赖 1.2）
- [ ] 2.2 创建 `TemplateData` 接口定义，统一所有模板入参（依赖 1.1）

## 3. 模板实现 — xhs-cover

- [ ] 3.1 实现 `createXhsCoverElement(data: TemplateData)` — 城市 TOP3 排名封面，1080×1440，warm 色系（依赖 2.1, 2.2）

## 4. 模板实现 — xhs-spot

- [ ] 4.1 实现 `createXhsSpotElement(data: TemplateData, spotIndex: number)` — 单景点种草卡，实景照片背景 + 渐变叠加（依赖 1.1, 2.1）

## 5. 模板实现 — xhs-compare

- [ ] 5.1 实现 `createXhsCompareElement(allCities: TemplateData[])` — 多城市花期时间轴横向对比（依赖 2.1）

## 6. 模板实现 — wechat-moment

- [ ] 6.1 实现 `createMomentElement(data: TemplateData)` — 朋友圈方图 1080×1080，展示城市 TOP1 景点 + 能冲指数（依赖 2.1）

## 7. 模板实现 — xhs-story

- [ ] 7.1 实现 `createXhsStoryElement(data: TemplateData)` — 竖版 1080×1920，适合短视频封面/Instagram Story（依赖 2.1）

## 8. 脚本重写

- [ ] 8.1 重写 `web/scripts/export-satori.ts` — 新 CLI 解析：--template, --city, --spot, --all, --output（依赖 3.1~7.1）
- [ ] 8.2 实现批量图片预下载逻辑 — 按城市 TOP spots fetch photos → 缓存（依赖 1.1）
- [ ] 8.3 实现 `--all` 模式：5城 × 5模板批量生成，控制台输出进度（依赖 8.1, 8.2）

## 9. API 路由更新

- [ ] 9.1 更新 `web/app/api/share/card/route.tsx` — 支持新模板名称参数 `?type=xhs-cover&city=tokyo`（依赖 3.1~7.1）

## 10. 测试 & 验证

- [ ] 10.1 运行 `npx tsx scripts/export-satori.ts --template xhs-cover --city tokyo` 验证输出 PNG 正确
- [ ] 10.2 运行 `npx tsx scripts/export-satori.ts --all` 验证批量生成 25+ 文件
- [ ] 10.3 目视检查：配色一致、CTA 文案正确、能冲指数显眼、照片加载正常
