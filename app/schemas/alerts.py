from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class URRDFAlert(BaseModel):
    state: str
    district: str
    month: str
    inflow_score: float
    level: str
    predicted_pressure: List[str]
    recommendations: List[str]


class URRDFAlertsResponse(BaseModel):
    month: str
    alerts: List[URRDFAlert]

    class Config:
        json_schema_extra = {  # <- was schema_extra
            "example": {
                "month": "2023-08",
                "alerts": [
                    {
                        "state": "Maharashtra",
                        "district": "Pune",
                        "month": "2023-08",
                        "inflow_score": 1.92,
                        "level": "SURGE",
                        "predicted_pressure": [
                            "PDS",
                            "Public Health",
                            "Housing",
                            "Aadhaar Centers",
                        ],
                            "recommendations": [
                            "Open 2 temporary enrollment/update camps",
                            "Deploy mobile Aadhaar van",
                            "Increase ration shop capacity",
                            "Set up drinking water + shade",
                        ],
                    }
                ],
            }
        }



class AFLBAlert(BaseModel):
    state: str
    district: str
    pincode: str
    month: str
    total_load: int
    stress_score: float
    tier: str
    recommendations: List[str]


class AFLBAlertsResponse(BaseModel):
    month: str
    alerts: List[AFLBAlert]

    class Config:
        json_schema_extra = {  # <- was schema_extra
            "example": {
                "month": "2023-08",
                "alerts": [
                    {
                        "state": "Karnataka",
                        "district": "Bengaluru Urban",
                        "pincode": "560001",
                        "month": "2023-08",
                        "total_load": 12873,
                        "stress_score": 1.76,
                        "tier": "HIGH",
                        "recommendations": [
                            "Add temporary Aadhaar camp (school/community hall)",
                            "Deploy 2-3 extra kits",
                            "Add queue tokens + helpdesk",
                        ],
                    }
                ],
            }
        }


class ErrorResponse(BaseModel):
    detail: str
    debug: Optional[str] = None


# --- ML migration response models ---
class MigrationMLAlert(BaseModel):
    state: str
    district: str
    month: str
    ml_inflow_score: float
    tier: str
    recommendations: List[str]


class MigrationMLAlertsResponse(BaseModel):
    month: str
    alerts: List[MigrationMLAlert]

    class Config:
        json_schema_extra = {
            "example": {
                "month": "2025-12",
                "alerts": [
                    {
                        "state": "Rajasthan",
                        "district": "Balotra",
                        "month": "2025-12",
                        "ml_inflow_score": 5.43,
                        "tier": "SURGE",
                        "recommendations": [
                            "Open 2 temporary enrollment/update camps",
                            "Deploy mobile Aadhaar van",
                            "Increase ration shop capacity",
                            "Set up drinking water + shade",
                        ],
                    }
                ],
            }
        }
