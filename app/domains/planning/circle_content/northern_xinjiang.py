"""北疆城市圈内容包（乌鲁木齐・喀纳斯・禾木・伊犁）"""

PERSONA_NAME = "小疆"

DEST_NAME = "北疆"

DEST_ALIASES = {
    "urumqi": "乌鲁木齐",
    "kanas": "喀纳斯",
    "hemu": "禾木",
    "yili": "伊犁",
    "nalati": "那拉提",
    "burqin": "布尔津",
    "northern_xinjiang": "北疆",
    "xinjiang": "北疆",
}

PERSONA_BIO = """\
你在北疆跋涉过无数次，喀纳斯的晨雾、禾木村的炊烟、伊犁薰衣草田里的蜜蜂——
这些画面对你来说不是风景，是生活。
你最懂北疆的节奏：路程说远就远，说近就近，关键是把时间用对地方。
你会告诉他们哪段路值得慢慢开，哪个村子只需要停留两小时。"""

# TODO: 补充北疆完整出行准备内容
STATIC_PREP = {
    "title": "出发前准备 / 北疆行前须知",
    "sections": [
        {"heading": "📱 上网", "content": "（待补充：新疆网络注意事项）"},
        {"heading": "💳 支付", "content": "（待补充）"},
        {"heading": "🚗 交通", "content": "（待补充：租车 vs 包车建议）"},
        {"heading": "🧳 行李", "content": "（待补充：防晒/保暖建议）"},
        {"heading": "🏕️ 住宿", "content": "（待补充：牧家乐注意事项）"},
        {"heading": "🏥 紧急联系", "content": "（待补充）"},
    ],
}

VISUAL_TRIGGER_TAGS = {
    "mountain", "lake", "sunset", "grassland", "forest",
    "snow", "valley", "lavender", "steppe", "sunrise",
}
