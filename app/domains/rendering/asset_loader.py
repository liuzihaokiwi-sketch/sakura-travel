"""
app/domains/rendering/asset_loader.py

本地素材包加载器（E2）

根据城市圈 + 实体名称查找对应成品图路径。
优先级：entity_media 表 > manifest.json entity_map > 类别默认图。

支持的圈：hokkaido（已有素材），kansai（待接入）。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 素材根目录（相对于项目根）
ASSETS_ROOT = Path("assets")


def _load_manifest(circle_id: str) -> dict:
    """加载城市圈的 manifest.json，缓存在模块级。"""
    path = ASSETS_ROOT / circle_id / "manifest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.debug("manifest load failed %s: %s", circle_id, e)
        return {}


# 模块级缓存
_manifest_cache: dict[str, dict] = {}


def get_manifest(circle_id: str) -> dict:
    if circle_id not in _manifest_cache:
        _manifest_cache[circle_id] = _load_manifest(circle_id)
    return _manifest_cache[circle_id]


def find_asset_url(
    circle_id: str,
    entity_name_zh: str,
    category: str = "spots",
    prefer_wide: bool = False,
) -> Optional[str]:
    """
    根据城市圈 + 实体中文名查找成品图 URL（相对路径）。

    Args:
        circle_id:       如 "hokkaido"
        entity_name_zh:  如 "富良野"、"支笏湖"
        category:        "spots" / "food" / "landmarks" / "onsen" / "streets" / "hotels" / "animals" / "themes"
        prefer_wide:     True 时优先选横版图（-wide 后缀）

    Returns:
        相对路径如 "assets/hokkaido/spots/furano_flowers.png"，找不到返回 None
    """
    manifest = get_manifest(circle_id)
    if not manifest:
        return None

    cat_data = manifest.get("categories", {}).get(category, {})
    entity_map: dict = cat_data.get("entity_map", {})
    files: dict = cat_data.get("files", {})

    # 1. 精确匹配实体名称
    keys = entity_map.get(entity_name_zh, [])
    if not keys:
        # 模糊匹配：实体名是 entity_map key 的子串
        for map_name, map_keys in entity_map.items():
            if entity_name_zh in map_name or map_name in entity_name_zh:
                keys = map_keys
                break

    if keys:
        # 有横版偏好时优先选宽版
        if prefer_wide:
            wide = [k for k in keys if "wide" in k or "横版" in k]
            chosen = wide[0] if wide else keys[0]
        else:
            chosen = keys[0]
        file_path = files.get(chosen)
        if file_path:
            return f"assets/{circle_id}/{file_path}"

    # 2. 返回该类别的第一张默认图
    if files:
        first_key = next(iter(files))
        return f"assets/{circle_id}/{files[first_key]}"

    return None


def find_food_asset(circle_id: str, food_name_zh: str) -> Optional[str]:
    """美食图快捷入口。"""
    return find_asset_url(circle_id, food_name_zh, category="food")


def find_hotel_asset(circle_id: str, hotel_name_zh: str) -> Optional[str]:
    """酒店图快捷入口。"""
    return find_asset_url(circle_id, hotel_name_zh, category="hotels")


def find_animal_asset(circle_id: str, animal_name_zh: str) -> Optional[str]:
    """动物贴纸图（用于 DIY 区域）快捷入口。"""
    return find_asset_url(circle_id, animal_name_zh, category="animals")


def list_circle_assets(circle_id: str, category: Optional[str] = None) -> list[dict]:
    """
    列出城市圈所有成品图（可按类别过滤）。
    返回 [{"key": ..., "url": ..., "category": ...}, ...]
    """
    manifest = get_manifest(circle_id)
    if not manifest:
        return []

    result = []
    cats = manifest.get("categories", {})
    for cat_name, cat_data in cats.items():
        if category and cat_name != category:
            continue
        if cat_name == "raw":
            continue
        for key, file_path in cat_data.get("files", {}).items():
            result.append({
                "key": key,
                "url": f"assets/{circle_id}/{file_path}",
                "category": cat_name,
                "circle_id": circle_id,
            })
    return result
