"use client";
import { useForm } from "./FormContext";

const BUDGET_LEVELS = [
  { value: "budget", label: "经济型", desc: "¥300-500/天", icon: "💚" },
  { value: "mid", label: "中端", desc: "¥500-1000/天", icon: "💛" },
  { value: "premium", label: "高端", desc: "¥1000-2000/天", icon: "🧡" },
  { value: "luxury", label: "奢华", desc: "¥2000+/天", icon: "💎" },
];

const ACCOMMODATION_TYPES = [
  { value: "hotel_business", label: "商务酒店", icon: "🏨" },
  { value: "hotel_boutique", label: "精品酒店", icon: "✨" },
  { value: "ryokan", label: "日式旅馆", icon: "⛩️" },
  { value: "airbnb", label: "民宿/公寓", icon: "🏠" },
  { value: "hostel", label: "背包客栈", icon: "🎒" },
  { value: "resort", label: "度假村", icon: "🏝️" },
];

export default function Step3Budget() {
  const { data, update, errors } = useForm();

  const toggleAccom = (v: string) => {
    const next = data.accommodation_pref.includes(v)
      ? data.accommodation_pref.filter((a) => a !== v)
      : [...data.accommodation_pref, v];
    update({ accommodation_pref: next });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">预算 &amp; 住宿</h2>
        <p className="text-sm text-gray-500 mt-0.5">帮助我们推荐适合的酒店和活动</p>
      </div>

      {/* 预算档位 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">预算档位（人均/天）</label>
        <div className="grid grid-cols-2 gap-2">
          {BUDGET_LEVELS.map((b) => (
            <button
              key={b.value}
              onClick={() => update({ budget_level: b.value })}
              className={`flex items-center gap-3 p-3.5 rounded-xl border-2 transition-all text-left
                ${data.budget_level === b.value
                  ? "border-indigo-500 bg-indigo-50"
                  : "border-gray-200 bg-white hover:border-indigo-300"
                }`}
            >
              <span className="text-2xl">{b.icon}</span>
              <div>
                <p className={`text-sm font-semibold ${data.budget_level === b.value ? "text-indigo-700" : "text-gray-900"}`}>
                  {b.label}
                </p>
                <p className="text-xs text-gray-500">{b.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 总预算（可选） */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          总预算（可选）
          <span className="text-gray-400 font-normal ml-1">日元</span>
        </label>
        <input
          type="number"
          value={data.budget_total_jpy ?? ""}
          onChange={(e) => update({ budget_total_jpy: e.target.value ? parseInt(e.target.value) : null })}
          placeholder="例：300000"
          className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
      </div>

      {/* 住宿类型 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">住宿偏好（可多选）</label>
        <div className="grid grid-cols-3 gap-2">
          {ACCOMMODATION_TYPES.map((a) => (
            <button
              key={a.value}
              onClick={() => toggleAccom(a.value)}
              className={`flex flex-col items-center gap-1 p-3 rounded-xl border-2 text-sm transition-all
                ${data.accommodation_pref.includes(a.value)
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700 font-semibold"
                  : "border-gray-200 bg-white text-gray-600 hover:border-indigo-300"
                }`}
            >
              <span className="text-xl">{a.icon}</span>
              <span className="text-xs text-center leading-tight">{a.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 酒店预订状态 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">酒店预订状态</label>
        <div className="space-y-2">
          {[
            { value: "not_booked", label: "尚未预订，全部交给你们" },
            { value: "partial", label: "部分已订，其余需要推荐" },
            { value: "all_booked", label: "全部已订，仅需安排活动" },
          ].map((opt) => (
            <label
              key={opt.value}
              onClick={() => update({ hotel_booking_status: opt.value })}
              className={`flex items-center gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all
                ${data.hotel_booking_status === opt.value
                  ? "border-indigo-500 bg-indigo-50"
                  : "border-gray-200 bg-white hover:border-indigo-300"
                }`}
            >
              <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0
                ${data.hotel_booking_status === opt.value ? "border-indigo-500" : "border-gray-300"}`}
              >
                {data.hotel_booking_status === opt.value && (
                  <div className="w-2 h-2 rounded-full bg-indigo-500" />
                )}
              </div>
              <span className="text-sm text-gray-700">{opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* 已订酒店（条件显示） */}
      {(data.hotel_booking_status === "partial" || data.hotel_booking_status === "all_booked") && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            已订酒店区域 / 备注
          </label>
          <textarea
            value={data.hotel_area_pref}
            onChange={(e) => update({ hotel_area_pref: e.target.value })}
            rows={2}
            placeholder="例：东京新宿区，大阪心斋桥附近..."
            className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
          />
        </div>
      )}
    </div>
  );
}
