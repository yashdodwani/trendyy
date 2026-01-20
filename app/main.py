from fastapi import FastAPI

from app.routers import alerts as alerts_router
from app.routers import ml as ml_router


app = FastAPI(title="Aadhaar Trend-Based Alerting API")


app.include_router(alerts_router.router, prefix="/alerts", tags=["alerts"])
app.include_router(ml_router.router, prefix="/alerts", tags=["alerts"])


# Example curl:
#   curl 'http://localhost:8000/health'
#   curl 'http://localhost:8000/alerts/migration'
#   curl 'http://localhost:8000/alerts/infrastructure?month=2023-08'
#   curl 'http://localhost:8000/alerts/migration-ml'


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}
