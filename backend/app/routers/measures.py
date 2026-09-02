from datetime import datetime, timedelta, timezone as dt_timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import AggregatedPoint, MeasurementOut, MeasuresResponse, Resolution

router = APIRouter(prefix="/api/measures", tags=["measures"])


@router.get("/latest", response_model=MeasurementOut)
def read_latest(db: Session = Depends(get_db)) -> MeasurementOut:
    measurement = crud.get_latest_measurement(db)
    if measurement is None:
        raise HTTPException(status_code=404, detail="No measurements stored yet")
    return measurement


@router.get("", response_model=MeasuresResponse)
def read_range(
    from_: datetime | None = Query(None, alias="from", description="Start of range, ISO-8601"),
    to: datetime | None = Query(None, description="End of range, ISO-8601"),
    db: Session = Depends(get_db),
) -> MeasuresResponse:
    now = datetime.now(dt_timezone.utc)
    to_ts = to or now
    from_ts = from_ or (to_ts - timedelta(days=1))

    if from_ts.tzinfo is None:
        from_ts = from_ts.replace(tzinfo=dt_timezone.utc)
    if to_ts.tzinfo is None:
        to_ts = to_ts.replace(tzinfo=dt_timezone.utc)

    if from_ts > to_ts:
        raise HTTPException(status_code=400, detail="'from' must be before 'to'")

    resolution = crud.choose_resolution(from_ts, to_ts)

    if resolution == "raw":
        rows = crud.get_raw_measurements(db, from_ts, to_ts)
        return MeasuresResponse(
            resolution=Resolution.raw, from_ts=from_ts, to_ts=to_ts, raw=rows
        )

    rows = crud.get_aggregated_measurements(db, from_ts, to_ts)
    return MeasuresResponse(
        resolution=Resolution.aggregated,
        from_ts=from_ts,
        to_ts=to_ts,
        aggregated=[AggregatedPoint(**row) for row in rows],
    )
