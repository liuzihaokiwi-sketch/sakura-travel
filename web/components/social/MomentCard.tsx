import React from "react";

export interface MomentCardProps {
  spotName: string;
  spotNameCn?: string;
  fullDate?: string;
  score: number;
  trees?: string;
  lightup?: boolean;
  region?: string;
}

export default function MomentCard({
  spotName,
  spotNameCn,
  fullDate,
  score,
  trees,
  lightup,
  region,
}: MomentCardProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        width: "1080px",
        height: "1080px",
        fontFamily: "Noto Sans SC, sans-serif",
      }}
    >
      {/* Top half — dark */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          flex: "55",
          background: "linear-gradient(180deg, #1a0a0f 0%, #2d1525 100%)",
          padding: "40px",
          gap: "8px",
        }}
      >
        {/* Brand badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            marginBottom: "16px",
            border: "1px solid rgba(247,147,30,0.3)",
            padding: "6px 18px",
            borderRadius: "4px",
          }}
        >
          <span style={{ color: "#f7931e", fontSize: "12px" }}>✦</span>
          <span style={{ fontSize: "12px", letterSpacing: "0.2em", color: "rgba(255,255,255,0.5)" }}>
            SAKURA RUSH 2026
          </span>
          <span style={{ color: "#f7931e", fontSize: "12px" }}>✦</span>
        </div>

        <div style={{ fontSize: "56px", fontWeight: 900, color: "white", textAlign: "center" }}>
          {spotName}
        </div>
        {spotNameCn && (
          <div style={{ fontSize: "24px", color: "rgba(255,255,255,0.5)" }}>
            {spotNameCn}
          </div>
        )}

        {/* Score */}
        <div style={{ display: "flex", alignItems: "baseline", gap: "4px", marginTop: "16px" }}>
          <div style={{ fontSize: "120px", fontWeight: 900, color: "#f7931e", lineHeight: 1 }}>
            {score}
          </div>
          <div style={{ fontSize: "32px", color: "rgba(255,255,255,0.25)" }}>/100</div>
        </div>
      </div>

      {/* Bottom half — light */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          flex: "45",
          background: "#fefaf6",
          padding: "40px 48px",
        }}
      >
        {/* Info grid */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "24px",
            flex: 1,
            alignContent: "center",
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              width: "45%",
              background: "white",
              borderRadius: "16px",
              padding: "20px",
              border: "1px solid #f0e8df",
            }}
          >
            <div style={{ fontSize: "16px", color: "#a8a29e" }}>🌸 满开日期</div>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "#ec407a", marginTop: "4px" }}>
              {fullDate || "待定"}
            </div>
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              width: "45%",
              background: "white",
              borderRadius: "16px",
              padding: "20px",
              border: "1px solid #f0e8df",
            }}
          >
            <div style={{ fontSize: "16px", color: "#a8a29e" }}>🌳 樱花树</div>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "#44403c", marginTop: "4px" }}>
              {trees || "未知"}
            </div>
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              width: "45%",
              background: "white",
              borderRadius: "16px",
              padding: "20px",
              border: "1px solid #f0e8df",
            }}
          >
            <div style={{ fontSize: "16px", color: "#a8a29e" }}>📍 区域</div>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "#44403c", marginTop: "4px" }}>
              {region || "—"}
            </div>
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              width: "45%",
              background: "white",
              borderRadius: "16px",
              padding: "20px",
              border: "1px solid #f0e8df",
            }}
          >
            <div style={{ fontSize: "16px", color: "#a8a29e" }}>🌙 夜樱</div>
            <div style={{ fontSize: "28px", fontWeight: 700, color: lightup ? "#6366f1" : "#d6d3d1", marginTop: "4px" }}>
              {lightup ? "有夜间灯光" : "无"}
            </div>
          </div>
        </div>

        {/* Bottom CTA */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            borderTop: "1px solid #e7e5e4",
            paddingTop: "20px",
            gap: "6px",
          }}
        >
          <div style={{ fontSize: "16px", color: "#a8a29e" }}>
            樱花冲刺 2026 · 数据融合预测
          </div>
          <div style={{ fontSize: "20px", color: "#f7931e", fontWeight: 600 }}>
            更多景点 → 微信 Kiwi_iloveu_O-o
          </div>
        </div>
      </div>
    </div>
  );
}
