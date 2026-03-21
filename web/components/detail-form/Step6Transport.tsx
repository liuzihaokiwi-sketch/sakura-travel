"use client";
import { useForm } from "./FormContext";

const ARRIVAL_PLACES = [
  "成田国际机场 (NRT)",
  "羽田机场 (HND)",
  "关西国际机场 (KIX)",
  "大阪伊丹机场 (ITM)",
  "新千岁机场 (CTS)",
  "福冈机场 (FUK)",
  "那霸机场 (OKA)",
  "其他",
];

const JR_PASS_TYPES = [
  { value: "7day", label: "7天 JR PASS" },
  { value: "14day", label: "14天 JR PASS" },
  { value: "21day", label: "21天 JR PASS" },
  { value: "regional", label: "区域 PASS（山阳、东北等）" },
];

export default function Step6Transport() {
  const { data, update } = useForm();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">航班 &amp; 交通</h2>
        <p className="text-sm text-gray-500 mt-0.5">帮助我们合理安排第一天和最后一天</p>
      </div>

      {/* 锁定交通 toggle */}
      <label className="flex items-center gap-3 cursor-pointer">
        <div
          onClick={() => update({ transport_locked: !data.transport_locked })}
          className={`w-11 h-6 rounded-full transition-colors relative ${data.transport_locked ? "bg-indigo-600" : "bg-gray-200"}`}
        >
          <div
            className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${data.transport_locked ? "translate-x-5" : ""}`}
          />
        </div>
        <div>
          <span className="text-sm font-medium text-gray-800">我已确定机票，时间固定</span>
          <p className="text-xs text-gray-500">开启后，行程将严格按照到离时间安排</p>
        </div>
      </label>

      {/* 到达信息 */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 border-b border-gray-100 pb-2">✈️ 抵达信息</h3>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">抵达日期</label>
            <input
              type="date"
              value={data.arrival_date}
              onChange={(e) => update({ arrival_date: e.target.value })}
              className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">抵达时间</label>
            <input
              type="time"
              value={data.arrival_time}
              onChange={(e) => update({ arrival_time: e.target.value })}
              className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">抵达机场/车站</label>
          <select
            value={data.arrival_place}
            onChange={(e) => update({ arrival_place: e.target.value })}
            className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
          >
            <option value="">请选择</option>
            {ARRIVAL_PLACES.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
      </div>

      {/* 离境信息 */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 border-b border-gray-100 pb-2">🛫 离境信息</h3>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">离境日期</label>
            <input
              type="date"
              value={data.departure_date}
              onChange={(e) => update({ departure_date: e.target.value })}
              min={data.arrival_date}
              className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">离境时间</label>
            <input
              type="time"
              value={data.departure_time}
              onChange={(e) => update({ departure_time: e.target.value })}
              className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">离境机场/车站</label>
          <select
            value={data.departure_place}
            onChange={(e) => update({ departure_place: e.target.value })}
            className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
          >
            <option value="">请选择</option>
            {ARRIVAL_PLACES.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
      </div>

      {/* JR PASS */}
      <div className="space-y-2">
        <label className="flex items-center gap-3 cursor-pointer">
          <div
            onClick={() => update({ has_jr_pass: !data.has_jr_pass })}
            className={`w-11 h-6 rounded-full transition-colors relative ${data.has_jr_pass ? "bg-indigo-600" : "bg-gray-200"}`}
          >
            <div
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${data.has_jr_pass ? "translate-x-5" : ""}`}
            />
          </div>
          <span className="text-sm font-medium text-gray-800">🚅 已购买 JR PASS</span>
        </label>
        {data.has_jr_pass && (
          <div className="pl-14">
            <div className="flex flex-wrap gap-2">
              {JR_PASS_TYPES.map((t) => (
                <button
                  key={t.value}
                  onClick={() => update({ jr_pass_type: t.value })}
                  className={`px-3 py-1.5 text-sm rounded-full border transition-all
                    ${data.jr_pass_type === t.value
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-600 border-gray-300 hover:border-indigo-400"
                    }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 随身 WiFi */}
      <label className="flex items-center gap-3 cursor-pointer">
        <div
          onClick={() => update({ has_pocket_wifi: !data.has_pocket_wifi })}
          className={`w-11 h-6 rounded-full transition-colors relative ${data.has_pocket_wifi ? "bg-indigo-600" : "bg-gray-200"}`}
        >
          <div
            className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${data.has_pocket_wifi ? "translate-x-5" : ""}`}
          />
        </div>
        <span className="text-sm font-medium text-gray-800">📶 已预定随身 WiFi / SIM 卡</span>
      </label>

      {/* 交通备注 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">交通备注（可选）</label>
        <textarea
          value={data.transport_notes}
          onChange={(e) => update({ transport_notes: e.target.value })}
          rows={2}
          placeholder="例：行李寄存安排、特殊需求..."
          className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
        />
      </div>
    </div>
  );
}
