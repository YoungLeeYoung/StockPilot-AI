#!/bin/sh
set -eu

echo "Applying database migrations..."
alembic upgrade head

echo "Starting StockPilot AI API..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-2}" \
    --proxy-headers \
    --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}"

