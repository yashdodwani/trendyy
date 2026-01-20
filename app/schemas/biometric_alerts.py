from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class BiometricIntegrityAlert(BaseModel):
    state: str
    district: str
    pincode: str
    month: str

    enrol_total: int
    bio_total: int

    capture_gap_ratio: float
    capture_gap_tier: str

    imbalance_score: Optional[float] = None
    imbalance_tier: Optional[str] = None

    tags: List[str]
    recommendations: List[str]


class BiometricIntegrityAlertsResponse(BaseModel):
    month: str
    alerts: List[BiometricIntegrityAlert]

    class Config:
        json_schema_extra = {
            "example": {
                "month": "2023-08",
                "alerts": [
                    {
                        "state": "Karnataka",
                        "district": "Bengaluru Urban",
                        "pincode": "560001",
                        "month": "2023-08",
                        "enrol_total": 123,
                        "bio_total": 45,
                        "capture_gap_ratio": 0.63,
                        "capture_gap_tier": "HIGH",
                        "imbalance_score": 0.12,
                        "imbalance_tier": "LOW",
                        "tags": ["CAPTURE_GAP_HIGH", "IMBALANCE_LOW"],
                        "recommendations": [
                            "Run targeted biometric update drives in affected pincodes",
                            "Allocate mobile biometric vans",
                        ],
                    }
                ],
            }
        }


class LostGenerationAlert(BaseModel):
    state: str
    district: str
    month: str

    enrol_age_0_5: int
    bio_age_5_17: int

    fafi_value: int
    fafi_ratio: float
    tier: str

    impact_statement: str
    recommendations: List[str]


class LostGenerationAlertsResponse(BaseModel):
    month: str
    alerts: List[LostGenerationAlert]

    class Config:
        json_schema_extra = {
            "example": {
                "month": "2023-08",
                "alerts": [
                    {
                        "state": "Rajasthan",
                        "district": "Jalore",
                        "month": "2023-08",
                        "enrol_age_0_5": 1200,
                        "bio_age_5_17": 200,
                        "fafi_value": 1000,
                        "fafi_ratio": 0.83,
                        "tier": "HIGH",
                        "impact_statement": "High risk of future authentication failures; urgent action required",
                        "recommendations": [
                            "Schedule school-based biometric update camps",
                            "Deploy mobile biometric vans",
                            "Set 30-day district update target",
                        ],
                    }
                ],
            }
        }
