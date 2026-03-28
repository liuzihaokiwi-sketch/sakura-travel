"""广东城市圈内容包（广州・潮汕・梅州・肇庆・江门）"""

PERSONA_NAME = "小鹤"

DEST_NAME = "广东"

DEST_ALIASES = {
    "guangzhou": "广州",
    "chaoshan": "潮汕",
    "meizhou": "梅州",
    "zhaoqing": "肇庆",
    "jiangmen": "江门",
    "shantou": "汕头",
    "guangdong": "广东",
}

PERSONA_BIO = """\
你走遍了广东的山川水乡，从潮汕的工夫茶馆到梅州的围龙屋，都是你熟悉的地方。
你特别懂广东在"网红"之外的那一面——老城区的骑楼、开平碉楼里的时光、肇庆星湖的清晨。
你的建议总是带着一种"不是第一次来，但每次都有新发现"的从容。"""

# TODO: 补充广东完整出行准备内容
STATIC_PREP = {
    "title": "出发前准备 / 广东行前须知",
    "sections": [
        {"heading": "📱 上网", "content": "（待补充）"},
        {"heading": "💳 支付", "content": "（待补充）"},
        {"heading": "🚌 交通", "content": "（待补充：城际大巴/高铁建议）"},
        {"heading": "🧳 行李", "content": "（待补充）"},
        {"heading": "🍽️ 饮食", "content": "（待补充：饮食注意事项）"},
        {"heading": "🏥 紧急联系", "content": "（待补充）"},
    ],
}

VISUAL_TRIGGER_TAGS = {
    "night_view", "sea", "sunset", "garden", "architecture",
    "old_town", "watchtower", "mountain", "lake", "heritage",
}
