"""北海道城市圈内容包（札幌・函馆・富良野・小樽）"""

PERSONA_NAME = "小白"

DEST_NAME = "北海道"

DEST_ALIASES = {
    "sapporo": "札幌",
    "hakodate": "函馆",
    "furano": "富良野",
    "otaru": "小樽",
    "niseko": "二世古",
    "abashiri": "网走",
    "hokkaido": "北海道",
}

PERSONA_BIO = """\
你在北海道度过了数个四季，见过富良野薰衣草盛开时连绵到天边的紫，
也在零下二十度的网走湖上看过破冰船划开厚冰的壮观。
你最懂北海道的时令——什么季节去哪里，避开什么时候，是你最拿手的功课。"""

# TODO: 补充北海道完整出行准备内容
STATIC_PREP = {
    "title": "出发前准备 / 北海道行前须知",
    "sections": [
        {"heading": "📱 上网", "content": "（待补充）"},
        {"heading": "💳 支付", "content": "（待补充）"},
        {"heading": "🚗 交通", "content": "（待补充：北海道租车建议）"},
        {"heading": "🧳 行李", "content": "（待补充：分季节穿着）"},
        {"heading": "📲 常用 App", "content": "（待补充）"},
        {"heading": "🏥 紧急联系", "content": "（待补充）"},
    ],
}

VISUAL_TRIGGER_TAGS = {
    "sakura", "night_view", "sea", "mountain", "sunset",
    "lavender", "snow", "farm", "lake", "aurora",
}
