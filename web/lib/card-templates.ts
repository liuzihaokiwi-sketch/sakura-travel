/**
 * Satori social card templates v2.
 *
 * 5 templates for XHS/WeChat distribution:
 *   1. xhs-cover    — City TOP3 ranking cover (1080×1440)
 *   2. xhs-spot     — Single spot with real photo (1080×1440)
 *   3. xhs-compare  — Multi-city bloom comparison (1080×1440)
 *   4. wechat-moment — Square moment card (1080×1080)
 *   5. xhs-story    — Vertical story (1080×1920)
 */

import React from "react";
import { C, BRAND, CITY_NAMES, getBloomInfo } from "./card-colors";
import type { Spot } from "./data";

const h = React.createElement;

// ── Shared types ────────────────────────────────────────────────────────────

export interface TemplateData {
  city: string;
  cityName: string;
  spots: Spot[];
  photoBuffers: Record<string, string>; // name → base64 data URI
  updatedAt: string;
}

// ── Shared sub-components ───────────────────────────────────────────────────

function FooterCTA() {
  return h("div", {
    style: {
      display: "flex", flexDirection: "column", alignItems: "center",
      borderTop: `1px solid ${C.divider}`, padding: "40px 40px 36px",
      background: C.bgPrimary,
    },
  },
    h("div", { style: { fontSize: "44px", color: C.textPrimary, fontWeight: 800 } }, BRAND.ctaPrimary),
    h("div", { style: { fontSize: "38px", color: C.accent, marginTop: "14px", fontWeight: 800 } }, BRAND.ctaSecondary),
    h("div", { style: { display: "flex", gap: "8px", marginTop: "18px", alignItems: "center" } },
      h("div", { style: { fontSize: "26px", color: C.textMuted, letterSpacing: "3px", fontWeight: 600 } }, BRAND.title),
      h("div", { style: { fontSize: "26px", color: C.textLight } }, "·"),
      h("div", { style: { fontSize: "26px", color: C.textMuted, fontWeight: 600 } }, BRAND.subtitle),
    ),
  );
}

function BrandHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return h("div", {
    style: {
      display: "flex", flexDirection: "column", alignItems: "center",
      padding: "56px 40px 44px",
      background: `linear-gradient(180deg, ${C.bgDark} 0%, ${C.bgDarkSoft} 100%)`,
    },
  },
    h("div", { style: { display: "flex", alignItems: "center", gap: "12px", marginBottom: "18px" } },
      h("div", { style: { fontSize: "40px", color: C.bloomFull } }, "✿"),
      h("div", { style: { fontSize: "32px", color: "rgba(255,255,255,0.4)", letterSpacing: "4px", fontWeight: 700 } }, BRAND.title),
    ),
    h("div", { style: { fontSize: "72px", fontWeight: 900, color: C.white, textAlign: "center" } }, title),
    subtitle ? h("div", { style: { fontSize: "38px", color: "rgba(255,255,255,0.5)", marginTop: "12px", fontWeight: 600 } }, subtitle) : null,
  );
}

function ScoreBadge({ score, size = "large" }: { score: number; size?: "large" | "small" }) {
  const fontSize = size === "large" ? "72px" : "48px";
  const labelSize = size === "large" ? "24px" : "20px";
  return h("div", { style: { display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 } },
    h("div", { style: { fontSize, fontWeight: 900, color: C.accent } }, `${score}`),
    h("div", { style: { fontSize: labelSize, color: C.textMuted, marginTop: "2px", fontWeight: 700 } }, "好看指数"),
  );
}

function BloomBadge({ spot }: { spot: Spot }) {
  const bloom = getBloomInfo(spot);
  return h("div", {
    style: {
      display: "flex", alignItems: "center", gap: "10px",
      background: bloom.color + "20", borderRadius: "12px",
      padding: "10px 20px",
    },
  },
    h("div", { style: { fontSize: "30px" } }, bloom.emoji),
    h("div", { style: { fontSize: "30px", color: bloom.color, fontWeight: 800 } }, bloom.labelCn),
  );
}

function TagPill({ text, color = C.textSecondary }: { text: string; color?: string }) {
  return h("div", {
    style: {
      display: "flex", fontSize: "30px", color, fontWeight: 600,
      background: color + "15", borderRadius: "12px", padding: "8px 18px",
    },
  }, text);
}

// ── 1. XHS Cover — City TOP3 ────────────────────────────────────────────────

export function createXhsCoverElement(data: TemplateData): React.ReactElement {
  const top3 = data.spots.slice(0, 3);

  return h("div", {
    style: {
      display: "flex", flexDirection: "column", width: "100%", height: "100%",
      background: C.bgPrimary, fontFamily: "Noto Sans SC",
    },
  },
    // Header
    BrandHeader({ title: `${data.cityName} 赏樱 TOP3`, subtitle: "数据融合排名 · 每天更新" }),
    // Decorative accent line
    h("div", { style: { display: "flex", height: "4px", background: `linear-gradient(90deg, ${C.accent}, ${C.bloomFull}, ${C.accent})` } }),
    // Spot list — each card uses flex:1 to fill the space equally
    h("div", { style: { display: "flex", flexDirection: "column", flex: 1, padding: "24px 40px 16px", gap: "20px" } },
      ...top3.map((spot, i) => {
        const bloom = getBloomInfo(spot);
        const photoUri = data.photoBuffers[spot.name];
        return h("div", {
          key: i,
          style: {
            display: "flex", alignItems: "center", gap: "20px", flex: 1,
            background: i === 0 ? C.accentLight : C.white,
            borderRadius: "20px", padding: "0 28px",
            border: i === 0 ? `2px solid ${C.accent}` : `1px solid ${C.divider}`,
          },
        },
          // Rank
          h("div", {
            style: {
              display: "flex", alignItems: "center", justifyContent: "center",
              width: "72px", height: "72px", borderRadius: "50%",
              background: i === 0 ? C.accent : i === 1 ? "#c0c0c0" : "#cd7f32",
              flexShrink: 0,
            },
          }, h("div", { style: { fontSize: "36px", fontWeight: 900, color: C.white } }, `${i + 1}`)),
          // Photo thumbnail — 140×140
          photoUri
            ? h("img", { src: photoUri, width: 140, height: 140, style: { borderRadius: "16px", objectFit: "cover", flexShrink: 0 } })
            : h("div", { style: { width: "140px", height: "140px", borderRadius: "16px", background: `linear-gradient(135deg, ${C.divider}, ${C.bgPrimary})`, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" } },
                h("div", { style: { fontSize: "48px", opacity: 0.3, color: C.bloomFull } }, "✿")),
          // Info
          h("div", { style: { display: "flex", flexDirection: "column", flex: 1, gap: "10px" } },
            h("div", { style: { fontSize: i === 0 ? "42px" : "36px", fontWeight: 700, color: C.textPrimary } }, spot.name),
            h("div", { style: { display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" } },
              h("div", { style: { display: "flex", alignItems: "center", gap: "8px", background: bloom.color + "18", borderRadius: "10px", padding: "6px 16px" } },
                h("div", { style: { fontSize: "28px", color: bloom.color, fontWeight: 600 } }, `${bloom.emoji} ${bloom.labelCn}`),
              ),
              spot.full ? h("div", { style: { fontSize: "28px", color: C.textSecondary } }, `满开 ${spot.full}`) : null,
            ),
            spot.lightup ? h("div", { style: { display: "flex", alignItems: "center", gap: "8px" } },
              h("div", { style: { width: "10px", height: "10px", borderRadius: "50%", background: "#6366f1" } }),
              h("div", { style: { fontSize: "26px", color: "#6366f1" } }, "夜樱灯光"),
            ) : null,
          ),
          // Score
          h("div", { style: { display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 } },
            h("div", { style: { fontSize: i === 0 ? "76px" : "60px", fontWeight: 900, color: C.accent } }, `${spot.score}`),
            h("div", { style: { fontSize: "22px", color: C.textMuted, marginTop: "2px", fontWeight: 700 } }, "好看指数"),
          ),
        );
      }),
    ),
    // Footer
    FooterCTA(),
  );
}

// ── 2. XHS Spot — Single spot spotlight ─────────────────────────────────────

export function createXhsSpotElement(data: TemplateData, spotIndex = 0): React.ReactElement {
  const spot = data.spots[spotIndex];
  const bloom = getBloomInfo(spot);
  const photoUri = data.photoBuffers[spot.name];

  return h("div", {
    style: {
      display: "flex", flexDirection: "column", width: "100%", height: "100%",
      fontFamily: "Noto Sans SC",
    },
  },
    // Hero photo area (top 55%)
    h("div", {
      style: {
        display: "flex", flexDirection: "column", justifyContent: "flex-end",
        position: "relative", height: "55%", overflow: "hidden",
        background: photoUri ? C.bgDark : `linear-gradient(135deg, ${C.bgDark} 0%, #3d1a2a 100%)`,
      },
    },
      // Background image
      photoUri ? h("img", {
        src: photoUri, width: 1080, height: 792,
        style: { position: "absolute", top: 0, left: 0, width: "100%", height: "100%", objectFit: "cover" },
      }) : null,
      // Gradient overlay
      h("div", {
        style: {
          position: "absolute", bottom: 0, left: 0, right: 0, height: "60%",
          background: "linear-gradient(transparent, rgba(0,0,0,0.7))",
        },
      }),
      // Text overlay
      h("div", { style: { position: "relative", padding: "0 48px 36px", display: "flex", flexDirection: "column" } },
        h("div", { style: { display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" } },
          h("div", {
            style: {
              display: "flex", padding: "6px 16px", borderRadius: "10px",
              background: bloom.color + "30", border: `1px solid ${bloom.color}60`,
            },
          }, h("div", { style: { fontSize: "30px", color: C.white } }, `${bloom.emoji} ${bloom.labelCn}`)),
          spot.meisyo100 ? h("div", {
            style: { display: "flex", padding: "8px 18px", borderRadius: "12px", background: "rgba(245,158,11,0.3)", border: "1px solid rgba(245,158,11,0.6)" },
          }, h("div", { style: { fontSize: "30px", color: C.white } }, "★ 名所百选")) : null,
        ),
        h("div", { style: { fontSize: "76px", fontWeight: 900, color: C.white, lineHeight: 1.2 } }, spot.name),
        h("div", { style: { fontSize: "36px", color: "rgba(255,255,255,0.6)", marginTop: "8px", fontWeight: 600 } }, `${data.cityName} · ${spot.region || ""}`),
      ),
    ),
    // Info area (bottom 45%)
    h("div", {
      style: {
        display: "flex", flexDirection: "column", flex: 1,
        background: C.bgPrimary, padding: "32px 48px",
      },
    },
      // Score row
      h("div", { style: { display: "flex", alignItems: "center", gap: "20px", marginBottom: "24px" } },
        h("div", { style: { fontSize: "108px", fontWeight: 900, color: C.accent } }, `${spot.score}`),
        h("div", { style: { display: "flex", flexDirection: "column" } },
          h("div", { style: { fontSize: "34px", color: C.textMuted, fontWeight: 800 } }, "好看指数 / 100"),
          h("div", { style: { fontSize: "28px", color: C.textSecondary, marginTop: "6px", fontWeight: 600 } }, "满开时好看程度 · 综合6大数据源"),
        ),
      ),
      // Tags row
      h("div", { style: { display: "flex", flexWrap: "wrap", gap: "12px", marginBottom: "20px" } },
        spot.full ? TagPill({ text: `✿ 满开 ${spot.full}`, color: C.bloomFull }) : null,
        spot.half ? TagPill({ text: `❀ 五分咲 ${spot.half}`, color: C.bloomHalf }) : null,
        spot.trees ? TagPill({ text: `♣ ${spot.trees}` }) : null,
        spot.lightup ? TagPill({ text: "夜樱灯光", color: "#6366f1" }) : null,
      ),
      // Description
      spot.desc_cn
        ? h("div", { style: { fontSize: "30px", color: C.textSecondary, lineHeight: 1.6, marginBottom: "16px", fontWeight: 500 } }, spot.desc_cn.slice(0, 80) + (spot.desc_cn.length > 80 ? "..." : ""))
        : null,
      // Spacer
      h("div", { style: { flex: 1 } }),
    ),
    // Footer
    FooterCTA(),
  );
}

// ── 3. XHS Compare — Multi-city timeline ────────────────────────────────────

export function createXhsCompareElement(allCities: TemplateData[]): React.ReactElement {
  const cities = allCities.slice(0, 5);

  // Generate simplified bloom timeline for a city
  function getCityTimeline(data: TemplateData) {
    // For visualization: mark which half-month periods have blooming
    const periods = ["3月上", "3月中", "3月下", "4月上", "4月中", "4月下"];
    const spotsWithFull = data.spots.filter((s) => s.full);
    const stages: number[] = periods.map((_, pi) => {
      const monthRef = pi < 3 ? 3 : 4;
      const dayRef = (pi % 3) * 10 + 10;
      let maxStage = 0;
      for (const s of spotsWithFull) {
        if (!s.full) continue;
        const [m, d] = s.full.split("/").map(Number);
        if (!m || !d) continue;
        const diff = (monthRef - m) * 30 + (dayRef - d);
        if (Math.abs(diff) <= 5) maxStage = Math.max(maxStage, 2); // full
        else if (Math.abs(diff) <= 12) maxStage = Math.max(maxStage, 1); // approaching
      }
      return maxStage;
    });
    return { periods, stages };
  }

  return h("div", {
    style: {
      display: "flex", flexDirection: "column", width: "100%", height: "100%",
      background: C.bgPrimary, fontFamily: "Noto Sans SC",
    },
  },
    BrandHeader({ title: "花期时间轴对比", subtitle: "什么时候去哪个城市最好？" }),
    h("div", { style: { display: "flex", flexDirection: "column", flex: 1, padding: "36px 48px", gap: "8px" } },
      // Period labels
      h("div", { style: { display: "flex", alignItems: "center", gap: "4px", marginBottom: "12px" } },
        h("div", { style: { width: "100px", flexShrink: 0 } }),
        ...["3月上", "3月中", "3月下", "4月上", "4月中", "4月下"].map((p) =>
          h("div", { key: p, style: { flex: 1, fontSize: "24px", color: C.textMuted, textAlign: "center" } }, p)
        ),
      ),
      // City rows
      ...cities.map((cityData) => {
        const { stages } = getCityTimeline(cityData);
        return h("div", {
          key: cityData.city,
          style: { display: "flex", alignItems: "center", gap: "4px", marginBottom: "16px" },
        },
          h("div", { style: { width: "120px", flexShrink: 0, fontSize: "30px", fontWeight: 700, color: C.textPrimary } }, cityData.cityName),
          ...stages.map((s, i) =>
            h("div", {
              key: i,
              style: {
                flex: 1, height: "48px", borderRadius: "10px",
                background: s === 0 ? C.divider : s === 1 ? "#fbcfe8" : C.bloomFull,
              },
            })
          ),
        );
      }),
      // Legend
      h("div", { style: { display: "flex", gap: "24px", justifyContent: "center", marginTop: "20px" } },
        h("div", { style: { display: "flex", alignItems: "center", gap: "8px" } },
          h("div", { style: { width: "24px", height: "24px", borderRadius: "6px", background: C.divider } }),
          h("div", { style: { fontSize: "24px", color: C.textMuted } }, "未开"),
        ),
        h("div", { style: { display: "flex", alignItems: "center", gap: "8px" } },
          h("div", { style: { width: "28px", height: "28px", borderRadius: "6px", background: "#fbcfe8" } }),
          h("div", { style: { fontSize: "24px", color: C.textMuted } }, "五分咲"),
        ),
        h("div", { style: { display: "flex", alignItems: "center", gap: "8px" } },
          h("div", { style: { width: "28px", height: "28px", borderRadius: "6px", background: C.bloomFull } }),
          h("div", { style: { fontSize: "24px", color: C.textMuted } }, "満開"),
        ),
      ),
      // Best timing callout
      h("div", {
        style: {
          display: "flex", flexDirection: "column", alignItems: "center",
          background: C.accentLight, borderRadius: "16px", padding: "24px",
          border: `1px solid ${C.accent}40`, marginTop: "24px",
        },
      },
        h("div", { style: { fontSize: "32px", fontWeight: 700, color: C.textPrimary } }, "▸ 最佳出行时间"),
        h("div", { style: { fontSize: "28px", color: C.textSecondary, marginTop: "8px", textAlign: "center" } },
          "东京 3月下旬 · 京都/大阪 4月上旬 · 满开仅持续 5-7 天"
        ),
      ),
      h("div", { style: { flex: 1 } }),
    ),
    FooterCTA(),
  );
}

// ── 4. WeChat Moment — Square card ──────────────────────────────────────────

export function createMomentElement(data: TemplateData): React.ReactElement {
  const spot = data.spots[0];
  const bloom = getBloomInfo(spot);
  const photoUri = data.photoBuffers[spot.name];

  return h("div", {
    style: {
      display: "flex", flexDirection: "column", width: "100%", height: "100%",
      fontFamily: "Noto Sans SC",
    },
  },
    // Top section with photo
    h("div", {
      style: {
        display: "flex", flexDirection: "column", justifyContent: "flex-end",
        position: "relative", height: "55%", overflow: "hidden",
        background: photoUri ? C.bgDark : `linear-gradient(135deg, ${C.bgDark}, #3d1a2a)`,
      },
    },
      photoUri ? h("img", {
        src: photoUri, width: 1080, height: 594,
        style: { position: "absolute", top: 0, left: 0, width: "100%", height: "100%", objectFit: "cover" },
      }) : null,
      h("div", { style: { position: "absolute", bottom: 0, left: 0, right: 0, height: "70%", background: "linear-gradient(transparent, rgba(0,0,0,0.75))" } }),
      h("div", { style: { position: "relative", padding: "0 40px 28px", display: "flex", flexDirection: "column" } },
        h("div", { style: { fontSize: "18px", color: "rgba(255,255,255,0.5)", letterSpacing: "3px", marginBottom: "8px" } }, BRAND.title),
        h("div", { style: { fontSize: "42px", fontWeight: 900, color: C.white } }, spot.name),
        h("div", { style: { fontSize: "20px", color: "rgba(255,255,255,0.6)", marginTop: "4px" } }, `${data.cityName} · ${bloom.emoji} ${bloom.labelCn}`),
      ),
    ),
    // Bottom info
    h("div", {
      style: {
        display: "flex", flex: 1, background: C.bgPrimary,
        padding: "28px 40px", alignItems: "center", gap: "28px",
      },
    },
      // Score
      h("div", { style: { display: "flex", flexDirection: "column", alignItems: "center" } },
        h("div", { style: { fontSize: "72px", fontWeight: 900, color: C.accent } }, `${spot.score}`),
        h("div", { style: { fontSize: "22px", color: C.textMuted, fontWeight: 700 } }, "好看指数"),
      ),
      // Divider
      h("div", { style: { width: "1px", height: "80px", background: C.divider } }),
      // Tags
      h("div", { style: { display: "flex", flexDirection: "column", flex: 1, gap: "10px" } },
        spot.full ? h("div", { style: { fontSize: "24px", color: C.textSecondary, fontWeight: 600 } }, `✿ 满开 ${spot.full}`) : null,
        spot.trees ? h("div", { style: { fontSize: "24px", color: C.textSecondary, fontWeight: 600 } }, `♣ ${spot.trees}`) : null,
        spot.lightup ? h("div", { style: { fontSize: "24px", color: "#6366f1", fontWeight: 600 } }, "夜樱灯光") : null,
        h("div", { style: { fontSize: "22px", color: C.accent, fontWeight: 800, marginTop: "4px" } }, BRAND.ctaSecondary),
      ),
    ),
  );
}

// ── 5. XHS Story — Vertical ─────────────────────────────────────────────────

export function createXhsStoryElement(data: TemplateData): React.ReactElement {
  const top3 = data.spots.slice(0, 3);
  const photoUri = data.photoBuffers[top3[0]?.name];

  return h("div", {
    style: {
      display: "flex", flexDirection: "column", width: "100%", height: "100%",
      fontFamily: "Noto Sans SC", position: "relative", overflow: "hidden",
      background: photoUri ? C.bgDark : `linear-gradient(180deg, ${C.bgDark} 0%, #3d1a2a 50%, ${C.bgDarkSoft} 100%)`,
    },
  },
    // Full-bleed photo
    photoUri ? h("img", {
      src: photoUri, width: 1080, height: 1920,
      style: { position: "absolute", top: 0, left: 0, width: "100%", height: "100%", objectFit: "cover" },
    }) : null,
    // Dark overlay — stronger gradient for text legibility
    h("div", { style: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, background: "linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.15) 25%, rgba(0,0,0,0.55) 45%, rgba(0,0,0,0.82) 65%, rgba(0,0,0,0.92) 100%)" } }),
    // Content
    h("div", { style: { position: "relative", display: "flex", flexDirection: "column", flex: 1, padding: "60px 48px" } },
      // Brand top
      h("div", { style: { display: "flex", alignItems: "center", gap: "12px" } },
        h("div", { style: { fontSize: "36px", color: C.bloomFull } }, "✿"),
        h("div", { style: { fontSize: "26px", color: "rgba(255,255,255,0.4)", letterSpacing: "4px" } }, BRAND.title),
      ),
      // Spacer
      h("div", { style: { flex: 1 } }),
      // City title
      h("div", { style: { fontSize: "88px", fontWeight: 900, color: C.white, marginBottom: "12px" } }, `${data.cityName}`),
      h("div", { style: { fontSize: "46px", color: "rgba(255,255,255,0.7)", marginBottom: "40px", fontWeight: 700 } }, "赏樱 TOP3 · 好看指数排名"),
      // Top 3 spots
      ...top3.map((spot, i) => {
        const bloom = getBloomInfo(spot);
        return h("div", {
          key: i,
          style: {
            display: "flex", alignItems: "center", gap: "16px",
            background: "rgba(255,255,255,0.1)", borderRadius: "16px",
            padding: "20px 24px", marginBottom: "12px",
          },
        },
          h("div", { style: { fontSize: "48px", fontWeight: 900, color: C.accent, width: "60px" } }, `${i + 1}`),
          h("div", { style: { display: "flex", flexDirection: "column", flex: 1 } },
            h("div", { style: { fontSize: "38px", fontWeight: 800, color: C.white } }, spot.name),
            h("div", { style: { fontSize: "26px", color: "rgba(255,255,255,0.5)", marginTop: "6px", fontWeight: 600 } }, `${bloom.emoji} ${bloom.labelCn} · 满开 ${spot.full || "待定"}`),
          ),
          h("div", { style: { fontSize: "56px", fontWeight: 900, color: C.accent } }, `${spot.score}`),
        );
      }),
      // Bottom CTA
      h("div", { style: { display: "flex", flexDirection: "column", alignItems: "center", marginTop: "32px" } },
        h("div", { style: { fontSize: "38px", color: "rgba(255,255,255,0.8)", fontWeight: 800 } }, BRAND.ctaPrimary),
        h("div", { style: { fontSize: "32px", color: C.accent, marginTop: "10px", fontWeight: 800 } }, BRAND.ctaSecondary),
        h("div", { style: { fontSize: "22px", color: "rgba(255,255,255,0.3)", marginTop: "14px", fontWeight: 600 } }, BRAND.sources),
      ),
    ),
  );
}
