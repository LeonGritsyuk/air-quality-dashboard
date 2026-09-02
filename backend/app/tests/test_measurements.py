from datetime import datetime, timedelta, timezone as dt_timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app import crud
from app.models import Measurement


def _insert(db_session, bucket_ts, **overrides):
    values = dict(
        bucket_ts=bucket_ts,
        measured_at=bucket_ts,
        pm01=1.0,
        pm02=5.0,
        pm10=6.0,
        pm003_count=100,
        pm02_compensated=5.0,
        atmp=21.0,
        atmp_compensated=21.0,
        rhum=40.0,
        rhum_compensated=40.0,
        rco2=500.0,
        wifi=-60,
    )
    values.update(overrides)
    stmt = (
        pg_insert(Measurement)
        .values(**values)
        .on_conflict_do_nothing(constraint="uq_measurements_bucket_ts")
        .returning(Measurement.id)
    )
    result = db_session.execute(stmt)
    inserted = 1 if result.first() is not None else 0
    db_session.commit()
    return inserted


def test_duplicate_bucket_is_not_inserted_twice(db_session):
    bucket = datetime(2026, 9, 2, 14, 0, tzinfo=dt_timezone.utc)

    first = _insert(db_session, bucket)
    second = _insert(db_session, bucket, pm02=999.0)  # different payload, same bucket

    assert first == 1
    assert second == 0  # silently ignored, no duplicate row

    rows = crud.get_raw_measurements(
        db_session, bucket - timedelta(minutes=1), bucket + timedelta(minutes=1)
    )
    assert len(rows) == 1
    assert rows[0].pm02 == 5.0  # first write wins


def test_get_latest_measurement_returns_most_recent(db_session):
    older = datetime(2026, 9, 2, 13, 0, tzinfo=dt_timezone.utc)
    newer = datetime(2026, 9, 2, 14, 0, tzinfo=dt_timezone.utc)
    _insert(db_session, older, pm02=1.0)
    _insert(db_session, newer, pm02=2.0)

    latest = crud.get_latest_measurement(db_session)

    assert latest.bucket_ts == newer
    assert latest.pm02 == 2.0


def test_get_raw_measurements_returns_chronological_order_within_range(db_session):
    base = datetime(2026, 9, 2, 0, 0, tzinfo=dt_timezone.utc)
    for i in [3, 1, 2]:
        _insert(db_session, base + timedelta(minutes=15 * i), pm02=float(i))

    rows = crud.get_raw_measurements(db_session, base, base + timedelta(hours=2))

    assert [r.pm02 for r in rows] == [1.0, 2.0, 3.0]


def test_choose_resolution_switches_at_seven_days():
    from_ts = datetime(2026, 9, 1, tzinfo=dt_timezone.utc)

    assert crud.choose_resolution(from_ts, from_ts + timedelta(days=1)) == "raw"
    assert crud.choose_resolution(from_ts, from_ts + timedelta(days=7)) == "raw"
    assert crud.choose_resolution(from_ts, from_ts + timedelta(days=8)) == "aggregated"


def test_get_aggregated_measurements_computes_avg_min_max(db_session):
    base = datetime(2026, 9, 2, 10, 0, tzinfo=dt_timezone.utc)
    _insert(db_session, base, pm02=2.0, rco2=400.0)
    _insert(db_session, base + timedelta(minutes=15), pm02=4.0, rco2=600.0)

    rows = crud.get_aggregated_measurements(db_session, base, base + timedelta(hours=1))

    assert len(rows) == 1
    bucket = rows[0]
    assert bucket["pm02_avg"] == 3.0
    assert bucket["pm02_min"] == 2.0
    assert bucket["pm02_max"] == 4.0
    assert bucket["sample_count"] == 2
