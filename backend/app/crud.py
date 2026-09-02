"""
Query helpers, including the downsampling strategy for large ranges.

Downsampling strategy
----------------------
Rather than adding a time-series extension, we lean on plain PostgreSQL
`date_trunc` + `GROUP BY`, which is simple and entirely sufficient at this
data volume (a single sensor producing 96 rows/day):

    range length            resolution returned
    ----------------------  -------------------------------
    <= 7 days                raw, 15-minute rows
    >  7 days, <= 90 days     aggregated, 1-hour buckets
    >  90 days                aggregated, 1-day buckets

Each aggregated bucket keeps avg/min/max for the metrics the frontend
charts (PM2.5 and CO2 get min/max bands, the rest just an average) plus a
sample_count, so the frontend can still show a meaningful range rather than
a smoothed-away line.
"""
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Measurement

RAW_THRESHOLD = timedelta(days=7)
HOURLY_THRESHOLD = timedelta(days=90)


def get_latest_measurement(db: Session) -> Measurement | None:
    stmt = select(Measurement).order_by(Measurement.bucket_ts.desc()).limit(1)
    return db.scalar(stmt)


def choose_resolution(from_ts: datetime, to_ts: datetime) -> str:
    span = to_ts - from_ts
    if span <= RAW_THRESHOLD:
        return "raw"
    return "aggregated"


def get_raw_measurements(db: Session, from_ts: datetime, to_ts: datetime) -> list[Measurement]:
    stmt = (
        select(Measurement)
        .where(Measurement.bucket_ts >= from_ts, Measurement.bucket_ts <= to_ts)
        .order_by(Measurement.bucket_ts.asc())
    )
    return list(db.scalars(stmt).all())


def get_aggregated_measurements(db: Session, from_ts: datetime, to_ts: datetime) -> list[dict]:
    span = to_ts - from_ts
    trunc_unit = "hour" if span <= HOURLY_THRESHOLD else "day"

    bucket = func.date_trunc(trunc_unit, Measurement.bucket_ts).label("bucket_ts")
    stmt = (
        select(
            bucket,
            func.avg(Measurement.pm01).label("pm01_avg"),
            func.avg(Measurement.pm02).label("pm02_avg"),
            func.min(Measurement.pm02).label("pm02_min"),
            func.max(Measurement.pm02).label("pm02_max"),
            func.avg(Measurement.pm10).label("pm10_avg"),
            func.avg(Measurement.rco2).label("rco2_avg"),
            func.min(Measurement.rco2).label("rco2_min"),
            func.max(Measurement.rco2).label("rco2_max"),
            func.avg(Measurement.atmp_compensated).label("atmp_avg"),
            func.avg(Measurement.rhum_compensated).label("rhum_avg"),
            func.count(Measurement.id).label("sample_count"),
        )
        .where(Measurement.bucket_ts >= from_ts, Measurement.bucket_ts <= to_ts)
        .group_by(bucket)
        .order_by(bucket.asc())
    )
    rows = db.execute(stmt).mappings().all()
    return [dict(row) for row in rows]
