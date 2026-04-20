"use client";

import { useEffect, useState, useMemo } from "react";
import { TemplateCard, type ViewMode } from "@/components/admin/TemplateCard";
import type { DayTemplate } from "@/app/api/admin/templates/route";

// ── 常量 ─────────────────────────────────────────────────────────────────

const PHASE_OPTIONS = [
  { value: "all", label: "全部类型" },
  { value: "arrival", label: "到达日" },
  { value: "sightseeing", label: "游玩日" },
  { value: "transfer", label: "换城日" },
  { value: "departure", label: "离开日" },
];

const AUDIENCE_OPTIONS = [
  { value: "all", label: "全部人群" },
  { value: "couple", label: "情侣" },
  { value: "friends", label: "闺蜜/朋友" },
  { value: "family", label: "亲子" },
  { value: "default", label: "通用" },
];

const TAG_OPTIONS = [
  { value: "all", label: "全部标签" },
  { value: "sakura", label: "樱花季" },
  { value: "koyo", label: "红叶季" },
  { value: "onsen", label: "温泉" },
  { value: "temple", label: "寺庙神社" },
  { value: "food", label: "美食" },
  { value: "nature", label: "自然" },
  { value: "castle", label: "城堡" },
  { value: "festival", label: "祭典" },
  { value: "modern", label: "现代体验" },
  { value: "recovery", label: "恢复留白" },
];

const PACE_OPTIONS = [
  { value: "all", label: "全部节奏" },
  { value: "compact", label: "紧凑" },
  { value: "standard", label: "标准" },
  { value: "relaxed", label: "悠闲" },
  { value: "locked", label: "强度固定" },
];

const VIEW_MODES: { value: ViewMode; label: string }[] = [
  { value: "opus", label: "Opus 视角" },
  { value: "full", label: "完整视角" },
];

const CITY_LABELS: Record<string, string> = {
  kyoto: "京都",
  osaka: "大阪",
  kobe: "神户",
  nara: "奈良",
  uji: "宇治",
  kinosaki: "城崎",
  koyasan: "高野山",
};

// ── 筛选 Select 组件 ──────────────────────────────────────────────────────

function FilterSelect({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-8 rounded-md border border-slate-200 bg-white px-2.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-400"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

// ── 主页面 ────────────────────────────────────────────────────────────────

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<DayTemplate[]>([]);
  const [areas, setAreas] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [city, setCity] = useState("all");
  const [phase, setPhase] = useState("all");
  const [pace, setPace] = useState("all");
  const [audience, setAudience] = useState("all");
  const [tag, setTag] = useState("all");
  const [viewMode, setViewMode] = useState<ViewMode>("opus");
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch("/api/admin/templates")
      .then((r) => r.json())
      .then((d) => { setTemplates(d.templates ?? []); setAreas(d.areas ?? {}); setLoading(false); });
  }, []);

  // 城市列表（动态从数据中取）
  const cities = useMemo(() => {
    const seen = new Set<string>();
    templates.forEach((t) => seen.add(t.city));
    return Array.from(seen).sort();
  }, [templates]);

  const cityOptions = useMemo(() => [
    { value: "all", label: "全部城市" },
    ...cities.map((c) => ({ value: c, label: CITY_LABELS[c] ?? c })),
  ], [cities]);

  // 过滤
  const filtered = useMemo(() => {
    return templates.filter((t) => {
      if (city !== "all" && t.city !== city) return false;
      if (phase !== "all" && t.assembly.phase !== phase) return false;
      if (pace !== "all" && t.assembly.best_pace !== pace) return false;
      if (audience !== "all") {
        const fit = t.fit_audience;
        const fits = Array.isArray(fit) ? fit : [fit];
        if (!fits.includes("all") && !fits.includes(audience)) return false;
      }
      if (tag !== "all" && !t.tags.includes(tag)) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          t.label.toLowerCase().includes(q) ||
          t.template_id.toLowerCase().includes(q) ||
          t.description.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [templates, city, phase, pace, audience, tag, search]);

  // 统计
  const stats = useMemo(() => {
    const byCity: Record<string, number> = {};
    templates.forEach((t) => {
      byCity[t.city] = (byCity[t.city] ?? 0) + 1;
    });
    return { total: templates.length, byCity };
  }, [templates]);

  return (
    <div className="p-6 max-w-screen-xl">
      {/* 页头 */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-900">模板库</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          共 {stats.total} 个模板
          {Object.entries(stats.byCity)
            .sort((a, b) => b[1] - a[1])
            .map(([c, n]) => ` · ${CITY_LABELS[c] ?? c} ${n}`)
            .join("")}
        </p>
      </div>

      {/* 工具栏 */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        {/* 视角切换 */}
        <div className="flex rounded-lg border border-slate-200 overflow-hidden">
          {VIEW_MODES.map((m) => (
            <button
              key={m.value}
              onClick={() => setViewMode(m.value)}
              className={`px-3.5 py-1.5 text-sm transition-colors ${
                viewMode === m.value
                  ? "bg-indigo-600 text-white font-medium"
                  : "bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        <div className="w-px h-6 bg-slate-200" />

        {/* 筛选器 */}
        <FilterSelect value={city} onChange={setCity} options={cityOptions} />
        <FilterSelect value={phase} onChange={setPhase} options={PHASE_OPTIONS} />
        <FilterSelect value={pace} onChange={setPace} options={PACE_OPTIONS} />
        <FilterSelect value={audience} onChange={setAudience} options={AUDIENCE_OPTIONS} />
        <FilterSelect value={tag} onChange={setTag} options={TAG_OPTIONS} />

        {/* 搜索 */}
        <input
          type="text"
          placeholder="搜索名称 / ID / 描述"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-8 rounded-md border border-slate-200 px-3 text-sm text-slate-700 w-52 focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />

        {/* 结果数 */}
        <span className="text-sm text-slate-400 ml-auto">
          {filtered.length} / {stats.total}
        </span>
      </div>

      {/* 内容区 */}
      {loading ? (
        <div className="text-center py-24 text-slate-400">加载中…</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-24 text-slate-400">无匹配模板</div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {filtered.map((t) => (
            <TemplateCard key={t.template_id} template={t} viewMode={viewMode} areas={areas} />
          ))}
        </div>
      )}
    </div>
  );
}
