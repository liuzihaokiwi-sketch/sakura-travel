"use client";
import { useForm } from "./FormContext";
import { useState } from "react";
import { PlusIcon, TrashIcon } from "@heroicons/react/24/outline";

const PACE_OPTIONS = [
  { value: "relaxed", label: "悠闲", desc: "每天2-3个景点，留大量自由时间", icon: "🌴" },
  { value: "balanced", label: "适中", desc: "每天3-5个景点，有适当休息", icon: "⚖️" },
  { value: "packed", label: "充实", desc: "每天5-7个景点，行程紧凑", icon: "🚀" },
];

const STYLE_OPTIONS = [
  { value: "must_see", label: "打卡必游", icon: "📍" },
  { value: "mixed", label: "主流+小众", icon: "🎯" },
  { value: "hidden_gem", label: "小众深度", icon: "💎" },
  { value: "local_style", label: "当地人视角", icon: "🏘️" },
];

const STAMINA_OPTIONS = [
  { value: "low", label: "轻松", desc: "少走路，多乘交通" },
  { value: "medium", label: "一般", desc: "正常步行量" },
  { value: "high", label: "强健", desc: "可接受长时间步行徒步" },
];

export default function Step5Pace() {
  const { data, update } = useForm();
  const [showEventForm, setShowEventForm] = useState(false);
  const [newEvent, setNewEvent] = useState({ date: "", time: "", name: "", location: "" });

  const addEvent = () => {
    if (!newEvent.name) return;
    update({ fixed_events: [...data.fixed_events, { ...newEvent }] });
    setNewEvent({ date: "", time: "", name: "", location: "" });
    setShowEventForm(false);
  };

  const removeEvent = (idx: number) => {
    update({ fixed_events: data.fixed_events.filter((_, i) => i !== idx) });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">行程节奏</h2>
        <p className="text-sm text-gray-500 mt-0.5">告诉我们你的旅行风格</p>
      </div>

      {/* 节奏偏好 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">节奏偏好</label>
        <div className="space-y-2">
          {PACE_OPTIONS.map((p) => (
            <button
              key={p.value}
              onClick={() => update({ pace_preference: p.value })}
              className={`w-full flex items-center gap-3 p-3.5 rounded-xl border-2 transition-all text-left
                ${data.pace_preference === p.value
                  ? "border-indigo-500 bg-indigo-50"
                  : "border-gray-200 bg-white hover:border-indigo-300"
                }`}
            >
              <span className="text-2xl">{p.icon}</span>
              <div>
                <p className={`font-semibold text-sm ${data.pace_preference === p.value ? "text-indigo-700" : "text-gray-900"}`}>
                  {p.label}
                </p>
                <p className="text-xs text-gray-500">{p.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 旅行风格 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">旅行风格</label>
        <div className="grid grid-cols-2 gap-2">
          {STYLE_OPTIONS.map((s) => (
            <button
              key={s.value}
              onClick={() => update({ trip_style: s.value })}
              className={`flex items-center gap-2 p-3 rounded-xl border-2 text-sm transition-all
                ${data.trip_style === s.value
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700 font-semibold"
                  : "border-gray-200 bg-white text-gray-600 hover:border-indigo-300"
                }`}
            >
              <span>{s.icon}</span>
              <span>{s.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 体力水平 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">体力水平</label>
        <div className="flex gap-2">
          {STAMINA_OPTIONS.map((s) => (
            <button
              key={s.value}
              onClick={() => update({ stamina_level: s.value })}
              className={`flex-1 p-3 rounded-xl border-2 text-center transition-all
                ${data.stamina_level === s.value
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                  : "border-gray-200 bg-white text-gray-600 hover:border-indigo-300"
                }`}
            >
              <p className="font-semibold text-sm">{s.label}</p>
              <p className="text-xs text-gray-500 mt-0.5 leading-tight">{s.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* 惯常起床时间 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">惯常起床时间</label>
        <input
          type="time"
          value={data.wake_up_time}
          onChange={(e) => update({ wake_up_time: e.target.value })}
          className="rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
      </div>

      {/* 固定事件 */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700">固定事件（已预订活动/演出）</label>
          <button
            onClick={() => setShowEventForm(!showEventForm)}
            className="flex items-center gap-1 text-xs text-indigo-600 font-medium hover:text-indigo-800"
          >
            <PlusIcon className="w-3.5 h-3.5" />
            添加
          </button>
        </div>

        {showEventForm && (
          <div className="bg-gray-50 rounded-xl p-3 space-y-2 border border-gray-200 mb-2">
            <div className="grid grid-cols-2 gap-2">
              <input
                type="date"
                value={newEvent.date}
                onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
                className="rounded-lg border border-gray-300 px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <input
                type="time"
                value={newEvent.time}
                onChange={(e) => setNewEvent({ ...newEvent, time: e.target.value })}
                className="rounded-lg border border-gray-300 px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            <input
              type="text"
              value={newEvent.name}
              onChange={(e) => setNewEvent({ ...newEvent, name: e.target.value })}
              placeholder="活动名称（必填）"
              className="w-full rounded-lg border border-gray-300 px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
            <input
              type="text"
              value={newEvent.location}
              onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
              placeholder="地点"
              className="w-full rounded-lg border border-gray-300 px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowEventForm(false)}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900"
              >取消</button>
              <button
                onClick={addEvent}
                className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >确认添加</button>
            </div>
          </div>
        )}

        {data.fixed_events.length > 0 && (
          <div className="space-y-1.5">
            {data.fixed_events.map((ev, idx) => (
              <div key={idx} className="flex items-center gap-2 p-2.5 bg-amber-50 rounded-lg border border-amber-200">
                <span className="text-amber-600">📅</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{ev.name}</p>
                  <p className="text-xs text-gray-500">{ev.date} {ev.time} {ev.location && `· ${ev.location}`}</p>
                </div>
                <button onClick={() => removeEvent(idx)} className="text-gray-400 hover:text-red-500">
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 自由心愿 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">其他心愿 / 特殊要求</label>
        <textarea
          value={data.free_text_wishes}
          onChange={(e) => update({ free_text_wishes: e.target.value })}
          rows={3}
          placeholder="例：希望第一天能轻松适应时差，最后一天早点收拾行李..."
          className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
        />
      </div>
    </div>
  );
}
