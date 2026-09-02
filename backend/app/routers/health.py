import logging

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud
from app.config import get_settings
from app.database import get_db
from app.schemas import HealthStatus

router = APIRouter(prefix="/api", tags=["health"])
logger = logging.getLogger("airquality.health")


@router.get("/health", response_model=HealthStatus)
def health(db: Session = Depends(get_db)) -> HealthStatus:
    settings = get_settings()

    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:
        logger.exception("Database health check failed")
        database_status = "unreachable"

    try:
        response = httpx.get(settings.sensor_url, timeout=3.0)
        response.raise_for_status()
        sensor_status = "ok"
    except Exception:
        sensor_status = "unreachable"

    last_measurement = None
    if database_status == "ok":
        latest = crud.get_latest_measurement(db)
        last_measurement = latest.bucket_ts if latest else None

    overall = "ok" if database_status == "ok" else "degraded"

    return HealthStatus(
        status=overall,
        database=database_status,
        sensor=sensor_status,
        last_measurement_at=last_measurement,
        timezone=settings.timezone,
    )
