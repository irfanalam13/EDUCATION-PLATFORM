#!/usr/bin/env sh
# Production web process. Used outside compose (e.g. Railway/Render) where the
# platform runs a single "start" command. Compose overrides CMD instead.
set -e
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout 120 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile - \
  --error-logfile -
