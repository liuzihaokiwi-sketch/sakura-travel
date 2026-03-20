import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Travel AI — 管理后台",
  description: "内部订单管理与审核工作台",
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50 !pt-0">
      {/* Override the main layout's pt-14 and hide sakura/navbar via CSS */}
      <style>{`
        body > .sakura-container,
        nav,
        body > div > nav,
        [data-floating-cta] {
          display: none !important;
        }
        main.relative {
          padding-top: 0 !important;
        }
      `}</style>
      {children}
    </div>
  );
}
