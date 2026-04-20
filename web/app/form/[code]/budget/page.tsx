"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

// ─── 类型 ────────────────────────────────────────────────────────────────────

interface TierOption {
  id: string;
  label: string;
  price_range: string;
  description: string;
}

interface BudgetEstimate {
  dining_total: number;
  hotel_total: number;
  transport: number;
  tickets: number;
  addons: number;
  total_per_person: number;
  currency: string;
}

interface BudgetOptions {
  dining_tiers: TierOption[];
  hotel_tiers: TierOption[];
  dining_preferences: { id: string; label: string }[];
  hotel_preferences: { id: string; label: string }[];
  comfort_addons: { id: string; label: string; price_range: string; description: string }[];
  default_estimate: BudgetEstimate;
}

interface Selections {
  dining_tier: string;
  dining_preference: string;
  hotel_tier: string;
  hotel_preferences: Set<string>;
  comfort_addons: Set<string>;
}

const colors = {
  bg: "#FBF7F0",
  white: "#FFFFFF",
  green: "#2D4A3E",
  greenLight: "#4A8B6E",
  greenBg: "#F0F5F2",
  sand: "#F5F0E8",
  border: "#E0D8CE",
  borderLight: "#F0EAE2",
  text: "#3D3029",
  textMuted: "#8B7E74",
  textFaint: "#A69B91",
  red: "#C65D3E",
};

// 费用系数（每人每顿均价 × 天数 × 系数估算）
const DINING_PRICE: Record<string, number> = {
  street: 50, local_good: 115, fine: 275, top: 600,
};
const HOTEL_PRICE: Record<string, number> = {
  budget: 350, comfort: 700, premium: 1400, luxury: 3000,
};

function calcEstimate(
  selections: Selections,
  tripDays: number,
  adults: number,
): BudgetEstimate {
  if (!selections.dining_tier || !selections.hotel_tier || !tripDays) {
    return { dining_total: 0, hotel_total: 0, transport: 500, tickets: 350, addons: 0, total_per_person: 0, currency: "CNY" };
  }
  const meals = tripDays * 2; // 早餐自理，算午晚
  const dining_total = Math.round(DINING_PRICE[selections.dining_tier] * meals);
  const nights = Math.max(1, tripDays - 1);
  const hotel_per_night = HOTEL_PRICE[selections.hotel_tier];
  const hotel_total = Math.round((hotel_per_night * nights) / Math.max(1, Math.floor(adults / 2)));
  const transport = 500;
  const tickets = 350;
  let addons = 0;
  if (selections.comfort_addons.has("luggage_delivery")) addons += 125 * Math.floor(tripDays / 2);
  if (selections.comfort_addons.has("occasional_taxi")) addons += 400;
  const total_per_person = dining_total + hotel_total + transport + tickets + addons;
  return { dining_total, hotel_total, transport, tickets, addons, total_per_person, currency: "CNY" };
}

// ─── 主组件 ──────────────────────────────────────────────────────────────────

export default function BudgetPage() {
  const params = useParams();
  const router = useRouter();
  const code = params.code as string;

  const [tripId, setTripId] = useState<string | null>(null);
  const [options, setOptions] = useState<BudgetOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [tripDays, setTripDays] = useState(7);
  const [adults, setAdults] = useState(2);

  const [sel, setSel] = useState<Selections>({
    dining_tier: "",
    dining_preference: "",
    hotel_tier: "",
    hotel_preferences: new Set(),
    comfort_addons: new Set(),
  });

  useEffect(() => {
    const id = localStorage.getItem(`trip_v2_${code}`);
    if (!id) { router.replace(`/form/${code}`); return; }
    setTripId(id);

    // 从 localStorage 的草稿中读取天数和人数
    const draft = localStorage.getItem(`form_v2_${code}`);
    if (draft) {
      try {
        const f = JSON.parse(draft);
        if (f.travel_start_date && f.travel_end_date) {
          const diff = new Date(f.travel_end_date).getTime() - new Date(f.travel_start_date).getTime();
          setTripDays(Math.max(1, Math.round(diff / (1000 * 60 * 60 * 24)) + 1));
        }
        if (f.adults) setAdults(f.adults);
      } catch {}
    }

    fetch(`/api/v2/trips/${id}/budget-options`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setOptions(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [code, router]);

  const estimate = calcEstimate(sel, tripDays, adults);
  const canConfirm = !!(sel.dining_tier && sel.hotel_tier);

  const handleConfirm = async () => {
    if (!tripId || !canConfirm) return;
    setConfirming(true);
    try {
      const res = await fetch(`/api/v2/trips/${tripId}/budget-confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dining_tier: sel.dining_tier,
          dining_preference: sel.dining_preference || null,
          hotel_tier: sel.hotel_tier,
          hotel_preferences: Array.from(sel.hotel_preferences),
          comfort_addons: Object.fromEntries(
            Array.from(sel.comfort_addons).map(k => [k, true])
          ),
        }),
      });
      if (res.ok) {
        localStorage.removeItem(`trip_v2_${code}`);
        router.push(`/guide/${code}`);
      } else {
        setConfirming(false);
        alert("确认失败，请重试");
      }
    } catch {
      setConfirming(false);
      alert("网络错误，请重试");
    }
  };

  if (loading) {
    return (
      <div style={{ backgroundColor: colors.bg, minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ fontSize: "15px", color: colors.textMuted }}>加载中…</p>
      </div>
    );
  }

  if (!options) {
    return (
      <div style={{ backgroundColor: colors.bg, minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}>
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: "15px", color: colors.text, marginBottom: "16px" }}>加载预算选项失败</p>
          <button onClick={() => window.location.reload()} style={{
            padding: "12px 28px", borderRadius: "10px", border: "none",
            backgroundColor: colors.red, color: "white", fontSize: "14px", cursor: "pointer",
          }}>刷新重试</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: colors.bg, minHeight: "100vh" }}>
      {/* 顶部说明 */}
      <div style={{ backgroundColor: colors.green, padding: "20px 24px 22px" }}>
        <div style={{ maxWidth: "560px", margin: "0 auto" }}>
          <h1 style={{
            fontFamily: '"Noto Serif SC", serif', fontSize: "20px", fontWeight: 700,
            color: "white", marginBottom: "6px",
          }}>
            你的路线已经确定
          </h1>
          <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.7)", lineHeight: 1.5 }}>
            这里选的是这趟旅行想住得多舒服、吃得多讲究。不会改变前面的行程安排。
          </p>
        </div>
      </div>

      <div style={{ maxWidth: "560px", margin: "0 auto", padding: "24px 24px 140px" }}>

        {/* 吃饭 */}
        <Section title="吃饭">
          <p style={{ fontSize: "13px", color: colors.textMuted, marginBottom: "14px" }}>每人每顿均价</p>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "20px" }}>
            {options.dining_tiers.map(tier => (
              <TierCard
                key={tier.id}
                tier={tier}
                selected={sel.dining_tier === tier.id}
                onClick={() => setSel(prev => ({ ...prev, dining_tier: tier.id }))}
              />
            ))}
          </div>
          <p style={{ fontSize: "13px", color: colors.textMuted, marginBottom: "10px" }}>
            吃饭更看重什么？
            <span style={{ color: colors.textFaint }}> （可不选，帮你平衡）</span>
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {options.dining_preferences.map(pref => {
              const on = sel.dining_preference === pref.id;
              return (
                <button
                  key={pref.id}
                  onClick={() => setSel(prev => ({ ...prev, dining_preference: on ? "" : pref.id }))}
                  style={{
                    padding: "12px 16px", borderRadius: "10px", textAlign: "left",
                    border: `1.5px solid ${on ? colors.green : colors.border}`,
                    backgroundColor: on ? colors.greenBg : colors.white,
                    fontSize: "13px", color: on ? colors.green : colors.textMuted,
                    fontWeight: on ? 600 : 400, cursor: "pointer", transition: "all 200ms ease",
                  }}
                >{pref.label}</button>
              );
            })}
          </div>
        </Section>

        {/* 住宿 */}
        <Section title="住宿">
          <p style={{ fontSize: "13px", color: colors.textMuted, marginBottom: "14px" }}>每间每晚均价</p>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "20px" }}>
            {options.hotel_tiers.map(tier => (
              <TierCard
                key={tier.id}
                tier={tier}
                selected={sel.hotel_tier === tier.id}
                onClick={() => setSel(prev => ({ ...prev, hotel_tier: tier.id }))}
              />
            ))}
          </div>
          <p style={{ fontSize: "13px", color: colors.textMuted, marginBottom: "10px" }}>
            住宿更看重什么？
            <span style={{ color: colors.textFaint }}> （可多选）</span>
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {options.hotel_preferences.map(pref => {
              const on = sel.hotel_preferences.has(pref.id);
              return (
                <button
                  key={pref.id}
                  onClick={() => {
                    setSel(prev => {
                      const next = new Set(prev.hotel_preferences);
                      if (next.has(pref.id)) next.delete(pref.id); else next.add(pref.id);
                      return { ...prev, hotel_preferences: next };
                    });
                  }}
                  style={{
                    padding: "12px 16px", borderRadius: "10px", textAlign: "left",
                    border: `1.5px solid ${on ? colors.green : colors.border}`,
                    backgroundColor: on ? colors.greenBg : colors.white,
                    fontSize: "13px", color: on ? colors.green : colors.textMuted,
                    fontWeight: on ? 600 : 400, cursor: "pointer", transition: "all 200ms ease",
                    display: "flex", alignItems: "center", gap: "10px",
                  }}
                >
                  <div style={{
                    width: "18px", height: "18px", borderRadius: "4px", flexShrink: 0,
                    border: `2px solid ${on ? colors.green : colors.border}`,
                    backgroundColor: on ? colors.green : "transparent",
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    {on && <span style={{ color: "white", fontSize: "11px" }}>✓</span>}
                  </div>
                  {pref.label}
                </button>
              );
            })}
          </div>
        </Section>

        {/* 舒适加购 */}
        <Section title="舒适加购（可选）">
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {options.comfort_addons.map(addon => {
              const on = sel.comfort_addons.has(addon.id);
              return (
                <button
                  key={addon.id}
                  onClick={() => {
                    setSel(prev => {
                      const next = new Set(prev.comfort_addons);
                      if (next.has(addon.id)) next.delete(addon.id); else next.add(addon.id);
                      return { ...prev, comfort_addons: next };
                    });
                  }}
                  style={{
                    padding: "14px 18px", borderRadius: "12px", textAlign: "left", width: "100%",
                    border: `1.5px solid ${on ? colors.green : colors.border}`,
                    backgroundColor: on ? colors.greenBg : colors.white,
                    cursor: "pointer", transition: "all 200ms ease",
                    display: "flex", alignItems: "center", gap: "14px",
                  }}
                >
                  <div style={{
                    width: "20px", height: "20px", borderRadius: "4px", flexShrink: 0,
                    border: `2px solid ${on ? colors.green : colors.border}`,
                    backgroundColor: on ? colors.green : "transparent",
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    {on && <span style={{ color: "white", fontSize: "12px", fontWeight: "bold" }}>✓</span>}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: "14px", fontWeight: 600, color: colors.text, marginBottom: "2px" }}>
                      {addon.label}
                      <span style={{ fontSize: "13px", fontWeight: 400, color: colors.textMuted, marginLeft: "8px" }}>
                        {addon.price_range}
                      </span>
                    </div>
                    <div style={{ fontSize: "12px", color: colors.textMuted }}>{addon.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </Section>

        {/* 费用预估 */}
        {canConfirm && (
          <div style={{
            backgroundColor: colors.white, borderRadius: "14px",
            border: `1.5px solid ${colors.border}`, overflow: "hidden", marginBottom: "8px",
          }}>
            <div style={{ backgroundColor: colors.sand, padding: "14px 20px" }}>
              <p style={{ fontSize: "13px", fontWeight: 600, color: colors.textMuted }}>
                💰 {tripDays} 天预估（每人，不含机票购物）
              </p>
            </div>
            <div style={{ padding: "16px 20px" }}>
              {[
                { label: `餐饮 ${tripDays * 2} 顿`, value: estimate.dining_total },
                { label: `住宿 ${Math.max(1, tripDays - 1)} 晚（2人分摊）`, value: estimate.hotel_total },
                { label: "交通", value: estimate.transport },
                { label: "门票·活动", value: estimate.tickets },
                ...(estimate.addons > 0 ? [{ label: "舒适加购", value: estimate.addons }] : []),
              ].map((row, i) => (
                <div key={i} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "8px 0",
                  borderBottom: i < 3 ? `1px solid ${colors.borderLight}` : "none",
                }}>
                  <span style={{ fontSize: "14px", color: colors.textMuted }}>{row.label}</span>
                  <span style={{ fontSize: "14px", color: colors.text }}>¥{row.value.toLocaleString()}</span>
                </div>
              ))}
              <div style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                paddingTop: "14px", marginTop: "8px", borderTop: `2px solid ${colors.border}`,
              }}>
                <span style={{ fontSize: "15px", fontWeight: 600, color: colors.text }}>合计约</span>
                <span style={{ fontSize: "22px", fontWeight: 700, color: colors.green }}>
                  ¥{estimate.total_per_person.toLocaleString()} / 人
                </span>
              </div>
              <p style={{ fontSize: "12px", color: colors.textFaint, marginTop: "8px" }}>
                选择不同档位，数字会实时变化
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 底部按钮 */}
      <div style={{
        position: "fixed", bottom: 0, left: 0, right: 0,
        backgroundColor: colors.white, borderTop: `1px solid ${colors.border}`,
        padding: "16px 24px",
      }}>
        <div style={{ maxWidth: "560px", margin: "0 auto" }}>
          <button
            onClick={handleConfirm}
            disabled={!canConfirm || confirming}
            style={{
              width: "100%", padding: "16px", borderRadius: "12px", border: "none",
              backgroundColor: canConfirm && !confirming ? colors.green : colors.border,
              color: canConfirm && !confirming ? "white" : colors.textFaint,
              fontSize: "16px", fontWeight: 600,
              cursor: canConfirm && !confirming ? "pointer" : "not-allowed",
              transition: "all 200ms ease",
            }}
          >
            {confirming ? "确认中…" : !canConfirm ? "先选吃饭和住宿档位" : "确认，开始制作我的手账本 →"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── 共用组件 ─────────────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "24px" }}>
      <h2 style={{
        fontSize: "16px", fontWeight: 700, color: colors.text,
        marginBottom: "16px", paddingBottom: "10px",
        borderBottom: `2px solid ${colors.border}`,
      }}>{title}</h2>
      {children}
    </div>
  );
}

function TierCard({
  tier, selected, onClick,
}: {
  tier: TierOption; selected: boolean; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "14px 18px", borderRadius: "12px", width: "100%", textAlign: "left",
        border: `1.5px solid ${selected ? colors.green : colors.border}`,
        backgroundColor: selected ? colors.greenBg : colors.white,
        cursor: "pointer", transition: "all 200ms ease",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div style={{
          width: "18px", height: "18px", borderRadius: "50%", flexShrink: 0,
          border: `2px solid ${selected ? colors.green : colors.border}`,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          {selected && <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: colors.green }} />}
        </div>
        <div>
          <span style={{ fontSize: "15px", fontWeight: 600, color: colors.text }}>{tier.label}</span>
          <span style={{ fontSize: "13px", color: colors.textMuted, marginLeft: "8px" }}>{tier.price_range}</span>
        </div>
      </div>
      <span style={{ fontSize: "12px", color: colors.textFaint, maxWidth: "130px", textAlign: "right" }}>
        {tier.description}
      </span>
    </button>
  );
}
