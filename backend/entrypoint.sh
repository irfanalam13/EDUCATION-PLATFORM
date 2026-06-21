#!/usr/bin/env sh
set -e

cd /app

# Only the web role runs migrations/collectstatic. Celery roles set
# RUN_MIGRATIONS=0 so they don't race each other on startup.
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  sh /app/scripts/wait_for_db.sh
  sh /app/scripts/migrate.sh
  sh /app/scripts/collectstatic.sh
fi

exec "$@"
