#!/usr/bin/env bash
# On-demand Postgres backup from the host. Writes a gzipped dump to ./backups.
#   ./scripts/backup.sh
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
cd "$(dirname "$0")/.."

mkdir -p backups
TS="$(date +%Y%m%d-%H%M%S)"
OUT="backups/edu-${TS}.sql.gz"

echo "[backup] dumping database -> ${OUT}"
docker compose -f "$COMPOSE_FILE" exec -T db \
  sh -c 'pg_dump -U "${POSTGRES_USER:-edu}" "${POSTGRES_DB:-edu}"' \
  | gzip > "$OUT"

echo "[backup] done ($(du -h "$OUT" | cut -f1))"
