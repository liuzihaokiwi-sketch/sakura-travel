"use client";

import { useState } from "react";
import Link from "next/link";

// 城市圈定义
const CITY_GROUPS = {
  domestic: [
    { id: "guangfu", label: "广府", desc: "广州·佛山·珠三角" },
    { id: "guangdong", label: "广东", desc: "潮汕·梅州·湛江" },
    { id: "bejiang", label: "北疆", desc: "喀什·伊犁·赛里木湖" },
  ],
  overseas: [
    { id: "kansai", label: "关西", desc: "京都·大阪·奈良" },
    { id: "kanto", label: "关东", desc: "东京·镰仓·日光" },
    { id: "hokkaido", label: "北海道", desc: "札幌·富良野·小樽" },
  ],
};

const DAYS_OPTIONS = [5, 6, 7, 8, 9, 10, 11, 12, 14];

function calcPrice(days: number, isOverseas: boolean): number {
  const base = 198 + (days - 7) * 20;
  const overseasSurcharge = isOverseas ? 30 : 0;
  return Math.max(158, base) + overseasSurcharge;
}

function calcPages(days: number): number {
  const raw = 18 + days * 6;
  return raw % 2 === 0 ? raw : raw + 1;
}

export default function OrderPage() {
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const [selectedDays, setSelectedDays] = useState(7);

  const isOverseas = CITY_GROUPS.overseas.some((g) => g.id === selectedGroup);
  const isDomestic = CITY_GROUPS.domestic.some((g) => g.id === selectedGroup);
  const price = calcPrice(selectedDays, isOverseas);
  const pages = calcPages(selectedDays);
  const needsSplit = selectedDays >= 11;

  const selectedGroupLabel =
    [...CITY_GROUPS.domestic, ...CITY_GROUPS.overseas].find((g) => g.id === selectedGroup)?.label || null;

  return (
    <div style={{ backgroundColor: "#FBF7F0", minHeight: "100vh", paddingBottom: "80px" }}>
      {/* 页头 */}
      <div
        style={{
          maxWidth: "640px",
          margin: "0 auto",
          padding: "40px 24px 0",
          textAlign: "center",
        }}
      >
        <h1
          style={{
            fontFamily: '"Noto Serif SC", serif',
            fontSize: "28px",
            fontWeight: 700,
            color: "#2D4A3E",
            marginBottom: "8px",
          }}
        >
          定制你的旅行手账
        </h1>
        <p style={{ fontSize: "15px", color: "#8B7E74" }}>
          选择城市圈和天数，我们会为你量身定制
        </p>
      </div>

      <div style={{ maxWidth: "640px", margin: "0 auto", padding: "32px 24px 0" }}>
        {/* 选择城市圈 */}
        <Section title="选择城市圈">
          <div style={{ marginBottom: "12px" }}>
            <GroupLabel color="#D4A855">国内</GroupLabel>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "8px" }}>
              {CITY_GROUPS.domestic.map((g) => (
                <CityCard
                  key={g.id}
                  id={g.id}
                  label={g.label}
                  desc={g.desc}
                  selected={selectedGroup === g.id}
                  accentColor="#D4A855"
                  onClick={() => setSelectedGroup(g.id)}
                />
              ))}
            </div>
          </div>
          <div>
            <GroupLabel color="#E8A0BF">海外</GroupLabel>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "8px" }}>
              {CITY_GROUPS.overseas.map((g) => (
                <CityCard
                  key={g.id}
                  id={g.id}
                  label={g.label}
                  desc={g.desc}
                  selected={selectedGroup === g.id}
                  accentColor="#4A6FA5"
                  onClick={() => setSelectedGroup(g.id)}
                />
              ))}
            </div>
          </div>
        </Section>

        {/* 选择天数 */}
        <Section title="选择天数">
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {DAYS_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setSelectedDays(d)}
                style={{
                  width: "52px",
                  height: "52px",
                  borderRadius: "12px",
                  border: selectedDays === d ? "2px solid #2D4A3E" : "1.5px solid #E0D8CE",
                  backgroundColor: selectedDays === d ? "#2D4A3E" : "#FFFFFF",
                  color: selectedDays === d ? "#FFFFFF" : "#3D3029",
                  fontSize: "15px",
                  fontWeight: selectedDays === d ? 700 : 500,
                  cursor: "pointer",
                  transition: "all 200ms ease",
                }}
              >
                {d}天
              </button>
            ))}
          </div>
          <p style={{ fontSize: "13px", color: "#A69B91", marginTop: "10px" }}>
            约 {pages} 页手账
          </p>
        </Section>

        {/* 价格汇总卡片 */}
        {selectedGroup && (
          <div
            style={{
              backgroundColor: "#FFFFFF",
              borderRadius: "16px",
              padding: "24px",
              boxShadow: "0 1px 3px rgba(61, 48, 41, 0.08)",
              marginBottom: "24px",
              animation: "fadeInUp 400ms ease forwards",
            }}
          >
            {/* 行程摘要 */}
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: "8px",
                marginBottom: "16px",
              }}
            >
              <span
                style={{
                  fontFamily: '"Noto Serif SC", serif',
                  fontSize: "20px",
                  fontWeight: 700,
                  color: "#2D4A3E",
                }}
              >
                {selectedGroupLabel} · {selectedDays}天
              </span>
              <span style={{ fontSize: "14px", color: "#8B7E74" }}>约{pages}页</span>
            </div>

            {/* 拆册提示 */}
            {needsSplit && (
              <div
                style={{
                  backgroundColor: "#FBF7F0",
                  border: "1px solid #E8D9B6",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  marginBottom: "16px",
                  fontSize: "13px",
                  color: "#8B7E74",
                }}
              >
                ℹ️ {selectedDays}天行程将拆为两册，含拆册费 ¥29。每册独立完整（封面/地图/每日行程/旅后层）。
              </div>
            )}

            {/* 价格 */}
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: "4px",
                marginBottom: "16px",
              }}
            >
              <span
                style={{
                  fontSize: "36px",
                  fontWeight: 800,
                  color: "#C65D3E",
                  fontFamily: '"Inter", sans-serif',
                }}
              >
                ¥{price}
              </span>
              {needsSplit && (
                <span style={{ fontSize: "13px", color: "#A69B91" }}>(含拆册费)</span>
              )}
            </div>

            {/* 包含内容 */}
            <div style={{ marginBottom: "20px" }}>
              <div style={{ fontSize: "13px", color: "#8B7E74", lineHeight: "2" }}>
                {["定制手账本", `${isDomestic ? "国内" : ""}城市圈贴纸包`, "包邮到家", "一轮免费修改", "确认前可全额退款"].map((item) => (
                  <div key={item} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <span style={{ color: "#4A8B6E", fontSize: "11px" }}>✓</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 支付按钮 */}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <PayButton label={`微信支付 ¥${price}`} primary />
              <PayButton label={`支付宝支付 ¥${price}`} primary={false} />
            </div>

            {/* 客服备用 */}
            <div
              style={{
                marginTop: "16px",
                padding: "12px",
                backgroundColor: "#F5F0E8",
                borderRadius: "8px",
                fontSize: "13px",
                color: "#8B7E74",
                textAlign: "center",
              }}
            >
              或联系客服下单：微信 <strong style={{ color: "#3D3029" }}>traveljournal2025</strong>
            </div>
          </div>
        )}

        {/* 未选城市圈时的占位卡 */}
        {!selectedGroup && (
          <div
            style={{
              backgroundColor: "#FFFFFF",
              borderRadius: "16px",
              padding: "32px 24px",
              textAlign: "center",
              boxShadow: "0 1px 3px rgba(61, 48, 41, 0.08)",
              marginBottom: "24px",
            }}
          >
            <p style={{ fontSize: "15px", color: "#A69B91" }}>↑ 先选择城市圈</p>
          </div>
        )}

        {/* 信任标签 */}
        <div
          style={{
            display: "flex",
            gap: "12px",
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          {["不满意可退款", "免费修改一轮", "2小时出方案"].map((tag) => (
            <span
              key={tag}
              style={{
                fontSize: "13px",
                color: "#8B7E74",
                backgroundColor: "#F5F0E8",
                borderRadius: "20px",
                padding: "6px 14px",
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "28px" }}>
      <h2
        style={{
          fontFamily: '"Noto Serif SC", serif',
          fontSize: "16px",
          fontWeight: 700,
          color: "#2D4A3E",
          marginBottom: "14px",
        }}
      >
        {title}
      </h2>
      {children}
    </div>
  );
}

function GroupLabel({ color, children }: { color: string; children: React.ReactNode }) {
  return (
    <span
      style={{
        fontSize: "12px",
        fontWeight: 600,
        color: color,
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      {children}
    </span>
  );
}

function CityCard({
  label,
  desc,
  selected,
  accentColor,
  onClick,
}: {
  id: string;
  label: string;
  desc: string;
  selected: boolean;
  accentColor: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        padding: "12px 16px",
        borderRadius: "12px",
        border: selected ? `2px solid ${accentColor}` : "1.5px solid #E0D8CE",
        backgroundColor: selected ? "#FFFFFF" : "#FFFFFF",
        boxShadow: selected ? `0 2px 12px ${accentColor}30` : "none",
        cursor: "pointer",
        minWidth: "100px",
        transition: "all 200ms ease",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* 左侧色条 */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: "3px",
          backgroundColor: selected ? accentColor : "transparent",
          transition: "background-color 200ms ease",
        }}
      />
      <span
        style={{
          fontSize: "15px",
          fontWeight: 700,
          color: selected ? "#2D4A3E" : "#3D3029",
          marginBottom: "2px",
        }}
      >
        {label}
      </span>
      <span style={{ fontSize: "11px", color: "#A69B91" }}>{desc}</span>
      {selected && (
        <span
          style={{
            position: "absolute",
            top: "6px",
            right: "8px",
            fontSize: "12px",
            color: accentColor,
            fontWeight: 700,
          }}
        >
          ✓
        </span>
      )}
    </button>
  );
}

function PayButton({ label, primary }: { label: string; primary: boolean }) {
  return (
    <button
      style={{
        width: "100%",
        padding: "14px",
        borderRadius: "12px",
        border: primary ? "none" : "1.5px solid #E0D8CE",
        backgroundColor: primary ? "#C65D3E" : "#FFFFFF",
        color: primary ? "#FFFFFF" : "#3D3029",
        fontSize: "15px",
        fontWeight: 600,
        cursor: "pointer",
        transition: "all 200ms ease",
      }}
      onMouseEnter={(e) => {
        if (primary) (e.currentTarget as HTMLButtonElement).style.backgroundColor = "#B04E32";
      }}
      onMouseLeave={(e) => {
        if (primary) (e.currentTarget as HTMLButtonElement).style.backgroundColor = "#C65D3E";
      }}
    >
      {label}
    </button>
  );
}
