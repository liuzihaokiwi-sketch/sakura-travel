"""
Opus 装配测试用例 — 按 4 屏表单规范设计。

每个用例对应一种真实用户画像，覆盖：
- 4 种风格（经典/约会/出片/亲子）
- 3 种节奏（紧凑/平衡/悠闲）
- 不同天数（4/5/7/9/10 天，测试城市分配和自动扩展规则）
- 不同人员组合（情侣/闺蜜/小家庭/带父母）
- 屏4 可选条件（已预订/去过/特殊要求）

命名规则：TC{编号}_{天数}d_{风格}_{人群}_{特征}
"""

# ── 基础用例（覆盖风格×节奏）─────────────────────────────────────────────

TC01_7d_classic_couple = {
    "_desc": "最典型用户：情侣第一次去关西，7天经典版，什么都没订",
    # 屏1
    "dates": {
        "start": "2026-05-10",
        "end": "2026-05-16",
        "arrival_slot": "afternoon",
        "departure_slot": "morning",
    },
    # 屏2
    "vibe": "classic",
    "party": {"adults": 2, "children": 0, "elderly": 0},
    # 屏3
    "density": "balanced",
    # 屏4（跳过）
    "pre_booked": [],
    "skip_tags": [],
    "skip_entities": [],
    "include_entities": [],
    "notes": "",
}

TC02_5d_romantic_couple = {
    "_desc": "蜜月短途：5天约会感，悠闲，不想太早起",
    "dates": {
        "start": "2026-10-15",
        "end": "2026-10-19",
        "arrival_slot": "afternoon",
        "departure_slot": "afternoon",
    },
    "vibe": "romantic",
    "party": {"adults": 2, "children": 0, "elderly": 0},
    "density": "relaxed",
    "pre_booked": [],
    "skip_tags": [],
    "skip_entities": [],
    "include_entities": [],
    "notes": "不想太早起，每天10点之后出发就好",
}

TC03_7d_photogenic_friends = {
    "_desc": "闺蜜出片团：3人樱花季，紧凑，想拍尽量多好看的地方",
    "dates": {
        "start": "2026-03-28",
        "end": "2026-04-03",
        "arrival_slot": "morning",
        "departure_slot": "evening",
    },
    "vibe": "photogenic",
    "party": {"adults": 3, "children": 0, "elderly": 0},
    "density": "packed",
    "pre_booked": [],
    "skip_tags": [],
    "skip_entities": [],
    "include_entities": [],
    "notes": "希望能赶上樱花",
}

TC04_7d_family_kids = {
    "_desc": "小家庭暑假：夫妻+1娃，亲子感，平衡节奏",
    "dates": {
        "start": "2026-07-20",
        "end": "2026-07-26",
        "arrival_slot": "morning",
        "departure_slot": "afternoon",
    },
    "vibe": "family_fun",
    "party": {"adults": 2, "children": 1, "elderly": 0},
    "density": "balanced",
    "pre_booked": [],
    "skip_tags": [],
    "skip_entities": [],
    "include_entities": [],
    "notes": "",
}

# ── 天数变化（测试城市分配规则）──────────────────────────────────────────

TC05_9d_classic_couple_long = {
    "_desc": "9天经典深度：测试 auto_add 9+加神户/温泉，大阪先京都后",
    "dates": {
        "start": "2026-05-01",
        "end": "2026-05-09",
        "arrival_slot": "morning",
        "departure_slot": "morning",
    },
    "vibe": "classic",
    "party": {"adults": 2, "children": 0, "elderly": 0},
    "density": "balanced",
    "pre_booked": [],
    "skip_tags": [],
    "skip_entities": [],
    "include_entities": [],
    "notes": "",
}

TC06_4d_classic_couple_short = {
    "_desc": "4天极短：晚到早走只有约2.25有效天，测试砍城市和压缩",
    "dates": {
        "start": "2026-06-12",
        "end": "2026-06-15",
        "arrival_slot": "evening",
        "departure_slot": "morning",
    },
    "vibe": "classic",
    "party": {"adults": 2, "children": 0, "elderly": 0},
    "density": "packed",
    "pre_booked": [],
    "skip_tags": [],
    "skip_entities": [],
    "include_entities": [],
    "notes": "",
}

# ── 特殊人群 ─────────────────────────────────────────────────────────────

TC07_7d_classic_elderly = {
    "_desc": "带父母：2成人+2老人，红叶季，悠闲，膝盖不好少爬坡",
    "dates": {
        "start": "2026-11-05",
        "end": "2026-11-11",
        "arrival_slot": "afternoon",
        "departure_slot": "afternoon",
    },
    "vibe": "classic",
    "party": {"adults": 2, "children": 0, "elderly": 2},
    "density": "relaxed",
    "pre_booked": [],
    "skip_tags": [],
    "skip_entities": [],
    "include_entities": [],
    "notes": "父母膝盖不好，尽量少爬坡和楼梯",
}

# ── 屏4 有内容（已预订/跳过/特殊要求）──────────────────────────────────

TC08_7d_classic_prebooked = {
    "_desc": "已订酒店+USJ门票，去过伏见稻荷，不吃生鱼片",
    "dates": {
        "start": "2026-04-10",
        "end": "2026-04-16",
        "arrival_slot": "afternoon",
        "departure_slot": "morning",
    },
    "vibe": "classic",
    "party": {"adults": 2, "children": 0, "elderly": 0},
    "density": "balanced",
    "pre_booked": [
        {"date": "2026-04-10", "item": "大阪南海瑞士酒店", "notes": "已付款不可退"},
        {"date": "2026-04-12", "item": "USJ门票+快速通关", "notes": ""},
    ],
    "skip_entities": ["kyo_fushimi_inari"],
    "skip_tags": [],
    "include_entities": [],
    "notes": "不吃生鱼片",
}

TC09_10d_romantic_honeymoon = {
    "_desc": "蜜月10天：约会感+温泉，测试长行程城市扩展和温泉住宿",
    "dates": {
        "start": "2026-09-15",
        "end": "2026-09-24",
        "arrival_slot": "morning",
        "departure_slot": "evening",
    },
    "vibe": "romantic",
    "party": {"adults": 2, "children": 0, "elderly": 0},
    "density": "relaxed",
    "pre_booked": [],
    "skip_tags": [],
    "skip_entities": [],
    "include_entities": [],
    "notes": "想住一晚温泉旅馆",
}

# ── 季节专用 ─────────────────────────────────────────────────────────────

TC10_7d_classic_koyo = {
    "_desc": "红叶季经典7天：测试季节模板命中（when条件过滤）",
    "dates": {
        "start": "2026-11-20",
        "end": "2026-11-26",
        "arrival_slot": "afternoon",
        "departure_slot": "morning",
    },
    "vibe": "classic",
    "party": {"adults": 2, "children": 0, "elderly": 0},
    "density": "balanced",
    "pre_booked": [],
    "skip_tags": [],
    "skip_entities": [],
    "include_entities": [],
    "notes": "",
}


# ── 汇总 ─────────────────────────────────────────────────────────────────

ALL_CASES = {
    "TC01_7d_classic_couple": TC01_7d_classic_couple,
    "TC02_5d_romantic_couple": TC02_5d_romantic_couple,
    "TC03_7d_photogenic_friends": TC03_7d_photogenic_friends,
    "TC04_7d_family_kids": TC04_7d_family_kids,
    "TC05_9d_classic_couple_long": TC05_9d_classic_couple_long,
    "TC06_4d_classic_couple_short": TC06_4d_classic_couple_short,
    "TC07_7d_classic_elderly": TC07_7d_classic_elderly,
    "TC08_7d_classic_prebooked": TC08_7d_classic_prebooked,
    "TC09_10d_romantic_honeymoon": TC09_10d_romantic_honeymoon,
    "TC10_7d_classic_koyo": TC10_7d_classic_koyo,
}

if __name__ == "__main__":
    from datetime import date
    for name, tc in ALL_CASES.items():
        d = tc["dates"]
        days = (date.fromisoformat(d["end"]) - date.fromisoformat(d["start"])).days + 1
        party = tc["party"]
        ppl = f"{party['adults']}A"
        if party["children"]:
            ppl += f"+{party['children']}C"
        if party["elderly"]:
            ppl += f"+{party['elderly']}E"
        flags = []
        if tc.get("pre_booked"):
            flags.append(f"预订{len(tc['pre_booked'])}项")
        if tc.get("skip_entities"):
            flags.append(f"跳过{len(tc['skip_entities'])}景点")
        if tc.get("notes"):
            flags.append("有备注")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(f"{name}: {days}天 {tc['vibe']} {tc['density']} {ppl}{flag_str}")
        print(f"  {tc['_desc']}")
