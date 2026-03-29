"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

// ─── 类型 ─────────────────────────────────────────────────────────────────────

type GuideStatus = "waiting" | "preview" | "unlocked";

interface BookingTask {
  name: string;
  action: string;
  deadline: string;
  link?: string;
  urgency: "red" | "yellow" | "green";
}

interface DaySummary {
  day: number;
  title: string;
  subtitle: string;
}

interface GuideData {
  status: GuideStatus;
  code: string;
  cityGroup: string;
  days: number;
  title: string;
  tagline: string;
  // 前置层内容
  summary: string;
  routeOverview: string;
  vibe: string;
  highlights: string[];
  hotelStrategy: string;
  restaurants: { name: string; mealType: string; price: string; note: string }[];
  budgetNotes: string;
  departure: string;
  bookingTasks: BookingTask[];
  daySummaries: DaySummary[];
  // 用户提交信息
  submittedInfo: string;
}

// 模拟数据（实际替换为 GET /api/guide/[code]）
const MOCK_DATA: GuideData = {
  status: "preview",
  code: "TRV-A3K9M2",
  cityGroup: "关西",
  days: 7,
  title: "关西 7天 · 专属手账",
  tagline: "「京都的风，大阪的胃」",
  summary: "这趟旅行的重心放在深度而非广度——前三天慢慢进入京都的节奏，第四天一口气去大阪感受反差，后半程用奈良和宇治做收尾。",
  routeOverview: "Day1 东山 → Day2 岚山+嵐山 → Day3 大阪美食 → Day4 奈良公园 → Day5 京都深度 → Day6 购物 → Day7 最后散步",
  vibe: "这是一趟慢旅行。我们刻意把每天的景点数量控制在2-3个，留出足够的时间在街角发呆、在咖啡馆看一本书、或者什么都不做只是坐着。",
  highlights: [
    "第三天有个值得留胃口的晚餐",
    "第五天下午的散步路线是私藏",
    "最后一天有个适合寄明信片的咖啡馆",
  ],
  hotelStrategy: "河原町 Hotel Gracery · 全程不换 · 到东山步行15分钟\n为什么选这家：位置在京都最核心的河原町商圈，步行可到祇园、东山、锦市场，价位在轻奢区间中偏低，评价稳定。",
  restaurants: [
    { name: "祇園 割烹○○", mealType: "晚餐", price: "¥3500/人", note: "需Tabelog预约，出发前10天" },
    { name: "锦市场 ○○寿司", mealType: "午餐", price: "¥2000", note: "现场排队，早上10点开门" },
    { name: "道顿堀 ○○拉面", mealType: "晚餐", price: "¥900", note: "约15分钟等位，可接受" },
    { name: "伏见稻荷 豆腐小店", mealType: "午餐", price: "¥600", note: "现金，价格实惠" },
  ],
  budgetNotes: "7天人均预算约 ¥4500：餐饮 ¥1800（每天约 ¥250），交通 ¥800（ICOCA 卡），门票 ¥700，购物 ¥1200。第三天和第六天花费较多。",
  departure: "ICOCA 交通卡（落地就买）· eSIM（出发前激活）· 行李寄送（酒店到酒店）· 必备 App：Google Maps / Tabelog / Google 翻译",
  bookingTasks: [
    { name: "祇園 割烹○○", action: "Tabelog 预约", deadline: "出发前10天", link: "#", urgency: "yellow" },
    { name: "岚山小火车", action: "官网购票", deadline: "出发前1周", link: "#", urgency: "green" },
    { name: "环球影城", action: "官网购票", deadline: "可现场", urgency: "green" },
  ],
  daySummaries: [
    { day: 1, title: "东山慢日", subtitle: "清水寺→八坂神社→鸭川" },
    { day: 2, title: "岚山竹林与小火车", subtitle: "竹林→小火车→岚山散步" },
    { day: 3, title: "大阪美食日", subtitle: "黑门市场→道顿堀→难波" },
    { day: 4, title: "奈良公园与宇治", subtitle: "奈良鹿→东大寺→宇治抹茶" },
    { day: 5, title: "京都深度", subtitle: "金阁寺→哲学之道→祇园夜" },
    { day: 6, title: "自由活动与购物", subtitle: "锦市场→四条河原町" },
    { day: 7, title: "最后的散步", subtitle: "南禅寺→寄明信片→机场" },
  ],
  submittedInfo: "关西 · 9.20-9.25 · 情侣 · 轻奢 · 美食+摄影",
};

// ─── 主页面 ──────────────────────────────────────────────────────────────────

export default function GuidePage() {
  const params = useParams();
  const router = useRouter();
  const code = params.code as string;
  const [data, setData] = useState<GuideData | null>(null);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    fetch(`/api/guide/${code}`)
      .then((r) => r.json())
      .then((d) => {
        if (d.status) {
          setData({
            ...MOCK_DATA,
            code,
            status: d.status,
            ...(d.data || {}),
          });
        } else {
          // fallback to mock if backend unavailable
          setData({ ...MOCK_DATA, code });
        }
      })
      .catch(() => setData({ ...MOCK_DATA, code }));
  }, [code]);

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      await fetch(`/api/guide/${code}/confirm`, { method: "POST" });
    } catch {
      // ignore errors, update UI optimistically
    }
    setData((prev) => prev ? { ...prev, status: "unlocked" } : prev);
    setConfirming(false);
  };

  if (!data) {
    return (
      <div
        style={{
          backgroundColor: "#FBF7F0",
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ textAlign: "center", color: "#8B7E74", fontSize: "15px" }}>
          加载中…
        </div>
      </div>
    );
  }

  if (data.status === "waiting") {
    return <WaitingState data={data} />;
  }

  return (
    <div style={{ backgroundColor: "#FBF7F0" }}>
      {/* 专属码提示 */}
      <div
        style={{
          backgroundColor: "#2D4A3E",
          color: "white",
          textAlign: "center",
          padding: "10px 24px",
          fontSize: "13px",
        }}
      >
        你的专属手账已生成 · <strong>{data.code}</strong>
      </div>

      {/* 封面区 */}
      <div
        style={{
          backgroundColor: "#FBF7F0",
          padding: "48px 24px 40px",
          textAlign: "center",
          maxWidth: "800px",
          margin: "0 auto",
        }}
      >
        <div
          style={{
            display: "inline-block",
            padding: "4px 12px",
            backgroundColor: "#F5F0E8",
            borderRadius: "20px",
            fontSize: "13px",
            color: "#8B7E74",
            marginBottom: "16px",
          }}
        >
          {data.cityGroup} · {data.days}天
        </div>
        <h1
          style={{
            fontFamily: '"Noto Serif SC", serif',
            fontSize: "32px",
            fontWeight: 700,
            color: "#2D4A3E",
            marginBottom: "8px",
            lineHeight: 1.3,
          }}
        >
          {data.title}
        </h1>
        <p
          style={{
            fontFamily: '"Noto Serif SC", serif',
            fontSize: "18px",
            color: "#8B7E74",
            fontStyle: "italic",
          }}
        >
          {data.tagline}
        </p>
      </div>

      {/* 路线地图占位 */}
      <Section alt>
        <SectionTitle>完整路线</SectionTitle>
        <div
          style={{
            backgroundColor: "#E8E0D6",
            borderRadius: "12px",
            padding: "24px",
            textAlign: "center",
            fontSize: "14px",
            color: "#8B7E74",
            marginBottom: "16px",
          }}
        >
          [路线地图]
        </div>
        <p style={{ fontSize: "14px", color: "#8B7E74", lineHeight: 1.8 }}>
          {data.routeOverview}
        </p>
      </Section>

      {/* 旅行气质 */}
      <Section>
        <SectionTitle>旅行气质</SectionTitle>
        <p style={{ fontSize: "15px", color: "#3D3029", lineHeight: 1.8 }}>{data.vibe}</p>
      </Section>

      {/* 亮点 */}
      <Section alt>
        <SectionTitle>这趟行程的亮点</SectionTitle>
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {data.highlights.map((h, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "10px",
                padding: "12px 16px",
                backgroundColor: "#FFFFFF",
                borderRadius: "10px",
              }}
            >
              <span style={{ color: "#D4A855", flexShrink: 0 }}>✦</span>
              <span style={{ fontSize: "14px", color: "#3D3029" }}>{h}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* 酒店策略 */}
      <Section>
        <SectionTitle>住宿策略</SectionTitle>
        <div
          style={{
            backgroundColor: "#F5F0E8",
            borderRadius: "12px",
            padding: "20px",
          }}
        >
          {data.hotelStrategy.split("\n").map((line, i) => (
            <p
              key={i}
              style={{
                fontSize: "14px",
                color: "#3D3029",
                marginBottom: i === 0 ? "8px" : 0,
                fontWeight: i === 0 ? 600 : 400,
              }}
            >
              {line}
            </p>
          ))}
        </div>
      </Section>

      {/* 餐厅总表 */}
      <Section alt>
        <SectionTitle>餐厅总表</SectionTitle>
        <div
          style={{
            backgroundColor: "#FFFFFF",
            borderRadius: "12px",
            overflow: "hidden",
            border: "1px solid #E8E0D6",
          }}
        >
          {data.restaurants.map((r, i) => (
            <div
              key={i}
              style={{
                padding: "14px 20px",
                borderBottom: i < data.restaurants.length - 1 ? "1px solid #F0EAE2" : "none",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                flexWrap: "wrap",
                gap: "4px",
              }}
            >
              <div>
                <span style={{ fontSize: "14px", fontWeight: 600, color: "#3D3029" }}>
                  {r.name}
                </span>
                <span
                  style={{
                    fontSize: "12px",
                    color: "#8B7E74",
                    marginLeft: "8px",
                  }}
                >
                  {r.mealType}
                </span>
              </div>
              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "13px", color: "#3D3029" }}>{r.price}</span>
                <span style={{ fontSize: "12px", color: "#A69B91", display: "block" }}>{r.note}</span>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* 预算分布 */}
      <Section>
        <SectionTitle>预算分布</SectionTitle>
        <p style={{ fontSize: "14px", color: "#3D3029", lineHeight: 1.8 }}>{data.budgetNotes}</p>
      </Section>

      {/* 出发准备 */}
      <Section alt>
        <SectionTitle>出发准备</SectionTitle>
        <p style={{ fontSize: "14px", color: "#3D3029", lineHeight: 1.8 }}>{data.departure}</p>
      </Section>

      {/* 预约行动清单 */}
      <Section>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "20px",
          }}
        >
          <SectionTitle style={{ marginBottom: 0 }}>预约行动清单</SectionTitle>
          <span
            style={{
              padding: "3px 10px",
              backgroundColor: "#FFF0E8",
              borderRadius: "20px",
              fontSize: "12px",
              color: "#C65D3E",
              fontWeight: 600,
            }}
          >
            ⚠ 需要尽快行动
          </span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {data.bookingTasks.map((task, i) => {
            const urgencyColor =
              task.urgency === "red" ? "#C94444" : task.urgency === "yellow" ? "#D4A855" : "#4A8B6E";
            const urgencyBg =
              task.urgency === "red" ? "#FFF0F0" : task.urgency === "yellow" ? "#FFFBF0" : "#F0FFF8";
            return (
              <div
                key={i}
                style={{
                  padding: "14px 16px",
                  backgroundColor: urgencyBg,
                  borderRadius: "10px",
                  border: `1px solid ${urgencyColor}30`,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "8px",
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ color: urgencyColor, fontSize: "14px" }}>●</span>
                    <span style={{ fontSize: "14px", fontWeight: 600, color: "#3D3029" }}>
                      {task.name}
                    </span>
                  </div>
                  <p style={{ fontSize: "13px", color: "#8B7E74", marginTop: "2px", marginLeft: "22px" }}>
                    {task.action} · {task.deadline}
                  </p>
                </div>
                {task.link && (
                  <a
                    href={task.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      padding: "8px 14px",
                      borderRadius: "8px",
                      backgroundColor: urgencyColor,
                      color: "#FFFFFF",
                      fontSize: "13px",
                      textDecoration: "none",
                      fontWeight: 600,
                    }}
                  >
                    打开链接 →
                  </a>
                )}
              </div>
            );
          })}
        </div>
      </Section>

      {/* 剧透提示页 */}
      <div
        style={{
          backgroundColor: "#2D4A3E",
          padding: "32px 24px",
          textAlign: "center",
          color: "white",
        }}
      >
        <p
          style={{
            fontFamily: '"Noto Serif SC", serif',
            fontSize: "16px",
            opacity: 0.9,
          }}
        >
          从下一页开始，这趟旅行会慢慢展开。
        </p>
      </div>

      {/* 锁定/解锁区域 */}
      <Section alt>
        <SectionTitle>每日行程</SectionTitle>
        {data.status === "preview" ? (
          <>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "24px" }}>
              {data.daySummaries.map((day) => (
                <div
                  key={day.day}
                  style={{
                    padding: "14px 20px",
                    backgroundColor: "#FFFFFF",
                    borderRadius: "10px",
                    border: "1px solid #E8E0D6",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    filter: "blur(0)",
                  }}
                >
                  <div>
                    <span
                      style={{
                        fontSize: "12px",
                        color: "#A69B91",
                        fontWeight: 600,
                        marginRight: "8px",
                      }}
                    >
                      Day {day.day}
                    </span>
                    <span style={{ fontSize: "14px", fontWeight: 600, color: "#3D3029" }}>
                      {day.title}
                    </span>
                    <span style={{ fontSize: "13px", color: "#8B7E74", marginLeft: "8px" }}>
                      {day.subtitle}
                    </span>
                  </div>
                  <span style={{ fontSize: "16px", color: "#A69B91" }}>🔒</span>
                </div>
              ))}
            </div>
            <p
              style={{
                fontSize: "13px",
                color: "#8B7E74",
                textAlign: "center",
                marginBottom: "20px",
              }}
            >
              确认后将解锁每天详细执行页
            </p>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <Link
                href={`/guide/${code}/modify`}
                style={{
                  flex: 1,
                  padding: "14px 20px",
                  borderRadius: "12px",
                  border: "1.5px solid #E0D8CE",
                  backgroundColor: "#FFFFFF",
                  color: "#3D3029",
                  fontSize: "15px",
                  fontWeight: 500,
                  textDecoration: "none",
                  textAlign: "center",
                  display: "block",
                  transition: "all 200ms ease",
                  minWidth: "120px",
                }}
              >
                我想修改方案
              </Link>
              <button
                onClick={handleConfirm}
                disabled={confirming}
                style={{
                  flex: 2,
                  padding: "14px 20px",
                  borderRadius: "12px",
                  border: "none",
                  backgroundColor: confirming ? "#D6CFC6" : "#C65D3E",
                  color: "#FFFFFF",
                  fontSize: "15px",
                  fontWeight: 600,
                  cursor: confirming ? "wait" : "pointer",
                  transition: "all 200ms ease",
                  minWidth: "160px",
                }}
              >
                {confirming ? "处理中…" : "确认，解锁全部 →"}
              </button>
            </div>
          </>
        ) : (
          <UnlockedDays daySummaries={data.daySummaries} />
        )}
      </Section>

      {/* 已解锁后的额外内容 */}
      {data.status === "unlocked" && (
        <>
          <Section>
            <SectionTitle>旅后层</SectionTitle>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
              {["购物清单", "预算回顾", "照片页", "心情页", "封底"].map((item) => (
                <div
                  key={item}
                  style={{
                    padding: "12px 20px",
                    backgroundColor: "#F5F0E8",
                    borderRadius: "10px",
                    fontSize: "14px",
                    color: "#3D3029",
                  }}
                >
                  {item}
                </div>
              ))}
            </div>
          </Section>
          {/* PDF 下载 */}
          <div
            style={{
              backgroundColor: "#FFFFFF",
              padding: "24px",
              textAlign: "center",
              borderTop: "1px solid #E8E0D6",
            }}
          >
            <button
              style={{
                padding: "14px 32px",
                borderRadius: "12px",
                border: "none",
                backgroundColor: "#2D4A3E",
                color: "#FFFFFF",
                fontSize: "15px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              下载 PDF
            </button>
          </div>
        </>
      )}

      {/* 底部 CTA */}
      <div
        style={{
          backgroundColor: "#2D4A3E",
          padding: "40px 24px",
          textAlign: "center",
          color: "white",
        }}
      >
        <p
          style={{
            fontFamily: '"Noto Serif SC", serif',
            fontSize: "16px",
            marginBottom: "20px",
          }}
        >
          看看其他城市圈 →
        </p>
        <Link
          href="/order"
          style={{
            padding: "12px 28px",
            borderRadius: "12px",
            border: "none",
            backgroundColor: "#C65D3E",
            color: "#FFFFFF",
            fontSize: "15px",
            fontWeight: 600,
            textDecoration: "none",
            display: "inline-block",
          }}
        >
          开始新的定制
        </Link>
      </div>
    </div>
  );
}

// ─── 子组件 ──────────────────────────────────────────────────────────────────

function WaitingState({ data }: { data: GuideData }) {
  return (
    <div
      style={{
        backgroundColor: "#FBF7F0",
        minHeight: "80vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 24px",
      }}
    >
      <div style={{ textAlign: "center", maxWidth: "400px" }}>
        <div style={{ fontSize: "64px", marginBottom: "24px" }}>📖</div>
        <h2
          style={{
            fontFamily: '"Noto Serif SC", serif',
            fontSize: "22px",
            fontWeight: 700,
            color: "#2D4A3E",
            marginBottom: "12px",
          }}
        >
          正在为你定制{data.cityGroup}{data.days}天旅行手账…
        </h2>
        <p style={{ fontSize: "15px", color: "#8B7E74", marginBottom: "8px" }}>
          预计 2-4 小时完成
        </p>
        <p style={{ fontSize: "14px", color: "#A69B91", marginBottom: "32px" }}>
          我们会通过微信通知你
        </p>
        <div
          style={{
            backgroundColor: "#FFFFFF",
            borderRadius: "12px",
            padding: "20px",
            border: "1px solid #E8E0D6",
            textAlign: "left",
          }}
        >
          <p style={{ fontSize: "13px", color: "#8B7E74", marginBottom: "8px" }}>你提交的信息：</p>
          <p style={{ fontSize: "14px", color: "#3D3029" }}>{data.submittedInfo}</p>
          <div
            style={{
              marginTop: "16px",
              paddingTop: "16px",
              borderTop: "1px solid #F0EAE2",
            }}
          >
            <p style={{ fontSize: "13px", color: "#8B7E74", marginBottom: "4px" }}>专属码</p>
            <p style={{ fontSize: "18px", fontWeight: 700, color: "#2D4A3E", letterSpacing: "0.05em" }}>
              {data.code}
            </p>
            <p style={{ fontSize: "12px", color: "#A69B91", marginTop: "4px" }}>截图保存</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Section({
  children,
  alt,
}: {
  children: React.ReactNode;
  alt?: boolean;
}) {
  return (
    <div
      style={{
        backgroundColor: alt ? "#F5F0E8" : "#FFFFFF",
        padding: "40px 24px",
      }}
    >
      <div style={{ maxWidth: "800px", margin: "0 auto" }}>{children}</div>
    </div>
  );
}

function SectionTitle({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <h2
      style={{
        fontFamily: '"Noto Serif SC", serif',
        fontSize: "20px",
        fontWeight: 700,
        color: "#2D4A3E",
        marginBottom: "20px",
        ...style,
      }}
    >
      {children}
    </h2>
  );
}

function UnlockedDays({ daySummaries }: { daySummaries: DaySummary[] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {daySummaries.map((day) => (
        <div
          key={day.day}
          style={{
            backgroundColor: "#FFFFFF",
            borderRadius: "12px",
            padding: "20px",
            border: "1px solid #E8E0D6",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }}>
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                backgroundColor: "#2D4A3E",
                color: "white",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "13px",
                fontWeight: 700,
                flexShrink: 0,
              }}
            >
              {day.day}
            </div>
            <div>
              <div style={{ fontSize: "16px", fontWeight: 700, color: "#2D4A3E" }}>{day.title}</div>
              <div style={{ fontSize: "13px", color: "#8B7E74" }}>{day.subtitle}</div>
            </div>
          </div>
          {/* 六页占位 */}
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {["封面", "逻辑", "上午", "下午", "晚上", "备选"].map((label) => (
              <div
                key={label}
                style={{
                  padding: "6px 12px",
                  backgroundColor: "#F5F0E8",
                  borderRadius: "6px",
                  fontSize: "12px",
                  color: "#8B7E74",
                }}
              >
                {label}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
