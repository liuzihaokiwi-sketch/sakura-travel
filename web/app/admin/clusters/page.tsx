"use client";

import { useState, useEffect, useCallback } from "react";

interface ClusterItem {
  cluster_id: string;
  circle_id: string;
  city_code: string | null;
  name_zh: string;
  name_en: string | null;
  level: string;
  default_duration: string | null;
  anchor_entities: Array<{ name: string; type: string; role: string }>;
  anchor_count: number;
  is_active: boolean;
  trip_role: string;
  experience_family: string | null;
  energy_level: string | null;
  created_at: string | null;
}

interface EntityRole {
  role_id: number;
  entity_id: string;
  entity_name: string;
  entity_type: string;
  role: string;
  sort_order: number;
  is_cluster_anchor: boolean;
}

interface ClusterDetail extends ClusterItem {
  entity_roles: EntityRole[];
  notes: string | null;
  description_zh: string | null;
}

interface ListResponse {
  total: number;
  offset: number;
  limit: number;
  items: ClusterItem[];
}

const CITIES = [
  { value: "", label: "全部城市" },
  { value: "tokyo", label: "东京" },
  { value: "osaka", label: "大阪" },
  { value: "kyoto", label: "京都" },
  { value: "sapporo", label: "札幌" },
  { value: "fukuoka", label: "福冈" },
  { value: "naha", label: "冲绳" },
  { value: "hakone", label: "箱根" },
  { value: "nikko", label: "日光" },
];

const LEVEL_STYLE: Record<string, string> = {
  S: "bg-amber-100 text-amber-800 border-amber-300",
  A: "bg-sky-100 text-sky-800 border-sky-300",
  B: "bg-slate-100 text-slate-600 border-slate-300",
};

const ENTITY_TYPE_ICON: Record<string, string> = {
  poi: "🗺️",
  hotel: "🏨",
  restaurant: "🍽️",
};

function ClusterDetailPanel({
  clusterId,
  onToggleActive,
}: {
  clusterId: string;
  onToggleActive: (id: string, val: boolean) => void;
}) {
  const [detail, setDetail] = useState<ClusterDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/admin/clusters/${clusterId}`)
      .then((r) => r.json())
      .then(setDetail)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [clusterId]);

  if (loading) return <div className="px-4 py-3 text-xs text-slate-400">加载中...</div>;
  if (!detail) return <div className="px-4 py-3 text-xs text-red-500">加载失败</div>;

  return (
    <div className="bg-slate-50 border-x border-b border-slate-200 rounded-b-lg px-4 py-4 space-y-3">
      {detail.description_zh && (
        <p className="text-xs text-slate-600 leading-relaxed">{detail.description_zh}</p>
      )}

      {/* anchor_entities JSON */}
      {detail.anchor_entities.length > 0 && (
        <div>
          <p className="text-xs font-medium text-slate-500 mb-2">Anchor 实体</p>
          <div className="flex flex-wrap gap-2">
            {detail.anchor_entities.map((ae, i) => (
              <span key={i} className="text-xs px-2 py-1 bg-white border border-slate-200 rounded-lg">
                {ENTITY_TYPE_ICON[ae.type] || "📌"} {ae.name}
                <span className="text-slate-400 ml-1">({ae.role})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* entity_roles */}
      {detail.entity_roles.length > 0 && (
        <div>
          <p className="text-xs font-medium text-slate-500 mb-2">关联实体角色（{detail.entity_roles.length} 条）</p>
          <div className="space-y-1">
            {detail.entity_roles.map((r) => (
              <div key={r.role_id} className="flex items-center gap-2 text-xs bg-white border border-slate-100 rounded px-3 py-1.5">
                {r.is_cluster_anchor && <span className="text-amber-500">⚓</span>}
                <span className="font-medium text-slate-700">{r.entity_name}</span>
                <span className="text-slate-400">{r.entity_type}</span>
                <span className="ml-auto text-slate-500 bg-slate-50 px-1.5 py-0.5 rounded">{r.role}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {detail.notes && (
        <p className="text-xs text-slate-500 italic border-t border-slate-100 pt-2">{detail.notes}</p>
      )}

      <div className="flex items-center gap-3 pt-2 border-t border-slate-100">
        <span className="text-xs text-slate-500">启用状态:</span>
        <button
          onClick={() => onToggleActive(detail.cluster_id, !detail.is_active)}
          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
            detail.is_active ? "bg-emerald-500" : "bg-slate-300"
          }`}
        >
          <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform ${
            detail.is_active ? "translate-x-4" : "translate-x-1"
          }`} />
        </button>
        <span className="text-xs text-slate-400">{detail.is_active ? "已启用" : "已停用"}</span>
      </div>
    </div>
  );
}

export default function ClustersPage() {
  const [city, setCity] = useState("");
  const [level, setLevel] = useState("");
  const [data, setData] = useState<ListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: "200" });
      if (city) params.set("city_code", city);
      if (level) params.set("level", level);
      const res = await fetch(`/api/admin/clusters?${params}`);
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [city, level]);

  useEffect(() => { load(); }, [city, level]);

  const handleToggleActive = async (clusterId: string, isActive: boolean) => {
    try {
      await fetch(`/api/admin/clusters/${clusterId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: isActive }),
      });
      // 更新本地状态
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          items: prev.items.map((c) =>
            c.cluster_id === clusterId ? { ...c, is_active: isActive } : c
          ),
        };
      });
    } catch (e: any) {
      alert(e.message);
    }
  };

  // 按城市分组
  const grouped: Record<string, ClusterItem[]> = {};
  for (const item of data?.items || []) {
    const key = item.city_code || "other";
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(item);
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <h1 className="text-sm font-semibold text-slate-900">活动簇管理</h1>
        <p className="text-xs text-slate-400">查看和管理所有城市的活动簇</p>
      </header>

      <div className="px-6 py-6">
        {/* 过滤器 */}
        <div className="flex flex-wrap gap-3 mb-5">
          <select value={city} onChange={e => setCity(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none">
            {CITIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
          <select value={level} onChange={e => setLevel(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none">
            <option value="">全部等级</option>
            <option value="S">S 级</option>
            <option value="A">A 级</option>
            <option value="B">B 级</option>
          </select>
          <div className="ml-auto text-sm text-slate-400 self-center">
            {data ? `共 ${data.total} 个簇` : ""}
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-20 text-slate-400 text-sm">加载中...</div>
        ) : (
          <>
            {/* 列头 */}
            <div className="flex items-center gap-3 px-4 py-2 text-xs text-slate-400 font-medium uppercase tracking-wide mb-1">
              <span className="w-4" />
              <span className="flex-1">簇 ID / 中文名</span>
              <span className="w-12 text-center hidden sm:block">等级</span>
              <span className="w-20 text-center hidden md:block">时长</span>
              <span className="w-20 text-center hidden md:block">Anchors</span>
              <span className="w-16 text-center">状态</span>
            </div>

            {Object.entries(grouped).map(([cityKey, clusters]) => (
              <div key={cityKey} className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-semibold text-slate-700 uppercase">
                    {CITIES.find(c => c.value === cityKey)?.label || cityKey}
                  </span>
                  <span className="text-xs text-slate-400">({clusters.length})</span>
                </div>

                {clusters.map((cluster) => (
                  <div key={cluster.cluster_id} className="mb-2">
                    <div
                      className={`flex items-center gap-3 px-4 py-3 bg-white border cursor-pointer hover:bg-slate-50 transition-colors
                        ${expandedId === cluster.cluster_id ? "rounded-t-lg border-b-0 border-slate-200" : "rounded-lg border-slate-200"}`}
                      onClick={() => setExpandedId(expandedId === cluster.cluster_id ? null : cluster.cluster_id)}
                    >
                      <span className={`text-slate-400 text-xs transition-transform ${expandedId === cluster.cluster_id ? "rotate-90" : ""}`}>▶</span>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-slate-900 text-sm">{cluster.name_zh}</span>
                          {cluster.name_en && <span className="text-xs text-slate-400 truncate hidden sm:inline">{cluster.name_en}</span>}
                          {!cluster.is_active && <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-600 rounded">停用</span>}
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5 font-mono">{cluster.cluster_id}</div>
                      </div>

                      <span className={`text-xs px-2 py-0.5 rounded border font-semibold hidden sm:inline-block ${LEVEL_STYLE[cluster.level] || "bg-slate-100 text-slate-500 border-slate-200"}`}>
                        {cluster.level}
                      </span>

                      <span className="text-xs text-slate-500 w-20 text-center hidden md:block">
                        {cluster.default_duration || "—"}
                      </span>

                      <span className="text-xs text-slate-500 w-20 text-center hidden md:block">
                        {cluster.anchor_count > 0 ? `${cluster.anchor_count} 个` : "—"}
                      </span>

                      <span className={`text-xs px-2 py-0.5 rounded-full w-16 text-center ${
                        cluster.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
                      }`}>
                        {cluster.is_active ? "启用" : "停用"}
                      </span>
                    </div>

                    {expandedId === cluster.cluster_id && (
                      <ClusterDetailPanel
                        clusterId={cluster.cluster_id}
                        onToggleActive={handleToggleActive}
                      />
                    )}
                  </div>
                ))}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
