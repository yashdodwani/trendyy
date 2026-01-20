from fastapi import FastAPI

from app.routers import alerts as alerts_router
from app.routers import ml as ml_router
from app.routers import biometric_alerts as biometric_alerts_router


app = FastAPI(title="Aadhaar Trend-Based Alerting API")

# Legacy routes: migration + infrastructure related (URRDF, AFLB, ML migration)
app.include_router(
    alerts_router.router,
    prefix="/alerts",
    tags=["Migration / Infra Alerts"],
)
app.include_router(
    ml_router.router,
    prefix="/alerts",
    tags=["Migration / Infra Alerts"],
)

# New biometric routes: BIS + Lost Generation
# NOTE: biometric_alerts router itself already uses prefix="/alerts"
# so we mount it at root to avoid "/alerts/alerts/...".
app.include_router(
    biometric_alerts_router.router,
    tags=["Biometric Alerts"],
)


# Example curl:
#   curl 'http://localhost:8000/health'
#   curl 'http://localhost:8000/alerts/migration'
#   curl 'http://localhost:8000/alerts/infrastructure?month=2023-08'
#   curl 'http://localhost:8000/alerts/migration-ml'
#   curl 'http://localhost:8000/alerts/biometric-integrity'
#   curl 'http://localhost:8000/alerts/lost-generation'


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}

