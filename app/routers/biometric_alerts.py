from __future__ import annotations

from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.core.data_loader import DataValidationError
from app.schemas.biometric_alerts import (
    BiometricIntegrityAlert,
    BiometricIntegrityAlertsResponse,
    LostGenerationAlert,
    LostGenerationAlertsResponse,
)
from app.services.analytics_service import (
    analytics_service,
)

# This router is mounted WITHOUT extra prefix in main.py,
# so its own prefix="/alerts" makes paths:
#   /alerts/biometric-integrity
#   /alerts/lost-generation
router = APIRouter(prefix="/alerts", tags=["Biometric Alerts"])


@router.get(
    "/biometric-integrity",
    response_model=BiometricIntegrityAlertsResponse,
    responses={404: {"model": dict}, 500: {"model": dict}},
)
async def get_biometric_integrity(
    month: Optional[str] = Query(None, description="Target month in YYYY-MM format")
) -> BiometricIntegrityAlertsResponse:
    """[NEW] BIS (Biometric Integrity Score) alerts at pincode level."""
    try:
        df = analytics_service.bis_alerts(month=month)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataValidationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if df.empty:
        raise HTTPException(
            status_code=404, detail="No biometric integrity alerts available for the requested month"
        )

    response_month = df["month"].iloc[0]

    alerts = [
        BiometricIntegrityAlert(
            state=row["state"],
            district=row["district"],
            pincode=str(row["pincode"]),
            month=row["month"],
            enrol_total=int(row["enrol_total"]),
            bio_total=int(row["bio_total"]),
            capture_gap_ratio=float(row["capture_gap_ratio"]),
            capture_gap_tier=row["capture_gap_tier"],
            imbalance_score=(None if pd.isna(row.get("imbalance_score")) else float(row.get("imbalance_score"))),
            imbalance_tier=(row.get("imbalance_tier") if row.get("imbalance_tier") is not None else None),
            tags=list(row["tags"]),
            recommendations=list(row["recommendations"]),
        )
        for _, row in df.iterrows()
    ]

    return BiometricIntegrityAlertsResponse(month=response_month, alerts=alerts)


@router.get(
    "/lost-generation",
    response_model=LostGenerationAlertsResponse,
    responses={404: {"model": dict}, 500: {"model": dict}},
)
async def get_lost_generation(
    month: Optional[str] = Query(None, description="Target month in YYYY-MM format")
) -> LostGenerationAlertsResponse:
    """[NEW] FAFI (Future Authentication Failure Index) alerts at district level."""
    try:
        df = analytics_service.lost_generation_alerts(month=month)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataValidationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if df.empty:
        raise HTTPException(status_code=404, detail="No lost-generation alerts available for the requested month")

    response_month = df["month"].iloc[0]

    alerts = [
        LostGenerationAlert(
            state=row["state"],
            district=row["district"],
            month=row["month"],
            enrol_age_0_5=int(row["enrol_age_0_5"]),
            bio_age_5_17=int(row["bio_age_5_17"]),
            fafi_value=int(row["fafi_value"]),
            fafi_ratio=float(row["fafi_ratio"]),
            tier=row["tier"],
            impact_statement=row["impact_statement"],
            recommendations=list(row["recommendations"]),
        )
        for _, row in df.iterrows()
    ]

    return LostGenerationAlertsResponse(month=response_month, alerts=alerts)


@router.get(
    "/biometric-integrity-old",
    response_model=List[BiometricIntegrityAlert],
)
def biometric_integrity_alerts(
    month: Optional[str] = Query(
        default=None,
        description="Target month in YYYY-MM format. If omitted, uses the latest available month.",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of pincodes to return, sorted by capture gap ratio desc.",
    ),
):
    """
    [NEW: legacy-style] Biometric Integrity Score (BIS) alerts.

    Returns top pincodes with high biometric capture gaps and potential
    equipment / operational imbalance (iris vs fingerprint).
    """
    # Use object-returning service for legacy endpoint
    return analytics_service.get_biometric_integrity_alerts(month=month, limit=limit)


@router.get(
    "/lost-generation-old",
    response_model=List[LostGenerationAlert],
)
def lost_generation_alerts(
    month: Optional[str] = Query(
        default=None,
        description="Target month in YYYY-MM format. If omitted, uses the latest available month.",
    ),
    limit: int = Query(
        default=15,
        ge=1,
        le=100,
        description="Maximum number of districts to return, sorted by FAFI ratio desc.",
    ),
):
    """
    [NEW: legacy-style] Lost Generation / Future Authentication Failure Index (FAFI) alerts.

    Highlights districts where child enrolments are not followed by timely
    biometric updates, raising future authentication failure risk.
    """
    return analytics_service.get_lost_generation_alerts(month=month, limit=limit)
