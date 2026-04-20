"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";

// ─── 类型 ────────────────────────────────────────────────────────────────────

interface DayPreview {
  day: number;
  city: string;
  title: string;
  description: string;
}

interface ExperienceCard {
  id: string;
  icon: string;
  label: string;
  description: string;
}

interface PlanPreview {
  plan_version: number;
  status: string;
  condition_summary: string;
  decisions: string[];
  daily_plans: DayPreview[];
  addable_experiences: ExperienceCard[];
  note: string;
}

const colors = {
  bg: "#FBF7F0",
  white: "#FFFFFF",
  green: "#2D4A3E",
  greenLight: "#4A8B6E",
  greenBg: "#F0F5F2",
  sand: "#F5F0E8",
  sandDark: "#EDE5D8",
  border: "#E0D8CE",
  borderLight: "#F0EAE2",
  text: "#3D3029",
  textMuted: "#8B7E74",
  textFaint: "#A69B91",
  red: "#C65D3E",
  amber: "#F5A623",
};

// ─── 主组件 ──────────────────────────────────────────────────────────────────

export default function PlanPage() {
  const params = useParams();
  const router = useRouter();
  const code = params.code as string;

  const [tripId, setTripId] = useState<string | null>(null);
  const [plan, setPlan] = useState<PlanPreview | null>(null);
  const [pollingStatus, setPollingStatus] = useState<"loading" | "ready" | "error">("loading");
  const [addedExperiences, setAddedExperiences] = useState<Set<string>>(new Set());
  const [showAdjust, setShowAdjust] = useState(false);
  const [adjustText, setAdjustText] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [showMoreExperiences, setShowMoreExperiences] = useState(false);
  const [adjustChips, setAdjustChips] = useState<Set<string>>(new Set());

  useEffect(() => {
    const id = localStorage.getItem(`trip_v2_${code}`);
    if (!id) {
      router.replace(`/form/${code}`);
      return;
    }
    setTripId(id);
  }, [code, router]);

  const fetchStatus = useCallback(async (id: string): Promise<boolean> => {
    const res = await fetch(`/api/v2/trips/${id}/status`);
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === "plan_preview" || data.status === "plan_confirmed";
  }, []);

  const fetchPlan = useCallback(async (id: string) => {
    const res = await fetch(`/api/v2/trips/${id}/plan-preview`);
    if (!res.ok) return null;
    return res.json();
  }, []);

  // 轮询
  useEffect(() => {
    if (!tripId) return;
    let stopped = false;

    const poll = async () => {
      for (let i = 0; i < 60; i++) {
        if (stopped) return;
        const ready = await fetchStatus(tripId);
        if (ready) {
          const data = await fetchPlan(tripId);
          if (data && !stopped) {
            setPlan(data);
            setPollingStatus("ready");
          } else if (!stopped) {
            setPollingStatus("error");
          }
          return;
        }
        await new Promise(r => setTimeout(r, 3000));
      }
      if (!stopped) setPollingStatus("error");
    };

    poll();
    return () => { stopped = true; };
  }, [tripId, fetchStatus, fetchPlan]);

  const toggleExperience = (id: string) => {
    setAddedExperiences(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleChip = (chip: string) => {
    setAdjustChips(prev => {
      const next = new Set(prev);
      if (next.has(chip)) next.delete(chip); else next.add(chip);
      return next;
    });
  };

  const handleConfirm = async () => {
    if (!tripId) return;
    setConfirming(true);
    try {
      // 如有加入体验，先提交 actions
      if (addedExperiences.size > 0 || adjustChips.size > 0 || adjustText) {
        const actions = [];
        Array.from(addedExperiences).forEach(id => {
          actions.push({ op: "add_experience", params: { id } });
        });
        Array.from(adjustChips).forEach(chip => {
          actions.push({ op: "avoid_tag", params: { tag: chip } });
        });
        if (adjustText) {
          actions.push({ op: "free_text", params: { text: adjustText } });
        }
        if (actions.length > 0) {
          await fetch(`/api/v2/trips/${tripId}/plan-actions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ actions }),
          });
          // 轮询等方案重新生成完成
          for (let i = 0; i < 60; i++) {
            await new Promise(r => setTimeout(r, 3000));
            const statusRes = await fetch(`/api/v2/trips/${tripId}/status`);
            if (statusRes.ok) {
              const statusData = await statusRes.json();
              if (statusData.status === "plan_preview") break;
              if (statusData.status === "failed") {
                setConfirming(false);
                alert("方案调整失败，请重试");
                return;
              }
            }
          }
        }
      }

      const res = await fetch(`/api/v2/trips/${tripId}/plan-confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmed: true }),
      });

      if (res.ok) {
        router.push(`/form/${code}/budget`);
      } else {
        setConfirming(false);
        alert("确认失败，请重试");
      }
    } catch {
      setConfirming(false);
      alert("网络错误，请重试");
    }
  };

  // ── Loading ──
  if (pollingStatus === "loading") {
    return (
      <div style={{ backgroundColor: colors.bg, minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "40px", marginBottom: "20px", animation: "pulse 2s infinite" }}>🗓</div>
          <p style={{ fontFamily: '"Noto Serif SC", serif', fontSize: "18px", color: colors.green, marginBottom: "8px" }}>
            正在帮你排第一版方案…
          </p>
          <p style={{ fontSize: "14px", color: colors.textMuted }}>大概需要 30-60 秒</p>
          <div style={{ marginTop: "24px", display: "flex", justifyContent: "center", gap: "6px" }}>
            {[0, 1, 2].map(i => (
              <div key={i} style={{
                width: "8px", height: "8px", borderRadius: "50%", backgroundColor: colors.greenLight,
                animation: `bounce 1.2s ${i * 0.2}s infinite`,
              }} />
            ))}
          </div>
        </div>
        <style>{`
          @keyframes bounce { 0%,80%,100%{transform:scale(0)} 40%{transform:scale(1)} }
        `}</style>
      </div>
    );
  }

  if (pollingStatus === "error" || !plan) {
    return (
      <div style={{ backgroundColor: colors.bg, minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}>
        <div style={{ textAlign: "center", maxWidth: "400px" }}>
          <div style={{ fontSize: "36px", marginBottom: "16px" }}>😓</div>
          <p style={{ fontSize: "16px", color: colors.text, marginBottom: "8px" }}>方案生成时间有点长</p>
          <p style={{ fontSize: "14px", color: colors.textMuted, marginBottom: "24px" }}>可能是服务比较忙，稍后刷新试试？</p>
          <button onClick={() => window.location.reload()} style={{
            padding: "12px 28px", borderRadius: "10px", border: "none",
            backgroundColor: colors.red, color: "white", fontSize: "14px", cursor: "pointer",
          }}>刷新重试</button>
        </div>
      </div>
    );
  }

  const visibleExperiences = showMoreExperiences
    ? plan.addable_experiences
    : plan.addable_experiences.slice(0, 3);

  const adjustChipOptions = [
    "想轻松一点", "想更紧凑一点", "不想太早起",
    "想多留一点京都", "想多留一点大阪",
  ];

  return (
    <div style={{ backgroundColor: colors.bg, minHeight: "100vh" }}>
      {/* 顶部 */}
      <div style={{
        backgroundColor: colors.green, padding: "20px 24px 24px",
        backgroundImage: "linear-gradient(135deg, #2D4A3E 0%, #3D6B58 100%)",
      }}>
        <div style={{ maxWidth: "640px", margin: "0 auto" }}>
          <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.6)", marginBottom: "6px" }}>
            {plan.condition_summary}
          </p>
          <h1 style={{
            fontFamily: '"Noto Serif SC", serif', fontSize: "22px", fontWeight: 700,
            color: "white", marginBottom: "16px", lineHeight: 1.3,
          }}>
            这是我们先帮你排好的第一版主线
          </h1>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {plan.decisions.map((d, i) => (
              <div key={i} style={{
                backgroundColor: "rgba(255,255,255,0.12)", borderRadius: "20px",
                padding: "6px 14px", fontSize: "13px", color: "rgba(255,255,255,0.85)",
                display: "flex", alignItems: "center", gap: "6px",
              }}>
                <span style={{ color: colors.amber }}>💡</span> {d}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 内容 */}
      <div style={{ maxWidth: "640px", margin: "0 auto", padding: "0 24px 120px" }}>

        {/* 每日主安排 */}
        <div style={{ paddingTop: "24px", marginBottom: "8px" }}>
          <p style={{ fontSize: "12px", fontWeight: 600, color: colors.textMuted, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            行程概览
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "8px" }}>
          {plan.daily_plans.map((day) => (
            <div key={day.day} style={{
              backgroundColor: colors.white, borderRadius: "12px",
              padding: "16px 20px", border: `1px solid ${colors.borderLight}`,
              display: "flex", gap: "16px",
            }}>
              <div style={{ flexShrink: 0, textAlign: "center" }}>
                <div style={{
                  width: "36px", height: "36px", borderRadius: "50%",
                  backgroundColor: colors.sand, display: "flex", alignItems: "center",
                  justifyContent: "center",
                }}>
                  <span style={{ fontSize: "13px", fontWeight: 700, color: colors.green }}>D{day.day}</span>
                </div>
              </div>
              <div>
                <p style={{ fontSize: "14px", fontWeight: 600, color: colors.text, marginBottom: "4px" }}>
                  {day.city} · {day.title}
                </p>
                <p style={{ fontSize: "13px", color: colors.textMuted, lineHeight: 1.6 }}>{day.description}</p>
              </div>
            </div>
          ))}
        </div>

        {plan.note && (
          <div style={{
            backgroundColor: colors.sand, borderRadius: "10px", padding: "12px 16px",
            marginBottom: "24px", fontSize: "13px", color: colors.textMuted, lineHeight: 1.6,
          }}>
            📌 {plan.note}
          </div>
        )}

        {/* 可加体验 */}
        {plan.addable_experiences.length > 0 && (
          <div style={{ marginBottom: "24px" }}>
            <p style={{ fontSize: "12px", fontWeight: 600, color: colors.textMuted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "12px" }}>
              你可能还想加的体验
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {visibleExperiences.map(exp => {
                const added = addedExperiences.has(exp.id);
                return (
                  <button
                    key={exp.id}
                    onClick={() => toggleExperience(exp.id)}
                    style={{
                      display: "flex", alignItems: "center", gap: "14px",
                      padding: "14px 18px", borderRadius: "12px", width: "100%", textAlign: "left",
                      border: `1.5px solid ${added ? colors.green : colors.border}`,
                      backgroundColor: added ? colors.greenBg : colors.white,
                      cursor: "pointer", transition: "all 200ms ease",
                    }}
                  >
                    <span style={{ fontSize: "22px", flexShrink: 0 }}>{exp.icon}</span>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontSize: "14px", fontWeight: 600, color: colors.text, marginBottom: "2px" }}>{exp.label}</p>
                      <p style={{ fontSize: "12px", color: colors.textMuted }}>{exp.description}</p>
                    </div>
                    <div style={{
                      width: "28px", height: "28px", borderRadius: "50%", flexShrink: 0,
                      backgroundColor: added ? colors.green : colors.sand,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      transition: "all 200ms ease",
                    }}>
                      <span style={{ fontSize: "14px", color: added ? "white" : colors.textMuted }}>
                        {added ? "✓" : "+"}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
            {plan.addable_experiences.length > 3 && (
              <button
                onClick={() => setShowMoreExperiences(!showMoreExperiences)}
                style={{
                  width: "100%", marginTop: "10px", padding: "12px",
                  backgroundColor: "transparent", border: `1px dashed ${colors.border}`,
                  borderRadius: "10px", fontSize: "13px", color: colors.textMuted, cursor: "pointer",
                }}
              >
                {showMoreExperiences ? "收起" : `查看更多 (${plan.addable_experiences.length - 3} 个)`}
              </button>
            )}
          </div>
        )}

        {/* 纠偏抽屉 */}
        <div style={{
          backgroundColor: colors.white, borderRadius: "12px",
          border: `1.5px solid ${colors.border}`, marginBottom: "24px", overflow: "hidden",
        }}>
          <button
            onClick={() => setShowAdjust(!showAdjust)}
            style={{
              width: "100%", padding: "16px 20px", display: "flex", alignItems: "center",
              justifyContent: "space-between", background: "none", border: "none", cursor: "pointer",
            }}
          >
            <span style={{ fontSize: "15px", color: colors.text }}>我想调整一点</span>
            <span style={{ fontSize: "20px", color: colors.textMuted, transition: "transform 200ms ease", transform: showAdjust ? "rotate(180deg)" : "none" }}>⌄</span>
          </button>

          {showAdjust && (
            <div style={{ padding: "0 20px 20px", borderTop: `1px solid ${colors.borderLight}` }}>
              <div style={{ marginTop: "16px", marginBottom: "14px" }}>
                <p style={{ fontSize: "13px", color: colors.textMuted, marginBottom: "10px" }}>想调整的：</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                  {adjustChipOptions.map(chip => {
                    const on = adjustChips.has(chip);
                    return (
                      <button
                        key={chip}
                        onClick={() => toggleChip(chip)}
                        style={{
                          padding: "7px 14px", borderRadius: "20px", fontSize: "13px",
                          border: `1.5px solid ${on ? colors.green : colors.border}`,
                          backgroundColor: on ? colors.greenBg : colors.white,
                          color: on ? colors.green : colors.textMuted,
                          fontWeight: on ? 600 : 400,
                          cursor: "pointer", transition: "all 200ms ease",
                        }}
                      >{chip}</button>
                    );
                  })}
                </div>
              </div>
              <p style={{ fontSize: "13px", color: colors.textMuted, marginBottom: "8px" }}>其他想法：</p>
              <textarea
                value={adjustText}
                onChange={e => setAdjustText(e.target.value)}
                placeholder="比如不吃生食 / 想少换酒店 / 其他特殊需求"
                rows={3}
                style={{
                  width: "100%", padding: "12px 14px", borderRadius: "10px",
                  border: `1.5px solid ${colors.border}`, backgroundColor: colors.sand,
                  fontSize: "13px", resize: "none", outline: "none",
                  boxSizing: "border-box", fontFamily: "inherit", color: colors.text,
                }}
              />
            </div>
          )}
        </div>
      </div>

      {/* 底部确认按钮 */}
      <div style={{
        position: "fixed", bottom: 0, left: 0, right: 0,
        backgroundColor: colors.white, borderTop: `1px solid ${colors.border}`,
        padding: "16px 24px",
      }}>
        <div style={{ maxWidth: "640px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "10px" }}>
          {(addedExperiences.size > 0 || adjustChips.size > 0 || adjustText) && (
            <p style={{ fontSize: "12px", color: colors.textMuted, textAlign: "center" }}>
              {addedExperiences.size > 0 && `已加入 ${addedExperiences.size} 个体验　`}
              {(adjustChips.size > 0 || adjustText) && "包含你的调整意见"}
            </p>
          )}
          <button
            onClick={handleConfirm}
            disabled={confirming}
            style={{
              width: "100%", padding: "16px", borderRadius: "12px", border: "none",
              backgroundColor: confirming ? colors.border : colors.green,
              color: confirming ? colors.textFaint : "white",
              fontSize: "16px", fontWeight: 600, cursor: confirming ? "not-allowed" : "pointer",
              transition: "all 200ms ease",
            }}
          >
            {confirming ? "确认中…" : "就按这个来 →"}
          </button>
          <p style={{ fontSize: "12px", color: colors.textFaint, textAlign: "center" }}>
            确认后进入预算选择，不会改变这个行程安排
          </p>
        </div>
      </div>
    </div>
  );
}
