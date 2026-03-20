from __future__ import annotations

"""
天气快照采集模块（Open-Meteo，免费无需 API Key）
- fetch_weather:  拉取指定城市某日天气预报
- sync_weather:   拉取 + 写 weather_snapshots 表
"""

from typing import Any, Dict, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.snapshots import record_snapshot
from app.db.models.snapshots import WeatherSnapshot

# Open-Meteo 免费 API
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# 主要城市坐标（lat, lng）
CITY_COORDS: Dict[str, Dict[str, float]] = {
    "tokyo":    {"lat": 35.6762, "lng": 139.6503},
    "osaka":    {"lat": 34.6937, "lng": 135.5023},
    "kyoto":    {"lat": 35.0116, "lng": 135.7681},
    "sapporo":  {"lat": 43.0618, "lng": 141.3545},
    "fukuoka":  {"lat": 33.5904, "lng": 130.4017},
    "naha":     {"lat": 26.2124, "lng": 127.6809},
    "hiroshima":{"lat": 34.3853, "lng": 132.4553},
    "nagoya":   {"lat": 35.1815, "lng": 136.9066},
    "hakone":   {"lat": 35.2323, "lng": 139.1069},
    "nikko":    {"lat": 36.7197, "lng": 139.6981},
}

# WMO 天气代码 → 简单描述
_WMO_CODE_MAP: Dict[int, str] = {
    0: "clear", 1: "mainly_clear", 2: "partly_cloudy", 3: "overcast",
    45: "fog", 48: "rime_fog",
    51: "light_drizzle", 53: "drizzle", 55: "heavy_drizzle",
    61: "light_rain", 63: "rain", 65: "heavy_rain",
    71: "light_snow", 73: "snow", 75: "heavy_snow",
    80: "light_showers", 81: "showers", 82: "heavy_showers",
    95: "thunderstorm", 96: "thunderstorm_hail", 99: "thunderstorm_heavy_hail",
}


async def fetch_weather(city: str, date: str) -> Dict[str, Any]:
    """
    拉取指定城市某日天气预报（Open-Meteo 免费接口）。

    Args:
        city: 城市代码，如 "tokyo"（见 CITY_COORDS）
        date: 日期字符串 "YYYY-MM-DD"

    Returns:
        标准化天气 dict：
        {
          "city": "tokyo",
          "date": "2024-04-01",
          "temp_high_c": 18.5,
          "temp_low_c": 12.1,
          "condition": "partly_cloudy",
          "precipitation_mm": 0.0,
          "raw": {...}   # 原始响应
        }

    Raises:
        ValueError: 城市不在支持列表中
        httpx.HTTPStatusError: API 请求失败
    """
    city_lower = city.lower()
    if city_lower not in CITY_COORDS:
        raise ValueError(
            f"Unsupported city: {city!r}. Supported: {list(CITY_COORDS.keys())}"
        )

    coords = CITY_COORDS[city_lower]

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            _FORECAST_URL,
            params={
                "latitude": coords["lat"],
                "longitude": coords["lng"],
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                "start_date": date,
                "end_date": date,
                "timezone": "Asia/Tokyo",
            },
        )
        resp.raise_for_status()
        raw = resp.json()

    daily = raw.get("daily", {})
    dates = daily.get("time", [])

    if not dates or dates[0] != date:
        # 超出预报范围（Open-Meteo 最多 16 天）
        return {
            "city": city_lower,
            "date": date,
            "temp_high_c": None,
            "temp_low_c": None,
            "condition": None,
            "precipitation_mm": None,
            "raw": raw,
        }

    wmo_code = int(daily.get("weathercode", [0])[0] or 0)
    condition = _WMO_CODE_MAP.get(wmo_code, "unknown")

    return {
        "city": city_lower,
        "date": date,
        "temp_high_c": daily.get("temperature_2m_max", [None])[0],
        "temp_low_c":  daily.get("temperature_2m_min", [None])[0],
        "condition": condition,
        "precipitation_mm": daily.get("precipitation_sum", [0.0])[0],
        "raw": raw,
    }


async def sync_weather(
    session: AsyncSession,
    city: str,
    date: str,
) -> WeatherSnapshot:
    """
    完整天气同步流程：
      1. fetch_weather 拉取数据
      2. record_snapshot 写原始快照
      3. 写 weather_snapshots 表

    Args:
        session: AsyncSession
        city:    城市代码
        date:    日期 "YYYY-MM-DD"

    Returns:
        已 flush 的 WeatherSnapshot 实例
    """
    data = await fetch_weather(city, date)

    # 写原始快照
    await record_snapshot(
        session=session,
        source_name="open_meteo",
        object_type="weather",
        object_id=f"{city}:{date}",
        raw_payload=data["raw"],
        expires_in_days=1,  # 天气数据每日失效
        http_status=200,
        request_url=_FORECAST_URL,
    )

    # 写 weather_snapshots
    snap = WeatherSnapshot(
        city_code=city.lower(),
        forecast_date=date,
        temp_high_c=data["temp_high_c"],
        temp_low_c=data["temp_low_c"],
        condition=data["condition"],
        precipitation_mm=data["precipitation_mm"],
        raw_payload=data["raw"],
    )
    session.add(snap)
    await session.flush()
    return snap
