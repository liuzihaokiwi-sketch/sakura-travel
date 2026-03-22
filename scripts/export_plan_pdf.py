"""
export_plan_pdf.py — 从 DB 读取最新 plan，生成 PDF 报告

使用 fpdf2 生成中文 PDF，需要中文字体。
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
                        # 描述在 entity_descriptions 表，这里用 area_name 代替
                        entity_desc = entity.area_name or ""
                
                notes = {}
                if item.notes_zh:
                    try:
                        notes = json.loads(item.notes_zh)
                    except:
                        notes = {"text": item.notes_zh}
                
                item_list.append({
                    "name": notes.get("name", entity_name),
                    "type": item.item_type,
                    "description": entity_desc[:200],
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
            
            summary_parts = (day.day_summary_zh or "").split(" | ")
            day_type = summary_parts[0] if len(summary_parts) > 0 else ""
            corridor = summary_parts[1] if len(summary_parts) > 1 else ""
            intensity = summary_parts[2] if len(summary_parts) > 2 else ""
            
            day_data.append({
                "day_number": day.day_number,
                "city": day.city_code or "",
                "theme": day.day_theme or f"Day {day.day_number}",
                "day_type": day_type,
                "corridor": corridor,
                "intensity": intensity,
                "items": item_list,
            })
        
        return {
            "plan_id": str(plan.plan_id),
            "meta": meta,
            "days": day_data,
        }


def generate_pdf(data: dict, output_path: str):
    """生成 PDF 报告"""
    from fpdf import FPDF
    
    font_path = _ensure_font()
    if not font_path:
        print("⚠️ 找不到中文字体，PDF 中文可能乱码")
    
    class TravelPDF(FPDF):
        def __init__(self):
            super().__init__()
            if font_path and font_path.endswith('.ttf'):
                self.add_font("zh", "", font_path, uni=True)
                self.add_font("zh", "B", font_path, uni=True)
                self._zh = "zh"
            elif font_path and font_path.endswith('.ttc'):
                self.add_font("zh", "", font_path, uni=True)
                self.add_font("zh", "B", font_path, uni=True)
                self._zh = "zh"
            else:
                self._zh = "Helvetica"
        
        def header(self):
            self.set_font(self._zh, "B", 10)
            self.set_text_color(150, 150, 150)
            self.cell(0, 8, "Travel AI - 行程攻略报告", align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)
        
        def footer(self):
            self.set_y(-15)
            self.set_font(self._zh, "", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"第 {self.page_no()} 页", align="C")
    
    pdf = TravelPDF()
    zh = pdf._zh
    
    # ════════════════ 封面 ════════════════
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font(zh, "B", 28)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 15, "关西经典圈 · 6天5晚", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.set_font(zh, "", 14)
    pdf.set_text_color(100, 100, 100)
    # 从 meta.actual_cities 推导，不硬编码
    city_display = {"kyoto": "京都", "osaka": "大阪", "nara": "奈良"}
    actual = data.get("meta", {}).get("actual_cities", ["kyoto", "osaka"])
    cities_str = " · ".join(city_display.get(c, c) for c in actual)
    pdf.cell(0, 10, cities_str, align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(3)
    pdf.set_font(zh, "", 12)
    pdf.cell(0, 8, "情侣 · 中等预算 · 文化美食", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "2026年4月10日 - 4月15日", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(20)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    
    pdf.ln(10)
    meta = data.get("meta", {})
    pdf.set_font(zh, "", 10)
    pdf.set_text_color(120, 120, 120)
    hotel_bases = meta.get("hotel_bases", [])
    if hotel_bases:
        base_str = " + ".join(f"{city_display.get(b['city'],b['city'])} {b['nights']}晚" for b in hotel_bases)
        pdf.cell(0, 6, f"住宿: {base_str}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"策略: {meta.get('hotel_strategy', '')}", align="C", new_x="LMARGIN", new_y="NEXT")
    
    # ════════════════ 总览页 ════════════════
    pdf.add_page()
    pdf.set_font(zh, "B", 18)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "行程总览", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    # 总览表格
    pdf.set_font(zh, "B", 10)
    pdf.set_fill_color(245, 245, 245)
    col_w = [20, 30, 55, 45, 40]
    headers = ["天", "城市", "主题", "走廊", "节奏"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 8, h, border=1, fill=True, align="C")
    pdf.ln()
    
    pdf.set_font(zh, "", 9)
    for d in data["days"]:
        pdf.set_text_color(50, 50, 50)
        pdf.cell(col_w[0], 7, str(d["day_number"]), border=1, align="C")
        pdf.cell(col_w[1], 7, d["city"], border=1, align="C")
        
        theme_text = d["theme"][:18]
        pdf.cell(col_w[2], 7, theme_text, border=1)
        pdf.cell(col_w[3], 7, d["corridor"], border=1, align="C")
        pdf.cell(col_w[4], 7, d["intensity"], border=1, align="C")
        pdf.ln()
    
    pdf.ln(8)
    
    # 设计理念
    pdf.set_font(zh, "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, "设计理念", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(zh, "", 10)
    pdf.set_text_color(60, 60, 60)
    
    # 从 meta 动态生成设计理念
    brief_items = [
        "路线策略: 京都前段深度文化 + 大阪后段都市美食，由静入动",
    ]
    if hotel_bases:
        base_brief = " + ".join(f"{city_display.get(b['city'],b['city'])} {b.get('area','')} {b['nights']}晚" for b in hotel_bases)
        brief_items.append(f"住法策略: {base_brief}")
    brief_items += [
        "节奏原则: 到达日轻启动，全日深游穿插，返程日轻收尾",
        "预算分配: 文化体验为主，美食集中道顿堀夜间，控制交通成本",
    ]
    for item in brief_items:
        pdf.cell(5, 6, "·")
        pdf.cell(0, 6, item, new_x="LMARGIN", new_y="NEXT")
    
    # 出发准备
    pdf.ln(8)
    pdf.set_font(zh, "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, "出发前准备", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(zh, "", 9)
    pdf.set_text_color(60, 60, 60)
    
    prep = [
        ("eSIM & 网络", "提前购买日本 eSIM（IIJmio / Ubigi），落地开机即用"),
        ("支付", "备 3-5 万日元现金；Visa/Master 大部分可用；7-11 ATM 支持银联"),
        ("交通卡", "Suica/PASMO 可刷地铁、公交、便利店。Apple Wallet 可开虚拟 Suica"),
        ("行李", "日本室内暖气足，外套里穿薄。带舒适步行鞋，日均 1.5-2 万步"),
        ("常用 App", "Google Maps · Tabelog · 乗換案内 · Google 翻译"),
        ("紧急联系", "110 警察 / 119 救护 · 中国驻日使馆 03-3403-3388"),
    ]
    for title, content in prep:
        pdf.set_font(zh, "B", 9)
        pdf.cell(35, 6, title)
        pdf.set_font(zh, "", 9)
        pdf.cell(0, 6, content, new_x="LMARGIN", new_y="NEXT")
    
    # ════════════════ 每日详情 ════════════════
    for d in data["days"]:
        pdf.add_page()
        
        # 日标题
        pdf.set_font(zh, "B", 18)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 12, f"Day {d['day_number']}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font(zh, "", 13)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 8, d["theme"], new_x="LMARGIN", new_y="NEXT")
        
        # 日信息条
        pdf.ln(2)
        pdf.set_font(zh, "", 9)
        pdf.set_text_color(120, 120, 120)
        info_parts = []
        if d["city"]:
            info_parts.append(f"住: {d['city']}")
        if d["corridor"]:
            info_parts.append(f"走廊: {d['corridor']}")
        if d["day_type"]:
            info_parts.append(f"类型: {d['day_type']}")
        if d["intensity"]:
            info_parts.append(f"节奏: {d['intensity']}")
        pdf.cell(0, 6, "  |  ".join(info_parts), new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(3)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # 活动列表
        for item in d["items"]:
            if item["placeholder"] and not item["meal_type"]:
                continue
            
            # 类型图标
            icon_map = {
                "poi": "景",
                "restaurant": "食",
                "hotel": "宿",
                "activity": "玩",
            }
            icon = icon_map.get(item["type"], "·")
            
            # 主驱动标记
            is_main = item.get("is_main", False)
            
            # 名称行
            pdf.set_font(zh, "B", 11)
            if is_main:
                pdf.set_text_color(200, 80, 30)  # 橙色标记主活动
            else:
                pdf.set_text_color(50, 50, 50)
            
            name = item["name"]
            if item["meal_type"]:
                meal_zh = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}.get(item["meal_type"], item["meal_type"])
                name = f"[{meal_zh}] {name}"
            if is_main:
                name = f"★ {name}"
            
            pdf.cell(8, 7, f"[{icon}]")
            pdf.cell(0, 7, name, new_x="LMARGIN", new_y="NEXT")
            
            # 区域 + 走廊信息 (景点)
            area_d = item.get("area_display", "")
            if area_d and item["type"] != "restaurant":
                pdf.set_font(zh, "", 8)
                pdf.set_text_color(130, 130, 130)
                pdf.set_x(18)
                corr_d = item.get("corridor_display", "")
                loc_str = area_d
                if corr_d and corr_d != area_d:
                    loc_str = f"{area_d} · {corr_d}沿线"
                pdf.cell(0, 5, loc_str, new_x="LMARGIN", new_y="NEXT")

            # 餐厅: 区域 + why_here + cuisine
            if item["type"] == "restaurant" and not item.get("placeholder"):
                pdf.set_font(zh, "", 8)
                pdf.set_text_color(130, 130, 130)
                pdf.set_x(18)
                parts = []
                sa = item.get("serving_area", "")
                if sa:
                    parts.append(sa)
                cu = item.get("cuisine", "")
                if cu and cu != "other":
                    cuisine_zh = {"sushi": "寿司", "ramen": "拉面", "yakiniku": "烧肉", "tempura": "天妇罗",
                                  "kushikatsu": "串炸", "yakitori": "烧鸟", "takoyaki": "章鱼烧",
                                  "okonomiyaki": "大阪烧", "kaiseki": "怀石", "cafe": "咖啡"}.get(cu, cu)
                    parts.append(cuisine_zh)
                wh = item.get("why_here", "")
                if wh:
                    parts.append(wh)
                if parts:
                    pdf.cell(0, 5, " · ".join(parts), new_x="LMARGIN", new_y="NEXT")

            # 描述
            desc = item.get("copy") or ""
            if desc and desc != item["name"]:
                pdf.set_font(zh, "", 9)
                pdf.set_text_color(100, 100, 100)
                pdf.set_x(18)
                pdf.multi_cell(170, 5, desc[:150], new_x="LMARGIN", new_y="NEXT")
            
            # Tips
            tips = item.get("tips", "")
            if tips:
                pdf.set_font(zh, "", 8)
                pdf.set_text_color(150, 120, 80)
                pdf.set_x(18)
                pdf.cell(0, 5, f"Tips: {tips}", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(3)
        
        # 如果有走廊信息，加 Plan B
        if d["corridor"]:
            pdf.ln(3)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            pdf.set_font(zh, "B", 10)
            pdf.set_text_color(100, 100, 180)
            pdf.cell(0, 7, "Plan B（雨天/体力不足时）", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font(zh, "", 9)
            pdf.set_text_color(120, 120, 120)
            
            fallbacks = {
                "namba": "转入难波地下街购物 + 黑门市场觅食",
                "arashiyama": "改去京都站伊势丹百货 + 地下街美食",
                "sakurajima": "USJ 有大量室内项目，雨天影响不大",
                "higashiyama": "改去京都国立博物馆 + 三十三间堂（室内）",
                "osakajo": "改去大阪历史博物馆（天守阁对面，室内）",
                "fushimi": "千本�的居顶段有遮荫，小雨可行；大雨改去东福寺",
                "shinsekai": "新世界大部分是室内串炸店，雨天反而舒适",
            }
            fb = fallbacks.get(d["corridor"], "根据天气灵活调整，可在酒店附近探索")
            pdf.set_x(15)
            pdf.cell(0, 6, f"· {fb}", new_x="LMARGIN", new_y="NEXT")
    
    # ════════════════ 预约提醒页 ════════════════
    pdf.add_page()
    pdf.set_font(zh, "B", 18)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "预约 & 注意事项", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    pdf.set_font(zh, "", 10)
    pdf.set_text_color(60, 60, 60)
    
    alerts = [
        ("必须预约", "USJ 环球影城门票 — 建议提前 2 周在官网购买，旺季当日票可能售罄"),
        ("建议预约", "热门餐厅 — 道顿堀/祇园区域人气店建议 Tabelog 预约或提前排队"),
        ("无需预约", "伏见稻荷大社 — 24 小时开放，建议清晨前往避开人潮"),
        ("无需预约", "岚山竹林 — 全天开放，早上 7-8 点人最少，光影最美"),
        ("无需预约", "清水寺 — 6:00 开门，建议开门即到，避开旅行团"),
        ("交通提示", "关西机场 → 京都：推荐 HARUKA 特急（75分钟），提前买 ICOCA+HARUKA 套票"),
        ("交通提示", "京都 → 大阪：推荐阪急电车河原町→梅田（45分钟，400日元）"),
    ]
    
    for level, content in alerts:
        color_map = {
            "必须预约": (200, 50, 50),
            "建议预约": (200, 150, 50),
            "无需预约": (80, 160, 80),
            "交通提示": (80, 120, 200),
        }
        r, g, b = color_map.get(level, (100, 100, 100))
        
        pdf.set_font(zh, "B", 9)
        pdf.set_text_color(r, g, b)
        pdf.cell(30, 7, f"[{level}]")
        pdf.set_font(zh, "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(150, 7, content, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    
    # ════════════════ 尾页 ════════════════
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font(zh, "B", 16)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 12, "祝旅途愉快！", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font(zh, "", 10)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, "本攻略由 Travel AI 自动生成", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "城市圈决策引擎 v1 · City Circle Pipeline", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Plan: {data['plan_id'][:8]}...", align="C", new_x="LMARGIN", new_y="NEXT")
    
    # 保存
    pdf.output(output_path)
    print(f"\n✅ PDF 已生成: {output_path}")
    print(f"   共 {pdf.pages_count} 页")


async def main():
    print("📄 正在从数据库加载行程数据...")
    data = await load_plan_data()
    if not data:
        return
    
    print(f"   {len(data['days'])} 天行程数据已加载")
    
    output = str(Path(__file__).parent / "kansai_6day_report_v2.pdf")
    generate_pdf(data, output)


asyncio.run(main())
