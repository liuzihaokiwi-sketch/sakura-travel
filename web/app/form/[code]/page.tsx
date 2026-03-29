"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";

// ─── 类型 ────────────────────────────────────────────────────────────────────

interface FormData {
  cityGroup: string;
  // 屏2
  departureDate: string;
  departureTime: string;
  departureAirport: string;
  returnDate: string;
  returnTime: string;
  returnAirport: string;
  // 屏3
  totalPeople: number;
  adults: number;
  children: number;
  elders: number;
  travelRelation: string;
  // 屏4
  budgetType: "per_person" | "total";
  budgetRange: string;
  accommodationType: string;
  hotelSwitch: string;
  // 屏5（选填）
  preferences: string[];
  dailyPace: string;
  earlyRise: string;
  nightActivity: string;
  acceptableConditions: string[];
  // 屏6（选填）
  visitedPlaces: string[];
  avoidPlaces: string[];
  avoidExperiences: string[];
  // 屏7（选填）
  bookedItems: BookedItem[];
  // 屏8
  mustVisit: string;
  dietaryRestrictions: string;
  specialNeeds: string;
  occasion: string;
  wechat: string;
  phone: string;
  confirmedNoCar: boolean;
}

interface BookedItem {
  type: string;
  name: string;
  date: string;
  time: string;
}

const INITIAL_FORM: FormData = {
  cityGroup: "",
  departureDate: "",
  departureTime: "",
  departureAirport: "",
  returnDate: "",
  returnTime: "",
  returnAirport: "",
  totalPeople: 2,
  adults: 2,
  children: 0,
  elders: 0,
  travelRelation: "",
  budgetType: "per_person",
  budgetRange: "",
  accommodationType: "",
  hotelSwitch: "ok",
  preferences: [],
  dailyPace: "balanced",
  earlyRise: "normal",
  nightActivity: "normal",
  acceptableConditions: [],
  visitedPlaces: [],
  avoidPlaces: [],
  avoidExperiences: [],
  bookedItems: [],
  mustVisit: "",
  dietaryRestrictions: "",
  specialNeeds: "",
  occasion: "",
  wechat: "",
  phone: "",
  confirmedNoCar: false,
};

const TOTAL_SCREENS = 9;

// ─── 主组件 ──────────────────────────────────────────────────────────────────

export default function FormPage() {
  const params = useParams();
  const router = useRouter();
  const code = params.code as string;

  const [screen, setScreen] = useState(1);
  const [form, setForm] = useState<FormData>(INITIAL_FORM);
  const [tagInput, setTagInput] = useState({ visited: "", avoid: "" });
  const [submitted, setSubmitted] = useState(false);

  // 从 localStorage 恢复草稿
  useEffect(() => {
    const saved = localStorage.getItem(`form_${code}`);
    if (saved) {
      try {
        setForm(JSON.parse(saved));
      } catch {}
    }
  }, [code]);

  // 自动保存草稿
  const saveDraft = useCallback(
    (data: FormData) => {
      localStorage.setItem(`form_${code}`, JSON.stringify(data));
    },
    [code]
  );

  const update = (patch: Partial<FormData>) => {
    const next = { ...form, ...patch };
    setForm(next);
    saveDraft(next);
  };

  const toggleArray = (key: keyof FormData, value: string) => {
    const arr = form[key] as string[];
    const next = arr.includes(value) ? arr.filter((x) => x !== value) : [...arr, value];
    update({ [key]: next } as Partial<FormData>);
  };

  const goNext = () => {
    if (screen < TOTAL_SCREENS) setScreen(screen + 1);
  };
  const goPrev = () => {
    if (screen > 1) setScreen(screen - 1);
  };

  const handleSubmit = async () => {
    setSubmitted(true);
    try {
      await fetch(`/api/forms/${code}/submit`, { method: "POST" });
    } catch {
      // ignore errors, proceed to guide page
    }
    router.push(`/guide/${code}`);
  };

  if (submitted) {
    return (
      <div
        style={{
          backgroundColor: "#FBF7F0",
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "24px",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>📖</div>
          <h2
            style={{
              fontFamily: '"Noto Serif SC", serif',
              fontSize: "22px",
              fontWeight: 700,
              color: "#2D4A3E",
              marginBottom: "8px",
            }}
          >
            提交成功
          </h2>
          <p style={{ fontSize: "15px", color: "#8B7E74" }}>正在跳转到你的手账…</p>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        backgroundColor: "#FBF7F0",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* 顶部进度 */}
      <div
        style={{
          position: "sticky",
          top: "64px",
          backgroundColor: "#FBF7F0",
          zIndex: 10,
          padding: "16px 24px 12px",
          borderBottom: "1px solid #E8E0D6",
        }}
      >
        <div
          style={{
            maxWidth: "640px",
            margin: "0 auto",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <button
            onClick={goPrev}
            style={{
              fontSize: "13px",
              color: screen === 1 ? "transparent" : "#8B7E74",
              background: "none",
              border: "none",
              cursor: screen === 1 ? "default" : "pointer",
              padding: "4px 0",
            }}
            disabled={screen === 1}
          >
            ← 返回
          </button>

          {/* 圆点进度指示器 */}
          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            {Array.from({ length: TOTAL_SCREENS }).map((_, i) => (
              <div
                key={i}
                style={{
                  width: i + 1 === screen ? "20px" : "7px",
                  height: "7px",
                  borderRadius: "4px",
                  backgroundColor:
                    i + 1 < screen ? "#4A8B6E" : i + 1 === screen ? "#2D4A3E" : "#D6CFC6",
                  transition: "all 300ms ease",
                }}
              />
            ))}
          </div>

          <span style={{ fontSize: "13px", color: "#A69B91" }}>
            {screen}/{TOTAL_SCREENS}
          </span>
        </div>
      </div>

      {/* 内容区 */}
      <div
        style={{
          flex: 1,
          maxWidth: "640px",
          margin: "0 auto",
          width: "100%",
          padding: "32px 24px",
        }}
      >
        {screen === 1 && <Screen1 form={form} update={update} />}
        {screen === 2 && <Screen2 form={form} update={update} />}
        {screen === 3 && <Screen3 form={form} update={update} />}
        {screen === 4 && <Screen4 form={form} update={update} />}
        {screen === 5 && (
          <Screen5
            form={form}
            update={update}
            toggleArray={toggleArray}
          />
        )}
        {screen === 6 && (
          <Screen6
            form={form}
            update={update}
            toggleArray={toggleArray}
            tagInput={tagInput}
            setTagInput={setTagInput}
          />
        )}
        {screen === 7 && <Screen7 form={form} update={update} />}
        {screen === 8 && <Screen8 form={form} update={update} />}
        {screen === 9 && <Screen9 form={form} />}
      </div>

      {/* 底部按钮 */}
      <div
        style={{
          position: "sticky",
          bottom: 0,
          backgroundColor: "#FFFFFF",
          borderTop: "1px solid #E8E0D6",
          padding: "16px 24px",
        }}
      >
        <div
          style={{
            maxWidth: "640px",
            margin: "0 auto",
            display: "flex",
            justifyContent: screen === 9 ? "space-between" : "flex-end",
            gap: "12px",
          }}
        >
          {screen === 9 && (
            <button
              onClick={goPrev}
              style={{
                padding: "14px 24px",
                borderRadius: "12px",
                border: "1.5px solid #E0D8CE",
                backgroundColor: "#FFFFFF",
                color: "#3D3029",
                fontSize: "15px",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              返回修改
            </button>
          )}
          {screen < 9 && [5, 6, 7].includes(screen) && (
            <button
              onClick={goNext}
              style={{
                padding: "14px 24px",
                borderRadius: "12px",
                border: "none",
                backgroundColor: "transparent",
                color: "#8B7E74",
                fontSize: "15px",
                cursor: "pointer",
              }}
            >
              跳过这一页
            </button>
          )}
          {screen < 9 ? (
            <button
              onClick={goNext}
              style={{
                padding: "14px 32px",
                borderRadius: "12px",
                border: "none",
                backgroundColor: "#C65D3E",
                color: "#FFFFFF",
                fontSize: "15px",
                fontWeight: 600,
                cursor: "pointer",
                transition: "background-color 200ms ease",
              }}
            >
              继续 →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!form.confirmedNoCar}
              style={{
                padding: "14px 32px",
                borderRadius: "12px",
                border: "none",
                backgroundColor: form.confirmedNoCar ? "#C65D3E" : "#E0D8CE",
                color: form.confirmedNoCar ? "#FFFFFF" : "#A69B91",
                fontSize: "15px",
                fontWeight: 600,
                cursor: form.confirmedNoCar ? "pointer" : "not-allowed",
                transition: "all 200ms ease",
              }}
            >
              提交，开始这趟旅行 →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── 各屏组件 ────────────────────────────────────────────────────────────────

function ScreenTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2
      style={{
        fontFamily: '"Noto Serif SC", serif',
        fontSize: "22px",
        fontWeight: 700,
        color: "#2D4A3E",
        marginBottom: "24px",
        lineHeight: 1.4,
      }}
    >
      {children}
    </h2>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label
      style={{
        fontSize: "13px",
        fontWeight: 600,
        color: "#8B7E74",
        display: "block",
        marginBottom: "6px",
      }}
    >
      {children}
    </label>
  );
}

function TextInput({
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: "100%",
        padding: "12px 14px",
        borderRadius: "10px",
        border: "1.5px solid #E0D8CE",
        backgroundColor: "#FFFFFF",
        fontSize: "15px",
        color: "#3D3029",
        outline: "none",
        boxSizing: "border-box",
        transition: "border-color 200ms ease",
      }}
      onFocus={(e) => (e.target.style.borderColor = "#2D4A3E")}
      onBlur={(e) => (e.target.style.borderColor = "#E0D8CE")}
    />
  );
}

function RadioGroup({
  options,
  value,
  onChange,
}: {
  options: { value: string; label: string }[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      {options.map((opt) => (
        <label
          key={opt.value}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            cursor: "pointer",
            padding: "10px 14px",
            borderRadius: "10px",
            border: `1.5px solid ${value === opt.value ? "#2D4A3E" : "#E0D8CE"}`,
            backgroundColor: value === opt.value ? "#F5F0E8" : "#FFFFFF",
            transition: "all 200ms ease",
          }}
        >
          <div
            style={{
              width: "16px",
              height: "16px",
              borderRadius: "50%",
              border: `2px solid ${value === opt.value ? "#2D4A3E" : "#D6CFC6"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            {value === opt.value && (
              <div
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  backgroundColor: "#2D4A3E",
                }}
              />
            )}
          </div>
          <span style={{ fontSize: "14px", color: "#3D3029" }}>{opt.label}</span>
          <input
            type="radio"
            checked={value === opt.value}
            onChange={() => onChange(opt.value)}
            style={{ display: "none" }}
          />
        </label>
      ))}
    </div>
  );
}

function CheckboxGroup({
  options,
  values,
  onChange,
}: {
  options: { value: string; label: string }[];
  values: string[];
  onChange: (value: string) => void;
}) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
      {options.map((opt) => {
        const checked = values.includes(opt.value);
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            style={{
              padding: "8px 14px",
              borderRadius: "20px",
              border: `1.5px solid ${checked ? "#2D4A3E" : "#E0D8CE"}`,
              backgroundColor: checked ? "#2D4A3E" : "#FFFFFF",
              color: checked ? "#FFFFFF" : "#3D3029",
              fontSize: "13px",
              fontWeight: checked ? 600 : 400,
              cursor: "pointer",
              transition: "all 200ms ease",
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

function NumberInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
      <span style={{ fontSize: "14px", color: "#3D3029" }}>{label}</span>
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <button
          onClick={() => onChange(Math.max(0, value - 1))}
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "50%",
            border: "1.5px solid #E0D8CE",
            backgroundColor: "#FFFFFF",
            fontSize: "18px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#3D3029",
          }}
        >
          −
        </button>
        <span style={{ fontSize: "16px", fontWeight: 600, color: "#2D4A3E", minWidth: "24px", textAlign: "center" }}>
          {value}
        </span>
        <button
          onClick={() => onChange(value + 1)}
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "50%",
            border: "1.5px solid #E0D8CE",
            backgroundColor: "#FFFFFF",
            fontSize: "18px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#3D3029",
          }}
        >
          +
        </button>
      </div>
    </div>
  );
}

// ─── 各屏 ─────────────────────────────────────────────────────────────────────

function Screen1({ form, update }: { form: FormData; update: (p: Partial<FormData>) => void }) {
  return (
    <div>
      <ScreenTitle>先告诉我们，这趟旅行想去哪里</ScreenTitle>
      {form.cityGroup ? (
        <div
          style={{
            backgroundColor: "#FFFFFF",
            borderRadius: "12px",
            padding: "16px 20px",
            border: "1.5px solid #4A8B6E",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <span style={{ fontSize: "16px", fontWeight: 700, color: "#2D4A3E" }}>
              已选：{form.cityGroup} ✓
            </span>
            <p style={{ fontSize: "13px", color: "#8B7E74", marginTop: "4px" }}>
              下一步我们会问你时间和同行人数。
            </p>
          </div>
          <button
            onClick={() => update({ cityGroup: "" })}
            style={{
              fontSize: "13px",
              color: "#8B7E74",
              background: "none",
              border: "none",
              cursor: "pointer",
              textDecoration: "underline",
            }}
          >
            想换？
          </button>
        </div>
      ) : (
        <div>
          <p style={{ fontSize: "14px", color: "#8B7E74", marginBottom: "16px" }}>
            城市圈决定了手账的内容结构。你在 /order 选过的话这里会自动填好。
          </p>
          <TextInput
            value={form.cityGroup}
            onChange={(v) => update({ cityGroup: v })}
            placeholder="例如：关西、广府、北海道…"
          />
        </div>
      )}
    </div>
  );
}

function Screen2({ form, update }: { form: FormData; update: (p: Partial<FormData>) => void }) {
  return (
    <div>
      <ScreenTitle>你会在什么时候正式落地开始这趟旅行？</ScreenTitle>
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div>
            <FieldLabel>落地日期</FieldLabel>
            <TextInput
              type="date"
              value={form.departureDate}
              onChange={(v) => update({ departureDate: v })}
            />
          </div>
          <div>
            <FieldLabel>落地时间</FieldLabel>
            <TextInput
              type="time"
              value={form.departureTime}
              onChange={(v) => update({ departureTime: v })}
            />
          </div>
        </div>
        <div>
          <FieldLabel>落地机场/城市</FieldLabel>
          <TextInput
            value={form.departureAirport}
            onChange={(v) => update({ departureAirport: v })}
            placeholder="例如：关西国际机场"
          />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div>
            <FieldLabel>返程日期</FieldLabel>
            <TextInput
              type="date"
              value={form.returnDate}
              onChange={(v) => update({ returnDate: v })}
            />
          </div>
          <div>
            <FieldLabel>返程时间</FieldLabel>
            <TextInput
              type="time"
              value={form.returnTime}
              onChange={(v) => update({ returnTime: v })}
            />
          </div>
        </div>
        <div>
          <FieldLabel>返程机场/城市</FieldLabel>
          <TextInput
            value={form.returnAirport}
            onChange={(v) => update({ returnAirport: v })}
            placeholder="例如：关西国际机场"
          />
        </div>
        <div
          style={{
            backgroundColor: "#F5F0E8",
            borderRadius: "8px",
            padding: "10px 14px",
            fontSize: "13px",
            color: "#8B7E74",
          }}
        >
          ℹ️ 机票由你自己预订，我们负责你落地之后的路线安排。
        </div>
      </div>
    </div>
  );
}

function Screen3({ form, update }: { form: FormData; update: (p: Partial<FormData>) => void }) {
  return (
    <div>
      <ScreenTitle>这趟旅行，是谁和你一起去？</ScreenTitle>
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div>
          <NumberInput
            label="出行人数（总计）"
            value={form.totalPeople}
            onChange={(v) => update({ totalPeople: v })}
          />
          <NumberInput label="成人" value={form.adults} onChange={(v) => update({ adults: v })} />
          <NumberInput label="儿童" value={form.children} onChange={(v) => update({ children: v })} />
          <NumberInput label="老人" value={form.elders} onChange={(v) => update({ elders: v })} />
        </div>
        <div>
          <FieldLabel>出行关系</FieldLabel>
          <RadioGroup
            value={form.travelRelation}
            onChange={(v) => update({ travelRelation: v })}
            options={[
              { value: "couple", label: "情侣/夫妻" },
              { value: "solo", label: "一个人出发" },
              { value: "friends", label: "朋友一起" },
              { value: "family", label: "家庭/亲子" },
              { value: "other", label: "其他" },
            ]}
          />
        </div>
      </div>
    </div>
  );
}

function Screen4({ form, update }: { form: FormData; update: (p: Partial<FormData>) => void }) {
  return (
    <div>
      <ScreenTitle>这趟旅行，你更想怎么住、怎么花？</ScreenTitle>
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <div>
          <FieldLabel>预算方式</FieldLabel>
          <div style={{ display: "flex", gap: "10px" }}>
            {[
              { value: "per_person", label: "人均预算" },
              { value: "total", label: "总预算" },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => update({ budgetType: opt.value as "per_person" | "total" })}
                style={{
                  padding: "10px 20px",
                  borderRadius: "10px",
                  border: `1.5px solid ${form.budgetType === opt.value ? "#2D4A3E" : "#E0D8CE"}`,
                  backgroundColor: form.budgetType === opt.value ? "#F5F0E8" : "#FFFFFF",
                  color: form.budgetType === opt.value ? "#2D4A3E" : "#8B7E74",
                  fontSize: "14px",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 200ms ease",
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <FieldLabel>预算区间</FieldLabel>
          <select
            value={form.budgetRange}
            onChange={(e) => update({ budgetRange: e.target.value })}
            style={{
              width: "100%",
              padding: "12px 14px",
              borderRadius: "10px",
              border: "1.5px solid #E0D8CE",
              backgroundColor: "#FFFFFF",
              fontSize: "15px",
              color: form.budgetRange ? "#3D3029" : "#A69B91",
              outline: "none",
              cursor: "pointer",
            }}
          >
            <option value="">选择预算区间</option>
            <option value="1000-2000">¥1000-2000</option>
            <option value="2000-3000">¥2000-3000</option>
            <option value="3000-5000">¥3000-5000</option>
            <option value="5000-8000">¥5000-8000</option>
            <option value="8000+">¥8000 以上</option>
          </select>
          <p style={{ fontSize: "12px", color: "#A69B91", marginTop: "6px" }}>
            ℹ️ 预算不用精确，大概区间就够。
          </p>
        </div>
        <div>
          <FieldLabel>住宿偏好</FieldLabel>
          <RadioGroup
            value={form.accommodationType}
            onChange={(v) => update({ accommodationType: v })}
            options={[
              { value: "budget", label: "经济（¥200以下/晚）" },
              { value: "comfort", label: "舒适（¥200-500/晚）" },
              { value: "upscale", label: "轻奢（¥500-1000/晚）" },
              { value: "luxury", label: "高端（¥1000+/晚）" },
            ]}
          />
        </div>
        <div>
          <FieldLabel>换酒店</FieldLabel>
          <RadioGroup
            value={form.hotelSwitch}
            onChange={(v) => update({ hotelSwitch: v })}
            options={[
              { value: "ok", label: "可以接受" },
              { value: "minimal", label: "尽量少换" },
              { value: "none", label: "最好不换" },
            ]}
          />
        </div>
      </div>
    </div>
  );
}

function Screen5({
  form,
  update,
  toggleArray,
}: {
  form: FormData;
  update: (p: Partial<FormData>) => void;
  toggleArray: (key: keyof FormData, value: string) => void;
}) {
  return (
    <div>
      <ScreenTitle>让这趟旅行更像你</ScreenTitle>
      <p style={{ fontSize: "14px", color: "#8B7E74", marginBottom: "24px" }}>
        这部分不是必填。什么都不选我们也会安排一个稳妥版本。
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <div>
          <FieldLabel>更想要的体验（多选）</FieldLabel>
          <CheckboxGroup
            options={[
              { value: "city_walk", label: "城市漫游" },
              { value: "landmark", label: "经典打卡" },
              { value: "food", label: "美食" },
              { value: "shopping", label: "购物" },
              { value: "onsen", label: "温泉放松" },
              { value: "theme_park", label: "乐园" },
              { value: "design", label: "设计感" },
              { value: "nature", label: "自然风景" },
              { value: "photography", label: "摄影" },
            ]}
            values={form.preferences}
            onChange={(v) => toggleArray("preferences", v)}
          />
        </div>
        <div>
          <FieldLabel>每日节奏</FieldLabel>
          <RadioGroup
            value={form.dailyPace}
            onChange={(v) => update({ dailyPace: v })}
            options={[
              { value: "balanced", label: "均衡" },
              { value: "relaxed", label: "轻松" },
              { value: "packed", label: "尽量多体验" },
            ]}
          />
        </div>
        <div>
          <FieldLabel>可以早起吗</FieldLabel>
          <RadioGroup
            value={form.earlyRise}
            onChange={(v) => update({ earlyRise: v })}
            options={[
              { value: "normal", label: "一般" },
              { value: "yes", label: "可以" },
              { value: "no", label: "不想" },
            ]}
          />
        </div>
        <div>
          <FieldLabel>夜间活动</FieldLabel>
          <RadioGroup
            value={form.nightActivity}
            onChange={(v) => update({ nightActivity: v })}
            options={[
              { value: "normal", label: "一般" },
              { value: "yes", label: "喜欢" },
              { value: "no", label: "不需要" },
            ]}
          />
        </div>
        <div>
          <FieldLabel>以下你可以接受吗？（不勾选我们会帮你避开）</FieldLabel>
          <CheckboxGroup
            options={[
              { value: "shabby_good_food", label: "环境简陋但味道好的小馆子" },
              { value: "rude_but_stable", label: "服务态度不太好但出品稳定的店" },
              { value: "long_queue", label: "排队超过30分钟的热门店" },
              { value: "cash_only", label: "只收现金的店" },
            ]}
            values={form.acceptableConditions}
            onChange={(v) => toggleArray("acceptableConditions", v)}
          />
        </div>
      </div>
    </div>
  );
}

function Screen6({
  form,
  update,
  toggleArray,
  tagInput,
  setTagInput,
}: {
  form: FormData;
  update: (p: Partial<FormData>) => void;
  toggleArray: (key: keyof FormData, value: string) => void;
  tagInput: { visited: string; avoid: string };
  setTagInput: React.Dispatch<React.SetStateAction<{ visited: string; avoid: string }>>;
}) {
  const addTag = (type: "visited" | "avoid", key: keyof FormData) => {
    const val = tagInput[type].trim();
    if (!val) return;
    const arr = form[key] as string[];
    if (!arr.includes(val)) {
      update({ [key]: [...arr, val] } as Partial<FormData>);
    }
    setTagInput((prev) => ({ ...prev, [type]: "" }));
  };

  const removeTag = (key: keyof FormData, val: string) => {
    const arr = form[key] as string[];
    update({ [key]: arr.filter((x) => x !== val) } as Partial<FormData>);
  };

  return (
    <div>
      <ScreenTitle>有些地方你已经去过，或者这次不想去吗？</ScreenTitle>
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <div>
          <FieldLabel>已经去过的地方</FieldLabel>
          <TagInput
            value={tagInput.visited}
            onChange={(v) => setTagInput((prev) => ({ ...prev, visited: v }))}
            onAdd={() => addTag("visited", "visitedPlaces")}
            tags={form.visitedPlaces}
            onRemove={(v) => removeTag("visitedPlaces", v)}
            placeholder="例如：清水寺"
          />
        </div>
        <div>
          <FieldLabel>不想去的地方</FieldLabel>
          <TagInput
            value={tagInput.avoid}
            onChange={(v) => setTagInput((prev) => ({ ...prev, avoid: v }))}
            onAdd={() => addTag("avoid", "avoidPlaces")}
            tags={form.avoidPlaces}
            onRemove={(v) => removeTag("avoidPlaces", v)}
            placeholder="例如：环球影城"
          />
        </div>
        <div>
          <FieldLabel>不想要的体验（多选）</FieldLabel>
          <CheckboxGroup
            options={[
              { value: "pure_shopping", label: "纯购物" },
              { value: "long_queue", label: "大量排队" },
              { value: "rush_checkin", label: "太赶的打卡" },
              { value: "nightlife", label: "夜生活" },
              { value: "intense_walk", label: "高强度暴走" },
              { value: "too_popular", label: "太多网红点" },
            ]}
            values={form.avoidExperiences}
            onChange={(v) => toggleArray("avoidExperiences", v)}
          />
        </div>
      </div>
    </div>
  );
}

function TagInput({
  value,
  onChange,
  onAdd,
  tags,
  onRemove,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  onAdd: () => void;
  tags: string[];
  onRemove: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "8px" }}>
        {tags.map((tag) => (
          <span
            key={tag}
            style={{
              padding: "4px 12px",
              borderRadius: "20px",
              backgroundColor: "#F5F0E8",
              fontSize: "13px",
              color: "#3D3029",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            {tag}
            <button
              onClick={() => onRemove(tag)}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "#A69B91",
                fontSize: "12px",
                padding: 0,
                lineHeight: 1,
              }}
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <div style={{ display: "flex", gap: "8px" }}>
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onAdd()}
          placeholder={placeholder}
          style={{
            flex: 1,
            padding: "10px 14px",
            borderRadius: "10px",
            border: "1.5px solid #E0D8CE",
            backgroundColor: "#FFFFFF",
            fontSize: "14px",
            outline: "none",
          }}
        />
        <button
          onClick={onAdd}
          style={{
            padding: "10px 16px",
            borderRadius: "10px",
            border: "none",
            backgroundColor: "#F5F0E8",
            color: "#3D3029",
            fontSize: "14px",
            cursor: "pointer",
          }}
        >
          + 添加
        </button>
      </div>
    </div>
  );
}

function Screen7({ form, update }: { form: FormData; update: (p: Partial<FormData>) => void }) {
  const addBookedItem = () => {
    update({
      bookedItems: [
        ...form.bookedItems,
        { type: "", name: "", date: "", time: "" },
      ],
    });
  };

  const updateItem = (index: number, patch: Partial<BookedItem>) => {
    const items = [...form.bookedItems];
    items[index] = { ...items[index], ...patch };
    update({ bookedItems: items });
  };

  const removeItem = (index: number) => {
    update({ bookedItems: form.bookedItems.filter((_, i) => i !== index) });
  };

  return (
    <div>
      <ScreenTitle>已经定下来的部分，我们来接住</ScreenTitle>
      <p style={{ fontSize: "14px", color: "#8B7E74", marginBottom: "20px" }}>
        没有已预订内容？直接跳过这页。
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "16px" }}>
        {form.bookedItems.map((item, i) => (
          <div
            key={i}
            style={{
              backgroundColor: "#FFFFFF",
              borderRadius: "10px",
              padding: "16px",
              border: "1.5px solid #E0D8CE",
            }}
          >
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
              <div>
                <FieldLabel>类型</FieldLabel>
                <select
                  value={item.type}
                  onChange={(e) => updateItem(i, { type: e.target.value })}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "8px",
                    border: "1.5px solid #E0D8CE",
                    backgroundColor: "#FFFFFF",
                    fontSize: "14px",
                  }}
                >
                  <option value="">选类型</option>
                  <option value="hotel">酒店</option>
                  <option value="restaurant">餐厅</option>
                  <option value="ticket">门票/活动</option>
                  <option value="transport">交通</option>
                </select>
              </div>
              <div>
                <FieldLabel>名称</FieldLabel>
                <TextInput
                  value={item.name}
                  onChange={(v) => updateItem(i, { name: v })}
                  placeholder="名称"
                />
              </div>
              <div>
                <FieldLabel>日期</FieldLabel>
                <TextInput
                  type="date"
                  value={item.date}
                  onChange={(v) => updateItem(i, { date: v })}
                />
              </div>
              <div>
                <FieldLabel>时间</FieldLabel>
                <TextInput
                  type="time"
                  value={item.time}
                  onChange={(v) => updateItem(i, { time: v })}
                />
              </div>
            </div>
            <button
              onClick={() => removeItem(i)}
              style={{
                fontSize: "13px",
                color: "#C94444",
                background: "none",
                border: "none",
                cursor: "pointer",
              }}
            >
              删除
            </button>
          </div>
        ))}
      </div>
      {["酒店", "餐厅", "门票/活动", "交通"].map((type) => (
        <button
          key={type}
          onClick={addBookedItem}
          style={{
            display: "block",
            width: "100%",
            marginBottom: "8px",
            padding: "12px 16px",
            borderRadius: "10px",
            border: "1.5px dashed #D6CFC6",
            backgroundColor: "transparent",
            color: "#8B7E74",
            fontSize: "14px",
            cursor: "pointer",
            textAlign: "left",
            transition: "all 200ms ease",
          }}
        >
          + 添加已订{type}
        </button>
      ))}
    </div>
  );
}

function Screen8({ form, update }: { form: FormData; update: (p: Partial<FormData>) => void }) {
  return (
    <div>
      <ScreenTitle>还有什么一定要被照顾到的？</ScreenTitle>
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {[
          { key: "mustVisit", label: "必去地点", placeholder: "例如：一定要去伏见稻荷" },
          { key: "dietaryRestrictions", label: "不吃/过敏", placeholder: "例如：不吃辣、海鲜过敏" },
          { key: "specialNeeds", label: "行动不便/特殊照顾", placeholder: "例如：轮椅、推婴儿车" },
          { key: "occasion", label: "纪念日/生日/惊喜", placeholder: "例如：9月21日结婚纪念日" },
        ].map((field) => (
          <div key={field.key}>
            <FieldLabel>{field.label}</FieldLabel>
            <TextInput
              value={form[field.key as keyof FormData] as string}
              onChange={(v) => update({ [field.key]: v } as Partial<FormData>)}
              placeholder={field.placeholder}
            />
          </div>
        ))}
        <div>
          <FieldLabel>联系方式</FieldLabel>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <TextInput
              value={form.wechat}
              onChange={(v) => update({ wechat: v })}
              placeholder="微信号"
            />
            <TextInput
              value={form.phone}
              onChange={(v) => update({ phone: v })}
              placeholder="手机号"
              type="tel"
            />
          </div>
        </div>
        <label
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "10px",
            padding: "14px",
            borderRadius: "10px",
            backgroundColor: "#F5F0E8",
            cursor: "pointer",
          }}
        >
          <input
            type="checkbox"
            checked={form.confirmedNoCar}
            onChange={(e) => update({ confirmedNoCar: e.target.checked })}
            style={{ marginTop: "2px", accentColor: "#2D4A3E" }}
          />
          <span style={{ fontSize: "13px", color: "#3D3029", lineHeight: 1.5 }}>
            我已知悉：机票需自行预订，当前服务仅提供落地旅行规划
          </span>
        </label>
      </div>
    </div>
  );
}

function Screen9({ form }: { form: FormData }) {
  const rows = [
    { label: "城市圈", value: form.cityGroup || "—" },
    {
      label: "时间",
      value:
        form.departureDate && form.returnDate
          ? `${form.departureDate} → ${form.returnDate}`
          : "—",
    },
    { label: "同行", value: form.travelRelation ? `${form.travelRelation}，${form.totalPeople}人` : "—" },
    {
      label: "预算",
      value: form.budgetRange ? `${form.budgetType === "per_person" ? "人均" : "总"} ${form.budgetRange}，${form.accommodationType}住宿` : "—",
    },
    { label: "偏好", value: form.preferences.join("、") || "—" },
    { label: "联系方式", value: form.wechat || form.phone || "—" },
  ];

  return (
    <div>
      <ScreenTitle>最后确认一下，我们就开始帮你排</ScreenTitle>
      <div
        style={{
          backgroundColor: "#FFFFFF",
          borderRadius: "12px",
          overflow: "hidden",
          border: "1.5px solid #E0D8CE",
        }}
      >
        {rows.map((row, i) => (
          <div
            key={row.label}
            style={{
              display: "flex",
              padding: "14px 20px",
              borderBottom: i < rows.length - 1 ? "1px solid #F0EAE2" : "none",
            }}
          >
            <span style={{ fontSize: "13px", color: "#8B7E74", width: "80px", flexShrink: 0 }}>
              {row.label}
            </span>
            <span style={{ fontSize: "14px", color: "#3D3029" }}>{row.value}</span>
          </div>
        ))}
      </div>
      <p style={{ fontSize: "13px", color: "#A69B91", marginTop: "16px", textAlign: "center" }}>
        提交后30分钟内如需修改可以撤回
      </p>
    </div>
  );
}
