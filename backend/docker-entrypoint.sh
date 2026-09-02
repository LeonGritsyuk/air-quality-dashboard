#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import time, sys
from sqlalchemy import create_engine, text
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)
for attempt in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database is ready')
        sys.exit(0)
    except Exception as exc:
        print(f'Database not ready yet ({exc}), retrying...')
        time.sleep(2)
print('Database never became ready', file=sys.stderr)
sys.exit(1)
"

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
