"""城市圈知识包 — 实用旅行信息（交通/通信/支付/紧急联系等）"""
from app.domains.planning.circle_knowledge.kansai import get_kansai_knowledge

_REGISTRY = {
    "kansai_classic": get_kansai_knowledge,
    "kansai": get_kansai_knowledge,  # 别名
}


def get_circle_knowledge(circle_id: str) -> dict | None:
    """获取城市圈知识包，circle_id 不存在返回 None。"""
    fn = _REGISTRY.get(circle_id)
    return fn() if fn else None
