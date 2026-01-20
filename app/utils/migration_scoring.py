from __future__ import annotations

from typing import Dict, List

import numpy as np


def to_inflow_score(s_log: float, raw_min: float, raw_max: float) -> float:
    """
    Convert log-scale prediction (s_log = log1p(demo_age_17_)) into
    an inflow_score in the 3.0–6.0 range for presentation.

    Parameters
    - s_log: model output (log1p(demo_age_17_))
    - raw_min, raw_max: 5th and 95th percentile raw demo values from training
    """
    raw = np.expm1(s_log)

    # Scale to 0–1
    denom = (raw_max - raw_min) + 1e-9
    x = (raw - raw_min) / denom
    x = float(np.clip(x, 0.0, 1.0))

    # Map to [3.0, 6.0]
    return round(3.0 + (6.0 - 3.0) * x, 2)


def inflow_tier(inflow_score: float, watch: float, surge: float) -> str:
    """
    Map inflow_score (3–6) to a tier label given thresholds.

    Returns one of: "SURGE", "WATCH", "NORMAL".
    """
    if inflow_score >= surge:
        return "SURGE"
    if inflow_score >= watch:
        return "WATCH"
    return "NORMAL"


# Public recommendations mapping used by the migration/URRDF API
RECOMMENDATIONS_MIGRATION: Dict[str, List[str]] = {
    "NORMAL": ["Monitor trends"],
    "WATCH": ["Increase staff shifts for 14 days", "Add multilingual helpdesk"],
    "SURGE": [
        "Open 2 temporary enrollment/update camps",
        "Deploy mobile Aadhaar van",
        "Increase ration shop capacity",
        "Set up drinking water + shade",
    ],
}


def recommendations_for_tier(tier: str) -> List[str]:
    """Return recommendation list for a given tier label (case-insensitive)."""
    return RECOMMENDATIONS_MIGRATION.get(tier.upper(), ["Monitor trends"])


__all__ = [
    "to_inflow_score",
    "inflow_tier",
    "RECOMMENDATIONS_MIGRATION",
    "recommendations_for_tier",
]
