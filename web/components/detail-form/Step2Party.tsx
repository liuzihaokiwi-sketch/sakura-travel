"use client";
import { useForm } from "./FormContext";

const PARTY_TYPES = [
  { value: "solo", label: "独自旅行", icon: "🧍" },
  { value: "couple", label: "情侣/夫妻", icon: "👫" },
  { value: "friends", label: "朋友结伴", icon: "👯" },
  { value: "family", label: "家庭出游", icon: "👨‍👩‍👧" },
  { value: "business", label: "商务出行", icon: "💼" },
];

export default function Step2Party() {
  const { data, update, errors } = useForm();

  const toggleAge = (age: number) => {
    const next = data.party_ages.includes(age)
      ? data.party_ages.filter((a) => a !== age)
      : [...data.party_ages, age];
    update({ party_ages: next });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">同行人信息</h2>
        <p className="text-sm text-gray-500 mt-0.5">帮助我们为不同人群定制合适的行程</p>
      </div>

      {/* 出行类型 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">出行类型</label>
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
          {PARTY_TYPES.map((pt) => (
            <button
              key={pt.value}
              onClick={() => update({ party_type: pt.value })}
              className={`flex flex-col items-center gap-1 p-3 rounded-xl border-2 text-sm transition-all
                ${data.party_type === pt.value
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700 font-semibold"
                  : "border-gray-200 bg-white text-gray-600 hover:border-indigo-300"
                }`}
            >
              <span className="text-xl">{pt.icon}</span>
              <span className="text-xs leading-tight text-center">{pt.label}</span>
            </button>
          ))}
        </div>
        {errors.party_type && <p className="text-xs text-red-500 mt-1">{errors.party_type}</p>}
      </div>

      {/* 人数 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">出行人数</label>
        <div className="flex items-center gap-4">
          <button
            onClick={() => update({ party_size: Math.max(1, data.party_size - 1) })}
            className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-xl font-bold text-gray-600 hover:bg-gray-200"
          >-</button>
          <span className="text-2xl font-bold w-10 text-center">{data.party_size}</span>
          <button
            onClick={() => update({ party_size: Math.min(20, data.party_size + 1) })}
            className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-xl font-bold text-gray-600 hover:bg-gray-200"
          >+</button>
          <span className="text-sm text-gray-500">人</span>
        </div>
      </div>

      {/* 特殊人群 */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">特殊同行人（可多选）</label>
        {[
          { key: "has_elderly", label: "有老人（60岁以上）", icon: "👴" },
          { key: "has_children", label: "有小孩", icon: "👶" },
        ].map(({ key, label, icon }) => (
          <label key={key} className="flex items-center gap-3 cursor-pointer">
            <div
              onClick={() => update({ [key]: !data[key as keyof typeof data] } as any)}
              className={`w-11 h-6 rounded-full transition-colors relative shrink-0
                ${data[key as keyof typeof data] ? "bg-indigo-600" : "bg-gray-200"}`}
            >
              <div className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform
                ${data[key as keyof typeof data] ? "translate-x-5" : ""}`} />
            </div>
            <span className="text-sm text-gray-700">{icon} {label}</span>
          </label>
        ))}
      </div>

      {/* 孩子年龄（条件显示） */}
      {data.has_children && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">孩子年龄段（可多选）</label>
          <div className="flex flex-wrap gap-2">
            {["0-2岁", "3-6岁", "7-12岁", "13-17岁"].map((label, idx) => {
              const age = [1, 5, 10, 15][idx];
              return (
                <button
                  key={label}
                  onClick={() => toggleAge(age)}
                  className={`px-3 py-1.5 rounded-full text-sm border transition-all
                    ${data.children_ages.includes(age)
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-600 border-gray-300 hover:border-indigo-400"
                    }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* 特殊需求 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">特殊需求（可选）</label>
        <textarea
          value={data.special_needs}
          onChange={(e) => update({ special_needs: e.target.value })}
          rows={2}
          placeholder="例：有轮椅用户、对花粉过敏、需要清真饮食..."
          className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
        />
      </div>
    </div>
  );
}
