"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import BookingWindowPage from "@/components/report/page-types/BookingWindowPage";
import ChapterOpenerPage from "@/components/report/page-types/ChapterOpenerPage";
import CoverPage from "@/components/report/page-types/CoverPage";
import DayExecutionPage from "@/components/report/page-types/DayExecutionPage";
import DeparturePrepPage from "@/components/report/page-types/DeparturePrepPage";
import HotelDetailPage from "@/components/report/page-types/HotelDetailPage";
import HotelStrategyPage from "@/components/report/page-types/HotelStrategyPage";
import LiveNoticePage from "@/components/report/page-types/LiveNoticePage";
import MajorActivityDetailPage from "@/components/report/page-types/MajorActivityDetailPage";
import MajorActivityOverviewPage from "@/components/report/page-types/MajorActivityOverviewPage";
import PhotoThemeDetailPage from "@/components/report/page-types/PhotoThemeDetailPage";
import PreferencePage from "@/components/report/page-types/PreferencePage";
import RestaurantDetailPage from "@/components/report/page-types/RestaurantDetailPage";
import RouteOverviewPage from "@/components/report/page-types/RouteOverviewPage";
import SupplementalSpotsPage from "@/components/report/page-types/SupplementalSpotsPage";
import TocPage from "@/components/report/page-types/TocPage";
import TransitDetailPage from "@/components/report/page-types/TransitDetailPage";
import type { PageViewModel } from "@/lib/report/types";

interface PageModelsResponse {
  plan_id?: string;
  page_models?: Record<string, PageViewModel>;
  error?: string;
}

type PageComponent = (props: { vm: PageViewModel; mode?: "screen" | "print" }) => JSX.Element;

const PAGE_COMPONENTS: Record<string, PageComponent> = {
  booking_window: BookingWindowPage,
  chapter_opener: ChapterOpenerPage,
  cover: CoverPage,
  day_execution: DayExecutionPage,
  departure_prep: DeparturePrepPage,
  hotel_detail: HotelDetailPage,
  hotel_strategy: HotelStrategyPage,
  live_notice: LiveNoticePage,
  major_activity_detail: MajorActivityDetailPage,
  major_activity_overview: MajorActivityOverviewPage,
  photo_theme_detail: PhotoThemeDetailPage,
  preference_fulfillment: PreferencePage,
  restaurant_detail: RestaurantDetailPage,
  route_overview: RouteOverviewPage,
  supplemental_spots: SupplementalSpotsPage,
  toc: TocPage,
  transit_detail: TransitDetailPage,
};

function toSortedPages(pageModels: Record<string, PageViewModel>): PageViewModel[] {
  return Object.values(pageModels).sort((left, right) => {
    const leftPage = Number(left.heading?.page_number ?? Number.MAX_SAFE_INTEGER);
    const rightPage = Number(right.heading?.page_number ?? Number.MAX_SAFE_INTEGER);
    if (leftPage !== rightPage) {
      return leftPage - rightPage;
    }
    return left.page_id.localeCompare(right.page_id);
  });
}

function deriveHandbookTitle(pages: PageViewModel[]): string {
  const cover = pages.find((page) => page.page_type === "cover" && page.heading?.title);
  return cover?.heading.title || pages[0]?.heading?.title || "旅行手册";
}

function deriveHandbookSubtitle(pages: PageViewModel[]): string {
  const cover = pages.find((page) => page.page_type === "cover" && page.heading?.subtitle);
  return cover?.heading.subtitle || "当前页面直接消费 page_models 主链";
}

function FallbackPageCard({ vm }: { vm: PageViewModel }) {
  const summary = vm.sections
    .map((section) => {
      const content = section.content as Record<string, unknown>;
      if (typeof content?.text === "string" && content.text.trim()) {
        return content.text.trim();
      }
      if (Array.isArray(content?.items)) {
        return `${content.items.length} 项内容`;
      }
      return "";
    })
    .find(Boolean);

  return (
    <article className="max-w-[210mm] mx-auto bg-white border border-stone-200 rounded-sm shadow-xl p-8">
      <p className="text-xs uppercase tracking-[0.25em] text-stone-400">{vm.page_type}</p>
      <h2 className="mt-3 text-2xl font-semibold text-stone-900">{vm.heading.title}</h2>
      {vm.heading.subtitle ? (
        <p className="mt-2 text-sm text-stone-500">{vm.heading.subtitle}</p>
      ) : null}
      {summary ? <p className="mt-6 text-sm leading-7 text-stone-700">{summary}</p> : null}
    </article>
  );
}

function PageModelSurface({ vm }: { vm: PageViewModel }) {
  const Component = PAGE_COMPONENTS[vm.page_type];
  if (Component) {
    return <Component vm={vm} mode="screen" />;
  }
  return <FallbackPageCard vm={vm} />;
}

function PlanContent({ params }: { params: { id: string } }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pages, setPages] = useState<PageViewModel[]>([]);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadPageModels() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/plan/${params.id}/page-models`, { cache: "no-store" });
        const json = (await res.json()) as PageModelsResponse;
        if (!res.ok) {
          throw new Error(json.error || "读取 page_models 失败");
        }

        const pageModels = json.page_models ?? {};
        const nextPages = toSortedPages(pageModels);
        if (!cancelled) {
          if (nextPages.length === 0) {
            setError("当前计划缺少 page_models，无法按 handbook 主链展示。");
            setPages([]);
          } else {
            setPages(nextPages);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "页面加载失败");
          setPages([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadPageModels();
    return () => {
      cancelled = true;
    };
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <p className="text-stone-500">正在加载 page-model handbook…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-stone-50">
        <div className="max-w-3xl mx-auto px-6 py-16">
          <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
            <p className="text-sm font-medium text-red-700">当前计划无法进入 page-model-first 展示</p>
            <p className="mt-2 text-sm text-red-600">{error}</p>
            <div className="mt-5 flex gap-3">
              <Link href={`/plan/${params.id}/edit`}>
                <Button variant="outline">打开编辑入口</Button>
              </Link>
              <Button variant="warm" onClick={() => window.location.reload()}>
                重新加载
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const title = deriveHandbookTitle(pages);
  const subtitle = deriveHandbookSubtitle(pages);
  const previewPages = pages.slice(0, 5);
  const remainingCount = Math.max(0, pages.length - previewPages.length);

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-200 bg-white/90 backdrop-blur">
        <div className="max-w-5xl mx-auto px-4 md:px-6 py-6">
          <p className="text-xs uppercase tracking-[0.3em] text-stone-400">Page-Model First Handbook</p>
          <h1 className="mt-3 text-3xl font-semibold text-stone-900">{title}</h1>
          <p className="mt-2 text-sm text-stone-500">{subtitle}</p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs text-stone-500">
            <span className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1">{pages.length} 页</span>
            <span className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1">主展示直接消费 page_models</span>
            <span className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1">legacy report/day-first 不再是主入口</span>
          </div>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href={`/plan/${params.id}/edit`}>
              <Button variant="outline">编辑 handbook 页面</Button>
            </Link>
            <Button
              variant="warm"
              disabled={exporting}
              onClick={async () => {
                setExporting(true);
                try {
                  const resp = await fetch(`/api/plan/${params.id}/pdf`);
                  if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.error || "PDF 导出失败");
                  }
                  const contentType = resp.headers.get("content-type") || "";
                  if (contentType.includes("application/pdf")) {
                    const blob = await resp.blob();
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = `travel-handbook-${params.id.slice(0, 8)}.pdf`;
                    link.click();
                    URL.revokeObjectURL(url);
                  } else {
                    const html = await resp.text();
                    const win = window.open("", "_blank");
                    if (win) {
                      win.document.write(html);
                      win.document.close();
                    }
                  }
                } catch (err) {
                  alert(err instanceof Error ? err.message : "PDF 导出失败");
                } finally {
                  setExporting(false);
                }
              }}
            >
              {exporting ? "正在导出 PDF…" : "导出 handbook PDF"}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 md:px-6 py-8 space-y-8">
        <section className="rounded-2xl border border-stone-200 bg-white p-5">
          <p className="text-sm font-medium text-stone-700">页面目录</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {pages.map((page) => (
              <a
                key={page.page_id}
                href={`#${page.page_id}`}
                className="rounded-full border border-stone-200 px-3 py-1 text-xs text-stone-600 hover:bg-stone-50"
              >
                {page.heading.page_number ? `${page.heading.page_number}. ` : ""}
                {page.heading.title}
              </a>
            ))}
          </div>
        </section>

        {previewPages.map((page) => (
          <section id={page.page_id} key={page.page_id}>
            <PageModelSurface vm={page} />
          </section>
        ))}

        {remainingCount > 0 ? (
          <section className="rounded-2xl border border-stone-200 bg-white p-8 text-center">
            <p className="text-sm text-stone-500">后续还有 {remainingCount} 页已生成，可在编辑入口继续查看与微调。</p>
            <div className="mt-4">
              <Link href={`/plan/${params.id}/edit`}>
                <Button variant="outline">进入编辑入口继续处理</Button>
              </Link>
            </div>
          </section>
        ) : null}
      </main>
    </div>
  );
}

export default function PlanPage({ params }: { params: { id: string } }) {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-stone-50 flex items-center justify-center">
          <p className="text-stone-500">加载 handbook 页面中…</p>
        </div>
      }
    >
      <PlanContent params={params} />
    </Suspense>
  );
}
