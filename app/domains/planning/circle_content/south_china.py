"""华南五市城市圈内容包（广州・深圳・珠海・佛山・中山）"""

PERSONA_NAME = "小粤"

DEST_NAME = "华南"

DEST_ALIASES = {
    "guangzhou": "广州",
    "shenzhen": "深圳",
    "zhuhai": "珠海",
    "foshan": "佛山",
    "zhongshan": "中山",
    "south_china": "华南",
}

PERSONA_BIO = """\
你在广州生活多年，对珠三角的早茶文化、夜生活和城中村宝藏小馆了如指掌。
你知道哪条村的肠粉是本地人才去的那种，也知道深圳哪个展览值得专程来一趟。
在你眼里，华南从来不只是转机城市——它是一个被严重低估的旅行目的地。"""

# TODO: 补充华南完整出行准备内容
STATIC_PREP = {
    "title": "出发前准备 / 华南行前须知",
    "sections": [
        {"heading": "📱 上网", "content": "（待补充）"},
        {"heading": "💳 支付", "content": "（待补充：微信/支付宝通用）"},
        {"heading": "🚇 交通", "content": "（待补充：城际高铁建议）"},
        {"heading": "🧳 行李", "content": "（待补充：天气注意事项）"},
        {"heading": "📲 常用 App", "content": "（待补充）"},
        {"heading": "🏥 紧急联系", "content": "（待补充）"},
    ],
}

VISUAL_TRIGGER_TAGS = {
    "night_view", "sea", "sunset", "garden", "architecture",
    "old_town", "market", "port", "wetland",
}
