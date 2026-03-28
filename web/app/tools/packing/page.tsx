"use client";

import { useState, useMemo } from "react";
import Link from "next/link";

// ── 数据定义 ─────────────────────────────────────────────────────────────────

const DESTINATIONS = [
  { key: "jp_kansai", label: "日本关西", emoji: "⛩️" },
  { key: "jp_kanto", label: "日本关东", emoji: "🗼" },
  { key: "jp_hokkaido", label: "日本北海道", emoji: "🐻" },
  { key: "jp_okinawa", label: "日本冲绳", emoji: "🌊" },
  { key: "cn_guangfu", label: "广府（广州/珠海）", emoji: "🏙️" },
  { key: "cn_xinjiang", label: "北疆", emoji: "🏔️" },
];

const SEASONS = [
  { key: "spring", label: "春季（3-5月）", emoji: "🌸" },
  { key: "summer", label: "夏季（6-8月）", emoji: "☀️" },
  { key: "autumn", label: "秋季（9-11月）", emoji: "🍁" },
  { key: "winter", label: "冬季（12-2月）", emoji: "❄️" },
];

const SPECIALS = [
  { key: "kids", label: "带娃", emoji: "👶" },
  { key: "onsen", label: "温泉", emoji: "♨️" },
  { key: "hiking", label: "登山/徒步", emoji: "🥾" },
  { key: "beach", label: "海边/潜水", emoji: "🤿" },
  { key: "business", label: "商务出行", emoji: "💼" },
];

interface CheckItem {
  id: string;
  label: string;
  note?: string;
  always?: boolean;
  seasons?: string[];
  specials?: string[];
  minDays?: number;
}

interface Category {
  id: string;
  icon: string;
  label: string;
  items: CheckItem[];
}

const PACKING_DATA: Category[] = [
  {
    id: "docs",
    icon: "📄",
    label: "证件与重要文件",
    items: [
      { id: "passport", label: "护照（有效期6个月以上）", always: true },
      { id: "visa", label: "签证（日本护照持有者可免签）", always: true },
      { id: "flight", label: "机票/行程单（截图离线备用）", always: true },
      { id: "hotel_confirm", label: "酒店预订确认单", always: true },
      { id: "insurance", label: "旅行保险单（医疗+行李险）", always: true },
      { id: "id_copy", label: "护照复印件（与原件分开存）", always: true },
      { id: "emergency", label: "紧急联系人信息卡", always: true },
    ],
  },
  {
    id: "electronics",
    icon: "📱",
    label: "电子设备",
    items: [
      { id: "phone", label: "手机+充电线+充电头", always: true },
      { id: "powerbank", label: "充电宝（10000mAh以上）", always: true },
      { id: "adapter", label: "万能转换插头（日本用A型）", always: true },
      { id: "esim", label: "eSIM/SIM卡（提前激活）", always: true },
      { id: "camera", label: "相机+电池+存储卡", always: false },
      { id: "tripod", label: "迷你三脚架", specials: ["beach", "hiking"] },
      { id: "goproetc", label: "运动相机/防水袋", specials: ["beach"] },
      { id: "laptop", label: "笔记本电脑+充电器", specials: ["business"] },
    ],
  },
  {
    id: "clothes",
    icon: "👕",
    label: "衣物",
    items: [
      { id: "underwear", label: "内衣裤（天数+1套）", always: true },
      { id: "tshirt", label: "短袖T恤", seasons: ["spring", "summer", "autumn"] },
      { id: "long_sleeve", label: "长袖薄衫", seasons: ["spring", "autumn"] },
      { id: "jacket", label: "防风外套/轻薄羽绒", seasons: ["spring", "autumn"] },
      { id: "coat", label: "厚外套（羽绒/毛呢）", seasons: ["winter"] },
      { id: "innerwear", label: "保暖内衣（上下各2套）", seasons: ["winter"] },
      { id: "gloves_hat", label: "手套+毛帽+围巾", seasons: ["winter"] },
      { id: "shorts", label: "短裤/裙子", seasons: ["summer"] },
      { id: "swimwear", label: "泳衣/泳裤", specials: ["beach", "onsen"] },
      { id: "yukata", label: "浴衣（旅馆一般有提供）", specials: ["onsen"] },
      { id: "hiking_pants", label: "速干徒步裤", specials: ["hiking"] },
      { id: "rain_gear", label: "雨衣/折叠雨伞", always: true },
      { id: "socks", label: "袜子（天数+2双）", always: true },
      { id: "walking_shoes", label: "舒适步行鞋（日本步行量大）", always: true },
      { id: "sandals", label: "凉鞋/拖鞋", seasons: ["summer"], specials: ["beach"] },
      { id: "hiking_boots", label: "专业登山鞋/防水鞋", specials: ["hiking"] },
    ],
  },
  {
    id: "toiletries",
    icon: "🧴",
    label: "洗护用品",
    items: [
      { id: "toothbrush", label: "牙刷+牙膏（日本酒店一般有）", always: true },
      { id: "cleanser", label: "洗面奶/护肤品", always: true },
      { id: "sunscreen", label: "防晒霜SPF50+（日本紫外线强）", seasons: ["spring", "summer"] },
      { id: "moisturizer", label: "保湿面霜（冬天空气干燥）", seasons: ["winter", "autumn"] },
      { id: "shampoo", label: "洗发水（精品酒店一般有提供）", always: true },
      { id: "makeup", label: "化妆品（按需）", always: false },
      { id: "tissue", label: "湿巾+面巾纸", always: true },
      { id: "feminine", label: "女性卫生用品（日本超市有售）", always: false },
    ],
  },
  {
    id: "medicine",
    icon: "💊",
    label: "药品",
    items: [
      { id: "cold_med", label: "感冒药（日本感冒药贵）", always: true },
      { id: "stomachmed", label: "肠胃药（消化/止泻）", always: true },
      { id: "painkiller", label: "止痛退烧药（布洛芬）", always: true },
      { id: "antiallergy", label: "抗过敏药（樱花季花粉多）", seasons: ["spring"] },
      { id: "bandage", label: "创可贴+消毒液（步行多易起泡）", always: true },
      { id: "personal_med", label: "个人处方药（须备证明）", always: false },
      { id: "kids_med", label: "儿童专用退烧药/感冒药", specials: ["kids"] },
      { id: "motion_sick", label: "晕车药（山路/轮船需要）", always: false },
    ],
  },
  {
    id: "misc",
    icon: "🎒",
    label: "其他实用物品",
    items: [
      { id: "ic_card", label: "Suica/ICOCA IC交通卡（提前准备）", always: true },
      { id: "cash_jpy", label: "日元现金（日本很多地方不收卡）", always: true },
      { id: "foldable_bag", label: "折叠购物袋（日本超市需自备）", always: true },
      { id: "ziplock", label: "密封袋（防液体泄漏）", always: true },
      { id: "neck_pillow", label: "颈枕（长途飞行）", always: true },
      { id: "eye_mask", label: "眼罩+耳塞（飞机/夜间用）", always: true },
      { id: "kid_stroller", label: "婴儿推车/背带", specials: ["kids"] },
      { id: "kid_snacks", label: "儿童零食+水壶", specials: ["kids"] },
      { id: "swim_goggle", label: "泳镜+浮潜面罩", specials: ["beach"] },
      { id: "hiking_poles", label: "登山杖（可折叠）", specials: ["hiking"] },
    ],
  },
];

// ── Component ────────────────────────────────────────────────────────────────

function CategorySection({
  category,
  checked,
  onToggle,
  activeFilter,
}: {
  category: Category;
  checked: Set<string>;
  onToggle: (id: string) => void;
  activeFilter: { season: string; specials: string[]; days: number };
}) {
  const visibleItems = category.items.filter((item) => {
    if (item.always) return true;
    if (item.seasons && !item.seasons.includes(activeFilter.season)) return false;
    if (item.specials && !item.specials.some((s) => activeFilter.specials.includes(s))) return false;
    if (item.minDays && activeFilter.days < item.minDays) return false;
    return true;
  });

  if (visibleItems.length === 0) return null;

  const doneCount = visibleItems.filter((i) => checked.has(i.id)).length;

  return (
    <div className="bg-white rounded-xl border border-stone-100 overflow-hidden mb-3">
      <div className="flex items-center justify-between px-4 py-3 bg-stone-50 border-b border-stone-100">
        <h3 className="text-sm font-bold text-stone-900">
          {category.icon} {category.label}
        </h3>
        <span className="text-xs text-stone-500">{doneCount}/{visibleItems.length}</span>
      </div>
      <div className="divide-y divide-stone-50">
        {visibleItems.map((item) => (
          <label
            key={item.id}
            className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-stone-50 transition-colors ${
              checked.has(item.id) ? "opacity-60" : ""
            }`}
          >
            <input
              type="checkbox"
              className="w-4 h-4 rounded accent-amber-500"
              checked={checked.has(item.id)}
              onChange={() => onToggle(item.id)}
            />
            <span className={`text-sm ${checked.has(item.id) ? "line-through text-stone-400" : "text-stone-700"}`}>
              {item.label}
            </span>
            {item.note && <span className="text-xs text-stone-400 ml-auto">{item.note}</span>}
          </label>
        ))}
      </div>
    </div>
  );
}

export default function PackingPage() {
  const [destination, setDestination] = useState("jp_kansai");
  const [season, setSeason] = useState("spring");
  const [days, setDays] = useState(7);
  const [specials, setSpecials] = useState<string[]>([]);
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [step, setStep] = useState<"config" | "list">("config");

  const toggleSpecial = (key: string) => {
    setSpecials((prev) => prev.includes(key) ? prev.filter((s) => s !== key) : [...prev, key]);
  };

  const toggleCheck = (id: string) => {
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const filter = useMemo(() => ({ season, specials, days }), [season, specials, days]);

  const totalItems = useMemo(() => {
    return PACKING_DATA.flatMap((cat) =>
      cat.items.filter((item) => {
        if (item.always) return true;
        if (item.seasons && !item.seasons.includes(season)) return false;
        if (item.specials && !item.specials.some((s) => specials.includes(s))) return false;
        return true;
      })
    ).length;
  }, [season, specials]);

  const checkedCount = checked.size;
  const progressPct = totalItems > 0 ? Math.round((checkedCount / totalItems) * 100) : 0;

  if (step === "config") {
    return (
      <div className="max-w-lg mx-auto">
        <h1 className="text-2xl font-black text-stone-900 mb-1">行李清单生成器</h1>
        <p className="text-sm text-stone-500 mb-6">根据你的出行定制专属行李清单</p>

        <div className="bg-white rounded-2xl border border-stone-100 p-5 space-y-5">
          <div>
            <label className="text-xs font-bold text-stone-700 mb-2 block">目的地</label>
            <div className="grid grid-cols-2 gap-2">
              {DESTINATIONS.map((d) => (
                <button
                  key={d.key}
                  onClick={() => setDestination(d.key)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-semibold transition-all text-left ${
                    destination === d.key ? "bg-amber-50 border-amber-300 text-amber-800" : "border-stone-200 text-stone-600"
                  }`}
                >
                  {d.emoji} {d.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-bold text-stone-700 mb-2 block">出行季节</label>
            <div className="grid grid-cols-2 gap-2">
              {SEASONS.map((s) => (
                <button
                  key={s.key}
                  onClick={() => setSeason(s.key)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-semibold transition-all ${
                    season === s.key ? "bg-amber-50 border-amber-300 text-amber-800" : "border-stone-200 text-stone-600"
                  }`}
                >
                  {s.emoji} {s.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-bold text-stone-700 mb-2 block">出行天数：{days}天</label>
            <input
              type="range" min={3} max={14} value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full accent-amber-500"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-stone-700 mb-2 block">特殊需求（可多选）</label>
            <div className="flex flex-wrap gap-2">
              {SPECIALS.map((s) => (
                <button
                  key={s.key}
                  onClick={() => toggleSpecial(s.key)}
                  className={`px-3 py-1.5 rounded-full border text-xs font-semibold transition-all ${
                    specials.includes(s.key) ? "bg-amber-100 border-amber-400 text-amber-800" : "border-stone-200 text-stone-600"
                  }`}
                >
                  {s.emoji} {s.label}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={() => setStep("list")}
            className="w-full bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold py-3 rounded-xl shadow hover:shadow-md transition-all"
          >
            生成清单 →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto">
      {/* 头部 */}
      <div className="flex items-center gap-3 mb-4">
        <button onClick={() => { setStep("config"); setChecked(new Set()); }} className="text-xs text-stone-500 hover:text-amber-600">← 重新设置</button>
        <div className="flex-1">
          <h2 className="text-sm font-bold text-stone-900">
            {DESTINATIONS.find(d => d.key === destination)?.label} · {SEASONS.find(s => s.key === season)?.label} · {days}天
          </h2>
        </div>
      </div>

      {/* 进度 */}
      <div className="bg-white rounded-xl border border-stone-100 p-3 mb-4 flex items-center gap-3">
        <div className="flex-1 bg-stone-100 rounded-full h-2">
          <div
            className="h-full bg-gradient-to-r from-amber-400 to-orange-400 rounded-full transition-all"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <span className="text-xs font-bold text-stone-700 whitespace-nowrap">
          {checkedCount}/{totalItems} ({progressPct}%)
        </span>
      </div>

      {checkedCount === totalItems && totalItems > 0 && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 mb-4 text-center">
          <p className="text-sm font-bold text-emerald-700">🎉 行李准备完成！祝旅途愉快</p>
        </div>
      )}

      {/* 清单 */}
      {PACKING_DATA.map((cat) => (
        <CategorySection
          key={cat.id}
          category={cat}
          checked={checked}
          onToggle={toggleCheck}
          activeFilter={filter}
        />
      ))}

      {/* 打印提示 */}
      <p className="text-xs text-stone-400 text-center mb-4">截图保存 · 方便出发前核对</p>

      {/* CTA */}
      <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 text-center">
        <p className="text-sm font-bold text-stone-900 mb-1">行李打好了，行程定好了吗？</p>
        <p className="text-xs text-stone-500 mb-2">AI定制30-40页完整手册</p>
        <Link href="/quiz?from=packing_tool" className="text-amber-600 font-bold text-sm hover:underline">
          免费定制行程 →
        </Link>
      </div>
    </div>
  );
}
