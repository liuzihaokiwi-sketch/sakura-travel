"""通用城市圈定位辅助·任意区圈 validator 复用。

约定：每个区圈根目录必有 area_registry.json·脚本从输入路径向上找到它。
适用结构：
    japan/kansai/area_registry.json
    japan/kansai/{hotels,restaurants,entities,templates,stops}/...
    japan/kanto/area_registry.json
    china/east_china/area_registry.json
    europe/iberia/area_registry.json

向上找的边界：找到 area_registry.json 即停·没找到走到仓库根停止报错。
"""
from __future__ import annotations
import json
from pathlib import Path


def find_circle_root(start: Path) -> Path:
    """从 start 向上找含 area_registry.json 的目录·返回该目录。

    给 AI 调用者：报错时给清楚的「下一步该怎么办」·不是栈跟踪。
    """
    p = start.resolve()
    if p.is_file():
        p = p.parent
    visited = []
    while True:
        if (p / "area_registry.json").is_file():
            return p
        visited.append(str(p))
        if p.parent == p:
            raise FileNotFoundError(
                f"\n[circle_resolver] 未找到 area_registry.json"
                f"\n  起点：{start}"
                f"\n  向上查询过：{', '.join(visited)}"
                f"\n  约定：每个城市圈根目录（如 japan/kansai/、japan/kanto/、china/east_china/）"
                f"必须有 area_registry.json·里面是 [{{area, type, city}}, ...] 列表。"
                f"\n  解决：(1) 确认输入路径在某区圈下 "
                f"(2) 若是新区圈·先建 area_registry.json"
            )
        p = p.parent


def load_area_registry(circle_root: Path) -> list[dict]:
    """读取区圈 area_registry.json 原始 list·每条 {area, type, city}"""
    return json.loads((circle_root / "area_registry.json").read_text(encoding="utf-8"))


def load_area_set(circle_root: Path) -> set[str]:
    """便捷 set·只取 area 名"""
    return {r["area"] for r in load_area_registry(circle_root)}


def load_city_set(circle_root: Path) -> set[str]:
    """便捷 set·从 registry 推 city 枚举"""
    return {r["city"] for r in load_area_registry(circle_root) if "city" in r}
