/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  webpack: (config, { isServer }) => {
    if (isServer) {
      // 让 resvg-js 的 native binding 走 externals，不被 webpack 打包
      config.externals = [
        ...(config.externals || []),
        "@resvg/resvg-js",
      ];
    }
    return config;
  },
};

module.exports = nextConfig;
