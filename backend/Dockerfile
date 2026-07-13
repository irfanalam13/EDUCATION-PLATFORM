# syntax=docker/dockerfile:1

# ---------- builder: compile/collect wheels into an isolated virtualenv ----------
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build deps only live in this stage; the runtime image stays slim.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Self-contained venv we can copy wholesale into the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# ---------- runtime: minimal image, non-root ----------
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

# curl is used by the container healthcheck; libpq for psycopg at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq5 && rm -rf /var/lib/apt/lists/*

# Create the unprivileged user first so app code is owned correctly on COPY.
RUN addgroup --system app && adduser --system --ingroup app app

# venv stays root-owned — world readable/executable, so `app` can run it without
# a costly recursive chown (which would also duplicate the whole venv layer).
COPY --from=builder /opt/venv /opt/venv

# App code, owned by the runtime user. Only static/media need to be writable.
# Build context is the backend/ directory (see render.yaml / docker-compose), so
# COPY paths are relative to backend/, not the repo root.
COPY --chown=app:app . /app/
RUN chmod +x /app/entrypoint.sh /app/scripts/*.sh 2>/dev/null || true \
    && mkdir -p /app/staticfiles /app/media \
    && chown app:app /app/staticfiles /app/media
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=5 \
  CMD curl -fsS http://127.0.0.1:${PORT:-8000}/healthz/ || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
# Bind to $PORT when the platform injects one (Render/Railway/Heroku route to it);
# fall back to 8000 for docker-compose/nginx where the port is fixed.
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-3} --timeout 120 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --error-logfile -"]
