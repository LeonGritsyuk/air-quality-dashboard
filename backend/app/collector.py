"""
Sensor collector
================

Runs on a schedule (APScheduler, in-process - no external cron needed) and,
on every tick:

  1. Computes the current 15-minute "bucket" in the configured timezone.
  2. Requests a fresh reading from the sensor.
  3. Upserts it into `measurements`, keyed by the unique `bucket_ts` column,
     so a retry or an overlapping tick can never create a duplicate row for
     the same bucket (INSERT ... ON CONFLICT DO NOTHING).
  4. Creates/updates the owning `sensors` row from the reading's metadata.

Timestamp / bucketing rules
----------------------------
- "Now" is computed in the configured TIMEZONE (default Europe/Prague), then
  floored down to the nearest 15-minute mark, e.g. 14:07:32 -> 14:00:00,
  14:52:01 -> 14:45:00. That floored, timezone-aware instant is `bucket_ts`
  and is what all range queries key off.
- The sensor's own JSON response has no timestamp field, so it is never
  trusted for timing - `bucket_ts`/`measured_at` are always assigned by this
  server, using its own clock.
- `measured_at` records the actual instant the HTTP response was received,
  which is normally a few seconds after the bucket boundary (or, if the
  process just (re)started mid-bucket, could be several minutes after it -
  that's expected and harmless).
- Failures (timeouts, connection errors, malformed JSON) are logged and
  skipped; the collector keeps running and simply tries again on the next
  tick. A gap in the data is preferable to crashing the service.
"""
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import Measurement, Sensor
from app.sensor import SensorUnavailableError, fetch_current_reading

logger = logging.getLogger("airquality.collector")


def current_bucket(now: datetime | None = None) -> datetime:
    """Floor `now` (or the current time) to the current 15-minute bucket.

    Returns a timezone-aware datetime in the configured TIMEZONE.
    """
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    now = (now or datetime.now(dt_timezone.utc)).astimezone(tz)
    floored_minute = (now.minute // 15) * 15
    return now.replace(minute=floored_minute, second=0, microsecond=0)


def _upsert_sensor(db: Session, serial_no: str | None, model: str | None, firmware: str | None, now: datetime) -> Sensor | None:
    if not serial_no:
        return None
    sensor = db.scalar(select(Sensor).where(Sensor.serial_no == serial_no))
    if sensor is None:
        sensor = Sensor(
            serial_no=serial_no,
            model=model,
            firmware=firmware,
            first_seen_at=now,
            last_seen_at=now,
        )
        db.add(sensor)
        db.flush()
    else:
        sensor.model = model or sensor.model
        sensor.firmware = firmware or sensor.firmware
        sensor.last_seen_at = now
    return sensor


def collect_once() -> None:
    """Poll the sensor once and persist a measurement for the current bucket.

    Safe to call repeatedly / concurrently: duplicate inserts for the same
    bucket are silently ignored at the database level.
    """
    settings = get_settings()
    bucket_ts = current_bucket()
    measured_at = datetime.now(dt_timezone.utc)

    try:
        reading = fetch_current_reading()
    except SensorUnavailableError as exc:
        logger.warning("Sensor unavailable, skipping this tick: %s", exc)
        return

    db = SessionLocal()
    try:
        sensor = _upsert_sensor(
            db, reading.serialno, reading.model, reading.firmware, measured_at
        )

        stmt = (
            pg_insert(Measurement)
            .values(
                bucket_ts=bucket_ts,
                measured_at=measured_at,
                sensor_id=sensor.id if sensor else None,
                pm01=reading.pm01,
                pm02=reading.pm02,
                pm10=reading.pm10,
                pm003_count=reading.pm003Count,
                pm02_compensated=reading.pm02Compensated,
                atmp=reading.atmp,
                atmp_compensated=reading.atmpCompensated,
                rhum=reading.rhum,
                rhum_compensated=reading.rhumCompensated,
                rco2=reading.rco2,
                wifi=reading.wifi,
                raw_payload=reading.model_dump() if settings.store_raw_payload else None,
            )
            .on_conflict_do_nothing(constraint="uq_measurements_bucket_ts")
            .returning(Measurement.id)
        )
        result = db.execute(stmt)
        inserted = result.first() is not None
        db.commit()

        if inserted:
            logger.info("Stored measurement for bucket %s", bucket_ts.isoformat())
        else:
            logger.info(
                "Bucket %s already has a measurement, skipped duplicate", bucket_ts.isoformat()
            )
    except Exception:
        db.rollback()
        logger.exception("Failed to persist measurement, will retry next tick")
    finally:
        db.close()


_scheduler: BackgroundScheduler | None = None


def start_collector() -> BackgroundScheduler:
    """Start the background scheduler. Runs one immediate collection, then
    repeats every COLLECTION_INTERVAL_SECONDS."""
    global _scheduler
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone=ZoneInfo(settings.timezone))
    scheduler.add_job(
        collect_once,
        "interval",
        seconds=settings.collection_interval_seconds,
        next_run_time=datetime.now(dt_timezone.utc),  # run once immediately
        id="sensor_collector",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Collector started: polling %s every %ss (timezone=%s)",
        settings.sensor_url,
        settings.collection_interval_seconds,
        settings.timezone,
    )
    return scheduler


def stop_collector() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
