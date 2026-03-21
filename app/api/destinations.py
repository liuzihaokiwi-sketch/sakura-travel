"""
目的地自动补全 API — Destination Autocomplete

端点：
  GET /destinations/autocomplete?q=xxx&limit=8  → 模糊匹配目的地列表
  GET /destinations/{place_id}                  → 目的地详情

数据源：data/seed/cities.json（本地 JSON，热路径无 DB 查询）
"""
from __future__ import annotations

import json
import logging
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/destinations", tags=["destinations"])

# ── 数据加载（进程级缓存）────────────────────────────────────────────────────

_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "seed" / "cities.json"


@lru_cache(maxsize=1)
def _load_cities() -> list[dict]:
    """一次性加载 cities.json，进程内缓存。"""
    with open(_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cities", [])


# ── 响应模型 ──────────────────────────────────────────────────────────────────

class AirportOut(BaseModel):
    code: str
    name_zh: str
    name_en: str


class StationOut(BaseModel):
    id: str
    name_zh: str
    name_en: str
    lines: list[str]


class DestinationSummary(BaseModel):
    place_id: str
    name_zh: str
    name_en: str
    region: Optional[str] = None
    type: Optional[str] = None
    match_score: float = 1.0   # 0-1，越高越相关


class DestinationDetail(BaseModel):
    place_id: str
    name_zh: str
    name_en: str
    region: Optional[str] = None
    type: Optional[str] = None
    aliases: list[str] = []
    airports: list[AirportOut] = []
    stations: list[StationOut] = []


class AutocompleteResponse(BaseModel):
    query: str
    results: list[DestinationSummary]
    total: int


# ── 搜索逻辑 ──────────────────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    """统一化：去空格 + NFKC 归一 + 小写。"""
    return unicodedata.normalize("NFKC", s).strip().lower()


def _score(city: dict, q_norm: str) -> float:
    """
    计算匹配分数（0-1）。
    精确匹配 name_zh/name_en → 1.0
    前缀匹配 → 0.9
    aliases 完全匹配 → 0.85
    aliases 前缀 → 0.8
    任意包含 → 0.5
    """
    name_zh = _normalize(city.get("name_zh", ""))
    name_en = _normalize(city.get("name_en", ""))
    aliases = [_normalize(a) for a in city.get("aliases", [])]

    if q_norm in (name_zh, name_en):
        return 1.0
    if name_zh.startswith(q_norm) or name_en.startswith(q_norm):
        return 0.9
    if q_norm in aliases:
        return 0.85
    if any(a.startswith(q_norm) for a in aliases):
        return 0.8
    if q_norm in name_zh or q_norm in name_en:
        return 0.5
    if any(q_norm in a for a in aliases):
        return 0.4
    # 机场代码精确匹配
    airport_codes = [ap["code"].lower() for ap in city.get("airports", [])]
    if q_norm in airport_codes:
        return 0.75
    return 0.0


def _search_cities(q: str, limit: int = 8) -> list[tuple[float, dict]]:
    q_norm = _normalize(q)
    if not q_norm:
        return []

    cities = _load_cities()
    scored: list[tuple[float, dict]] = []
    for city in cities:
        s = _score(city, q_norm)
        if s > 0:
            scored.append((s, city))

    # 按分数降序，同分按 name_zh 字母排
    scored.sort(key=lambda x: (-x[0], x[1].get("name_zh", "")))
    return scored[:limit]


# ── 端点 ──────────────────────────────────────────────────────────────────────

@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_destinations(
    q: str = Query(..., min_length=1, max_length=50, description="搜索关键词"),
    limit: int = Query(8, ge=1, le=20, description="返回条数"),
):
    """
    目的地模糊搜索自动补全。
    支持中文（东京）、英文（Tokyo）、别名（TYO）、机场代码（NRT）。
    """
    matches = _search_cities(q=q, limit=limit)

    results = [
        DestinationSummary(
            place_id=city["place_id"],
            name_zh=city.get("name_zh", ""),
            name_en=city.get("name_en", ""),
            region=city.get("region"),
            type=city.get("type"),
            match_score=score,
        )
        for score, city in matches
    ]

    return AutocompleteResponse(query=q, results=results, total=len(results))


@router.get("/{place_id}", response_model=DestinationDetail)
async def get_destination(place_id: str):
    """获取目的地详情，包含机场和主要车站。"""
    cities = _load_cities()
    city = next((c for c in cities if c["place_id"] == place_id), None)
    if not city:
        raise HTTPException(404, f"Destination '{place_id}' not found")

    return DestinationDetail(
        place_id=city["place_id"],
        name_zh=city.get("name_zh", ""),
        name_en=city.get("name_en", ""),
        region=city.get("region"),
        type=city.get("type"),
        aliases=city.get("aliases", []),
        airports=[AirportOut(**ap) for ap in city.get("airports", [])],
        stations=[
            StationOut(
                id=st["id"],
                name_zh=st["name_zh"],
                name_en=st["name_en"],
                lines=st.get("lines", []),
            )
            for st in city.get("stations", [])
        ],
    )
