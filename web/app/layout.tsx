import type { Metadata } from "next";
import { Inter, Playfair_Display, Noto_Serif_SC, JetBrains_Mono } from "next/font/google";
import { Suspense } from "react";
import { Navbar } from "@/components/shared/Navbar";
import { FloatingCTA } from "@/components/shared/FloatingCTA";
import { SakuraParticles } from "@/components/shared/SakuraParticles";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const notoSerifSC = Noto_Serif_SC({
  subsets: ["latin"],
  weight: ["400", "700", "900"],
  variable: "--font-display-cjk",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
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
      className={`${inter.variable} ${playfair.variable} ${notoSerifSC.variable} ${jetbrainsMono.variable}`}
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
