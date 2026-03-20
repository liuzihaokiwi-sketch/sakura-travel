from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SourceMeta(BaseModel):
    source_name: str
    source_url: str
    fetched_at: str
    parser_version: str = "1.0"


class CityBloomObservation(BaseModel):
    city_name: str
    prefecture_region: Optional[str] = None
    bloom_date: Optional[str] = None
    full_bloom_date: Optional[str] = None
    bloom_observed: bool = False
    full_bloom_observed: bool = False
    variety: Optional[str] = None
    source_meta: SourceMeta


class SpotForecast(BaseModel):
    spot_name: str
    city_name: Optional[str] = None
    prefecture: Optional[str] = None
    forecast_bloom_date: Optional[str] = None
    forecast_full_bloom_date: Optional[str] = None
    current_stage: Optional[str] = None
    flowering_meter: Optional[int] = None
    best_viewing_start: Optional[str] = None
    best_viewing_end: Optional[str] = None
    festival_start: Optional[str] = None
    festival_end: Optional[str] = None
    illumination_start: Optional[str] = None
    illumination_end: Optional[str] = None
    confidence: Optional[int] = None
    extra: Dict[str, Any] = Field(default_factory=dict)
    source_meta: SourceMeta


class FusedCityTruth(BaseModel):
    city_name: str
    year: int
    bloom_date: Optional[str] = None
    full_bloom_date: Optional[str] = None
    truth_source: str
    confidence: int
    source_refs: List[str]


class FusedSpotTruth(BaseModel):
    spot_name: str
    city_name: Optional[str] = None
    forecast_bloom_date: Optional[str] = None
    forecast_full_bloom_date: Optional[str] = None
    current_stage: Optional[str] = None
    best_viewing_start: Optional[str] = None
    best_viewing_end: Optional[str] = None
    confidence: int
    source_refs: List[str]
