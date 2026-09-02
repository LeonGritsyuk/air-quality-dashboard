from datetime import datetime
from zoneinfo import ZoneInfo

from app.collector import current_bucket


def test_bucket_floors_to_nearest_15_minutes():
    tz = ZoneInfo("Europe/Prague")
    now = datetime(2026, 9, 2, 14, 7, 32, tzinfo=tz)

    bucket = current_bucket(now)

    assert bucket.hour == 14
    assert bucket.minute == 0
    assert bucket.second == 0
    assert bucket.microsecond == 0


def test_bucket_floors_late_in_the_quarter_hour():
    tz = ZoneInfo("Europe/Prague")
    now = datetime(2026, 9, 2, 14, 52, 1, tzinfo=tz)

    bucket = current_bucket(now)

    assert bucket.minute == 45


def test_bucket_is_timezone_aware_in_configured_timezone():
    now = datetime(2026, 9, 2, 14, 7, 32, tzinfo=ZoneInfo("UTC"))

    bucket = current_bucket(now)

    assert bucket.tzinfo is not None
    assert str(bucket.tzinfo) == "Europe/Prague"


def test_exact_bucket_boundary_stays_at_boundary():
    tz = ZoneInfo("Europe/Prague")
    now = datetime(2026, 9, 2, 14, 30, 0, tzinfo=tz)

    bucket = current_bucket(now)

    assert bucket.minute == 30
    assert bucket.second == 0
