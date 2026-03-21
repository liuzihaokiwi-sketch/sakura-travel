/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "smtgvs.cdn.weathernews.jp" },
    ],
  },
};

export default nextConfig;