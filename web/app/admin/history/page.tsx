"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface ArchivedItem {
  id: string;
  name: string | null;
  destination: string;
  duration_days: number;
  party_type: string;
  styles: string[];
  wechat_id: string | null;
  status: string;
  notes: string | null;
  archived_at: string | null;
  travel_end_date: string | null;
  created_at: string;
  updated_at: string;
}

const DEST_LABELS: Record<string, string> = {
  tokyo: "🗼 东京",
  "osaka-kyoto": "⛩️ 大阪+京都",
  "tokyo-osaka-kyoto": "🗼 东京+大阪+京都",
  hokkaido: "🏔️ 北海道",
  okinawa: "🏖️ 冲绳",
};

const PARTY_LABELS: Record<string, string> = {
  solo: "独自一人",
  couple: "情侣/夫妻",
  family: "带孩子/家庭",
  family_child: "带孩子/家庭",
  friends: "朋友/闺蜜",
  parents: "带父母",
  unknown: "未指定",
};

export default function HistoryPage() {
  const [items, setItems] = useState<ArchivedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Fetch archived items
  useEffect(() => {
    setLoading(true);
    const url = debouncedSearch
      ? `/api/admin/submissions/archived?destination=${encodeURIComponent(debouncedSearch)}`
      : "/api/admin/submissions/archived";

    fetch(url)
      .then((r) => r.json())
      .then((data) => {
        setItems(Array.isArray(data) ? data : []);
      })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [debouncedSearch]);

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return "—";
    const d = new Date(dateStr);
    return d.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" });
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-[1200px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/admin"
              className="text-sm text-slate-500 hover:text-slate-900 transition-colors"
            >
              ← 返回看板
            </Link>
            <div className="h-4 w-px bg-slate-200" />
            <div>
              <h1 className="text-sm font-semibold text-slate-900">📁 历史表单</h1>
              <p className="text-xs text-slate-500">已归档的旅行方案</p>
            </div>
          </div>
          <span className="text-xs text-slate-400">
            共 {items.length} 条记录
          </span>
        </div>
      </header>

      <div className="max-w-[1200px] mx-auto p-6">
        {/* Search bar */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="🔍 按目的地搜索..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full max-w-md px-4 py-2.5 rounded-lg border border-slate-200 bg-white text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-300 focus:border-transparent transition-all"
          />
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-sm text-slate-400">加载中...</div>
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-4xl mb-3">📭</div>
            <p className="text-sm text-slate-500">暂无归档记录</p>
            <p className="text-xs text-slate-400 mt-1">
              用户旅程结束后，攻略会自动归档到这里
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                    编号
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                    目的地
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                    天数
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                    同行
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                    风格
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                    微信
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                    创建时间
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                    归档时间
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs text-slate-500">
                        #{item.id.slice(0, 8)}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-900">
                      {DEST_LABELS[item.destination] || item.destination}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{item.duration_days}天</td>
                    <td className="px-4 py-3 text-slate-600">
                      {PARTY_LABELS[item.party_type] || item.party_type}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1 flex-wrap">
                        {(item.styles || []).map((s) => (
                          <span
                            key={s}
                            className="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-600"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {item.wechat_id || "—"}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {formatDate(item.created_at)}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {formatDate(item.archived_at)}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/admin/order/${item.id}`}
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                      >
                        查看详情
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
