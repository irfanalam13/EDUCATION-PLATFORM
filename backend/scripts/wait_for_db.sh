#!/usr/bin/env sh
# Block until the database accepts connections. Safe no-op for sqlite (dev).
set -e

MAX_TRIES="${DB_WAIT_TRIES:-30}"
i=0
echo "[wait_for_db] waiting for database..."
until python - <<'PY'
import sys
import django
from django.db import connections
from django.db.utils import OperationalError
django.setup()
try:
    connections["default"].ensure_connection()
except OperationalError as exc:
    print(f"  not ready: {exc}")
    sys.exit(1)
PY
do
  i=$((i + 1))
  if [ "$i" -ge "$MAX_TRIES" ]; then
    echo "[wait_for_db] database not reachable after ${MAX_TRIES} tries" >&2
    exit 1
  fi
  sleep 2
done
echo "[wait_for_db] database is ready."
