"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";

// ─── 类型 ────────────────────────────────────────────────────────────────────

interface BookedItem {
  type: string;
  name: string;
  date: string;
  notes: string;
}

interface FormData {
  // 屏1：日期
  travel_start_date: string;
  travel_end_date: string;
  arrival_slot: string;
  departure_slot: string;
  // 屏2：风格 + 人数
  trip_vibe: string;
  adults: number;
  children: number;
  elders: number;
  // 屏3：节奏
  density: string;
  // 屏4：特殊情况（可选）
  has_booked: boolean;
  pre_booked: BookedItem[];
  has_skip: boolean;
  skip_notes: string;
  special_notes: string;
}

const INITIAL_FORM: FormData = {
  travel_start_date: "",
  travel_end_date: "",
  arrival_slot: "afternoon",
  departure_slot: "morning",
  trip_vibe: "",
  adults: 2,
  children: 0,
  elders: 0,
  density: "",
  has_booked: false,
  pre_booked: [],
  has_skip: false,
  skip_notes: "",
  special_notes: "",
};

const TOTAL_SCREENS = 4;

// ─── 共用样式常量 ─────────────────────────────────────────────────────────────

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
  dot: "#D6CFC6",
  red: "#C65D3E",
};

// ─── 主组件 ──────────────────────────────────────────────────────────────────

export default function FormPage() {
  const params = useParams();
  const router = useRouter();
  const code = params.code as string;

  const [screen, setScreen] = useState(1);
  const [form, setForm] = useState<FormData>(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(`form_v2_${code}`);
    if (saved) {
      try { setForm(JSON.parse(saved)); } catch {}
    }
  }, [code]);

  const saveDraft = useCallback(
    (data: FormData) => localStorage.setItem(`form_v2_${code}`, JSON.stringify(data)),
    [code]
  );

  const update = (patch: Partial<FormData>) => {
    const next = { ...form, ...patch };
    setForm(next);
    saveDraft(next);
  };

  const goNext = () => { if (screen < TOTAL_SCREENS) setScreen(screen + 1); };
  const goPrev = () => { if (screen > 1) setScreen(screen - 1); };

  const canProceed = (): boolean => {
    if (screen === 1) return !!(form.travel_start_date && form.travel_end_date);
    if (screen === 2) return !!form.trip_vibe;
    if (screen === 3) return !!form.density;
    return true;
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const res = await fetch(`/api/v2/trips`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          form_code: code,
          travel_start_date: form.travel_start_date,
          travel_end_date: form.travel_end_date,
          arrival_slot: form.arrival_slot,
          departure_slot: form.departure_slot,
          trip_vibe: form.trip_vibe,
          adults: form.adults,
          children: form.children,
          elders: form.elders,
          density: form.density,
          pre_booked: form.has_booked ? form.pre_booked.map(b => ({
            type: b.type, name: b.name, date_from: b.date, fixed: true
          })) : [],
          skip_tags: [],
          special_notes: [
            form.has_skip && form.skip_notes ? `不想去：${form.skip_notes}` : "",
            form.special_notes,
          ].filter(Boolean).join("；") || undefined,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        const tripId = data.trip_request_id;
        localStorage.setItem(`trip_v2_${code}`, tripId);
        localStorage.removeItem(`form_v2_${code}`);
        router.push(`/form/${code}/plan`);
      } else {
        setSubmitting(false);
        alert("提交失败，请重试");
      }
    } catch {
      setSubmitting(false);
      alert("提交失败，请检查网络");
    }
  };

  const tripDays = (() => {
    if (!form.travel_start_date || !form.travel_end_date) return 0;
    const diff = new Date(form.travel_end_date).getTime() - new Date(form.travel_start_date).getTime();
    return Math.round(diff / (1000 * 60 * 60 * 24)) + 1;
  })();

  if (submitting) {
    return (
      <div style={{ backgroundColor: colors.bg, minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "40px", marginBottom: "16px" }}>✈️</div>
          <p style={{ fontFamily: '"Noto Serif SC", serif', fontSize: "18px", color: colors.green }}>
            正在帮你排第一版方案…
          </p>
          <p style={{ fontSize: "14px", color: colors.textMuted, marginTop: "8px" }}>
            大概需要 30 秒
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: colors.bg, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* 顶部进度 */}
      <div style={{
        position: "sticky", top: 0, backgroundColor: colors.bg, zIndex: 10,
        padding: "16px 24px 12px", borderBottom: `1px solid ${colors.border}`,
      }}>
        <div style={{ maxWidth: "560px", margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <button
            onClick={goPrev}
            style={{
              fontSize: "13px", color: screen === 1 ? "transparent" : colors.textMuted,
              background: "none", border: "none", cursor: screen === 1 ? "default" : "pointer", padding: "4px 0",
            }}
            disabled={screen === 1}
          >
            ← 返回
          </button>
          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            {Array.from({ length: TOTAL_SCREENS }).map((_, i) => (
              <div key={i} style={{
                width: i + 1 === screen ? "20px" : "7px", height: "7px",
                borderRadius: "4px",
                backgroundColor: i + 1 < screen ? colors.greenLight : i + 1 === screen ? colors.green : colors.dot,
                transition: "all 300ms ease",
              }} />
            ))}
          </div>
          <span style={{ fontSize: "13px", color: colors.textFaint }}>{screen} / {TOTAL_SCREENS}</span>
        </div>
      </div>

      {/* 内容区 */}
      <div style={{ flex: 1, maxWidth: "560px", margin: "0 auto", width: "100%", padding: "32px 24px 100px" }}>
        {screen === 1 && <Screen1 form={form} update={update} tripDays={tripDays} />}
        {screen === 2 && <Screen2 form={form} update={update} />}
        {screen === 3 && <Screen3 form={form} update={update} />}
        {screen === 4 && <Screen4 form={form} update={update} />}
      </div>

      {/* 底部按钮 */}
      <div style={{
        position: "fixed", bottom: 0, left: 0, right: 0,
        backgroundColor: colors.white, borderTop: `1px solid ${colors.border}`,
        padding: "16px 24px",
      }}>
        <div style={{
          maxWidth: "560px", margin: "0 auto",
          display: "flex", gap: "12px",
          justifyContent: screen === 4 ? "space-between" : "flex-end",
        }}>
          {screen === 4 && (
            <button onClick={goNext} style={{
              padding: "14px 20px", borderRadius: "12px",
              border: "none", backgroundColor: "transparent",
              color: colors.textMuted, fontSize: "14px", cursor: "pointer",
            }}>
              跳过，直接提交
            </button>
          )}
          {screen < TOTAL_SCREENS ? (
            <button
              onClick={goNext}
              disabled={!canProceed()}
              style={{
                padding: "14px 40px", borderRadius: "12px", border: "none",
                backgroundColor: canProceed() ? colors.red : colors.border,
                color: canProceed() ? colors.white : colors.textFaint,
                fontSize: "15px", fontWeight: 600, cursor: canProceed() ? "pointer" : "not-allowed",
                transition: "all 200ms ease",
              }}
            >
              继续 →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              style={{
                padding: "14px 40px", borderRadius: "12px", border: "none",
                backgroundColor: colors.red, color: colors.white,
                fontSize: "15px", fontWeight: 600, cursor: "pointer",
              }}
            >
              帮我排方案 →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── 共用组件 ─────────────────────────────────────────────────────────────────

function ScreenTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{
      fontFamily: '"Noto Serif SC", serif', fontSize: "22px", fontWeight: 700,
      color: colors.green, marginBottom: "8px", lineHeight: 1.4,
    }}>
      {children}
    </h2>
  );
}

function ScreenHint({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: "14px", color: colors.textMuted, marginBottom: "28px", lineHeight: 1.5 }}>
      {children}
    </p>
  );
}

function RadioCard({
  selected, onClick, icon, label, desc,
}: {
  selected: boolean; onClick: () => void; icon: string; label: string; desc: string;
}) {
  return (
    <button onClick={onClick} style={{
      display: "flex", alignItems: "flex-start", gap: "14px",
      padding: "16px 18px", borderRadius: "12px", width: "100%",
      border: `1.5px solid ${selected ? colors.green : colors.border}`,
      backgroundColor: selected ? colors.greenBg : colors.white,
      cursor: "pointer", textAlign: "left", transition: "all 200ms ease",
    }}>
      <div style={{
        width: "18px", height: "18px", borderRadius: "50%", flexShrink: 0, marginTop: "2px",
        border: `2px solid ${selected ? colors.green : colors.dot}`,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        {selected && <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: colors.green }} />}
      </div>
      <div>
        <div style={{ fontSize: "15px", fontWeight: 600, color: colors.text, marginBottom: "3px" }}>
          {icon} {label}
        </div>
        <div style={{ fontSize: "13px", color: colors.textMuted, lineHeight: 1.5 }}>{desc}</div>
      </div>
    </button>
  );
}

function NumberStepper({
  label, value, onChange, min = 0,
}: {
  label: string; value: number; onChange: (v: number) => void; min?: number;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 0", borderBottom: `1px solid ${colors.borderLight}` }}>
      <span style={{ fontSize: "15px", color: colors.text }}>{label}</span>
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <button
          onClick={() => onChange(Math.max(min, value - 1))}
          style={{
            width: "32px", height: "32px", borderRadius: "50%",
            border: `1.5px solid ${colors.border}`, backgroundColor: colors.white,
            fontSize: "18px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
            color: colors.text,
          }}
        >−</button>
        <span style={{ fontSize: "17px", fontWeight: 600, color: colors.green, minWidth: "24px", textAlign: "center" }}>{value}</span>
        <button
          onClick={() => onChange(value + 1)}
          style={{
            width: "32px", height: "32px", borderRadius: "50%",
            border: `1.5px solid ${colors.border}`, backgroundColor: colors.white,
            fontSize: "18px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
            color: colors.text,
          }}
        >+</button>
      </div>
    </div>
  );
}

// ─── 各屏 ─────────────────────────────────────────────────────────────────────

function Screen1({ form, update, tripDays }: { form: FormData; update: (p: Partial<FormData>) => void; tripDays: number }) {
  return (
    <div>
      <ScreenTitle>你们什么时候去关西？</ScreenTitle>
      <ScreenHint>只需要到达和离开的日期，机票你们自己订。</ScreenHint>

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div>
            <label style={{ fontSize: "12px", fontWeight: 600, color: colors.textMuted, display: "block", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.05em" }}>到达日期</label>
            <input
              type="date"
              value={form.travel_start_date}
              onChange={e => update({ travel_start_date: e.target.value })}
              style={{
                width: "100%", padding: "12px 14px", borderRadius: "10px",
                border: `1.5px solid ${form.travel_start_date ? colors.green : colors.border}`,
                backgroundColor: colors.white, fontSize: "15px", color: colors.text,
                outline: "none", boxSizing: "border-box",
              }}
            />
          </div>
          <div>
            <label style={{ fontSize: "12px", fontWeight: 600, color: colors.textMuted, display: "block", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.05em" }}>离开日期</label>
            <input
              type="date"
              value={form.travel_end_date}
              onChange={e => update({ travel_end_date: e.target.value })}
              style={{
                width: "100%", padding: "12px 14px", borderRadius: "10px",
                border: `1.5px solid ${form.travel_end_date ? colors.green : colors.border}`,
                backgroundColor: colors.white, fontSize: "15px", color: colors.text,
                outline: "none", boxSizing: "border-box",
              }}
            />
          </div>
        </div>

        {tripDays > 0 && (
          <div style={{
            backgroundColor: colors.greenBg, borderRadius: "10px", padding: "14px 18px",
            display: "flex", alignItems: "center", gap: "10px",
          }}>
            <span style={{ fontSize: "20px" }}>🗓</span>
            <span style={{ fontSize: "15px", fontWeight: 600, color: colors.green }}>
              {tripDays} 天关西之旅
            </span>
          </div>
        )}

        <div>
          <p style={{ fontSize: "13px", fontWeight: 600, color: colors.textMuted, marginBottom: "10px" }}>到达时间段</p>
          <div style={{ display: "flex", gap: "8px" }}>
            {[
              { v: "morning", l: "上午落地" },
              { v: "afternoon", l: "下午落地" },
              { v: "evening", l: "傍晚落地" },
            ].map(opt => (
              <button
                key={opt.v}
                onClick={() => update({ arrival_slot: opt.v })}
                style={{
                  flex: 1, padding: "10px 8px", borderRadius: "10px", fontSize: "13px",
                  border: `1.5px solid ${form.arrival_slot === opt.v ? colors.green : colors.border}`,
                  backgroundColor: form.arrival_slot === opt.v ? colors.greenBg : colors.white,
                  color: form.arrival_slot === opt.v ? colors.green : colors.textMuted,
                  fontWeight: form.arrival_slot === opt.v ? 600 : 400,
                  cursor: "pointer", transition: "all 200ms ease",
                }}
              >{opt.l}</button>
            ))}
          </div>
        </div>

        <div>
          <p style={{ fontSize: "13px", fontWeight: 600, color: colors.textMuted, marginBottom: "10px" }}>离开时间段</p>
          <div style={{ display: "flex", gap: "8px" }}>
            {[
              { v: "morning", l: "早上出发" },
              { v: "afternoon", l: "下午出发" },
              { v: "evening", l: "傍晚出发" },
            ].map(opt => (
              <button
                key={opt.v}
                onClick={() => update({ departure_slot: opt.v })}
                style={{
                  flex: 1, padding: "10px 8px", borderRadius: "10px", fontSize: "13px",
                  border: `1.5px solid ${form.departure_slot === opt.v ? colors.green : colors.border}`,
                  backgroundColor: form.departure_slot === opt.v ? colors.greenBg : colors.white,
                  color: form.departure_slot === opt.v ? colors.green : colors.textMuted,
                  fontWeight: form.departure_slot === opt.v ? 600 : 400,
                  cursor: "pointer", transition: "all 200ms ease",
                }}
              >{opt.l}</button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Screen2({ form, update }: { form: FormData; update: (p: Partial<FormData>) => void }) {
  return (
    <div>
      <ScreenTitle>这趟旅行更像哪种感觉？</ScreenTitle>
      <ScreenHint>选一个最接近你们这次的状态，之后可以微调。</ScreenHint>

      <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "28px" }}>
        <RadioCard
          selected={form.trip_vibe === "classic"}
          onClick={() => update({ trip_vibe: "classic" })}
          icon="🏯"
          label="经典版"
          desc="把最值得的都安排好，轻松出发不纠结"
        />
        <RadioCard
          selected={form.trip_vibe === "romantic"}
          onClick={() => update({ trip_vibe: "romantic" })}
          icon="🌙"
          label="约会感"
          desc="浪漫·夜景·有情调的餐厅·安静的两人时光"
        />
        <RadioCard
          selected={form.trip_vibe === "photogenic"}
          onClick={() => update({ trip_vibe: "photogenic" })}
          icon="📷"
          label="出片感"
          desc="好看的地方·咖啡甜品·古着·逛逛拍拍"
        />
        <RadioCard
          selected={form.trip_vibe === "family_fun"}
          onClick={() => update({ trip_vibe: "family_fun" })}
          icon="🎠"
          label="亲子感"
          desc="孩子玩得开心最重要·轻松不赶"
        />
      </div>

      <div style={{ backgroundColor: colors.white, borderRadius: "12px", padding: "20px", border: `1.5px solid ${colors.border}` }}>
        <p style={{ fontSize: "14px", fontWeight: 600, color: colors.text, marginBottom: "16px" }}>几位出行？</p>
        <NumberStepper label="成人" value={form.adults} onChange={v => update({ adults: v })} min={1} />
        <NumberStepper label="儿童（12岁以下）" value={form.children} onChange={v => update({ children: v })} />
        <NumberStepper label="老人（65岁以上）" value={form.elders} onChange={v => update({ elders: v })} />
        <div style={{ marginTop: "12px", padding: "10px 14px", backgroundColor: colors.sand, borderRadius: "8px" }}>
          <span style={{ fontSize: "13px", color: colors.textMuted }}>
            合计 <strong style={{ color: colors.green }}>{form.adults + form.children + form.elders} 位</strong>
            {form.children > 0 && "　含儿童，方案会自动调整节奏"}
            {form.elders > 0 && "　含老人，会适当减少步行量"}
          </span>
        </div>
      </div>
    </div>
  );
}

function Screen3({ form, update }: { form: FormData; update: (p: Partial<FormData>) => void }) {
  return (
    <div>
      <ScreenTitle>想走什么节奏？</ScreenTitle>
      <ScreenHint>节奏决定每天安排几个地方，以及留多少自由时间。</ScreenHint>

      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <RadioCard
          selected={form.density === "packed"}
          onClick={() => update({ density: "packed" })}
          icon="⚡️"
          label="能走多少走多少"
          desc="每天行程密集，景点串联紧凑，适合第一次来想看全的"
        />
        <RadioCard
          selected={form.density === "balanced"}
          onClick={() => update({ density: "balanced" })}
          icon="☀️"
          label="平衡一点"
          desc="每天 2-3 个主要地点，留出午后喝咖啡、随便逛的时间"
        />
        <RadioCard
          selected={form.density === "relaxed"}
          onClick={() => update({ density: "relaxed" })}
          icon="🌿"
          label="悠闲，不想赶"
          desc="一天只做一件主要的事，节奏很慢，以感受为主"
        />
      </div>
    </div>
  );
}

function Screen4({ form, update }: { form: FormData; update: (p: Partial<FormData>) => void }) {
  const addBookedItem = () => {
    update({ pre_booked: [...form.pre_booked, { type: "", name: "", date: "", notes: "" }] });
  };

  const updateItem = (i: number, patch: Partial<BookedItem>) => {
    const items = [...form.pre_booked];
    items[i] = { ...items[i], ...patch };
    update({ pre_booked: items });
  };

  const removeItem = (i: number) => {
    update({ pre_booked: form.pre_booked.filter((_, idx) => idx !== i) });
  };

  return (
    <div>
      <ScreenTitle>还有什么想告诉我们的？</ScreenTitle>
      <ScreenHint>大部分人直接跳过这页。但如果你已经订了酒店或去过某些地方，告诉我们能让方案更准。</ScreenHint>

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* 已预订 */}
        <div style={{
          backgroundColor: colors.white, borderRadius: "12px", border: `1.5px solid ${colors.border}`, overflow: "hidden",
        }}>
          <button
            onClick={() => update({ has_booked: !form.has_booked, pre_booked: form.has_booked ? [] : form.pre_booked })}
            style={{
              width: "100%", padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between",
              background: "none", border: "none", cursor: "pointer", textAlign: "left",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <div style={{
                width: "20px", height: "20px", borderRadius: "4px",
                border: `2px solid ${form.has_booked ? colors.green : colors.border}`,
                backgroundColor: form.has_booked ? colors.green : "transparent",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {form.has_booked && <span style={{ color: "white", fontSize: "13px", fontWeight: "bold" }}>✓</span>}
              </div>
              <span style={{ fontSize: "15px", color: colors.text }}>有些酒店或门票已经订好了</span>
            </div>
            <span style={{ color: colors.textFaint, fontSize: "13px" }}>{form.has_booked ? "收起" : "展开"}</span>
          </button>

          {form.has_booked && (
            <div style={{ padding: "0 20px 20px", borderTop: `1px solid ${colors.borderLight}` }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "16px" }}>
                {form.pre_booked.map((item, i) => (
                  <div key={i} style={{ backgroundColor: colors.sand, borderRadius: "10px", padding: "14px" }}>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                      <div>
                        <label style={{ fontSize: "12px", color: colors.textMuted, display: "block", marginBottom: "4px" }}>类型</label>
                        <select
                          value={item.type}
                          onChange={e => updateItem(i, { type: e.target.value })}
                          style={{
                            width: "100%", padding: "9px 12px", borderRadius: "8px",
                            border: `1.5px solid ${colors.border}`, backgroundColor: colors.white, fontSize: "14px",
                          }}
                        >
                          <option value="">选类型</option>
                          <option value="hotel">酒店</option>
                          <option value="ticket">门票/活动</option>
                          <option value="restaurant">餐厅</option>
                          <option value="transport">交通</option>
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: "12px", color: colors.textMuted, display: "block", marginBottom: "4px" }}>名称</label>
                        <input
                          value={item.name}
                          onChange={e => updateItem(i, { name: e.target.value })}
                          placeholder="例：东京JR新宿店"
                          style={{
                            width: "100%", padding: "9px 12px", borderRadius: "8px",
                            border: `1.5px solid ${colors.border}`, backgroundColor: colors.white, fontSize: "14px",
                            boxSizing: "border-box",
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ fontSize: "12px", color: colors.textMuted, display: "block", marginBottom: "4px" }}>日期</label>
                        <input
                          type="date"
                          value={item.date}
                          onChange={e => updateItem(i, { date: e.target.value })}
                          style={{
                            width: "100%", padding: "9px 12px", borderRadius: "8px",
                            border: `1.5px solid ${colors.border}`, backgroundColor: colors.white, fontSize: "14px",
                            boxSizing: "border-box",
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ fontSize: "12px", color: colors.textMuted, display: "block", marginBottom: "4px" }}>备注（可选）</label>
                        <input
                          value={item.notes}
                          onChange={e => updateItem(i, { notes: e.target.value })}
                          placeholder="例：住2晚"
                          style={{
                            width: "100%", padding: "9px 12px", borderRadius: "8px",
                            border: `1.5px solid ${colors.border}`, backgroundColor: colors.white, fontSize: "14px",
                            boxSizing: "border-box",
                          }}
                        />
                      </div>
                    </div>
                    <button onClick={() => removeItem(i)} style={{ fontSize: "13px", color: "#C94444", background: "none", border: "none", cursor: "pointer" }}>
                      删除
                    </button>
                  </div>
                ))}
                <button onClick={addBookedItem} style={{
                  padding: "11px 16px", borderRadius: "10px", border: `1.5px dashed ${colors.dot}`,
                  backgroundColor: "transparent", color: colors.textMuted, fontSize: "14px", cursor: "pointer",
                }}>
                  + 添加一条
                </button>
              </div>
            </div>
          )}
        </div>

        {/* 不想去 */}
        <div style={{
          backgroundColor: colors.white, borderRadius: "12px", border: `1.5px solid ${colors.border}`, overflow: "hidden",
        }}>
          <button
            onClick={() => update({ has_skip: !form.has_skip })}
            style={{
              width: "100%", padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between",
              background: "none", border: "none", cursor: "pointer", textAlign: "left",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <div style={{
                width: "20px", height: "20px", borderRadius: "4px",
                border: `2px solid ${form.has_skip ? colors.green : colors.border}`,
                backgroundColor: form.has_skip ? colors.green : "transparent",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {form.has_skip && <span style={{ color: "white", fontSize: "13px", fontWeight: "bold" }}>✓</span>}
              </div>
              <span style={{ fontSize: "15px", color: colors.text }}>有些地方去过了，或这次不想去</span>
            </div>
          </button>

          {form.has_skip && (
            <div style={{ padding: "0 20px 20px", borderTop: `1px solid ${colors.borderLight}` }}>
              <input
                value={form.skip_notes}
                onChange={e => update({ skip_notes: e.target.value })}
                placeholder="例：清水寺去过了 / 不想去USJ"
                style={{
                  width: "100%", marginTop: "14px", padding: "12px 14px", borderRadius: "10px",
                  border: `1.5px solid ${colors.border}`, backgroundColor: colors.white, fontSize: "14px",
                  boxSizing: "border-box", outline: "none",
                }}
              />
            </div>
          )}
        </div>

        {/* 其他需求 */}
        <div style={{ backgroundColor: colors.white, borderRadius: "12px", border: `1.5px solid ${colors.border}`, padding: "16px 20px" }}>
          <p style={{ fontSize: "14px", color: colors.text, marginBottom: "10px" }}>还有别的特别要求？</p>
          <textarea
            value={form.special_notes}
            onChange={e => update({ special_notes: e.target.value })}
            placeholder="例：不吃生食 / 有老人同行 / 不想太早起 / 想多留购物时间"
            rows={3}
            style={{
              width: "100%", padding: "12px 14px", borderRadius: "10px",
              border: `1.5px solid ${colors.border}`, backgroundColor: colors.sand, fontSize: "14px",
              resize: "none", outline: "none", boxSizing: "border-box", color: colors.text,
              fontFamily: "inherit",
            }}
          />
        </div>
      </div>
    </div>
  );
}
