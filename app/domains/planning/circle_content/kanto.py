"""关东城市圈内容包（东京・横滨・镰仓・箱根）"""

PERSONA_NAME = "小雪"

DEST_NAME = "关东"

DEST_ALIASES = {
    "tokyo": "东京",
    "yokohama": "横滨",
    "kamakura": "镰仓",
    "hakone": "箱根",
    "nikko": "日光",
    "kanto": "关东",
}

PERSONA_BIO = """\
你在东京生活多年，从涩谷的潮流街区到镰仓的海边小道，都留下过你的足迹。
你最擅长帮人在这座超级大都市里找到人少、好吃、出片的隐藏路线，
也知道箱根哪家温泉旅馆值得多花那两千块。"""

# TODO: 补充关东完整出行准备内容
STATIC_PREP = {
    "title": "出发前准备 / 关东行前须知",
    "sections": [
        {"heading": "📱 上网", "content": "（待补充）"},
        {"heading": "💳 支付", "content": "（待补充）"},
        {"heading": "🚃 交通卡", "content": "（待补充）"},
        {"heading": "🧳 行李", "content": "（待补充）"},
        {"heading": "📲 常用 App", "content": "（待补充）"},
        {"heading": "🏥 紧急联系", "content": "（待补充）"},
    ],
}

VISUAL_TRIGGER_TAGS = {
    "sakura", "night_view", "sea", "mountain", "sunset",
    "temple", "garden", "snow", "fuji", "shrine",
}
