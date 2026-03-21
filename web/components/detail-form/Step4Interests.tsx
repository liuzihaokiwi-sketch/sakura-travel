"use client";
import { useForm } from "./FormContext";

const MUST_HAVE_OPTIONS = [
  { value: "nature", label: "自然风光", icon: "🌿" },
  { value: "culture", label: "文化历史", icon: "⛩️" },
  { value: "food", label: "美食探索", icon: "🍜" },
  { value: "shopping", label: "购物血拼", icon: "🛍️" },
  { value: "onsen", label: "温泉体验", icon: "♨️" },
  { value: "anime", label: "动漫圣地", icon: "🎮" },
  { value: "photography", label: "拍照出片", icon: "📸" },
  { value: "nightlife", label: "夜生活", icon: "🌃" },
  { value: "theme_park", label: "主题乐园", icon: "🎡" },
  { value: "art", label: "艺术展览", icon: "🎨" },
  { value: "sport", label: "运动户外", icon: "⛷️" },
  { value: "local_life", label: "体验当地生活", icon: "🏘️" },
];

const FOOD_PREFS = [
  { value: "ramen", label: "拉面", icon: "🍜" },
  { value: "sushi", label: "寿司/刺身", icon: "🍣" },
  { value: "yakiniku", label: "烤肉", icon: "🥩" },
  { value: "kaiseki", label: "怀石料理", icon: "🍱" },
  { value: "izakaya", label: "居酒屋", icon: "🍻" },
  { value: "street_food", label: "街头小吃", icon: "🥟" },
  { value: "cafe", label: "特色咖啡", icon: "☕" },
  { value: "convenience", label: "便利店美食", icon: "🏪" },
];

const FOOD_RESTRICTIONS = [
  { value: "halal", label: "清真" },
  { value: "vegetarian", label: "素食" },
  { value: "vegan", label: "纯素" },
  { value: "gluten_free", label: "无麸质" },
  { value: "no_shellfish", label: "不吃贝类" },
  { value: "no_raw", label: "不吃生食" },
];

function TagGroup({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string;
  options: { value: string; label: string; icon?: string }[];
  selected: string[];
  onToggle: (v: string) => void;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onToggle(opt.value)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm border transition-all
              ${selected.includes(opt.value)
                ? "bg-indigo-600 text-white border-indigo-600"
                : "bg-white text-gray-600 border-gray-300 hover:border-indigo-400"
              }`}
          >
            {opt.icon && <span>{opt.icon}</span>}
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function Step4Interests() {
  const { data, update } = useForm();

  const toggle = (field: keyof typeof data, v: string) => {
    const arr = data[field] as string[];
    const next = arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];
    update({ [field]: next } as any);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">兴趣偏好</h2>
        <p className="text-sm text-gray-500 mt-0.5">选得越准确，行程就越贴合你</p>
      </div>

      <TagGroup
        label="必玩项目（可多选）"
        options={MUST_HAVE_OPTIONS}
        selected={data.must_have_tags}
        onToggle={(v) => toggle("must_have_tags", v)}
      />

      <TagGroup
        label="美食偏好（可多选）"
        options={FOOD_PREFS}
        selected={data.food_preferences}
        onToggle={(v) => toggle("food_preferences", v)}
      />

      <TagGroup
        label="饮食禁忌（可多选）"
        options={FOOD_RESTRICTIONS}
        selected={data.food_restrictions}
        onToggle={(v) => toggle("food_restrictions", v)}
      />

      {data.food_restrictions.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">饮食禁忌补充说明</label>
          <textarea
            value={data.food_restrictions_note}
            onChange={(e) => update({ food_restrictions_note: e.target.value })}
            rows={2}
            placeholder="例：花生严重过敏，请特别注意..."
            className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
          />
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          必去地点 <span className="text-gray-400 font-normal">（每行一个）</span>
        </label>
        <textarea
          value={data.must_go_places.join("\n")}
          onChange={(e) =>
            update({ must_go_places: e.target.value.split("\n").filter(Boolean) })
          }
          rows={3}
          placeholder="例：築地市场&#10;迪士尼乐园&#10;岚山竹林"
          className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          不想去的地方 <span className="text-gray-400 font-normal">（可选）</span>
        </label>
        <textarea
          value={data.dont_want_places.join("\n")}
          onChange={(e) =>
            update({ dont_want_places: e.target.value.split("\n").filter(Boolean) })
          }
          rows={2}
          placeholder="例：太拥挤的景区..."
          className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
        />
      </div>
    </div>
  );
}
