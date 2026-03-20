from __future__ import annotations
from typing import Optional
from .lexicon import STAGE_MAP, STAGE_SCORE


def normalize_stage(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = text.strip()
    for k, v in STAGE_MAP.items():
        if k in text:
            return v
    return text


def stage_to_score(stage: Optional[str]) -> Optional[int]:
    if not stage:
        return None
    return STAGE_SCORE.get(stage)
