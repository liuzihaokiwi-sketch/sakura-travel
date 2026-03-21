/** @type {import('next').NextConfig} */
const nextConfig = {
  // 阿里云 FC 部署：standalone 模式生成独立可运行包
  // 构建后执行：node .next/standalone/server.js
  output: "standalone",

  images: {
    remotePatterns: [
      // Unsplash 已迁移到本地 public/images/，仅保留天气图作为外部源
      { protocol: "https", hostname: "smtgvs.cdn.weathernews.jp" },
    ],
  },

  // 阿里云 OSS + CDN 静态资源路径
  // 生产环境设置环境变量 NEXT_PUBLIC_CDN_URL=https://cdn.yourdomain.com
  // 未设置时 assetPrefix 为空，本地开发不受影响
  assetPrefix: process.env.NEXT_PUBLIC_CDN_URL || "",

  experimental: {
    // Native .node binaries used by the XHS card API route (Node.js runtime)
    serverComponentsExternalPackages: ["@resvg/resvg-js"],
  },
};

export default nextConfig;