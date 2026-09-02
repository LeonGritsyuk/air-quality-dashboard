from datetime import datetime, timedelta, timezone as dt_timezone

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.tests.test_measurements import _insert


def _client(db_session):
    # Lifespan (which starts the background collector) only runs when the
    # TestClient is used as a context manager, so a plain instantiation here
    # keeps these tests focused on the HTTP layer only.
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_latest_returns_404_when_empty(db_session):
    for client in _client(db_session):
        response = client.get("/api/measures/latest")
        assert response.status_code == 404


def test_latest_returns_most_recent_measurement(db_session):
    bucket = datetime(2026, 9, 2, 12, 0, tzinfo=dt_timezone.utc)
    _insert(db_session, bucket, pm02=7.5)

    for client in _client(db_session):
        response = client.get("/api/measures/latest")
        assert response.status_code == 200
        assert response.json()["pm02"] == 7.5


def test_range_query_returns_raw_points_in_chronological_order(db_session):
    base = datetime(2026, 9, 2, 0, 0, tzinfo=dt_timezone.utc)
    _insert(db_session, base + timedelta(minutes=30), pm02=2.0)
    _insert(db_session, base, pm02=1.0)

    for client in _client(db_session):
        response = client.get(
            "/api/measures",
            params={
                "from": base.isoformat(),
                "to": (base + timedelta(hours=1)).isoformat(),
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["resolution"] == "raw"
        assert [p["pm02"] for p in body["raw"]] == [1.0, 2.0]


def test_range_query_over_a_week_returns_aggregated(db_session):
    base = datetime(2026, 8, 1, 0, 0, tzinfo=dt_timezone.utc)
    _insert(db_session, base, pm02=1.0)

    for client in _client(db_session):
        response = client.get(
            "/api/measures",
            params={
                "from": base.isoformat(),
                "to": (base + timedelta(days=10)).isoformat(),
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["resolution"] == "aggregated"
        assert len(body["raw"]) == 0


def test_range_query_rejects_inverted_range(db_session):
    for client in _client(db_session):
        response = client.get(
            "/api/measures",
            params={"from": "2026-09-02T10:00:00Z", "to": "2026-09-01T10:00:00Z"},
        )
        assert response.status_code == 400
