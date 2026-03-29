"use client";

import { useState, useMemo } from "react";
import Link from "next/link";

// ── 交通卡数据 ───────────────────────────────────────────────────────────────

interface Pass {
  id: string;
  name: string;
  nameJp: string;
  price_cny: number;       // 人民币参考价
  price_jpy: number;       // 日元定价
  coverage: string[];      // 覆盖城市key列表
  type: "ic" | "jr" | "private" | "combo";
  valid_days?: number;     // 有效天数（连续）
  desc: string;
  pros: string[];
  cons: string[];
  buy_method: string;
  suitable: string[];      // 适合的旅行类型
  min_days?: number;
  max_days?: number;
}

const PASSES: Pass[] = [
  {
    id: "suica",
    name: "Suica/ICOCA IC卡",
    nameJp: "Suica / ICOCA",
    price_cny: 130,         // 首充1000日元，约48元；押金500日元
    price_jpy: 1000,
    coverage: ["tokyo", "osaka", "kyoto", "kobe", "sapporo", "hiroshima", "naha"],
    type: "ic",
    desc: "全国通用IC交通卡，地铁+公交+便利店购物，无过期时间",
    pros: ["全国90%地铁公交通用", "便利店刷卡消费", "无需规划，随用随充"],
    cons: ["没有折扣优惠，不省钱", "不能坐新干线（需补票）"],
    buy_method: "在国内App提前申请数字Suica，或到达机场/车站购买实体卡",
    suitable: ["短途出行", "城市内游玩", "随机出行"],
  },
  {
    id: "jr_kansai_wide",
    name: "JR关西广域铁路周游券",
    nameJp: "JR関西ワイドエリアパス",
    price_cny: 490,
    price_jpy: 10000,
    coverage: ["osaka", "kyoto", "kobe", "nara", "hiroshima", "okayama", "tottori"],
    type: "jr",
    valid_days: 5,
    desc: "5天内无限乘坐关西地区JR列车（含部分新干线），最远可到广岛",
    pros: ["包含广岛/姬路新干线", "含JR特急列车", "适合跨城出行"],
    cons: ["不含私铁（京阪/阪急）", "不含地铁", "需在JR窗口兑换"],
    buy_method: "国内旅行网站（携程/飞猪）提前购买兑换券，入境后到JR绿窗口兑换",
    suitable: ["关西多城市游", "包含广岛行程", "5天内频繁乘JR"],
    min_days: 4,
    max_days: 7,
  },
  {
    id: "kansai_thru",
    name: "关西私铁周游券",
    nameJp: "関西スルーパス",
    price_cny: 360,
    price_jpy: 7200,
    coverage: ["osaka", "kyoto", "kobe", "nara"],
    type: "private",
    valid_days: 3,
    desc: "3天内无限乘坐京阪神地区私铁+地铁，专门覆盖JR周游券的盲区",
    pros: ["覆盖京阪/阪急/地铁", "京都市内移动非常便捷", "与JR周游券互补"],
    cons: ["不含JR线路", "不含新干线", "仅限关西核心区"],
    buy_method: "国内旅行网站购买，入境后领取",
    suitable: ["深度关西游", "频繁乘私铁", "配合JR周游券使用"],
    min_days: 3,
    max_days: 5,
  },
  {
    id: "jr_pass_7",
    name: "JR全国铁路周游券 7天",
    nameJp: "ジャパン・レールパス 7日間",
    price_cny: 2480,
    price_jpy: 50000,
    coverage: ["tokyo", "osaka", "kyoto", "hiroshima", "fukuoka", "sapporo", "sendai"],
    type: "jr",
    valid_days: 7,
    desc: "7天内全国新干线+JR特快无限乘，跨越日本最优选",
    pros: ["包含所有JR新干线（除部分站）", "一张卡走遍日本", "含飞驒（高山）等支线"],
    cons: ["价格较高，需跨区域才合算", "不含私铁/地铁", "不含东京-新大阪一部分希望号"],
    buy_method: "国内旅行网站，或海外JR官网购买",
    suitable: ["日本多区域旅行", "东京+关西+广岛行程", "行程跨越关东到关西"],
    min_days: 7,
    max_days: 14,
  },
  {
    id: "jr_pass_14",
    name: "JR全国铁路周游券 14天",
    nameJp: "ジャパン・レールパス 14日間",
    price_cny: 3980,
    price_jpy: 80000,
    coverage: ["tokyo", "osaka", "kyoto", "hiroshima", "fukuoka", "sapporo", "sendai"],
    type: "jr",
    valid_days: 14,
    desc: "14天内全国新干线+JR特快无限乘，长行程利器",
    pros: ["时间更充裕", "跨越更多区域"], cons: ["价格更高"],
    buy_method: "国内旅行网站，或海外JR官网购买",
    suitable: ["长途深度游", "日本全程旅行"],
    min_days: 10,
    max_days: 14,
  },
  {
    id: "hokkaido_rail",
    name: "JR北海道铁路周游券",
    nameJp: "北海道レールパス",
    price_cny: 520,
    price_jpy: 10500,
    coverage: ["sapporo", "hakodate", "asahikawa", "kushiro", "abashiri"],
    type: "jr",
    valid_days: 5,
    desc: "5天内北海道JR全线（含特急）自由乘，环岛旅行利器",
    pros: ["覆盖北海道全线", "含部分特急无需预约", "性价比高"],
    cons: ["仅限北海道", "部分热门车次仍需预约"],
    buy_method: "国内旅行网站购买兑换券",
    suitable: ["北海道多点游", "自驾+铁路结合"],
    min_days: 4,
    max_days: 7,
  },
];

const CITIES = [
  { key: "tokyo", name: "东京/关东", emoji: "🗼" },
  { key: "osaka", name: "大阪", emoji: "🏙️" },
  { key: "kyoto", name: "京都", emoji: "⛩️" },
  { key: "kobe", name: "神户", emoji: "🌃" },
  { key: "nara", name: "奈良", emoji: "🦌" },
  { key: "hiroshima", name: "广岛", emoji: "🕊️" },
  { key: "okayama", name: "冈山", emoji: "🏯" },
  { key: "fukuoka", name: "福冈/九州", emoji: "🍜" },
  { key: "sapporo", name: "北海道", emoji: "🐻" },
  { key: "sendai", name: "仙台/东北", emoji: "🏔️" },
  { key: "naha", name: "冲绳", emoji: "🌊" },
];

function scorePass(pass: Pass, selectedCities: string[], days: number): { score: number; reason: string } {
  let score = 0;
  const reasons: string[] = [];

  const coverageMatch = selectedCities.filter((c) => pass.coverage.includes(c)).length;
  const coverageRatio = selectedCities.length > 0 ? coverageMatch / selectedCities.length : 0;

  score += coverageRatio * 50;
  if (coverageRatio === 1) reasons.push("完全覆盖你的目的地");
  else if (coverageRatio > 0.5) reasons.push(`覆盖 ${coverageMatch}/${selectedCities.length} 个目的地`);

  if (pass.valid_days) {
    if (days >= (pass.min_days || 0) && days <= (pass.max_days || 99)) {
      score += 30;
      reasons.push(`${pass.valid_days}天有效期适合你的行程`);
    } else if (days < (pass.min_days || 0)) {
      score -= 20;
    }
  } else {
    score += 15; // IC卡，随时有用
  }

  if (pass.id === "suica" && selectedCities.length <= 1) score += 10;

  return { score, reason: reasons.join("，") || "通用选择" };
}

// ── Component ────────────────────────────────────────────────────────────────

function PassCard({ pass, score, reason, isTop }: { pass: Pass; score: number; reason: string; isTop: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const typeColors: Record<string, string> = {
    ic: "bg-sky-100 text-sky-700",
    jr: "bg-blue-100 text-blue-700",
    private: "bg-violet-100 text-violet-700",
    combo: "bg-emerald-100 text-emerald-700",
  };
  const typeLabels: Record<string, string> = { ic: "IC卡", jr: "JR周游", private: "私铁", combo: "组合" };

  return (
    <div className={`bg-white rounded-xl border overflow-hidden transition-all ${
      isTop ? "border-amber-300 shadow-md shadow-amber-100" : "border-stone-100"
    }`}>
      <div className="p-4">
        <div className="flex items-start gap-3">
          {isTop && (
            <div className="shrink-0 bg-amber-400 text-white text-[10px] font-black px-2 py-0.5 rounded-full mt-0.5">推荐</div>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-0.5">
              <h3 className="text-sm font-bold text-stone-900">{pass.name}</h3>
              <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold ${typeColors[pass.type]}`}>
                {typeLabels[pass.type]}
              </span>
            </div>
            <p className="text-[10px] text-stone-400 mb-1">{pass.nameJp}</p>
            <p className="text-xs text-stone-600 mb-2">{pass.desc}</p>
            {reason && (
              <p className="text-[10px] text-amber-700 bg-amber-50 rounded px-2 py-1">✓ {reason}</p>
            )}
          </div>
          <div className="shrink-0 text-right">
            <div className="text-base font-black text-stone-900">¥{pass.price_cny.toLocaleString()}</div>
            <div className="text-[10px] text-stone-400">{pass.valid_days ? `${pass.valid_days}天` : "不限期"}</div>
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-3 text-xs text-amber-600 hover:underline"
        >
          {expanded ? "收起详情 ↑" : "查看详情 ↓"}
        </button>
      </div>

      {expanded && (
        <div className="border-t border-stone-50 px-4 pb-4 pt-3 space-y-3 bg-stone-50/50">
          <div>
            <p className="text-[10px] font-bold text-emerald-700 mb-1">优点</p>
            <ul className="space-y-0.5">
              {pass.pros.map((p, i) => <li key={i} className="text-xs text-stone-600 flex gap-1.5"><span className="text-emerald-500">✓</span>{p}</li>)}
            </ul>
          </div>
          <div>
            <p className="text-[10px] font-bold text-rose-700 mb-1">局限</p>
            <ul className="space-y-0.5">
              {pass.cons.map((c, i) => <li key={i} className="text-xs text-stone-500 flex gap-1.5"><span className="text-rose-400">✕</span>{c}</li>)}
            </ul>
          </div>
          <div className="bg-blue-50 rounded-lg px-3 py-2">
            <p className="text-[10px] font-bold text-blue-700 mb-0.5">购买方式</p>
            <p className="text-xs text-blue-800">{pass.buy_method}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function TransportPassPage() {
  const [selectedCities, setSelectedCities] = useState<string[]>([]);
  const [days, setDays] = useState(7);

  const toggleCity = (key: string) => {
    setSelectedCities((prev) =>
      prev.includes(key) ? prev.filter((c) => c !== key) : [...prev, key]
    );
  };

  const rankedPasses = useMemo(() => {
    return PASSES
      .map((pass) => ({ pass, ...scorePass(pass, selectedCities, days) }))
      .sort((a, b) => b.score - a.score);
  }, [selectedCities, days]);

  const topScore = rankedPasses[0]?.score ?? 0;

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-black text-stone-900 mb-1">交通卡选择器</h1>
      <p className="text-sm text-stone-500 mb-6">告诉我你要去哪，帮你推荐最划算的交通方案</p>

      {/* 城市选择 */}
      <div className="bg-white rounded-2xl border border-stone-100 p-5 mb-4">
        <label className="text-xs font-bold text-stone-700 mb-3 block">你要去哪些城市/地区？（可多选）</label>
        <div className="flex flex-wrap gap-2">
          {CITIES.map((city) => (
            <button
              key={city.key}
              onClick={() => toggleCity(city.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-semibold transition-all ${
                selectedCities.includes(city.key)
                  ? "bg-amber-100 border-amber-400 text-amber-800"
                  : "border-stone-200 text-stone-600 hover:border-amber-200"
              }`}
            >
              {city.emoji} {city.name}
            </button>
          ))}
        </div>

        <div className="mt-4">
          <label className="text-xs font-bold text-stone-700 mb-2 block">行程天数：{days}天</label>
          <input
            type="range" min={3} max={14} value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="w-full accent-amber-500"
          />
          <div className="flex justify-between text-[10px] text-stone-400 mt-1">
            <span>3天</span><span>14天</span>
          </div>
        </div>
      </div>

      {/* 结果 */}
      {selectedCities.length > 0 ? (
        <>
          <div className="mb-4">
            <p className="text-xs text-stone-500 mb-3">
              根据你的行程（{selectedCities.map(k => CITIES.find(c => c.key === k)?.name).join("→")} · {days}天），推荐方案：
            </p>
            <div className="space-y-3">
              {rankedPasses.map(({ pass, score, reason }, i) => (
                score > 0 && (
                  <PassCard
                    key={pass.id}
                    pass={pass}
                    score={score}
                    reason={reason}
                    isTop={i === 0 && score === topScore}
                  />
                )
              ))}
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 text-center mb-4">
            <p className="text-xs text-stone-600 mb-2">💡 通常建议：IC卡（必备）+ 对应区域周游券（省钱）</p>
          </div>
        </>
      ) : (
        <div className="text-center py-10 text-stone-400">
          <p className="text-3xl mb-2">🗺️</p>
          <p className="text-sm">选择目的地城市，查看推荐方案</p>
        </div>
      )}

      {/* CTA */}
      <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-100 rounded-2xl p-5 text-center">
        <p className="text-sm font-bold text-stone-900 mb-1">交通搞定了，要不要来一份完整行程？</p>
        <p className="text-xs text-stone-500 mb-3">含每日路线+交通换乘+餐厅推荐，30-40页手册</p>
        <Link
          href="/order"
          className="inline-block bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold text-sm px-5 py-2.5 rounded-full shadow hover:shadow-md transition-all"
        >
          免费定制行程 →
        </Link>
      </div>
    </div>
  );
}
