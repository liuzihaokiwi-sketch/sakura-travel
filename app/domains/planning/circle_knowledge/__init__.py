"""城市圈知识包 — 实用旅行信息（交通/通信/支付/紧急联系等）"""
from app.domains.planning.circle_knowledge.kansai import get_kansai_knowledge
from app.domains.planning.circle_knowledge.hokkaido import get_hokkaido_knowledge
from app.domains.planning.circle_knowledge.kyushu import get_kyushu_knowledge
from app.domains.planning.circle_knowledge.okinawa import get_okinawa_knowledge
from app.domains.planning.circle_knowledge.chubu import get_chubu_knowledge
from app.domains.planning.circle_knowledge.huadong import get_huadong_knowledge
from app.domains.planning.circle_knowledge.guangfu import get_guangfu_knowledge
from app.domains.planning.circle_knowledge.xinjiang import get_xinjiang_knowledge

_REGISTRY = {
    "kansai_classic": get_kansai_knowledge,
    "kansai_classic_circle": get_kansai_knowledge,
    "kansai": get_kansai_knowledge,
    # 北海道
    "hokkaido": get_hokkaido_knowledge,
    "hokkaido_circle": get_hokkaido_knowledge,
    "hokkaido_nature_circle": get_hokkaido_knowledge,
    "sapporo": get_hokkaido_knowledge,
    # 九州
    "kyushu": get_kyushu_knowledge,
    "kyushu_onsen": get_kyushu_knowledge,
    "kyushu_onsen_circle": get_kyushu_knowledge,
    # 冲绳
    "okinawa": get_okinawa_knowledge,
    "okinawa_island": get_okinawa_knowledge,
    "okinawa_island_circle": get_okinawa_knowledge,
    # 中部
    "chubu": get_chubu_knowledge,
    "chubu_mountain": get_chubu_knowledge,
    "chubu_mountain_circle": get_chubu_knowledge,
    # 华东
    "huadong": get_huadong_knowledge,
    "huadong_circle": get_huadong_knowledge,
    "shanghai": get_huadong_knowledge,
    # 广府
    "guangfu": get_guangfu_knowledge,
    "guangfu_circle": get_guangfu_knowledge,
    "guangzhou": get_guangfu_knowledge,
    # 北疆
    "xinjiang": get_xinjiang_knowledge,
    "xinjiang_yili": get_xinjiang_knowledge,
    "xinjiang_yili_circle": get_xinjiang_knowledge,
}


def get_circle_knowledge(circle_id: str) -> dict | None:
    """获取城市圈知识包，circle_id 不存在时尝试模糊匹配。"""
    fn = _REGISTRY.get(circle_id)
    if fn:
        return fn()
    # 模糊匹配：去掉 _circle/_v1 等后缀再试
    if circle_id:
        normalized = circle_id.lower().replace("_circle", "").rstrip("_v1").rstrip("_v2")
        fn = _REGISTRY.get(normalized)
        if fn:
            return fn()
    return None
