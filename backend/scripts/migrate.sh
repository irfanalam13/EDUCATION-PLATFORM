#!/usr/bin/env sh
set -e
echo "[migrate] applying database migrations..."
python manage.py migrate --noinput
