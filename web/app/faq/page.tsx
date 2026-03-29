"use client";

import { useState } from "react";
import Link from "next/link";

const FAQ_GROUPS: { category: string; items: { q: string; a: string }[] }[] = [
  {
    category: "关于产品",
    items: [
      {
        q: "手账是模板还是定制的？",
        a: "完全定制。根据你的出行日期、天数、同行人数、预算、偏好逐一生成。不同用户的手账内容完全不同，我们不套模板。",
      },
      {
        q: "手账里有什么内容？",
        a: "封面 · 全程路线地图 · 旅行气质 · 亮点预告 · 酒店策略 · 餐厅总表 · 预算分布 · 出发准备 · 预约行动清单 · 每日执行页（上午/下午/晚上详细）· Plan B 备选 · 出片指南 · 旅后层（购物/预算回顾）。标准7天约62页。",
      },
      {
        q: "纸质版什么材质？",
        a: "哑粉纸128g，铁圈装订，附折叠地图、PVC袋页×2、可撕明信片×2、城市圈定制贴纸包。",
      },
    ],
  },
  {
    category: "关于价格",
    items: [
      {
        q: "怎么收费的？",
        a: "以7天为基础，国内圈 ¥198 / 海外圈 ¥228。每多1天 +¥20，每少1天 -¥20。最低5天 ¥158（国内）/ ¥188（海外）。",
      },
      {
        q: "11天以上怎么算？",
        a: "11天起拆为两册，加收拆册费 ¥29。每册独立完整，有各自的封面、地图、行程和旅后层。",
      },
      {
        q: "不满意可以退款吗？",
        a: "确认方案之前可以全额退款，无任何条件。确认解锁全部内容后不可退。如果你在确认前觉得方案不符合预期，直接提出，我们会调整或退款。",
      },
    ],
  },
  {
    category: "关于流程",
    items: [
      {
        q: "下单到收到手账要多久？",
        a: "填写表单提交后约2小时内生成数字版，我们会通过微信通知你。确认方案后安排打印，顺丰快递2-3天送达。",
      },
      {
        q: "可以修改方案吗？",
        a: "可以。在确认解锁之前，你可以通过AI对话提交修改意见（一轮免费），我们会据此调整手账内容（约5分钟）。确认解锁后内容定稿，需要再改可以联系客服。",
      },
      {
        q: "你们能帮订机票/酒店吗？",
        a: "不管机票，机票需要自己预订。酒店我们会在手账里给出推荐方案和理由，但最终也是你自己去订。手账负责帮你想清楚住哪、为什么住这里。",
      },
    ],
  },
  {
    category: "关于使用",
    items: [
      {
        q: "手账本能永久在线查看吗？",
        a: "数字版可以通过专属链接随时访问，长期有效，不会过期。建议同时下载PDF作为备份，旅途中离线也能看。",
      },
      {
        q: "可以分享给同行朋友吗？",
        a: "可以。你可以把专属链接发给同行的人，他们可以查看完整手账。",
      },
      {
        q: "旅途中有问题怎么办？",
        a: "手账里有安全应急信息（紧急电话/使馆信息），以及当地实用App推荐。如果遇到行程临时变化，可以联系客服微信，我们会人工协助。",
      },
    ],
  },
];

export default function FAQPage() {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());

  const toggle = (key: string) => {
    setOpenItems((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <div style={{ backgroundColor: "#FBF7F0", minHeight: "100vh", paddingBottom: "80px" }}>
      {/* 页头 */}
      <div
        style={{
          padding: "48px 24px 40px",
          textAlign: "center",
          maxWidth: "720px",
          margin: "0 auto",
        }}
      >
        <h1
          style={{
            fontFamily: '"Noto Serif SC", serif',
            fontSize: "32px",
            fontWeight: 700,
            color: "#2D4A3E",
            marginBottom: "8px",
          }}
        >
          常见问题
        </h1>
        <p style={{ fontSize: "15px", color: "#8B7E74" }}>
          找不到答案？微信联系我们：traveljournal2025
        </p>
      </div>

      {/* 问题列表 */}
      <div style={{ maxWidth: "720px", margin: "0 auto", padding: "0 24px" }}>
        {FAQ_GROUPS.map((group) => (
          <div key={group.category} style={{ marginBottom: "40px" }}>
            <h2
              style={{
                fontFamily: '"Noto Serif SC", serif',
                fontSize: "16px",
                fontWeight: 700,
                color: "#2D4A3E",
                marginBottom: "12px",
                paddingLeft: "12px",
                borderLeft: "3px solid #2D4A3E",
              }}
            >
              {group.category}
            </h2>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {group.items.map((item, i) => {
                const key = `${group.category}-${i}`;
                const isOpen = openItems.has(key);
                return (
                  <div
                    key={key}
                    style={{
                      backgroundColor: "#FFFFFF",
                      borderRadius: "12px",
                      border: "1px solid #E8E0D6",
                      overflow: "hidden",
                    }}
                  >
                    <button
                      onClick={() => toggle(key)}
                      style={{
                        width: "100%",
                        padding: "16px 20px",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "12px",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        textAlign: "left",
                      }}
                    >
                      <span
                        style={{
                          fontSize: "14px",
                          fontWeight: 600,
                          color: "#3D3029",
                          lineHeight: 1.4,
                        }}
                      >
                        {item.q}
                      </span>
                      <span
                        style={{
                          color: "#8B7E74",
                          transition: "transform 200ms ease",
                          transform: isOpen ? "rotate(180deg)" : "none",
                          fontSize: "12px",
                          flexShrink: 0,
                        }}
                      >
                        ▾
                      </span>
                    </button>
                    {isOpen && (
                      <div
                        style={{
                          padding: "0 20px 16px",
                          borderTop: "1px solid #F0EAE2",
                        }}
                      >
                        <p
                          style={{
                            paddingTop: "12px",
                            fontSize: "14px",
                            color: "#8B7E74",
                            lineHeight: 1.8,
                          }}
                        >
                          {item.a}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}

        {/* 底部 CTA */}
        <div
          style={{
            backgroundColor: "#2D4A3E",
            borderRadius: "16px",
            padding: "32px",
            textAlign: "center",
            color: "white",
          }}
        >
          <p
            style={{
              fontFamily: '"Noto Serif SC", serif',
              fontSize: "18px",
              fontWeight: 700,
              marginBottom: "8px",
            }}
          >
            准备好了吗？
          </p>
          <p style={{ fontSize: "14px", opacity: 0.7, marginBottom: "20px" }}>
            7天定制手账 ¥198 起，不满意全额退
          </p>
          <Link
            href="/order"
            style={{
              display: "inline-block",
              padding: "12px 28px",
              borderRadius: "10px",
              backgroundColor: "#C65D3E",
              color: "white",
              fontSize: "15px",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            开始定制 →
          </Link>
        </div>
      </div>
    </div>
  );
}
