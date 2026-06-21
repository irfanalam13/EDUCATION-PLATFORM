#!/usr/bin/env bash
# Restore a gzipped pg_dump into the running db container. DESTRUCTIVE.
#   ./scripts/restore.sh backups/edu-20260101-120000.sql.gz
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
cd "$(dirname "$0")/.."

DUMP="${1:-}"
if [ -z "$DUMP" ] || [ ! -f "$DUMP" ]; then
  echo "usage: $0 <path-to-dump.sql.gz>" >&2
  exit 1
fi

read -r -p "This will OVERWRITE the current database. Type 'yes' to continue: " confirm
[ "$confirm" = "yes" ] || { echo "aborted"; exit 1; }

echo "[restore] restoring from ${DUMP}"
gunzip -c "$DUMP" | docker compose -f "$COMPOSE_FILE" exec -T db \
  sh -c 'psql -U "${POSTGRES_USER:-edu}" -d "${POSTGRES_DB:-edu}"'

echo "[restore] done."
