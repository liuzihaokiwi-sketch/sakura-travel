import type { Metadata } from "next";
import localFont from "next/font/local";
import { Suspense } from "react";
import { Navbar } from "@/components/shared/Navbar";
import { FloatingCTA } from "@/components/shared/FloatingCTA";
import { SakuraParticles } from "@/components/shared/SakuraParticles";
import "@fontsource/noto-serif-sc/400.css";
import "@fontsource/noto-serif-sc/700.css";
import "@fontsource/noto-serif-sc/900.css";
import "./globals.css";

const inter = localFont({
  src: [
    { path: "../public/fonts/inter-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "../public/fonts/inter-latin-700-normal.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-sans",
  display: "swap",
});

const playfair = localFont({
  src: [
    { path: "../public/fonts/playfair-display-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "../public/fonts/playfair-display-latin-700-normal.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-display",
  display: "swap",
});

const jetbrainsMono = localFont({
  src: [
    { path: "../public/fonts/jetbrains-mono-latin-400-normal.woff2", weight: "400", style: "normal" },
  ],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Sakura Rush 2026 · 全日本樱花追踪",
  description:
    "4大权威数据源融合 · 240+赏樱景点 · 每天3次更新 · 精准追樱不踩坑",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="zh-CN"
      className={`${inter.variable} ${playfair.variable} ${jetbrainsMono.variable}`}
    >
      <body className="font-sans antialiased bg-warm-50 text-stone-900">
        <SakuraParticles />
        <Suspense>
          <Navbar />
        </Suspense>
        <main className="relative z-10 pt-14">{children}</main>
        <Suspense>
          <FloatingCTA />
        </Suspense>
      </body>
    </html>
  );
}