#!/bin/sh
set -eu

alembic upgrade head

if [ "${INITIALIZE_DEMO:-false}" = "true" ]; then
  python -m app.services.seed --demo
  python -m app.services.seed_analytics --demo
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
