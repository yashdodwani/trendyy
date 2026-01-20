from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.data_loader import DataValidationError
from app.schemas.alerts import MigrationMLAlert, MigrationMLAlertsResponse, ErrorResponse
from app.services.analytics_service import analytics_service


router = APIRouter()


@router.get(
    "/migration-ml",
    response_model=MigrationMLAlertsResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_migration_ml(month: Optional[str] = Query(None, description="Target month in YYYY-MM format")) -> MigrationMLAlertsResponse:
    """Return ML-predicted migration inflow scores and tiers for districts."""
    try:
        df = analytics_service.predict_migration_model(month=month, top_n=10)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataValidationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if df.empty:
        raise HTTPException(status_code=404, detail="No ML migration alerts available for the requested month")

    response_month = df["month"].iloc[0]

    alerts = [
        MigrationMLAlert(
            state=row["state"],
            district=row["district"],
            month=row["month"],
            ml_inflow_score=float(row["ml_inflow_score"]),
            tier=row["tier"],
            recommendations=list(row["recommendations"]),
        )
        for _, row in df.iterrows()
    ]

    return MigrationMLAlertsResponse(month=response_month, alerts=alerts)

