/**
 * 4.2 分享卡生成 API — 使用 @vercel/og (Satori) 生成 PNG
 * 
 * GET /api/share/card?type=day1&plan=xxx&city=tokyo&theme=上野浅草
 * 
 * 5 种卡片类型：
 *   day1     — 行程第一天预告（最常分享）
 *   result   — 行程生成完成通知（提交后跳转用）
 *   review   — 旅行后好评晒图（��星级评分）
 *   savings  — 省了多少做功课时间（"帮你省了2周"）
 *   invite   — 带邀请码的裂变卡（老带新）
 */
import { ImageResponse } from "next/og";
import { NextRequest } from "next/server";

// 改为 Node runtime，兼容阿里云 FC（FC 不支持 Vercel Edge Runtime）
// next/og 的 ImageResponse 在 Node runtime 下通过 @resvg/resvg-js 正常工作
export const runtime = "nodejs";

// ── 城市封面配置（使用相对路径，运行时由 getCover 拼接为绝对 URL）────────
const CITY_COVERS: Record<string, { img: string; name: string; color: string }> = {
  tokyo:    { img: "/images/tokyo.jpg", name: "东京", color: "#d4a373" },
  osaka:    { img: "/images/osaka.jpg", name: "大阪", color: "#e76f51" },
  kyoto:    { img: "/images/kyoto.jpg", name: "京都", color: "#8b5cf6" },
  hokkaido: { img: "/images/hokkaido.jpg", name: "北海道", color: "#3b82f6" },
  okinawa:  { img: "/images/okinawa.jpg", name: "冲绳", color: "#06b6d4" },
};

const DEFAULT_COVER = { img: "/images/kyoto.jpg", name: "日本", color: "#d4a373" };

/** Satori 需要绝对 URL 来 fetch 图片；从请求中提取 origin 拼接 */
function resolveImg(relPath: string, origin: string): string {
  return `${origin}${relPath}`;
}

// ── 卡片渲染函数 ─────────────────────────────────────────────────────────

function CardDay1({ city, theme, plan, origin }: { city: string; theme?: string; plan?: string; origin: string }) {
  const cover = CITY_COVERS[city] || DEFAULT_COVER;
  return (
    <div style={{ display: "flex", width: 800, height: 420, position: "relative", fontFamily: "sans-serif" }}>
      {/* 背景图 */}
      <img src={resolveImg(cover.img, origin)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
      {/* 渐变遮罩 */}
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0.3) 60%, rgba(0,0,0,0.6) 100%)" }} />
      {/* 内容 */}
      <div style={{ position: "relative", display: "flex", flexDirection: "column", padding: "40px 48px", width: "100%", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ background: cover.color, borderRadius: 6, padding: "4px 12px", fontSize: 13, color: "white", fontWeight: 700 }}>
            {cover.name} · Day 1
          </div>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.6)" }}>专属行程预览</div>
        </div>
        <div>
          <div style={{ fontSize: 36, fontWeight: 800, color: "white", lineHeight: 1.2, marginBottom: 12, letterSpacing: -1 }}>
            {theme || `${cover.name}最值得去的一天`}
          </div>
          <div style={{ fontSize: 14, color: "rgba(255,255,255,0.75)", marginBottom: 24 }}>
            免费预览 · AI 定制行程 · 精确到每一餐每一站
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ background: "white", borderRadius: 999, padding: "10px 24px", fontSize: 14, fontWeight: 700, color: "#1c1917" }}>
              查看我的专属行程 →
            </div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.5)" }}>jtrip.ai</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function CardResult({ city, days, origin }: { city: string; days: number; origin: string }) {
  const cover = CITY_COVERS[city] || DEFAULT_COVER;
  return (
    <div style={{ display: "flex", width: 800, height: 420, background: "#0f172a", fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", padding: "40px 56px", flex: 1 }}>
        <div style={{ fontSize: 52, marginBottom: 16 }}>✨</div>
        <div style={{ fontSize: 32, fontWeight: 800, color: "white", lineHeight: 1.3, marginBottom: 8 }}>
          我的 {cover.name} {days} 天行程<br />生成完毕！
        </div>
        <div style={{ fontSize: 15, color: "#94a3b8", marginBottom: 24 }}>
          30-40页完整攻略 · 精确到每个时间段
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <div style={{ background: cover.color, borderRadius: 8, padding: "10px 20px", fontSize: 14, color: "white", fontWeight: 700 }}>
            免费先看第一天
          </div>
          <div style={{ border: "1px solid #334155", borderRadius: 8, padding: "10px 20px", fontSize: 14, color: "#94a3b8" }}>
            完整版 ¥248
          </div>
        </div>
      </div>
      <div style={{ width: 300, position: "relative", overflow: "hidden" }}>
        <img src={resolveImg(cover.img, origin)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: 0.6 }} />
      </div>
    </div>
  );
}

function CardSavings({ days, hours }: { days: number; hours: number }) {
  return (
    <div style={{ display: "flex", width: 800, height: 420, background: "linear-gradient(135deg, #d4a373 0%, #e9c46a 100%)", fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", width: "100%", padding: "40px" }}>
        <div style={{ fontSize: 80, fontWeight: 900, color: "white", lineHeight: 1 }}>{hours}小时</div>
        <div style={{ fontSize: 22, color: "rgba(255,255,255,0.85)", marginBottom: 24, fontWeight: 600 }}>
          被我省下来了
        </div>
        <div style={{ fontSize: 15, color: "rgba(255,255,255,0.7)", textAlign: "center", maxWidth: 480 }}>
          {days}天日本行程 · AI替你做完了所有功课 · 你只需要出发
        </div>
        <div style={{ marginTop: 32, background: "rgba(255,255,255,0.2)", borderRadius: 12, padding: "12px 32px" }}>
          <span style={{ fontSize: 14, color: "white", fontWeight: 700 }}>jtrip.ai · 日本AI定制攻略</span>
        </div>
      </div>
    </div>
  );
}

function CardReview({ city, rating, comment, origin }: { city: string; rating: number; comment?: string; origin: string }) {
  const cover = CITY_COVERS[city] || DEFAULT_COVER;
  const stars = "⭐".repeat(Math.min(5, Math.max(1, rating)));
  return (
    <div style={{ display: "flex", width: 800, height: 420, background: "#fafaf9", fontFamily: "sans-serif" }}>
      <div style={{ width: 280, position: "relative" }}>
        <img src={resolveImg(cover.img, origin)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to right, transparent, #fafaf9)" }} />
      </div>
      <div style={{ flex: 1, padding: "40px 48px 40px 16px", display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <div style={{ fontSize: 24, marginBottom: 12 }}>{stars}</div>
        <div style={{ fontSize: 22, fontWeight: 800, color: "#1c1917", marginBottom: 12 }}>
          {cover.name}旅行 · 强烈推荐这个攻略
        </div>
        {comment && (
          <div style={{ fontSize: 15, color: "#57534e", lineHeight: 1.6, marginBottom: 20, borderLeft: `3px solid ${cover.color}`, paddingLeft: 16 }}>
            {comment}
          </div>
        )}
        <div style={{ fontSize: 13, color: "#a8a29e" }}>jtrip.ai · AI日本定制行程</div>
      </div>
    </div>
  );
}

function CardInvite({ code, discount }: { code?: string; discount?: number }) {
  return (
    <div style={{ display: "flex", width: 800, height: 420, background: "#0f172a", fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", padding: "40px 56px", flex: 1 }}>
        <div style={{ fontSize: 16, color: "#d4a373", fontWeight: 700, marginBottom: 16 }}>专属邀请</div>
        <div style={{ fontSize: 34, fontWeight: 900, color: "white", lineHeight: 1.2, marginBottom: 16 }}>
          我在用 AI 定制<br />日本旅行攻略
        </div>
        <div style={{ fontSize: 15, color: "#94a3b8", marginBottom: 28 }}>
          用我的邀请码，你可以享受{discount ?? 20}元专属优惠
        </div>
        {code && (
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 10, padding: "14px 24px" }}>
              <span style={{ fontSize: 13, color: "#64748b", marginRight: 8 }}>邀请码</span>
              <span style={{ fontSize: 22, fontWeight: 800, color: "#d4a373", letterSpacing: 3 }}>{code}</span>
            </div>
          </div>
        )}
      </div>
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", padding: "40px", background: "linear-gradient(135deg, #1e293b, #0f172a)" }}>
        <div style={{ width: 120, height: 120, background: "#1e293b", border: "2px solid #334155", borderRadius: 16, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontSize: 48 }}>🗾</span>
        </div>
        <div style={{ fontSize: 13, color: "#64748b", marginTop: 12 }}>扫码了解</div>
        <div style={{ fontSize: 12, color: "#334155", marginTop: 4 }}>jtrip.ai</div>
      </div>
    </div>
  );
}

// ── Route Handler ─────────────────────────────────────────────────────────

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const type = searchParams.get("type") ?? "day1";
  const city = (searchParams.get("city") ?? "tokyo").toLowerCase();
  const plan = searchParams.get("plan") ?? undefined;
  const theme = searchParams.get("theme") ?? undefined;
  const days = parseInt(searchParams.get("days") ?? "5", 10);
  const hours = parseInt(searchParams.get("hours") ?? "40", 10);
  const rating = parseInt(searchParams.get("rating") ?? "5", 10);
  const comment = searchParams.get("comment") ?? undefined;
  const code = searchParams.get("code") ?? undefined;
  const discount = parseInt(searchParams.get("discount") ?? "20", 10);

  const origin = new URL(req.url).origin;
  let element: React.ReactElement;

  switch (type) {
    case "result":
      element = <CardResult city={city} days={days} origin={origin} />;
      break;
    case "savings":
      element = <CardSavings days={days} hours={hours} />;
      break;
    case "review":
      element = <CardReview city={city} rating={rating} comment={comment} origin={origin} />;
      break;
    case "invite":
      element = <CardInvite code={code} discount={discount} />;
      break;
    case "day1":
    default:
      element = <CardDay1 city={city} theme={theme} plan={plan} origin={origin} />;
      break;
  }

  return new ImageResponse(element, {
    width: 800,
    height: 420,
  });
}