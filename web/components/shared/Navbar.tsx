"use client";

import Link from "next/link";
import { useSearchParams, usePathname } from "next/navigation";
import { useState, useEffect } from "react";

const NAV_ITEMS = [
  { href: "/", label: "首页" },
  { href: "/tools", label: "工具" },
  { href: "/faq", label: "常见问题" },
  { href: "/contact", label: "联系我们" },
];

export function Navbar() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const isExport = searchParams.get("export") === "true";
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  if (isExport) return null;

  return (
    <nav
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        height: "64px",
        transition: "background-color 300ms ease, box-shadow 300ms ease",
        backgroundColor: scrolled ? "rgba(251, 247, 240, 0.92)" : "transparent",
        backdropFilter: scrolled ? "blur(12px)" : "none",
        boxShadow: scrolled ? "0 1px 3px rgba(61, 48, 41, 0.08)" : "none",
      }}
    >
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px",
        }}
      >
        {/* Logo */}
        <Link
          href="/"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            textDecoration: "none",
          }}
        >
          <span
            style={{
              fontFamily: '"Noto Serif SC", serif',
              fontSize: "18px",
              fontWeight: 700,
              color: "#2D4A3E",
              letterSpacing: "-0.02em",
            }}
          >
            旅行手账
          </span>
        </Link>

        {/* 桌面端导航 */}
        <div
          className="hidden-mobile"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
          }}
        >
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              style={{
                padding: "6px 16px",
                borderRadius: "8px",
                fontSize: "14px",
                fontWeight: 500,
                color: pathname === item.href ? "#2D4A3E" : "#8B7E74",
                backgroundColor: pathname === item.href ? "#F5F0E8" : "transparent",
                textDecoration: "none",
                transition: "all 200ms ease",
              }}
              onMouseEnter={(e) => {
                if (pathname !== item.href) {
                  (e.target as HTMLElement).style.color = "#3D3029";
                  (e.target as HTMLElement).style.backgroundColor = "#F5F0E8";
                }
              }}
              onMouseLeave={(e) => {
                if (pathname !== item.href) {
                  (e.target as HTMLElement).style.color = "#8B7E74";
                  (e.target as HTMLElement).style.backgroundColor = "transparent";
                }
              }}
            >
              {item.label}
            </Link>
          ))}
          <Link
            href="/admin"
            style={{
              marginLeft: "8px",
              padding: "6px 12px",
              borderRadius: "8px",
              fontSize: "13px",
              color: "#A69B91",
              textDecoration: "none",
              transition: "color 200ms ease",
            }}
          >
            管理
          </Link>
        </div>

        {/* 移动端汉堡 */}
        <button
          className="show-mobile"
          onClick={() => setMobileOpen(!mobileOpen)}
          style={{
            display: "none",
            flexDirection: "column",
            gap: "5px",
            padding: "8px",
            background: "none",
            border: "none",
            cursor: "pointer",
          }}
          aria-label="菜单"
        >
          <span
            style={{
              width: "22px",
              height: "2px",
              backgroundColor: "#3D3029",
              display: "block",
              transition: "transform 200ms ease",
              transform: mobileOpen ? "rotate(45deg) translate(5px, 5px)" : "none",
            }}
          />
          <span
            style={{
              width: "22px",
              height: "2px",
              backgroundColor: "#3D3029",
              display: "block",
              opacity: mobileOpen ? 0 : 1,
              transition: "opacity 200ms ease",
            }}
          />
          <span
            style={{
              width: "22px",
              height: "2px",
              backgroundColor: "#3D3029",
              display: "block",
              transition: "transform 200ms ease",
              transform: mobileOpen ? "rotate(-45deg) translate(5px, -5px)" : "none",
            }}
          />
        </button>
      </div>

      {/* 移动端菜单 */}
      {mobileOpen && (
        <div
          style={{
            backgroundColor: "#FBF7F0",
            borderTop: "1px solid #E8E0D6",
            padding: "12px 24px 20px",
          }}
        >
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              style={{
                display: "block",
                padding: "12px 0",
                fontSize: "16px",
                fontWeight: 500,
                color: pathname === item.href ? "#2D4A3E" : "#3D3029",
                textDecoration: "none",
                borderBottom: "1px solid #F0EAE2",
              }}
            >
              {item.label}
            </Link>
          ))}
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .hidden-mobile { display: none !important; }
          .show-mobile { display: flex !important; }
        }
        @media (min-width: 769px) {
          .show-mobile { display: none !important; }
          .hidden-mobile { display: flex !important; }
        }
      `}</style>
    </nav>
  );
}
