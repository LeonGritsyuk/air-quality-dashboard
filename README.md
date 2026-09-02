# Home Air Quality Monitor

A small, self-hosted app that polls a local air-quality sensor every 15 minutes, stores the
history in PostgreSQL, and shows it on a clean, responsive dashboard.

```
Air Quality Sensor (LAN)
        |  HTTP GET, every 15 min
        v
   Backend (FastAPI) ---- REST API ----> Frontend (React)
        |
        v
   PostgreSQL
```

## 1. Architecture & key decisions

**Backend — FastAPI + Python.** The collector (a background scheduler) and the REST API live
naturally in the same process and share the same DB models, which keeps a single-user app this
small from needing a second service. FastAPI gives typed request/response validation (Pydantic)
and free OpenAPI docs at `/docs` with very little code.

**Frontend — React + TypeScript + Vite + Tailwind + shadcn-style components + Recharts.**
Recharts is used for the timeseries charts (composable, good defaults for time axes, handles
tooltips/responsive sizing out of the box). UI primitives (`Card`, `Button`, `Badge`, `Skeleton`,
Radix-based `Tabs`) are hand-written in the shadcn/ui pattern (small, local, editable components
rather than a black-box UI kit) so they're easy to restyle.

**Database schema.** Two tables:
- `sensors` — one row per physical device (serial number, model, firmware), rarely changes.
- `measurements` — one row per stored reading, with a **unique index on `bucket_ts`** (see
  below) and an index on `sensor_id`. All range queries filter on `bucket_ts`, which is indexed.

The full sensor payload is optionally stored in a `raw_payload` JSON column
(`STORE_RAW_PAYLOAD=true` by default) purely for debugging — e.g. if a firmware update adds a
field you want to backfill later, or a reading looks wrong and you want to see exactly what the
sensor sent. Set `STORE_RAW_PAYLOAD=false` to skip it if you'd rather keep rows smaller.

**15-minute bucketing.** The sensor response has no timestamp, so the *server* assigns one:
`current_bucket()` takes "now" in the configured `TIMEZONE`, and floors it down to the nearest
quarter-hour (`14:07:32 → 14:00:00`, `14:52:01 → 14:45:00`). That floored, timezone-aware instant
is `bucket_ts`. Because `bucket_ts` has a **unique constraint**, inserts use
`INSERT ... ON CONFLICT (bucket_ts) DO NOTHING` — so a retry, a container restart mid-bucket, or
two overlapping ticks can never create two rows for the same 15-minute window. `measured_at`
separately records the exact instant the HTTP response arrived, kept for debugging even though
queries always key off `bucket_ts`.

**Sensor polling.** An in-process APScheduler `BackgroundScheduler` runs `collect_once()` on a
fixed interval (`COLLECTION_INTERVAL_SECONDS`, default 900s), starting immediately on boot. No
external cron needed — one process, one schedule, `max_instances=1` so ticks can't overlap.
Network errors, timeouts, HTTP errors, and malformed JSON are all caught, logged, and skipped;
the process keeps running and just tries again next tick.

**Timezone handling.** Set once via `TIMEZONE` (default `Europe/Prague`), used by the collector
for bucketing. All timestamps are stored as `timestamptz` (PostgreSQL stores these internally as
UTC + your session/column knows the offset), and the API always returns ISO-8601 with an
explicit offset — so there's a single source of truth for "what time is it" and no ambiguity
crossing the network boundary. The frontend renders using the browser's local timezone, which
for a single-household app normally matches the server's.

**Historical queries & downsampling.** `GET /api/measures?from=...&to=...` picks a resolution
automatically:

| Range span        | Resolution         | Notes                                    |
|--------------------|---------------------|-------------------------------------------|
| ≤ 7 days            | raw (15-min rows)   | Small at this data volume — no need to aggregate |
| 7–90 days           | aggregated, hourly  | `date_trunc('hour', ...)` + avg/min/max in Postgres |
| > 90 days            | aggregated, daily   | `date_trunc('day', ...)` + avg/min/max |

Aggregated buckets keep `avg`/`min`/`max` (not just an average) so the PM2.5 and CO2 charts can
still show a shaded min/max band rather than a flattened line. This is plain SQL `GROUP BY` —
no time-series extension needed at this scale (a single sensor produces ~96 rows/day).

**Docker networking to `192.168.0.245`.** The sensor is a plain device on your LAN, not part of
the Docker Compose network. The default Docker **bridge** network is sufficient: containers can
reach the host's LAN (including other devices on it) through the host's network stack/routing —
no `host` network mode, no extra config needed on Linux, macOS, or Windows, *as long as the
Docker host itself can reach `192.168.0.245`* (i.e. it's physically on the same network/VLAN).
`SENSOR_URL` is fully configurable via `.env`; nothing is hard-coded.

**Why this architecture fits a home deployment.** One Postgres instance, one backend process
(API + collector together), one static frontend behind nginx. No queue, no cache, no
microservices, no auth layer — appropriate for a single household reading its own sensor. It
scales trivially if you add a second sensor later (the schema already supports multiple
`sensors` rows), without needing to change the shape of the system.

## 2. Project structure

```
air-quality/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app + lifespan (starts/stops collector)
│   │   ├── config.py          Settings from env vars
│   │   ├── database.py        SQLAlchemy engine/session
│   │   ├── models.py          ORM models (sensors, measurements)
│   │   ├── schemas.py         Pydantic request/response models
│   │   ├── sensor.py          HTTP client for the physical sensor
│   │   ├── collector.py       Scheduler, bucketing, upsert/dedupe logic
│   │   ├── crud.py            Queries incl. downsampling strategy
│   │   ├── routers/           measures.py, health.py
│   │   └── tests/             pytest suite
│   ├── alembic/                Migrations
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/Dashboard.tsx
    │   ├── components/         MetricCard, TimeseriesChart, RangeSelector, ui/*
    │   ├── lib/                api client, dateRange, thresholds, chartData
    │   └── types/api.ts
    ├── Dockerfile
    └── nginx.conf
```

## 3. Running with Docker Compose (recommended)

```bash
cp .env.example .env
# edit .env — at minimum set SENSOR_URL to your sensor's address
docker compose up -d
```

- Frontend: http://localhost:8080
- Backend API + docs: http://localhost:8000/docs
- The backend container waits for Postgres, runs Alembic migrations automatically, then starts.

## 4. Running locally (without Docker)

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export POSTGRES_HOST=localhost POSTGRES_USER=airquality POSTGRES_PASSWORD=change-me POSTGRES_DB=airquality
export SENSOR_URL=http://192.168.0.245/measures/current
alembic upgrade head
uvicorn app.main:app --reload
```
(Run a local Postgres however you like, e.g. `docker run -e POSTGRES_PASSWORD=change-me -e POSTGRES_USER=airquality -e POSTGRES_DB=airquality -p 5432:5432 postgres:16-alpine`.)

**Frontend**
```bash
cd frontend
npm install
npm run dev
```
Vite proxies `/api` to `http://localhost:8000` in dev (see `vite.config.ts`).

## 5. Database migrations

Migrations use Alembic. The initial schema lives in `backend/alembic/versions/0001_initial.py`
and is applied automatically by the backend container on startup (`alembic upgrade head`, see
`docker-entrypoint.sh`). To create a new migration after changing `app/models.py`:

```bash
cd backend
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

## 6. API reference

**`GET /api/measures/latest`** → the most recent stored measurement, or `404` if none exist yet.

**`GET /api/measures?from=<iso8601>&to=<iso8601>`** → measurements in chronological order.
`from`/`to` default to "last 24 hours" if omitted. Response shape:

```json
{
  "resolution": "raw",
  "from_ts": "2026-09-02T00:00:00+02:00",
  "to_ts": "2026-09-02T23:59:59+02:00",
  "raw": [
    {
      "id": 1,
      "bucket_ts": "2026-09-02T14:00:00+02:00",
      "measured_at": "2026-09-02T14:00:04.812Z",
      "pm01": 3.73, "pm02": 4.2, "pm10": 4.2, "pm003_count": 847,
      "pm02_compensated": 4.18, "atmp": 27.98, "atmp_compensated": 27.98,
      "rhum": 43.74, "rhum_compensated": 43.74, "rco2": 494.43, "wifi": -64
    }
  ],
  "aggregated": []
}
```

For ranges over 7 days, `resolution` becomes `"aggregated"` and `aggregated` is populated
instead, e.g.:

```json
{
  "resolution": "aggregated",
  "from_ts": "2026-08-01T00:00:00+02:00",
  "to_ts": "2026-09-02T00:00:00+02:00",
  "raw": [],
  "aggregated": [
    {
      "bucket_ts": "2026-08-01T00:00:00+02:00",
      "pm02_avg": 4.1, "pm02_min": 2.0, "pm02_max": 9.5,
      "rco2_avg": 510.2, "rco2_min": 420.0, "rco2_max": 780.0,
      "atmp_avg": 22.4, "rhum_avg": 41.0, "sample_count": 96
    }
  ]
}
```

**`GET /api/health`** → `{"status": "ok", "database": "ok", "sensor": "ok", "last_measurement_at": "...", "timezone": "Europe/Prague"}`.
`status` is `"ok"` if the database is reachable (the sensor being briefly offline doesn't count
as unhealthy — that's expected and handled gracefully by the collector).

Full interactive docs (OpenAPI/Swagger) are always available at `/docs` on the backend.

## 7. Configuration reference

| Variable | Default | Purpose |
|---|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | `airquality` / `airquality` / `change-me` | Database credentials |
| `SENSOR_URL` | `http://192.168.0.245/measures/current` | Sensor's HTTP endpoint |
| `COLLECTION_INTERVAL_SECONDS` | `900` | Polling interval |
| `TIMEZONE` | `Europe/Prague` | IANA timezone for bucketing |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:8080` | Allowed frontend origins |
| `STORE_RAW_PAYLOAD` | `true` | Whether to keep the raw sensor JSON per row |
| `FRONTEND_PORT` / `BACKEND_PORT` | `8080` / `8000` | Host ports in Docker Compose |

## 8. Testing

```bash
cd backend
pip install -r requirements.txt
pytest                      # sensor parsing + bucketing run with no DB needed
```

Tests that exercise the database (duplicate-bucket prevention, range queries, API endpoints)
need a reachable PostgreSQL instance, configured via the same `POSTGRES_*` env vars as the app;
they automatically **skip** (not fail) if no database is reachable, so `pytest` works out of the
box. To run the full suite:

```bash
docker run --rm -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=airquality postgres:16-alpine
POSTGRES_HOST=localhost POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres pytest
```

```bash
cd frontend
npm install
npm test         # vitest — date-range logic, threshold classification, chart data mapping
```

## 9. Troubleshooting: sensor unreachable

- Check `GET /api/health` — `"sensor": "unreachable"` confirms the backend can't reach `SENSOR_URL`.
- Confirm the Docker **host** (not just your laptop) can reach the sensor: `curl http://192.168.0.245/measures/current` from the host machine.
- Confirm the sensor and the Docker host are on the same network/VLAN — Docker's bridge network
  routes through the host's network stack, so if the host can't reach the sensor, neither can the container.
- The collector never crashes on a sensor outage — it logs a warning (`docker compose logs backend`)
  and simply tries again on the next tick. Existing historical data stays intact; you'll just see
  a gap for the buckets that were missed.
- Double-check `SENSOR_URL` in `.env` for typos, and that it's the full URL including
  `/measures/current`.
