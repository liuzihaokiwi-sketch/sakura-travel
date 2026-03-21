"use client";

import { useEffect, useState } from "react";

// ── 类型 ──────────────────────────────────────────────────────────────────────

interface ContentSection {
  id: string;
  type: "overview" | "day" | "conditional" | "static_block";
  title: string;
  source: "fragment" | "ai" | "static" | "template";
  fragment_slug?: string;
  day_number?: number;
  word_count?: number;
  children?: ContentSection[];
}

interface RunVersion {
  run_id: string;
  created_at: string;
  quality_score?: number;
  generation_mode?: string;
  status: string;
}

interface Props {
  runId: string;
}

// ── 工具 ──────────────────────────────────────────────────────────────────────

const API = process.env.NEXT_PUBLIC_API_URL ?? "";

const SOURCE_CONFIG: Record<string, { label: string; color: string; dot: string }> = {
  fragment: { label: "片段库", color: "bg-indigo-50 text-indigo-700 border-indigo-200",  dot: "bg-indigo-500"  },
  ai:       { label: "AI 生成", color: "bg-purple-50 text-purple-700 border-purple-200", dot: "bg-purple-500"  },
  static:   { label: "静态块",  color: "bg-gray-50   text-gray-600   border-gray-200",   dot: "bg-gray-400"   },
  template: { label: "模板",    color: "bg-amber-50  text-amber-700  border-amber-200",  dot: "bg-amber-400"  },
};

const SECTION_ICONS: Record<string, string> = {
  overview:     "📋",
  day:          "📅",
  conditional:  "⚡",
  static_block: "📦",
};

// ── 章节树节点 ────────────────────────────────────────────────────────────────

function SectionNode({ section, depth = 0 }: { section: ContentSection; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = section.children && section.children.length > 0;
  const src = SOURCE_CONFIG[section.source] ?? SOURCE_CONFIG.ai;

  return (
    <div className={`${depth > 0 ? "ml-5 border-l border-gray-100 pl-3" : ""}`}>
      <div
        className={`flex items-center gap-2 py-1.5 px-2 rounded-lg hover:bg-gray-50 transition-colors ${
          hasChildren ? "cursor-pointer" : ""
        }`}
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        {hasChildren && (
          <span className="text-gray-400 text-xs w-3 flex-shrink-0">
            {expanded ? "▼" : "▶"}
          </span>
        )}
        {!hasChildren && <span className="w-3 flex-shrink-0" />}

        <span className="text-sm flex-shrink-0">
          {SECTION_ICONS[section.type] ?? "📄"}
        </span>

        <span className="text-sm text-gray-800 flex-1 min-w-0 truncate font-medium">
          {section.title}
        </span>

        <span className={`text-xs px-1.5 py-0.5 rounded border ${src.color} flex-shrink-0`}>
          {src.label}
        </span>

        {section.fragment_slug && (
          <span className="text-xs text-gray-400 font-mono flex-shrink-0 hidden sm:block">
            {section.fragment_slug}
          </span>
        )}

        {section.word_count && (
          <span className="text-xs text-gray-400 flex-shrink-0">
            {section.word_count}字
          </span>
        )}
      </div>

      {expanded && hasChildren && (
        <div className="mt-0.5">
          {section.children!.map((child) => (
            <SectionNode key={child.id} section={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── 版本选择器 ────────────────────────────────────────────────────────────────

function VersionSelector({
  versions,
  activeId,
  onSelect,
}: {
  versions: RunVersion[];
  activeId: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {versions.map((v, i) => (
        <button
          key={v.run_id}
          onClick={() => onSelect(v.run_id)}
          className={`flex-shrink-0 px-3 py-2 rounded-lg text-xs border transition-colors ${
            v.run_id === activeId
              ? "bg-indigo-600 text-white border-indigo-600"
              : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
          }`}
        >
          <span className="font-medium">v{versions.length - i}</span>
          {v.quality_score && (
            <span className={`ml-1.5 ${v.run_id === activeId ? "text-indigo-200" : "text-gray-400"}`}>
              {v.quality_score.toFixed(0)}分
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

// ── 主页面 ────────────────────────────────────────────────────────────────────

export default function TraceStructurePage({ runId }: Props) {
  const [structure, setStructure] = useState<ContentSection[]>([]);
  const [versions, setVersions] = useState<RunVersion[]>([]);
  const [activeRunId, setActiveRunId] = useState(runId);
  const [loading, setLoading] = useState(true);
  const [rerunning, setRerunning] = useState(false);
  const [rerunMsg, setRerunMsg] = useState("");

  useEffect(() => {
    loadStructure(activeRunId);
  }, [activeRunId]);

  async function loadStructure(rid: string) {
    setLoading(true);
    try {
      const [structRes, verRes] = await Promise.all([
        fetch(`${API}/admin/generation-runs/${rid}/structure`),
        fetch(`${API}/admin/generation-runs/${rid}/versions`),
      ]);
      const structData = structRes.ok ? await structRes.json() : { sections: _MOCK_STRUCTURE };
      const verData    = verRes.ok    ? await verRes.json()    : { versions: _MOCK_VERSIONS };
      setStructure(structData.sections ?? _MOCK_STRUCTURE);
      setVersions(verData.versions ?? _MOCK_VERSIONS);
    } catch {
      setStructure(_MOCK_STRUCTURE);
      setVersions(_MOCK_VERSIONS);
    } finally {
      setLoading(false);
    }
  }

  async function handleRerun() {
    setRerunning(true);
    setRerunMsg("");
    try {
      const res = await fetch(`${API}/admin/generation-runs/${activeRunId}/rerun`, {
        method: "POST",
      });
      const data = res.ok ? await res.json() : {};
      setRerunMsg(data.message ?? "重跑任务已提交，稍后刷新查看");
    } catch {
      setRerunMsg("提交失败，请稍后重试");
    } finally {
      setRerunning(false);
    }
  }

  // 统计来源分布
  const sourceCounts = structure.flatMap((s) => [s, ...(s.children ?? [])]).reduce(
    (acc, s) => ({ ...acc, [s.source]: (acc[s.source] ?? 0) + 1 }),
    {} as Record<string, number>,
  );

  return (
    <div className="space-y-5">
      {/* 版本历史 + 一键重跑 */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-800 text-sm">版本历史</h3>
          <button
            onClick={handleRerun}
            disabled={rerunning}
            className="text-xs px-3 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors font-medium"
          >
            {rerunning ? "提交中…" : "🔁 一键重跑"}
          </button>
        </div>
        <VersionSelector versions={versions} activeId={activeRunId} onSelect={setActiveRunId} />
        {rerunMsg && (
          <p className="text-xs text-indigo-600 mt-2">{rerunMsg}</p>
        )}
      </div>

      {/* 来源分布摘要 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {Object.entries(SOURCE_CONFIG).map(([key, cfg]) => (
          <div key={key} className={`rounded-xl border p-3 ${cfg.color}`}>
            <div className="flex items-center gap-1.5 mb-1">
              <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
              <span className="text-xs font-medium">{cfg.label}</span>
            </div>
            <p className="text-xl font-bold">{sourceCounts[key] ?? 0}</p>
            <p className="text-xs opacity-70">个章节</p>
          </div>
        ))}
      </div>

      {/* 结构树 */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <h3 className="font-semibold text-gray-800 text-sm">攻略结构树</h3>
          <span className="text-xs text-gray-400">点击展开/收起章节</span>
        </div>
        <div className="p-4">
          {loading ? (
            <div className="space-y-2 animate-pulse">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-8 bg-gray-100 rounded-lg" />
              ))}
            </div>
          ) : structure.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">暂无结构数据</p>
          ) : (
            <div className="space-y-1">
              {structure.map((s) => <SectionNode key={s.id} section={s} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Mock 数据 ──────────────────────────────────────────────────────────────────

const _MOCK_STRUCTURE: ContentSection[] = [
  {
    id: "overview", type: "overview", title: "行程总纲", source: "ai", word_count: 320,
    children: [
      { id: "ov-intro",   type: "overview", title: "旅行亮点摘要", source: "template", word_count: 80  },
      { id: "ov-profile", type: "overview", title: "用户画像解读", source: "ai",       word_count: 120 },
      { id: "ov-route",   type: "overview", title: "路线总览",     source: "fragment",
        fragment_slug: "tokyo_route_shinjuku", word_count: 120 },
    ],
  },
  {
    id: "day1", type: "day", title: "Day 1 — 抵达 + 新宿", source: "fragment",
    fragment_slug: "tokyo_day1_classic", day_number: 1, word_count: 580,
    children: [
      { id: "d1-morning",   type: "day", title: "上午：机场 → 酒店",     source: "fragment", fragment_slug: "tokyo_logistics_nrt" },
      { id: "d1-afternoon", type: "day", title: "下午：新宿漫游",         source: "fragment", fragment_slug: "tokyo_route_shinjuku" },
      { id: "d1-dinner",    type: "day", title: "晚餐：居酒屋推荐",       source: "ai"       },
    ],
  },
  {
    id: "day2", type: "day", title: "Day 2 — 原宿 + 涩谷", source: "ai",
    day_number: 2, word_count: 620,
  },
  {
    id: "day3", type: "day", title: "Day 3 — 浅草 + 上野", source: "ai",
    day_number: 3, word_count: 590,
  },
  {
    id: "transport", type: "static_block", title: "交通通票指南", source: "static", word_count: 280 },
  {
    id: "cond-jr",  type: "conditional",  title: "JR Pass 购买建议（条件触发）", source: "template", word_count: 150 },
];

const _MOCK_VERSIONS: RunVersion[] = [
  {
    run_id: "11111111-0000-0000-0000-000000000001",
    created_at: "2026-03-22T04:00:00Z",
    quality_score: 83.5,
    generation_mode: "fragment_first",
    status: "completed",
  },
];
