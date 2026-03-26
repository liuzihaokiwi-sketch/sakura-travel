"""
export_plan_pdf.py — v3: 用户级攻略 PDF 报告

结构: 封面 → 目录 → 设计理念 → 总览表 → 住宿概览 → 每日详情×N →
      预约&执行提醒 → 出发准备 → 尾页

字段净化: 走廊/区域/城市 key 全部转中文展示名，无内部 ID 泄露
"""
import asyncio
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from sqlalchemy import select, text
from app.db.session import AsyncSessionLocal


# -- display_registry import (single source of truth) --
from app.domains.planning.display_registry import (
    CORRIDOR_ZH as _CORRIDOR_ZH,
    CITY_ZH as _CITY_ZH,
    AREA_ZH as _AREA_ZH,
    CUISINE_ZH as _CUISINE_ZH,
    DAY_TYPE_ZH as _DAY_TYPE_ZH,
    INTENSITY_ZH as _INTENSITY_ZH,
    MEAL_ZH as _MEAL_ZH,
    sanitize as _sanitize_text,
    display_corridor as _corridor_zh,
    display_city as _city_zh,
    display_area as _area_zh,
)



# ── 字体准备 ──────────────────────────────────────────────────────────────────

FONT_DIR = Path(__file__).parent / "_fonts"
FONT_DIR.mkdir(exist_ok=True)

def _ensure_font():
    """确保有中文字体文件"""
    font_path = FONT_DIR / "NotoSansSC-Regular.ttf"
    if font_path.exists():
        return str(font_path)
    
    # 尝试找系统字体
    system_fonts = [
        r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑
        r"C:\Windows\Fonts\simhei.ttf",     # 黑体
        r"C:\Windows\Fonts\simsun.ttc",     # 宋体
    ]
    for f in system_fonts:
        if os.path.exists(f):
            return f
    
    # 在项目 web 目录找 Noto Sans
    web_font = Path(__file__).resolve().parents[1] / "web" / "node_modules" / "@fontsource" / "noto-sans-sc"
    if web_font.exists():
        for ttf in web_font.rglob("*.ttf"):
            return str(ttf)
        for woff2 in web_font.rglob("*.woff2"):
            return str(woff2)
    
    return None


async def load_plan_data():
    """从 DB 加载最新 plan 的完整数据"""
    async with AsyncSessionLocal() as session:
        # 获取最新 plan
        from app.db.models.derived import ItineraryPlan, ItineraryDay, ItineraryItem
        
        result = await session.execute(
            select(ItineraryPlan)
            .order_by(ItineraryPlan.created_at.desc())
            .limit(1)
        )
        plan = result.scalars().first()
        if not plan:
            print("❌ 没有找到任何 plan")
            return None
        
        print(f"📋 Plan: {plan.plan_id}")
        print(f"   Status: {plan.status}")
        print(f"   Created: {plan.created_at}")
        
        meta = plan.plan_metadata or {}
        
        # 获取 days
        days_q = await session.execute(
            select(ItineraryDay)
            .where(ItineraryDay.plan_id == plan.plan_id)
            .order_by(ItineraryDay.day_number)
        )
        days = days_q.scalars().all()
        
        day_data = []
        for day in days:
            items_q = await session.execute(
                select(ItineraryItem)
                .where(ItineraryItem.day_id == day.day_id)
                .order_by(ItineraryItem.sort_order)
            )
            items = items_q.scalars().all()

            item_list = []
            for item in items:
                entity_name = "自由安排"
                entity_desc = ""
                if item.entity_id:
                    from app.db.models.catalog import EntityBase
                    entity = await session.get(EntityBase, item.entity_id)
                    if entity:
                        entity_name = entity.name_zh or entity.name_en or "未知"
                        entity_desc = entity.area_name or ""

                notes = {}
                if item.notes_zh:
                    try:
                        notes = json.loads(item.notes_zh)
                    except Exception:
                        notes = {"text": item.notes_zh}

                item_list.append({
                    "name": notes.get("name", entity_name),
                    "type": item.item_type,
                    "description": entity_desc[:200],
                    "area_raw": entity_desc,
                    "area_display": notes.get("area_display", entity_desc),
                    "corridor_display": notes.get("corridor_display", ""),
                    "copy": notes.get("copy_zh", ""),
                    "tips": notes.get("tips_zh", ""),
                    "is_main": notes.get("is_main_driver", False),
                    "corridor": notes.get("corridor", ""),
                    "meal_type": notes.get("meal_type", ""),
                    "placeholder": notes.get("placeholder", False),
                    "cuisine": notes.get("cuisine", ""),
                    "why_here": notes.get("why_here", ""),
                    "serving_area": notes.get("serving_area", ""),
                })

            # 解析 day_summary_zh — 格式可能是 "corridor · intensity" 或 "day_type | corridor | intensity"
            raw_summary = day.day_summary_zh or ""
            summary_parts = raw_summary.split(" | ")
            day_type_raw = summary_parts[0].strip() if len(summary_parts) > 0 else ""
            corridor_raw = summary_parts[1].strip() if len(summary_parts) > 1 else ""
            intensity_raw = summary_parts[2].strip() if len(summary_parts) > 2 else ""
            # 兼容 "corridor · intensity" 单段格式
            if not corridor_raw and " · " in day_type_raw:
                p2 = day_type_raw.split(" · ")
                corridor_raw = p2[0]
                intensity_raw = p2[1] if len(p2) > 1 else ""
                day_type_raw = ""

            day_data.append({
                "day_number": day.day_number,
                "city_raw": day.city_code or "",
                "city": _city_zh(day.city_code or ""),
                "theme": day.day_theme or f"Day {day.day_number}",
                "day_type_raw": day_type_raw,
                "day_type": _DAY_TYPE_ZH.get(day_type_raw, day_type_raw),
                "corridor_raw": corridor_raw,
                "corridor": _corridor_zh(corridor_raw),
                "intensity_raw": intensity_raw,
                "intensity": _INTENSITY_ZH.get(intensity_raw, intensity_raw),
                "items": item_list,
            })
        
        return {
            "plan_id": str(plan.plan_id),
            "meta": meta,
            "days": day_data,
        }


def generate_pdf(data: dict, output_path: str):
    """v3: 用户级 PDF 报告"""
    from fpdf import FPDF

    font_path = _ensure_font()
    if not font_path:
        print("⚠️ 找不到中文字体，PDF 中文可能乱码")

    class TravelPDF(FPDF):
        def __init__(self):
            super().__init__()
            if font_path and (font_path.endswith('.ttf') or font_path.endswith('.ttc')):
                self.add_font("zh", "", font_path, uni=True)
                self.add_font("zh", "B", font_path, uni=True)
                self._zh = "zh"
            else:
                self._zh = "Helvetica"

        def header(self):
            if self.page_no() == 1:
                return  # 封面无 header
            self.set_font(self._zh, "", 8)
            self.set_text_color(170, 170, 170)
            self.cell(0, 6, "Travel AI · 关西经典圈攻略", align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(220, 220, 220)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(2)

        def footer(self):
            self.set_y(-12)
            self.set_font(self._zh, "", 7)
            self.set_text_color(170, 170, 170)
            self.cell(0, 8, f"— {self.page_no()} —", align="C")

    pdf = TravelPDF()
    zh = pdf._zh
    meta = data.get("meta", {})

    # 推导城市
    actual_cities = meta.get("actual_cities", [])
    if not actual_cities:
        seen = []
        for d in data["days"]:
            c = d.get("city_raw", d.get("city", ""))
            if c and c not in seen:
                seen.append(c)
        actual_cities = seen
    cities_str = " · ".join(_city_zh(c) for c in actual_cities)
    hotel_bases = meta.get("hotel_bases", [])
    total_days = len(data["days"])
    total_nights = total_days - 1

    # ═══════════════ 封面 ═══════════════
    pdf.add_page()
    pdf.ln(45)
    pdf.set_font(zh, "B", 28)
    pdf.set_text_color(35, 35, 35)
    pdf.cell(0, 15, f"关西经典圈 · {total_days}天{total_nights}晚", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.set_font(zh, "", 15)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 10, cities_str, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font(zh, "", 11)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 7, "情侣 · 中等预算 · 文化美食", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "2026年4月10日 — 4月15日", align="C", new_x="LMARGIN", new_y="NEXT")

    # ── 同源标识 ──
    bundle = meta.get("evidence_bundle", {})
    _pdf_run_id = bundle.get("run_id", data.get("plan_id", "N/A"))
    _pdf_plan_id = data.get("plan_id", "N/A")
    pdf.ln(8)
    pdf.set_font(zh, "", 8)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(0, 5, f"run_id: {_pdf_run_id}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, f"plan_id: {_pdf_plan_id}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_creator(f"travel-ai run={_pdf_run_id}")

    pdf.ln(18)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(65, pdf.get_y(), 145, pdf.get_y())

    if hotel_bases:
        pdf.ln(10)
        pdf.set_font(zh, "", 10)
        pdf.set_text_color(130, 130, 130)
        base_parts = []
        for b in hotel_bases:
            area = _area_zh(b.get("area", ""))
            nights = b.get("nights", 1)
            base_parts.append(f"{area} {nights}晚")
        pdf.cell(0, 6, f"住宿: {' + '.join(base_parts)}", align="C", new_x="LMARGIN", new_y="NEXT")

    # ═══════════════ 目录 ═══════════════
    pdf.add_page()
    pdf.set_font(zh, "B", 20)
    pdf.set_text_color(35, 35, 35)
    pdf.cell(0, 14, "目 录", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font(zh, "", 10)
    pdf.set_text_color(60, 60, 60)

    toc = ["一、设计理念与偏好兑现", "二、行程总览", "三、住宿概览"]
    for i, d in enumerate(data["days"], 1):
        toc.append(f"四-{i}、Day {d['day_number']} — {d['theme'][:25]}")
    toc += ["五、预约 & 执行提醒", "六、出发准备清单"]
    for t in toc:
        pdf.cell(0, 7, t, new_x="LMARGIN", new_y="NEXT")

    # ═══════════════ 一、设计理念 ═══════════════
    pdf.add_page()
    pdf.set_font(zh, "B", 18)
    pdf.set_text_color(35, 35, 35)
    pdf.cell(0, 12, "一、设计理念", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font(zh, "", 9)
    pdf.set_text_color(60, 60, 60)
    briefs = [
        f"路线策略: {cities_str}，由静入动——前半段京都寺社古巷，后半段大阪都市活力",
    ]
    if hotel_bases:
        hb_str = " + ".join(f"{_area_zh(b.get('area',''))} {b.get('nights',1)}晚" for b in hotel_bases)
        briefs.append(f"住宿策略: {hb_str}")
    briefs += [
        "节奏原则: 到达日轻启动 → 全日深游穿插 → 主题公园日集中体验 → 回程日轻收尾",
        "餐饮策略: 每餐跟随当日走廊，午餐沿线顺路，晚餐目的地品质优先，全程菜系不重复",
        "预算分配: 文化体验为主，美食集中夜间街区，交通以地铁/JR为主控制成本",
    ]
    for item in briefs:
        pdf.cell(4, 6, "·")
        pdf.cell(0, 6, item, new_x="LMARGIN", new_y="NEXT")

    # 偏好兑现
    pdf.ln(5)
    pdf.set_font(zh, "B", 12)
    pdf.set_text_color(35, 35, 35)
    pdf.cell(0, 8, "偏好兑现", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(zh, "", 9)
    pdf.set_text_color(70, 70, 70)
    # 动态偏好兑现 — 只引用 plan 中真正出现的走廊/城市
    _PREF_CATALOG = {
        "fushimi": ("文化体验", "伏见稻荷大社 -- 千本鸟居，京都必访"),
        "higashiyama": ("文化体验", "清水寺·东山散策 -- 古寺石阶、二年坂三年坂"),
        "arashiyama": ("自然风光", "岚山竹林·嵯峨野 -- 竹林小径、天龙寺庭园"),
        "sakurajima": ("主题公园", "USJ 环球影城整日 -- 独立成天，沉浸体验"),
        "nara_park": ("奈良日归", "奈良公园·东大寺 -- 鹿、大佛、春日大社"),
        "osakajo": ("历史建筑", "大阪城天守阁 -- 丰臣秀吉筑城，俯瞰市区"),
        "namba": ("美食探索", "道顿堀·难波 -- 串炸、章鱼烧、大阪夜食"),
        "shinsekai": ("美食探索", "新世界·通天阁 -- 复古商店街、串炸一条街"),
        "gion": ("文化体验", "祇园·花见小路 -- 舞伎文化、町家建筑"),
    }
    actual_corridors = set()
    for d in data["days"]:
        cr = d.get("corridor_raw", "")
        if cr:
            actual_corridors.add(cr)
    prefs_rendered = []
    for corr in actual_corridors:
        if corr in _PREF_CATALOG:
            prefs_rendered.append(_PREF_CATALOG[corr])
    # 去重 title
    seen_titles = set()
    for title, desc in prefs_rendered:
        if title in seen_titles:
            continue
        seen_titles.add(title)
        pdf.set_font(zh, "B", 9)
        pdf.cell(22, 6, f"[v] {title}")
        pdf.set_font(zh, "", 9)
        pdf.cell(0, 6, desc, new_x="LMARGIN", new_y="NEXT")

    # ═══════════════ 二、行程总览 ═══════════════
    pdf.add_page()
    pdf.set_font(zh, "B", 18)
    pdf.set_text_color(35, 35, 35)
    pdf.cell(0, 12, "二、行程总览", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font(zh, "B", 9)
    pdf.set_fill_color(245, 245, 245)
    col_w = [15, 22, 62, 50, 22]
    headers = ["天", "城市", "主题", "走廊", "节奏"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 8, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font(zh, "", 8)
    for d in data["days"]:
        pdf.set_text_color(50, 50, 50)
        pdf.cell(col_w[0], 7, str(d["day_number"]), border=1, align="C")
        pdf.cell(col_w[1], 7, d["city"], border=1, align="C")
        pdf.cell(col_w[2], 7, d["theme"][:22], border=1)
        pdf.cell(col_w[3], 7, d["corridor"], border=1, align="C")
        pdf.cell(col_w[4], 7, d["intensity"] or "均衡", border=1, align="C")
        pdf.ln()

    # ═══════════════ 三、住宿概览 ═══════════════
    pdf.ln(8)
    pdf.set_font(zh, "B", 18)
    pdf.set_text_color(35, 35, 35)
    pdf.cell(0, 12, "三、住宿概览", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    if hotel_bases:
        for idx, b in enumerate(hotel_bases, 1):
            city = _city_zh(b.get("city", ""))
            area = _area_zh(b.get("area", ""))
            nights = b.get("nights", 1)
            pdf.set_font(zh, "B", 11)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 8, f"基点 {idx}: {area}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font(zh, "", 9)
            pdf.set_text_color(90, 90, 90)
            pdf.cell(0, 6, f"城市: {city}    住 {nights} 晚", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
    else:
        pdf.set_font(zh, "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, "住宿信息待补充", new_x="LMARGIN", new_y="NEXT")

    # ═══════════════ 每日详情 ═══════════════
    for d in data["days"]:
        pdf.add_page()

        # 日标题
        pdf.set_font(zh, "B", 20)
        pdf.set_text_color(35, 35, 35)
        pdf.cell(0, 13, f"Day {d['day_number']}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font(zh, "", 12)
        pdf.set_text_color(70, 70, 70)
        pdf.cell(0, 8, d["theme"], new_x="LMARGIN", new_y="NEXT")

        # 日信息条 — 纯中文，无 key 泄露
        pdf.ln(2)
        pdf.set_font(zh, "", 8)
        pdf.set_text_color(130, 130, 130)
        info_parts = []
        if d["city"]:
            info_parts.append(f"城市: {d['city']}")
        if d["corridor"]:
            info_parts.append(f"走廊: {d['corridor']}")
        if d["day_type"]:
            info_parts.append(d["day_type"])
        if d["intensity"]:
            info_parts.append(f"节奏: {d['intensity']}")
        pdf.cell(0, 5, "  ·  ".join(info_parts), new_x="LMARGIN", new_y="NEXT")

        pdf.ln(2)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        # 活动列表
        for item in d["items"]:
            if item.get("placeholder") and not item.get("meal_type"):
                continue

            icon_map = {"poi": "景", "restaurant": "食", "hotel": "宿", "activity": "玩"}
            icon = icon_map.get(item["type"], "·")
            is_main = item.get("is_main", False)

            # 名称行
            pdf.set_font(zh, "B", 11)
            if is_main:
                pdf.set_text_color(200, 80, 30)
            elif item["type"] == "restaurant":
                pdf.set_text_color(60, 120, 60)
            else:
                pdf.set_text_color(50, 50, 50)

            name = item["name"]
            if item.get("meal_type"):
                ml = _MEAL_ZH.get(item["meal_type"], item["meal_type"])
                name = f"[{ml}] {name}"
            if is_main:
                name = f"★ {name}"

            pdf.cell(8, 7, f"[{icon}]")
            pdf.cell(0, 7, name, new_x="LMARGIN", new_y="NEXT")

            # 位置信息（景点）
            if item["type"] != "restaurant":
                area_d = item.get("area_display") or item.get("area_raw", "")
                if area_d:
                    area_d = _sanitize_text(area_d)
                    pdf.set_font(zh, "", 7)
                    pdf.set_text_color(140, 140, 140)
                    pdf.set_x(18)
                    corr_d = item.get("corridor_display", "")
                    if corr_d:
                        corr_d = _corridor_zh(corr_d) if corr_d in _CORRIDOR_ZH else corr_d
                        corr_d = _sanitize_text(corr_d)
                    loc = area_d
                    if corr_d and corr_d != area_d:
                        loc = f"{area_d} · {corr_d}沿线"
                    pdf.cell(0, 4, loc, new_x="LMARGIN", new_y="NEXT")

            # 餐厅: 走廊+菜系+why_here
            if item["type"] == "restaurant" and not item.get("placeholder"):
                pdf.set_font(zh, "", 7)
                pdf.set_text_color(140, 140, 140)
                pdf.set_x(18)
                parts = []
                sa = item.get("serving_area", "")
                if sa:
                    sa_zh = _corridor_zh(sa) if sa in _CORRIDOR_ZH else _area_zh(sa)
                    sa_zh = _sanitize_text(sa_zh)
                    parts.append(sa_zh)
                cu = item.get("cuisine", "")
                if cu and cu != "other":
                    cu_zh = _CUISINE_ZH.get(cu, cu)
                    cu_zh = _sanitize_text(cu_zh)
                    parts.append(cu_zh)
                wh = item.get("why_here", "")
                if wh:
                    wh = _sanitize_text(wh)
                    parts.append(wh)
                if parts:
                    pdf.cell(0, 4, " · ".join(parts), new_x="LMARGIN", new_y="NEXT")

            # 描述
            desc = item.get("copy") or ""
            if desc and desc != item["name"]:
                desc = _sanitize_text(desc)
                pdf.set_font(zh, "", 8)
                pdf.set_text_color(100, 100, 100)
                pdf.set_x(18)
                pdf.multi_cell(170, 5, desc[:150], new_x="LMARGIN", new_y="NEXT")

            # Tips
            tips = item.get("tips", "")
            if tips:
                tips = _sanitize_text(tips)
                pdf.set_font(zh, "", 7)
                pdf.set_text_color(160, 130, 80)
                pdf.set_x(18)
                pdf.cell(0, 4, f"Tips: {tips}", new_x="LMARGIN", new_y="NEXT")

            pdf.ln(2)

        # Plan B
        corr_raw = d.get("corridor_raw", "")
        if corr_raw:
            pdf.ln(2)
            pdf.set_draw_color(230, 230, 230)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            pdf.set_font(zh, "B", 9)
            pdf.set_text_color(100, 100, 170)
            pdf.cell(0, 6, "[雨天] Plan B（雨天/体力不足）", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font(zh, "", 8)
            pdf.set_text_color(120, 120, 120)

            fallbacks = {
                "namba": "转入难波地下街购物 + 黑门市场觅食",
                "arashiyama": "改去京都站伊势丹百货 + 地下街美食",
                "sakurajima": "USJ 有大量室内项目，雨天影响不大",
                "higashiyama": "改去京都国立博物馆 + 三十三间堂（室内）",
                "osakajo": "改去大阪历史博物馆（天守阁对面，室内）",
                "fushimi": "千本鸟居顶段有遮荫，小雨可行；大雨改去东福寺",
                "shinsekai": "新世界大部分是室内串炸店，雨天反而舒适",
                "nara_park": "奈良国立博物馆（室内）+ 商店街避雨",
                "kawaramachi": "锦市场（有顶棚）+ 百货逛街",
                "gion": "建仁寺（室内枯山水）+ 花见小路有屋檐",
            }
            fb = fallbacks.get(corr_raw, "根据天气灵活调整，可在酒店附近探索")
            pdf.set_x(15)
            pdf.cell(0, 5, f"· {fb}", new_x="LMARGIN", new_y="NEXT")

    # ═══════════════ 五、预约 & 执行提醒 ═══════════════
    pdf.add_page()
    pdf.set_font(zh, "B", 18)
    pdf.set_text_color(35, 35, 35)
    pdf.cell(0, 12, "五、预约 & 执行提醒", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    alerts = [
        ("必须预约", "USJ 环球影城门票 — 建议提前 2 周在官网购买，旺季(4月)当日票大概率售罄"),
        ("建议预约", "热门餐厅 — 道顿堀/祇园区域人气店建议 Tabelog 预约或提前排队"),
        ("无需预约", "伏见稻荷大社 — 24h 开放，建议 7-9 点前往（千本鸟居拍空景窗口）"),
        ("无需预约", "岚山竹林 — 全天开放，7:00-8:00 人最少、光影最美"),
        ("时间敏感", "清水寺 — 6:00 开门。注: 4/10-15 不在春季夜间特别参拜期间(3/27-4/5已结束)，白天正常"),
        ("时间敏感", "USJ 运营时间 — 4月工作日通常 9:00-20:00，出发前确认官网当日时刻"),
        ("交通", "关西机场→京都: HARUKA 特急（75min），买 ICOCA+HARUKA 套票"),
        ("交通", "京都→大阪: 阪急电车 河原町→梅田（45min，400円）"),
        ("交通", "难波→USJ: JR难波→西九条→环球城（约35min）"),
    ]

    color_map = {
        "必须预约": (200, 50, 50), "建议预约": (200, 150, 50),
        "无需预约": (80, 160, 80), "时间敏感": (180, 100, 40),
        "交通": (80, 120, 200),
    }
    for level, content in alerts:
        r, g, b = color_map.get(level, (100, 100, 100))
        pdf.set_font(zh, "B", 8)
        pdf.set_text_color(r, g, b)
        pdf.cell(28, 6, f"[{level}]")
        pdf.set_font(zh, "", 8)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(150, 6, content, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # ═══════════════ 六、出发准备 ═══════════════
    pdf.add_page()
    pdf.set_font(zh, "B", 18)
    pdf.set_text_color(35, 35, 35)
    pdf.cell(0, 12, "六、出发准备清单", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    prep = [
        ("[网络]", "提前购买日本 eSIM（IIJmio / Ubigi），落地开机即用"),
        ("[支付]", "备 3-5 万日元现金；Visa/Master 大部分可用；7-11 ATM 银联取现"),
        ("[交通卡]", "ICOCA 刷地铁公交便利店（也可用全国互通交通卡 Suica 等）。Apple Wallet 可开虚拟卡"),
        ("[行李]", "4月中旬京都 15-22 C，早晚凉需薄外套。舒适步行鞋，日均 1.5-2 万步"),
        ("[App]", "Google Maps / Tabelog / 乗换案内 / Google 翻译"),
        ("[紧急]", "110 警察 / 119 救护 / 中国驻日使馆 03-3403-3388"),
    ]
    for title, content in prep:
        pdf.set_font(zh, "B", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(30, 7, title)
        pdf.set_font(zh, "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 7, content, new_x="LMARGIN", new_y="NEXT")

    # ═══════════════ 尾页 ═══════════════
    pdf.add_page()
    pdf.ln(55)
    pdf.set_font(zh, "B", 18)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 14, "祝旅途愉快！", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font(zh, "", 9)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(0, 7, "本攻略由 Travel AI 自动生成", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "如有疑问请联系客服", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.output(output_path)
    print(f"\n✅ PDF 已生成: {output_path}")
    print(f"   共 {pdf.pages_count} 页")


async def main(output_path: str | None = None, run_id: str | None = None):
    print("📄 正在从数据库加载行程数据...")
    data = await load_plan_data()
    if not data:
        return

    # ── 同源校验 ──
    bundle = data.get("meta", {}).get("evidence_bundle", {})
    if run_id and bundle:
        bundle_rid = bundle.get("run_id", "")
        if bundle_rid != run_id:
            print(f"❌ SOURCE_ID_MISMATCH: expect run_id={run_id[:8]}… got={bundle_rid[:8]}…")
            print("   拒绝导出：回归报告与当前 plan 不是同一次运行")
            return
        print(f"✅ 同源校验通过: run_id={run_id[:8]}…")
    elif not bundle:
        print("⚠️ plan_metadata 无 evidence_bundle，跳过同源校验")

    if not output_path:
        output_path = str(Path(__file__).parent / "kansai_6day_report_v5.pdf")
    generate_pdf(data, output_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="导出关西 6 天行程 PDF")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent / "kansai_6day_report_v5.pdf"),
        help="输出 PDF 路径",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="同源 run_id，用于校验导出与回归报告一致",
    )
    args = parser.parse_args()

    asyncio.run(main(args.output, run_id=args.run_id))
