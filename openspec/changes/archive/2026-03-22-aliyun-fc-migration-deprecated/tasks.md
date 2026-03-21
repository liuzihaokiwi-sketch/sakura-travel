# 阿里云 FC 迁移任务

## 背景
前端部署在 Vercel，国内访问不稳定。迁移到阿里云函数计算（FC）+ OSS + CDN，实现国内秒开。

## 前提条件
- [ ] 域名 ICP 备案完成（7-15 个工作日）
- [ ] 开通阿里云 FC、OSS、CDN 服务

## 任务清单

### 1. 阿里云基础设施（🟢 运维操作）
- [ ] 1.1 开通函数计算 FC 3.0 服务，选择华东 2（上海）region ~5min
- [ ] 1.2 创建 OSS Bucket（存放静态资源），开启 CDN 加速 ~10min
- [ ] 1.3 域名绑定 + SSL 证书申请（阿里云免费证书）~10min

### 2. Next.js 构建适配（🟡 前端改动）
- [x] 2.1 `next.config.mjs` 添加 `output: "standalone"` 配置 ~5min
- [ ] 2.2 Edge Runtime → Node Runtime 改造：~30-60min
  - `app/api/share/card/route.tsx`：移除 `export const runtime = "edge"`，改为 Node runtime ✅
  - `app/api/share/xhs/route.tsx`：待检查（grep 未找到 edge runtime 声明）
  - 验证 `@vercel/og` (ImageResponse) 在 Node runtime 下正常工作，如不兼容则改用 `@resvg/resvg-js` + `satori` 直接调用
- [x] 2.3 检查是否有其他 Vercel 专属 API 使用（`@vercel/analytics`、`@vercel/speed-insights` 等），替换或移除 ~15min（未发现使用，已确认）

### 3. Serverless Devs 部署配置（🟡 运维 + 配置）
- [ ] 3.1 安装 Serverless Devs CLI：`npm i -g @serverless-devs/s` ~5min
- [ ] 3.2 创建 `s.yaml` 部署描述文件：~20min
  ```yaml
  edition: 3.0.0
  name: travel-ai-web
  resources:
    web:
      component: fc3
      props:
        region: cn-shanghai
        functionName: travel-ai-web
        runtime: custom.debian10
        handler: index.handler
        code: ./.next/standalone
        customRuntimeConfig:
          command: ["node", "server.js"]
          port: 3000
        environmentVariables:
          NEXT_PUBLIC_SUPABASE_URL: ${env.NEXT_PUBLIC_SUPABASE_URL}
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ${env.NEXT_PUBLIC_SUPABASE_ANON_KEY}
          # ... 其他环境变量
  ```
- [ ] 3.3 环境变量从 `.env.local` 迁移到 FC 控制台 ~10min

### 4. 静态资源分离到 OSS + CDN（🟢 运维操作）
- [ ] 4.1 构建后将 `.next/static/` 和 `public/` 上传到 OSS ~10min
- [x] 4.2 `next.config.mjs` 配置 `assetPrefix` 指向 CDN 域名 ~5min（读取 NEXT_PUBLIC_CDN_URL 环境变量）
- [ ] 4.3 CDN 缓存策略：图片/字体 30 天，JS/CSS 7 天 ~5min

### 5. CI/CD 自动化（🟢 可选，后续优化）
- [ ] 5.1 GitHub Actions workflow：push → build → deploy to FC ~30min
- [ ] 5.2 或使用阿里云云效 Flow 关联 GitHub 仓库 ~20min

### 6. 验证与切换（🟢 运维操作）
- [ ] 6.1 FC 部署后功能测试：首页、quiz、rush 花期地图、分享卡生成 ~20min
- [ ] 6.2 国内多地区测速（北京/上海/广州/成都）~10min
- [ ] 6.3 DNS 切换：域名从 Vercel CNAME → 阿里云 CDN CNAME ~5min
- [ ] 6.4 保留 Vercel 部署作为备用，不删除 ~0min

## 预计总耗时
- 有备案域名：**2-3 小时**
- 无备案域名：**+7-15 个工作日**（备案等待）

## 注意事项
- Supabase 在国内通常可访问，暂不迁移数据库
- 后端 FastAPI 独立部署（Docker），不在本次迁移范围
- 高德地图瓦片已在内网适配中完成替换
- 字体和图片已全部本地化，不再依赖外网 CDN
