"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// 在这些路径下不显示浮动CTA（用户已在流程中）
const HIDE_PATHS = ["/order", "/form", "/guide"];

export function FloatingCTA() {
  const pathname = usePathname();

  const shouldHide = HIDE_PATHS.some((p) => pathname.startsWith(p));
  if (shouldHide) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 40,
        backgroundColor: "#FFFFFF",
        boxShadow: "0 -2px 12px rgba(61, 48, 41, 0.10)",
        padding: "12px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
      className="floating-cta-bar"
    >
      <div>
        <span
          style={{
            fontFamily: '"Noto Serif SC", serif',
            fontSize: "15px",
            fontWeight: 600,
            color: "#2D4A3E",
          }}
        >
          7天定制手账
        </span>
        <span
          style={{
            fontSize: "14px",
            color: "#8B7E74",
            marginLeft: "8px",
          }}
        >
          ¥198 起
        </span>
      </div>
      <Link
        href="/order"
        style={{
          backgroundColor: "#C65D3E",
          color: "white",
          borderRadius: "12px",
          padding: "10px 20px",
          fontSize: "14px",
          fontWeight: 600,
          textDecoration: "none",
          whiteSpace: "nowrap",
          transition: "background-color 200ms ease",
        }}
      >
        开始定制 →
      </Link>

      <style>{`
        @media (min-width: 769px) {
          .floating-cta-bar { display: none !important; }
        }
      `}</style>
    </div>
  );
}
