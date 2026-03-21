/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "smtgvs.cdn.weathernews.jp" },
    ],
  },
  experimental: {
    // Native .node binaries used by the XHS card API route (Node.js runtime)
    serverComponentsExternalPackages: ["@resvg/resvg-js"],
  },
};

export default nextConfig;