"use client";

import Link from "next/link";
import { useState } from "react";

// ─── 数据 ─────────────────────────────────────────────────────────────────────

const CONTENT_MODULES = [
  { id: "route", icon: "🗺️", title: "路线规划", desc: "完整7天行程，每天2-3个重点，不赶场" },
  { id: "food", icon: "🍜", title: "餐厅推荐", desc: "精选午餐+晚餐，附预约时机和排队说明" },
  { id: "hotel", icon: "🏨", title: "酒店策略", desc: "为什么住这里，值不值，要不要换" },
  { id: "budget", icon: "💰", title: "预算明细", desc: "每天花多少，哪天花得多，哪里值得花" },
  { id: "planb", icon: "🔄", title: "Plan B备选", desc: "下雨了怎么办，景点关门了怎么办" },
  { id: "photo", icon: "📷", title: "出片指南", desc: "哪里拍最好看，什么时间光线最好" },
];

const SAMPLE_GUIDES = [
  {
    id: "kansai",
    city: "关西",
    days: 7,
    tag: "情侣蜜月",
    desc: "京都·大阪·奈良",
    color: "#E8A0BF",
  },
  {
    id: "guangfu",
    city: "广府",
    days: 5,
    tag: "家庭美食",
    desc: "广州·佛山·顺德",
    color: "#D4A855",
  },
  {
    id: "hokkaido",
    city: "北海道",
    days: 6,
    tag: "冬季温泉",
    desc: "札幌·富良野·小樽",
    color: "#4A6FA5",
  },
];

const STEPS = [
  { num: "01", title: "选天数下单", desc: "30秒完成" },
  { num: "02", title: "填写偏好", desc: "懒人1分钟搞定" },
  { num: "03", title: "确认方案", desc: "有一次修改机会" },
  { num: "04", title: "收到手账", desc: "快递到家" },
];

const TRUST_ITEMS = [
  { icon: "↩", title: "不满意可退款", desc: "确认前全额退，没有条件" },
  { icon: "✏", title: "免费修改一轮", desc: "AI对话式调整，说人话就行" },
  { icon: "⚡", title: "2小时出方案", desc: "说2-4小时，实际更快" },
];

const FAQ_ITEMS = [
  {
    q: "手账是模板还是定制的？",
    a: "完全定制。根据你的出行日期、人数、预算、偏好生成，不是套模板。",
  },
  {
    q: "多久能收到？",
    a: "数字版2小时内完成，可立刻查看。纸质版打印后顺丰快递，2-3天到。",
  },
  {
    q: "不满意怎么办？",
    a: "确认方案之前可以全额退款，无条件。确认后还有一轮免费修改机会。",
  },
];

// ─── 主页面 ──────────────────────────────────────────────────────────────────

export default function HomePage() {
  const [activeModule, setActiveModule] = useState<string | null>(null);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <div style={{ backgroundColor: "#FBF7F0" }}>
      {/* A. Hero */}
      <section
        style={{
          backgroundColor: "#FBF7F0",
          padding: "64px 24px 56px",
          textAlign: "center",
        }}
      >
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          {/* 手账示意占位 */}
          <div
            style={{
              width: "200px",
              height: "140px",
              backgroundColor: "#FFFFFF",
              borderRadius: "16px",
              boxShadow: "0 8px 32px rgba(61, 48, 41, 0.12)",
              margin: "0 auto 40px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "48px",
            }}
          >
            📖
          </div>

          <h1
            style={{
              fontFamily: '"Noto Serif SC", serif',
              fontSize: "clamp(24px, 5vw, 40px)",
              fontWeight: 700,
              color: "#2D4A3E",
              marginBottom: "16px",
              lineHeight: 1.3,
            }}
          >
            一本替你想好一切的旅行手账
          </h1>
          <p
            style={{
              fontSize: "16px",
              color: "#8B7E74",
              marginBottom: "40px",
              lineHeight: 1.6,
            }}
          >
            路线 · 餐厅 · 酒店 · 预算 · Plan B · 全部安排好
          </p>

          {/* 双入口 */}
          <div
            style={{
              display: "flex",
              gap: "16px",
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            <EntryCard
              title="国内出发"
              subtitle="广府·广东·北疆"
              price="¥198 起"
              color="#D4A855"
              href="/order"
            />
            <EntryCard
              title="海外出发"
              subtitle="关西·关东·北海道"
              price="¥228 起"
              color="#E8A0BF"
              href="/order"
            />
          </div>
        </div>
      </section>

      {/* B. 手账内容展示 */}
      <section style={{ backgroundColor: "#F5F0E8", padding: "64px 24px" }}>
        <div style={{ maxWidth: "900px", margin: "0 auto" }}>
          <SectionHeading>你的手账里有什么</SectionHeading>

          {/* 模块卡片 */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
              gap: "12px",
              marginBottom: "32px",
            }}
          >
            {CONTENT_MODULES.map((mod) => (
              <button
                key={mod.id}
                onClick={() => setActiveModule(activeModule === mod.id ? null : mod.id)}
                style={{
                  padding: "16px",
                  borderRadius: "12px",
                  border: `2px solid ${activeModule === mod.id ? "#2D4A3E" : "transparent"}`,
                  backgroundColor: activeModule === mod.id ? "#FFFFFF" : "#FFFFFF",
                  boxShadow:
                    activeModule === mod.id
                      ? "0 4px 16px rgba(61, 48, 41, 0.12)"
                      : "0 1px 3px rgba(61, 48, 41, 0.06)",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 200ms ease",
                }}
              >
                <div style={{ fontSize: "24px", marginBottom: "8px" }}>{mod.icon}</div>
                <div
                  style={{
                    fontSize: "14px",
                    fontWeight: 600,
                    color: "#2D4A3E",
                    marginBottom: "4px",
                  }}
                >
                  {mod.title}
                </div>
                <div style={{ fontSize: "12px", color: "#8B7E74", lineHeight: 1.5 }}>
                  {mod.desc}
                </div>
              </button>
            ))}
          </div>

          {/* 展示区 */}
          {activeModule && (
            <div
              style={{
                backgroundColor: "#FFFFFF",
                borderRadius: "16px",
                padding: "32px",
                boxShadow: "0 4px 16px rgba(61, 48, 41, 0.08)",
                textAlign: "center",
                color: "#8B7E74",
                fontSize: "14px",
                animation: "fadeInUp 300ms ease forwards",
              }}
            >
              <div style={{ fontSize: "40px", marginBottom: "12px" }}>
                {CONTENT_MODULES.find((m) => m.id === activeModule)?.icon}
              </div>
              <p>
                {CONTENT_MODULES.find((m) => m.id === activeModule)?.title} 示例截图
              </p>
              <p style={{ fontSize: "12px", color: "#A69B91", marginTop: "4px" }}>
                （实际手账截图放置位置）
              </p>
            </div>
          )}
        </div>
        <style>{`
          @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}</style>
      </section>

      {/* C. 样本展示 */}
      <section style={{ backgroundColor: "#FFFFFF", padding: "64px 24px" }}>
        <div style={{ maxWidth: "900px", margin: "0 auto" }}>
          <SectionHeading>看看别人收到的手账</SectionHeading>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
              gap: "20px",
            }}
          >
            {SAMPLE_GUIDES.map((guide) => (
              <div
                key={guide.id}
                style={{
                  backgroundColor: "#FFFFFF",
                  borderRadius: "16px",
                  border: "1px solid #E8E0D6",
                  overflow: "hidden",
                  transition: "transform 200ms ease, box-shadow 200ms ease",
                  cursor: "pointer",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.transform = "translateY(-4px)";
                  (e.currentTarget as HTMLElement).style.boxShadow =
                    "0 12px 32px rgba(61, 48, 41, 0.12)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.transform = "translateY(0)";
                  (e.currentTarget as HTMLElement).style.boxShadow = "none";
                }}
              >
                {/* 封面占位 */}
                <div
                  style={{
                    height: "160px",
                    backgroundColor: `${guide.color}20`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "48px",
                    borderBottom: `3px solid ${guide.color}`,
                  }}
                >
                  📖
                </div>
                <div style={{ padding: "16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                    <span
                      style={{
                        fontFamily: '"Noto Serif SC", serif',
                        fontSize: "16px",
                        fontWeight: 700,
                        color: "#2D4A3E",
                      }}
                    >
                      {guide.city} {guide.days}天
                    </span>
                    <span
                      style={{
                        fontSize: "11px",
                        padding: "2px 8px",
                        borderRadius: "10px",
                        backgroundColor: `${guide.color}25`,
                        color: guide.color,
                        fontWeight: 600,
                      }}
                    >
                      {guide.tag}
                    </span>
                  </div>
                  <p style={{ fontSize: "13px", color: "#8B7E74", marginBottom: "14px" }}>
                    {guide.desc}
                  </p>
                  <button
                    style={{
                      width: "100%",
                      padding: "8px",
                      borderRadius: "8px",
                      border: "1.5px solid #E0D8CE",
                      backgroundColor: "transparent",
                      color: "#8B7E74",
                      fontSize: "13px",
                      cursor: "pointer",
                      transition: "all 200ms ease",
                    }}
                  >
                    翻看样本
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* D. 4步流程 */}
      <section style={{ backgroundColor: "#F5F0E8", padding: "64px 24px" }}>
        <div style={{ maxWidth: "900px", margin: "0 auto" }}>
          <SectionHeading>4步拿到你的手账</SectionHeading>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "20px",
              position: "relative",
            }}
          >
            {STEPS.map((step, i) => (
              <div
                key={step.num}
                style={{ textAlign: "center", position: "relative" }}
              >
                <div
                  style={{
                    width: "56px",
                    height: "56px",
                    borderRadius: "50%",
                    backgroundColor: "#2D4A3E",
                    color: "white",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 auto 16px",
                    fontFamily: '"Inter", sans-serif',
                    fontSize: "16px",
                    fontWeight: 700,
                  }}
                >
                  {step.num}
                </div>
                <div
                  style={{
                    fontSize: "15px",
                    fontWeight: 700,
                    color: "#2D4A3E",
                    marginBottom: "6px",
                    fontFamily: '"Noto Serif SC", serif',
                  }}
                >
                  {step.title}
                </div>
                <div style={{ fontSize: "13px", color: "#8B7E74" }}>{step.desc}</div>
                {/* 连接线（桌面） */}
                {i < STEPS.length - 1 && (
                  <div
                    style={{
                      position: "absolute",
                      top: "28px",
                      right: "-10px",
                      width: "20px",
                      height: "1px",
                      borderTop: "2px dashed #C0B8AE",
                    }}
                    className="step-connector"
                  />
                )}
              </div>
            ))}
          </div>
        </div>
        <style>{`
          @media (max-width: 768px) { .step-connector { display: none; } }
        `}</style>
      </section>

      {/* E. 信任区 */}
      <section style={{ backgroundColor: "#FFFFFF", padding: "64px 24px" }}>
        <div style={{ maxWidth: "700px", margin: "0 auto" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "16px",
            }}
          >
            {TRUST_ITEMS.map((item) => (
              <div
                key={item.title}
                style={{
                  padding: "24px",
                  backgroundColor: "#F5F0E8",
                  borderRadius: "16px",
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    fontSize: "24px",
                    color: "#2D4A3E",
                    marginBottom: "12px",
                    fontWeight: 700,
                  }}
                >
                  {item.icon}
                </div>
                <div
                  style={{
                    fontSize: "15px",
                    fontWeight: 700,
                    color: "#2D4A3E",
                    marginBottom: "6px",
                    fontFamily: '"Noto Serif SC", serif',
                  }}
                >
                  {item.title}
                </div>
                <div style={{ fontSize: "13px", color: "#8B7E74", lineHeight: 1.5 }}>
                  {item.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* F. FAQ */}
      <section style={{ backgroundColor: "#F5F0E8", padding: "64px 24px" }}>
        <div style={{ maxWidth: "640px", margin: "0 auto" }}>
          <SectionHeading>常见问题</SectionHeading>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "24px" }}>
            {FAQ_ITEMS.map((item, i) => (
              <div
                key={i}
                style={{
                  backgroundColor: "#FFFFFF",
                  borderRadius: "12px",
                  overflow: "hidden",
                  border: "1px solid #E8E0D6",
                }}
              >
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  style={{
                    width: "100%",
                    padding: "16px 20px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    textAlign: "left",
                  }}
                >
                  <span style={{ fontSize: "14px", fontWeight: 600, color: "#3D3029" }}>
                    {item.q}
                  </span>
                  <span
                    style={{
                      color: "#8B7E74",
                      transition: "transform 200ms ease",
                      transform: openFaq === i ? "rotate(180deg)" : "none",
                      fontSize: "12px",
                    }}
                  >
                    ▾
                  </span>
                </button>
                {openFaq === i && (
                  <div
                    style={{
                      padding: "0 20px 16px",
                      fontSize: "14px",
                      color: "#8B7E74",
                      lineHeight: 1.7,
                      borderTop: "1px solid #F0EAE2",
                    }}
                  >
                    <div style={{ paddingTop: "12px" }}>{item.a}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
          <div style={{ textAlign: "center" }}>
            <Link
              href="/faq"
              style={{
                fontSize: "14px",
                color: "#2D4A3E",
                textDecoration: "none",
                borderBottom: "1px solid #2D4A3E",
                paddingBottom: "1px",
              }}
            >
              查看全部问题 →
            </Link>
          </div>
        </div>
      </section>

      {/* G. 底部 CTA */}
      <section
        style={{
          backgroundColor: "#2D4A3E",
          padding: "64px 24px",
          textAlign: "center",
          color: "white",
        }}
      >
        <div style={{ maxWidth: "480px", margin: "0 auto" }}>
          <h2
            style={{
              fontFamily: '"Noto Serif SC", serif',
              fontSize: "24px",
              fontWeight: 700,
              marginBottom: "8px",
            }}
          >
            一本替你想好一切的旅行手账
          </h2>
          <p style={{ fontSize: "16px", opacity: 0.7, marginBottom: "32px" }}>
            7天定制 ¥198 起
          </p>
          <Link
            href="/order"
            style={{
              display: "inline-block",
              padding: "14px 36px",
              borderRadius: "12px",
              backgroundColor: "#C65D3E",
              color: "white",
              fontSize: "16px",
              fontWeight: 600,
              textDecoration: "none",
              transition: "background-color 200ms ease",
            }}
          >
            开始定制 →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer
        style={{
          backgroundColor: "#2D4A3E",
          borderTop: "1px solid rgba(255,255,255,0.1)",
          padding: "24px",
          textAlign: "center",
          fontSize: "13px",
          color: "rgba(255,255,255,0.4)",
        }}
      >
        旅行手账 · 联系我们 · 服务条款 · 隐私政策
      </footer>
    </div>
  );
}

// ─── 子组件 ──────────────────────────────────────────────────────────────────

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2
      style={{
        fontFamily: '"Noto Serif SC", serif',
        fontSize: "clamp(20px, 3vw, 28px)",
        fontWeight: 700,
        color: "#2D4A3E",
        marginBottom: "32px",
        textAlign: "center",
      }}
    >
      {children}
    </h2>
  );
}

function EntryCard({
  title,
  subtitle,
  price,
  color,
  href,
}: {
  title: string;
  subtitle: string;
  price: string;
  color: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      style={{
        display: "block",
        width: "200px",
        padding: "20px",
        borderRadius: "16px",
        border: "2px solid #E8E0D6",
        backgroundColor: "#FFFFFF",
        textDecoration: "none",
        position: "relative",
        overflow: "hidden",
        transition: "transform 200ms ease, box-shadow 200ms ease",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.transform = "translateY(-4px)";
        (e.currentTarget as HTMLElement).style.boxShadow =
          "0 12px 32px rgba(61, 48, 41, 0.12)";
        (e.currentTarget as HTMLElement).style.borderColor = color;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.transform = "translateY(0)";
        (e.currentTarget as HTMLElement).style.boxShadow = "none";
        (e.currentTarget as HTMLElement).style.borderColor = "#E8E0D6";
      }}
    >
      {/* 左色条 */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: "4px",
          backgroundColor: color,
        }}
      />
      <div
        style={{
          fontSize: "16px",
          fontWeight: 700,
          color: "#2D4A3E",
          marginBottom: "4px",
          fontFamily: '"Noto Serif SC", serif',
        }}
      >
        {title}
      </div>
      <div style={{ fontSize: "12px", color: "#8B7E74", marginBottom: "12px" }}>
        {subtitle}
      </div>
      <div
        style={{
          fontSize: "18px",
          fontWeight: 800,
          color: "#C65D3E",
          fontFamily: '"Inter", sans-serif',
        }}
      >
        {price}
      </div>
    </Link>
  );
}
