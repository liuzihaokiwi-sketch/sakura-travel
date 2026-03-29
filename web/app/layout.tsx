import type { Metadata } from "next";
import localFont from "next/font/local";
import { Suspense } from "react";
import { Navbar } from "@/components/shared/Navbar";
import { FloatingCTA } from "@/components/shared/FloatingCTA";
import "@fontsource/noto-serif-sc/400.css";
import "@fontsource/noto-serif-sc/700.css";
import "@fontsource/noto-serif-sc/900.css";
import "./globals.css";

const inter = localFont({
  src: [
    { path: "../public/fonts/inter-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "../public/fonts/inter-latin-700-normal.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-inter",
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
  title: "旅行手账 · AI定制你的旅行规划",
  description: "一本替你想好一切的旅行手账。路线·餐厅·酒店·预算·Plan B，全部安排好。7天起 ¥198。",
  openGraph: {
    title: "旅行手账 · AI定制你的旅行规划",
    description: "一本替你想好一切的旅行手账。路线·餐厅·酒店·预算·Plan B，全部安排好。",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="zh-CN"
      className={`${inter.variable} ${jetbrainsMono.variable}`}
    >
      <body>
        <Suspense>
          <Navbar />
        </Suspense>
        <main style={{ paddingTop: "64px" }}>{children}</main>
        <Suspense>
          <FloatingCTA />
        </Suspense>
      </body>
    </html>
  );
}
