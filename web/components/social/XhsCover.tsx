import React from "react";

export interface XhsCoverProps {
  cityName: string;
  spots: Array<{ name: string; full: string; score: number }>;
  weekDate: string;
}

export default function XhsCover({ cityName, spots, weekDate }: XhsCoverProps) {
  const top3 = spots.slice(0, 3);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        width: "1080px",
        height: "1440px",
        background: "linear-gradient(180deg, #1a0a0f 0%, #2d1525 50%, #1a0a0f 100%)",
        padding: "60px",
        fontFamily: "Noto Sans SC, sans-serif",
      }}
    >
      {/* Top badge */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: "20px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            border: "1px solid rgba(247,147,30,0.4)",
            padding: "8px 24px",
            borderRadius: "4px",
          }}
        >
          <span style={{ color: "#f7931e", fontSize: "16px" }}>✦</span>
          <span style={{ fontSize: "14px", letterSpacing: "0.25em", color: "rgba(255,255,255,0.6)" }}>
            SAKURA RUSH 2026
          </span>
          <span style={{ color: "#f7931e", fontSize: "16px" }}>✦</span>
        </div>
      </div>

      {/* Title */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: "50px" }}>
        <div style={{ fontSize: "56px", fontWeight: 900, color: "white", letterSpacing: "0.05em" }}>
          2026 樱花季
        </div>
        <div style={{ fontSize: "36px", color: "#f8bbd0", marginTop: "12px", letterSpacing: "0.1em" }}>
          {cityName} · TOP 赏樱地
        </div>
        <div style={{ fontSize: "18px", color: "rgba(255,255,255,0.4)", marginTop: "8px" }}>
          {weekDate}
        </div>
      </div>

      {/* Spot list */}
      <div style={{ display: "flex", flexDirection: "column", flex: 1, gap: "24px" }}>
        {top3.map((spot, i) => (
          <div
            key={spot.name}
            style={{
              display: "flex",
              alignItems: "center",
              background: i === 0 ? "rgba(247,147,30,0.12)" : "rgba(255,255,255,0.06)",
              borderRadius: "20px",
              padding: "28px 32px",
              gap: "28px",
              border: i === 0 ? "1px solid rgba(247,147,30,0.3)" : "1px solid rgba(255,255,255,0.06)",
            }}
          >
            {/* Rank */}
            <div
              style={{
                fontSize: "72px",
                fontWeight: 900,
                color: i === 0 ? "#f7931e" : i === 1 ? "#f8bbd0" : "rgba(255,255,255,0.3)",
                width: "100px",
                textAlign: "center",
                lineHeight: 1,
              }}
            >
              {i + 1}
            </div>

            {/* Info */}
            <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
              <div style={{ fontSize: "32px", color: "white", fontWeight: 700 }}>
                {spot.name}
              </div>
              <div style={{ fontSize: "24px", color: "#f8bbd0", marginTop: "8px" }}>
                🌸 满开: {spot.full || "待定"}
              </div>
            </div>

            {/* Score */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                background: "rgba(247,147,30,0.15)",
                borderRadius: "16px",
                padding: "12px 20px",
                border: "1px solid rgba(247,147,30,0.3)",
              }}
            >
              <div style={{ fontSize: "40px", fontWeight: 900, color: "#f7931e", lineHeight: 1 }}>
                {spot.score}
              </div>
              <div style={{ fontSize: "14px", color: "rgba(255,255,255,0.4)", marginTop: "4px" }}>
                /100
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          borderTop: "1px solid rgba(255,255,255,0.08)",
          paddingTop: "32px",
          marginTop: "32px",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", gap: "32px", fontSize: "20px", color: "#f8bbd0" }}>
          <span>📊 4大权威数据源融合</span>
          <span>🌸 每天3次更新</span>
        </div>
        <div style={{ fontSize: "18px", color: "rgba(255,255,255,0.35)" }}>
          240+景点覆盖 · JMA · JMC · Weathernews · 地方官方
        </div>
        <div
          style={{
            fontSize: "28px",
            fontWeight: 700,
            color: "#f7931e",
            marginTop: "8px",
            letterSpacing: "0.05em",
          }}
        >
          关注获取完整榜单 ↑
        </div>
      </div>
    </div>
  );
}
