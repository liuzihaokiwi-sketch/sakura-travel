import React from "react";

export interface XhsContentProps {
  cityName: string;
  spots: Array<{
    name: string;
    region?: string;
    full?: string;
    trees?: string;
    lightup?: boolean;
    score: number;
  }>;
  pageNum: number;
}

export default function XhsContent({ cityName, spots, pageNum }: XhsContentProps) {
  const top8 = spots.slice(0, 8);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        width: "1080px",
        height: "1440px",
        background: "#fefaf6",
        fontFamily: "Noto Sans SC, sans-serif",
        padding: "48px",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          paddingBottom: "24px",
          borderBottom: "2px solid #f0e8df",
          marginBottom: "24px",
        }}
      >
        <div style={{ fontSize: "40px", fontWeight: 900, color: "#1c1917" }}>
          {cityName} 赏樱 TOP 8
        </div>
        <div
          style={{
            display: "flex",
            background: "#f7931e",
            color: "white",
            padding: "8px 20px",
            borderRadius: "24px",
            fontSize: "18px",
            fontWeight: 700,
          }}
        >
          第{pageNum}页
        </div>
      </div>

      {/* Spot rows */}
      <div style={{ display: "flex", flexDirection: "column", flex: 1, gap: "4px" }}>
        {top8.map((spot, i) => (
          <div
            key={spot.name}
            style={{
              display: "flex",
              alignItems: "center",
              padding: "20px 16px",
              borderBottom: i < 7 ? "1px solid #f5f5f4" : "none",
              gap: "16px",
            }}
          >
            {/* Rank */}
            <div
              style={{
                width: "52px",
                height: "52px",
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "24px",
                fontWeight: 900,
                color: i < 3 ? "white" : "#78716c",
                background: i < 3 ? "#f7931e" : "#f5f5f4",
                flexShrink: 0,
              }}
            >
              {i + 1}
            </div>

            {/* Name */}
            <div style={{ display: "flex", flexDirection: "column", flex: 1, gap: "4px" }}>
              <div style={{ fontSize: "28px", fontWeight: 700, color: "#1c1917" }}>
                {spot.name}
              </div>
              <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                {spot.region && (
                  <span
                    style={{
                      fontSize: "16px",
                      color: "#a8a29e",
                      background: "#f5f5f4",
                      padding: "2px 10px",
                      borderRadius: "8px",
                    }}
                  >
                    📍 {spot.region}
                  </span>
                )}
                {spot.trees && (
                  <span style={{ fontSize: "16px", color: "#78716c" }}>🌳 {spot.trees}</span>
                )}
                {spot.lightup && (
                  <span
                    style={{
                      fontSize: "16px",
                      background: "#eef2ff",
                      color: "#6366f1",
                      padding: "2px 10px",
                      borderRadius: "8px",
                    }}
                  >
                    🌙 夜樱
                  </span>
                )}
              </div>
            </div>

            {/* Full bloom date */}
            <div style={{ fontSize: "22px", fontWeight: 600, color: "#ec407a", flexShrink: 0 }}>
              {spot.full || "—"}
            </div>

            {/* Score */}
            <div
              style={{
                fontSize: "36px",
                fontWeight: 900,
                color: spot.score >= 90 ? "#16a34a" : spot.score >= 80 ? "#2563eb" : "#78716c",
                flexShrink: 0,
                width: "72px",
                textAlign: "right",
              }}
            >
              {spot.score}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderTop: "2px solid #f0e8df",
          paddingTop: "24px",
          marginTop: "16px",
        }}
      >
        <div style={{ fontSize: "22px", color: "#f7931e", fontWeight: 600 }}>
          想看完整攻略？私信免费领 →
        </div>
        <div style={{ fontSize: "20px", color: "#78716c" }}>
          微信: Kiwi_iloveu_O-o
        </div>
      </div>
    </div>
  );
}
