"""九州知识包 — 九州温泉圈实用信息"""
from __future__ import annotations
from typing import Any


def get_kyushu_knowledge() -> dict[str, Any]:
    return {
        "circle_id": "kyushu_onsen",
        "version": "v1.0",
        "sections": {
            "airport_transport": _airport_transport(),
            "ic_card": _ic_card(),
            "communication": _communication(),
            "luggage": _luggage(),
            "payment": _payment(),
            "useful_apps": _useful_apps(),
            "emergency": _emergency(),
            "seasonal_tips": _seasonal_tips(),
        },
    }


def _airport_transport() -> dict:
    return {
        "title": "机场 → 市区交通",
        "items": [
            "【福冈机场(FUK)→博多/天神】",
            "地铁空港线：福冈机场→博多5分钟/¥260，→天神11分钟/¥310。日本最方便的机场。",
            "国际线→国内线需免费接驳巴士约15分钟。",
            "【北九州机场(KKJ)→小仓】",
            "巴士约33分钟/¥710。适合去别府/由布院方向。",
            "【长崎机场(NGS)→长崎市区】",
            "巴士约43分钟/¥1000。",
            "【�的儿岛机场(KOJ)→鹿儿岛市区】",
            "巴士约38分钟/¥1300。",
        ],
        "tips": [
            "福冈机场是九州游的首选进出口，地铁直达市区极为便利",
            "别府/由布院方向建议博多坐JR音速号（ソニック）约2小时",
            "长崎方向建议博多坐JR海鸥号（かもめ）约2小时（2022年开通西九州新干线后约1.5小时）",
        ],
    }


def _ic_card() -> dict:
    return {
        "title": "IC 卡与交通 Pass",
        "items": [
            "【SUGOCA卡（JR九州）】九州版 IC 卡，全九州 JR/地铁/巴士/便利店通用。",
            "与 ICOCA/Suica 互通，已有其他 IC 卡无需另购。",
            "【JR九州铁路周游券（外国人专享）】",
            "北九州3日¥8500/5日¥10000 — 覆盖博多-别府-由布院-长崎-�的儿岛。",
            "全九州3日¥15000/5日¥18000 — 含鹿儿岛-指宿-宫崎。",
            "可乘坐指定席，含特色列车（由布院之森/指宿玉手箱号等）。",
            "【SUNQ PASS（巴士通票）】",
            "北九州3日¥8000/全九州3日¥11000 — 高速巴士+路线巴士无限乘。",
            "适合不走 JR 线路的巴士旅行。",
        ],
        "tips": [
            "由布院之森极热门，建议提前在JR九州官网预约指定席",
            "JR 周游券在博多站绿窗口（みどりの窓口）兑换，需护照",
        ],
    }


def _communication() -> dict:
    return {
        "title": "通信方案",
        "items": [
            "SIM 卡/eSIM：福冈机场国际线到达厅有售，推荐 IIJmio/Sakura Mobile。",
            "Wi-Fi 路由器：可在机场取/还，适合多人共用。",
            "免费 Wi-Fi：JR 九州车站、博多运河城、各大温泉旅馆大多提供。",
        ],
        "tips": [
            "别府/由布院部分温泉区域信号较弱，提前下载离线地图",
        ],
    }


def _luggage() -> dict:
    return {
        "title": "行李寄存",
        "items": [
            "博多站：站内 coin locker 大量，大件¥600-800/天。",
            "别府/由布院：建议先寄行李到酒店再出游。JR 站有少量 locker。",
            "TA-Q-BIN 行李寄送：酒店→酒店隔日达约¥1500-2500/件。",
        ],
        "tips": [
            "九州各城市间移动频繁时，善用 TA-Q-BIN 省体力",
        ],
    }


def _payment() -> dict:
    return {
        "title": "支付方式",
        "items": [
            "IC 卡（SUGOCA/ICOCA）：便利店/车站/连锁餐厅普及。",
            "信用卡：大型店铺和酒店基本都收 VISA/Mastercard。",
            "现金：温泉旅馆、屋台、地方小店仍以现金为主。建议携带¥30000-50000现金。",
            "PayPay（电子支付）：日本最流行的 QR 支付，外国游客可注册使用。",
        ],
        "tips": [
            "别府/由布院的温泉和小店现金使用率极高",
            "博多屋台几乎全部只收现金",
        ],
    }


def _useful_apps() -> dict:
    return {
        "title": "推荐 App",
        "items": [
            "Google Maps — 日本公交导航最准确",
            "JR 九州 App — 列车时刻/指定席预约/周游券管理",
            "食べログ（Tabelog） — 餐厅评分",
            "PayPay — 电子支付",
        ],
        "tips": [],
    }


def _emergency() -> dict:
    return {
        "title": "紧急联系",
        "items": [
            "警察：110 / 火警·救护车：119",
            "JNTO 旅游热线（英/中/韩）：050-3816-2787（24小时）",
            "中国驻福冈总领事馆：092-713-1121（工作日 9:00-12:00, 14:00-17:30）",
            "管辖范围：福冈、佐贺、大分、熊本、鹿儿岛、宫崎",
        ],
        "tips": [
            "温泉区烫伤请立即冷水冲洗，严重时拨 119",
            "火山活动区（阿苏）注意当日喷发警报等级",
        ],
    }


def _seasonal_tips() -> dict:
    return {
        "title": "季节贴士",
        "items": [
            "春（3-5月）：福� �的冈樱花3月底-4月初；温泉+花见组合最佳",
            "夏（6-8月）：梅雨6月中-7月中；博多祇园山笠（7月）；花火大会（8月）",
            "秋（9-11月）：九州温泉+红叶黄金期；由布院金鳞湖晨雾最美",
            "冬（12-2月）：温泉旺季；别府/由布院最有氛围；长崎灯笼节（1-2月）",
        ],
        "tips": [
            "台风季（8-10月）可能影响交通，建议买旅行保险",
            "由布院之森冬季减班，注意确认时刻表",
        ],
    }
