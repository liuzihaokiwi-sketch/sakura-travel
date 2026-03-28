"""关西城市圈内容包（京都・大阪・神户・奈良）"""

PERSONA_NAME = "小樱"

DEST_NAME = "关西"

DEST_ALIASES = {
    "kyoto": "京都",
    "osaka": "大阪",
    "kobe": "神户",
    "nara": "奈良",
    "himeji": "姬路",
    "kansai": "关西",
}

PERSONA_BIO = """\
你在京都生活了多年，对关西每个街区了如指掌——
从岚山早晨最安静的时段，到大阪道顿堀深夜最地道的串烧摊，再到神户元町不起眼却好吃到哭的法式小馆。
你特别懂得如何在"不踩坑"和"有惊喜"之间找到平衡。"""

# TODO: 补充关西完整出行准备内容
STATIC_PREP = {
    "title": "出发前准备 / 关西行前须知",
    "sections": [
        {"heading": "📱 上网",
         "content": "（待补充）"},
        {"heading": "💳 支付",
         "content": "（待补充）"},
        {"heading": "🚃 交通卡",
         "content": "（待补充）"},
        {"heading": "🧳 行李",
         "content": "（待补充）"},
        {"heading": "📲 常用 App",
         "content": "（待补充）"},
        {"heading": "🏥 紧急联系",
         "content": "（待补充）"},
    ],
}

VISUAL_TRIGGER_TAGS = {
    "sakura", "night_view", "sea", "mountain", "sunset",
    "temple", "garden", "snow", "shrine", "bamboo",
}
