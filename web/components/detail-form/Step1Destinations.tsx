"use client";
import { useForm } from "./FormContext";
import DestinationAutocomplete from "@/components/ui/DestinationAutocomplete";
import { PlusIcon, TrashIcon } from "@heroicons/react/24/outline";

export default function Step1Destinations() {
  const { data, update, errors } = useForm();

  const addCity = (city: { place_id: string; name: string; name_zh: string }) => {
    if (data.cities.find((c) => c.place_id === city.place_id)) return;
    update({ cities: [...data.cities, { ...city, nights: 2 }] });
  };

  const removeCity = (idx: number) => {
    const next = data.cities.filter((_, i) => i !== idx);
    update({ cities: next, duration_days: next.reduce((s, c) => s + c.nights, 0) });
  };

  const setNights = (idx: number, nights: number) => {
    const next = data.cities.map((c, i) => (i === idx ? { ...c, nights } : c));
    update({ cities: next, duration_days: next.reduce((s, c) => s + c.nights, 0) });
  };

  const recalcDays = () => data.cities.reduce((s, c) => s + c.nights, 0);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">目的地 &amp; 日期</h2>
        <p className="text-sm text-gray-500 mt-0.5">选择您想去的城市，安排每地天数</p>
      </div>

      {/* 城市搜索 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">添加目的地城市</label>
        <DestinationAutocomplete
          onSelect={(city) => addCity({ place_id: city.place_id, name: city.name_en, name_zh: city.name_zh })}
          placeholder="搜索日本城市（中英文均可）"
        />
        {errors.cities && <p className="text-xs text-red-500 mt-1">{errors.cities}</p>}
      </div>

      {/* 已选城市列表 */}
      {data.cities.length > 0 && (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">已选城市（拖动可调顺序）</label>
          {data.cities.map((city, idx) => (
            <div
              key={city.place_id}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-gray-200"
            >
              <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold shrink-0">
                {idx + 1}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 text-sm truncate">{city.name_zh || city.name}</p>
              </div>
              {/* 晚数调节 */}
              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  onClick={() => setNights(idx, Math.max(1, city.nights - 1))}
                  className="w-6 h-6 rounded-full bg-white border border-gray-300 flex items-center justify-center text-gray-600 hover:bg-gray-100"
                >-</button>
                <span className="w-8 text-center text-sm font-semibold">{city.nights}晚</span>
                <button
                  onClick={() => setNights(idx, Math.min(14, city.nights + 1))}
                  className="w-6 h-6 rounded-full bg-white border border-gray-300 flex items-center justify-center text-gray-600 hover:bg-gray-100"
                >+</button>
              </div>
              <button
                onClick={() => removeCity(idx)}
                className="text-gray-400 hover:text-red-500 transition-colors shrink-0"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
          <p className="text-xs text-gray-500 text-right">合计 {recalcDays()} 天</p>
        </div>
      )}

      {/* 出发日期 */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">出发日期</label>
          <input
            type="date"
            value={data.travel_start_date}
            onChange={(e) => update({ travel_start_date: e.target.value })}
            className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          {errors.travel_start_date && <p className="text-xs text-red-500 mt-1">{errors.travel_start_date}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">返回日期</label>
          <input
            type="date"
            value={data.travel_end_date}
            onChange={(e) => update({ travel_end_date: e.target.value })}
            min={data.travel_start_date}
            className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>
      </div>

      {/* 日期灵活性 */}
      <label className="flex items-center gap-3 cursor-pointer">
        <div
          onClick={() => update({ date_flexible: !data.date_flexible })}
          className={`w-11 h-6 rounded-full transition-colors relative ${data.date_flexible ? "bg-indigo-600" : "bg-gray-200"}`}
        >
          <div
            className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${data.date_flexible ? "translate-x-5" : ""}`}
          />
        </div>
        <span className="text-sm text-gray-700">日期可灵活调整（±2天）</span>
      </label>
    </div>
  );
}
