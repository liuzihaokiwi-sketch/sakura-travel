"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import DayExecutionPage from "@/components/report/page-types/DayExecutionPage";
import type { PageViewModel } from "@/lib/report/types";

interface PageModelsResponse {
  page_models: Record<string, PageViewModel>;
}

interface RenderResponse {
  mode: "preview" | "render";
  render_payload?: {
    count?: number;
    nodes?: Array<{
      page_id?: string;
      summary?: string;
      editable_content?: Record<string, unknown>;
    }>;
  };
}

function pickEditableSamplePage(pageModels: Record<string, PageViewModel>): PageViewModel | null {
  const pages = Object.values(pageModels);
  const dayExecution = pages.find(
    (p) =>
      p.page_type === "day_execution" &&
      p.editable_content &&
      Object.keys(p.editable_content).length > 0
  );
  if (dayExecution) return dayExecution;

  const anyEditable = pages.find(
    (p) => p.editable_content && Object.keys(p.editable_content).length > 0
  );
  return anyEditable ?? null;
}

function buildPatchedVm(base: PageViewModel, editableDraft: Record<string, string>): PageViewModel {
  return {
    ...base,
    editable_content: {
      ...(base.editable_content ?? {}),
      ...editableDraft,
    },
  };
}

export default function EditPage({ params }: { params: { id: string } }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [checkingRender, setCheckingRender] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [selectedPage, setSelectedPage] = useState<PageViewModel | null>(null);
  const [editableDraft, setEditableDraft] = useState<Record<string, string>>({});
  const [renderSummary, setRenderSummary] = useState<string | null>(null);

  const editableKeys = useMemo(
    () => Object.keys(selectedPage?.editable_content ?? {}),
    [selectedPage]
  );

  async function loadPageModels(showLoading = true) {
    if (showLoading) setLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/plan/${params.id}/page-models`, { cache: "no-store" });
      const json = (await res.json()) as PageModelsResponse | { error?: string };
      if (!res.ok) {
        throw new Error("error" in json && json.error ? json.error : "读取 page_models 失败");
      }

      const pageModels = "page_models" in json ? json.page_models : {};
      const samplePage = pickEditableSamplePage(pageModels);
      if (!samplePage) {
        throw new Error("未找到可编辑样板页（editable_content 为空）");
      }

      setSelectedPage(samplePage);
      const nextDraft: Record<string, string> = {};
      Object.entries(samplePage.editable_content ?? {}).forEach(([k, v]) => {
        nextDraft[k] = typeof v === "string" ? v : JSON.stringify(v);
      });
      setEditableDraft(nextDraft);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      if (showLoading) setLoading(false);
    }
  }

  useEffect(() => {
    loadPageModels(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  async function handleSave() {
    if (!selectedPage) return;
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(`/api/plan/${params.id}/page-overrides`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          edits_by_page: {
            [selectedPage.page_id]: {
              editable_content: editableDraft,
            },
          },
        }),
      });

      const json = (await res.json()) as { error?: string; saved_pages?: number };
      if (!res.ok) {
        throw new Error(json.error || "保存失败");
      }

      await loadPageModels(false);
      setNotice(`保存成功，已回读最新编辑结果（saved_pages=${json.saved_pages ?? 0}）`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function verifyRenderPath() {
    setCheckingRender(true);
    setRenderSummary(null);
    setError(null);
    try {
      const res = await fetch(`/api/plan/${params.id}/page-render?mode=preview`, {
        cache: "no-store",
      });
      const raw = (await res.json()) as RenderResponse | { error?: string };
      if (!res.ok) {
        throw new Error("error" in raw && raw.error ? raw.error : "调用 page-render 失败");
      }
      const json = raw as RenderResponse;

      const node = json.render_payload?.nodes?.find((n) => n.page_id === selectedPage?.page_id);
      setRenderSummary(
        `render 链路可用：mode=${json.mode}，nodes=${json.render_payload?.count ?? 0}，样板页摘要=${
          node?.summary || "（空）"
        }`
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "render 校验失败");
    } finally {
      setCheckingRender(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-3.5rem)] bg-warm-50 flex items-center justify-center">
        <p className="text-stone-500">正在加载可编辑页面...</p>
      </div>
    );
  }

  return (
    <main className="min-h-[calc(100vh-3.5rem)] bg-warm-50 py-6 px-4 md:px-6">
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-[370px_1fr] gap-6">
        <aside className="bg-white border border-stone-200 rounded-2xl p-5 h-fit">
          <h1 className="text-xl font-bold text-stone-900">最小编辑入口（A 线样板）</h1>
          <p className="text-xs text-stone-500 mt-1">
            当前仅开放一个样板页，并且只允许编辑 editable_content。
          </p>

          {selectedPage && (
            <div className="mt-4 rounded-xl border border-stone-200 p-3 text-xs text-stone-600 bg-stone-50">
              <p>
                page_id: <span className="font-mono">{selectedPage.page_id}</span>
              </p>
              <p>
                page_type: <span className="font-mono">{selectedPage.page_type}</span>
              </p>
              <p>可编辑字段数: {editableKeys.length}</p>
            </div>
          )}

          <div className="mt-4 space-y-3">
            {editableKeys.length === 0 && (
              <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                当前样板页没有 editable_content 字段可编辑。
              </p>
            )}

            {editableKeys.map((key) => (
              <label key={key} className="block">
                <span className="text-xs font-medium text-stone-700">{key}</span>
                <textarea
                  className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-warm-300"
                  rows={key.includes("note") ? 5 : 3}
                  value={editableDraft[key] ?? ""}
                  onChange={(e) =>
                    setEditableDraft((prev) => ({
                      ...prev,
                      [key]: e.target.value,
                    }))
                  }
                />
              </label>
            ))}
          </div>

          <div className="mt-5 flex flex-col gap-2">
            <Button variant="warm" onClick={handleSave} disabled={saving || !selectedPage}>
              {saving ? "保存中..." : "保存 editable_content"}
            </Button>
            <Button variant="outline" onClick={verifyRenderPath} disabled={checkingRender || !selectedPage}>
              {checkingRender ? "校验中..." : "校验 preview/render 链路"}
            </Button>
            <Link href={`/plan/${params.id}`}>
              <Button variant="outline" className="w-full">
                返回计划页
              </Button>
            </Link>
          </div>

          {notice && (
            <p className="mt-4 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
              {notice}
            </p>
          )}
          {renderSummary && (
            <p className="mt-3 text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
              {renderSummary}
            </p>
          )}
          {error && (
            <p className="mt-3 text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
        </aside>

        <section className="space-y-3">
          <p className="text-sm text-stone-500">
            右侧预览仅用于验证本次样板编辑，不暴露 stable_inputs / internal_state 为可编辑输入。
          </p>
          <div className="bg-stone-100 border border-stone-200 rounded-2xl p-3 overflow-x-auto">
            {selectedPage?.page_type === "day_execution" ? (
              <DayExecutionPage
                vm={buildPatchedVm(selectedPage, editableDraft)}
                mode="screen"
              />
            ) : (
              <div className="bg-white rounded-xl border border-stone-200 p-4 text-sm text-stone-600">
                当前样板页类型为 <span className="font-mono">{selectedPage?.page_type}</span>，暂未接入该页型组件预览。
                你仍可编辑并保存 editable_content，再刷新验证持久化。
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
