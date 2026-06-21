#!/usr/bin/env sh
set -e
echo "[collectstatic] gathering static files..."
python manage.py collectstatic --noinput
