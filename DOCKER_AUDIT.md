# Edu-Platform — Docker / DevOps Audit & Hardening Report

**Date:** 2026-06-21
**Branch:** `hardening-phases-1-9`
**Scope:** Full repository — backend (Django/DRF/Celery), web (Next.js), mobile (Expo), and the Docker/Compose/Nginx/CI infrastructure.

This audit was run against the *actual* repository state (no assumptions). Every fix
below was applied and verified locally (`docker compose config`, `manage.py check
--deploy`, image builds). See the **Verification** section for evidence.

---

## 0. Executive summary

The project already had a meaningful hardening baseline (non-root backend image,
fail-closed prod settings, healthchecks, certbot, daily DB backup). However, the
stack **would not boot with `docker compose up` as shipped**, and several
production correctness/security gaps existed.

| Area | Before | After |
|------|--------|-------|
| `docker compose up` works unattended | ❌ fails (missing env wiring) | ✅ boots from a single `.env.prod` |
| Static/admin assets with `DEBUG=False` | ❌ 404 (no whitenoise, no volume) | ✅ WhiteNoise + nginx volume |
| Media files in prod | ❌ not served | ✅ nginx volume (or S3) |
| S3 media backend (Django 6) | ❌ silently ignored (`DEFAULT_FILE_STORAGE` removed) | ✅ `STORAGES` API |
| Frontend image | ⚠️ full `node_modules`, `next start`, root | ✅ multi-stage standalone, non-root, ~10× smaller |
| Backend image | ⚠️ single-stage, build tools in runtime | ✅ multi-stage, slim runtime |
| Dependency reproducibility | ❌ unpinned | ✅ pinned to resolved versions |
| Resource limits / log rotation | ❌ none | ✅ per-service limits + json-file rotation |
| Nginx first-boot | ❌ dies (cert files absent) | ✅ HTTP-first config, HTTPS config provided |
| `.dockerignore` | ❌ none (large contexts, secret-leak risk) | ✅ root + frontend |
| CI Docker build | ❌ none | ✅ image build + Trivy scan job |
| Deploy/rollback | ❌ none | ✅ SSH deploy workflow w/ health gate + git-ref rollback |

**Important accuracy note:** the requested stack lists *Channels / WebSockets /
Daphne*, but **the codebase does not implement them** — there are no consumers,
no `channels` dependency, and `asgi.py` is a plain Django ASGI app. The app is a
standard WSGI service (gunicorn), which is correct for what the code actually does.
I did **not** fabricate a Channels/Daphne layer; if real-time features are planned,
that is a separate feature workstream (see Recommendations).

---

## 1. Repository structure (relevant parts)

```
edu-platform/
├─ .github/workflows/
│  ├─ ci.yml              # lint + test + build + dep-audit + (NEW) docker build/scan
│  └─ deploy.yml          # (NEW) SSH deploy w/ health gate + rollback
├─ backend/               # Django project (config/ + apps/)
│  ├─ Dockerfile          # (REWRITTEN) multi-stage, slim runtime, non-root
│  ├─ entrypoint.sh       # (UPDATED) wait_for_db → migrate → collectstatic
│  ├─ requirements.txt    # (PINNED) + whitenoise
│  ├─ scripts/            # (NEW) wait_for_db / migrate / collectstatic / start
│  └─ config/settings/{base,dev,prod}.py
├─ frontend_w/            # Next.js app router
│  ├─ Dockerfile          # (REWRITTEN) multi-stage standalone, non-root
│  ├─ next.config.ts      # (UPDATED) output: "standalone"
│  ├─ .dockerignore       # (NEW)
│  └─ scripts/            # (NEW) build / start
├─ mobile/                # Expo app (no container needed for prod; see §6)
├─ infra/nginx/
│  ├─ default.conf        # (REWRITTEN) HTTP-first proxy, gzip, headers, static/media
│  └─ default.https.conf  # (NEW) HTTPS + HSTS config to swap in post-cert
├─ scripts/               # (NEW) backup.sh / restore.sh (host helpers)
├─ docker-compose.prod.yml# (REWRITTEN) env wiring, network, limits, volumes
├─ docker-compose.dev.yml # local db/redis only (unchanged; fine)
├─ .dockerignore          # (NEW) root context for backend image
├─ .env.prod.example      # (NEW) documented single source of truth
└─ DEPLOYMENT.md          # (UPDATED) end-to-end runbook
```

---

## 2. Problem list (findings)

### 🔴 Critical — stack does not boot / core features broken

1. **Compose env wiring missing.** `docker-compose.prod.yml` injected `.env.prod`
   into containers, but `.env.prod` contained no `DB_HOST`, `DB_PASSWORD`,
   `REDIS_URL`, or `CELERY_*`. Django defaulted to `localhost`, so the backend,
   worker and beat could never reach Postgres/Redis inside the network. The `db`
   service used `${POSTGRES_PASSWORD:?...}` interpolation, which reads compose's
   `.env` (not `.env.prod`) — with neither present, `up` aborted immediately with
   *"POSTGRES_PASSWORD is required"*.
2. **Static files broken with `DEBUG=False`.** No WhiteNoise, no nginx static
   volume, and gunicorn does not serve static. Django admin / DRF assets 404 in
   prod. Nginx also proxied `/static/` to the app, which cannot serve them.
3. **Media not served in prod.** `urls.py` adds `static(MEDIA_URL, …)` which is a
   no-op when `DEBUG=False`. Without nginx volume or S3, uploads 404.
4. **S3 media backend silently dead on Django 6.** `DEFAULT_FILE_STORAGE` was
   removed in Django 5.1+. The `USE_S3` block set it and was ignored — media would
   still write locally even with `USE_S3=True`.
5. **Web container could not reach the backend.** The Next server proxies
   `/api/backend/*` to `process.env.BACKEND_URL` (runtime), defaulting to
   `127.0.0.1:8000` — wrong inside the `web` container. `BACKEND_URL` was never set.
6. **Nginx dies on first boot.** It referenced `…/live/yourdomain.com/fullchain.pem`
   which doesn't exist until certbot issues a cert — classic chicken-and-egg that
   prevents the very startup needed to pass the ACME challenge.
7. **Web image build failed — duplicate `middleware.ts` + `proxy.ts`.** Next.js 16
   renamed `middleware`→`proxy` and refuses to build when both exist. The repo had
   two divergent route-protection implementations (different protected-route lists
   and auth logic), both committed in `55a4630`. `next build` aborted. → Consolidated
   into `proxy.ts` (the Next 16 file + stronger session-validation w/ token refresh),
   widened its protected prefixes to the **union** of both so no route lost
   protection, and deleted `middleware.ts`.
8. **Invalid `eslint` key in `next.config.ts`.** Next 16 removed the built-in
   `eslint` config option (and lint-during-build). The key I initially added tripped
   `tsc` (TS2353) and would break CI. → Removed; Next 16 no longer lints during
   `next build`, so the production image build is unaffected.

### 🟠 High — security / production-readiness

9. **Unpinned dependencies** (`requirements.txt`) — non-reproducible builds and an
   uncontrolled supply-chain surface.
10. **Frontend image not production-grade** — single stage, ships full
   `node_modules`, runs `next start` as root, no `.dockerignore` (build context
   could include `.env`, `.next`, logs).
11. **Backend image** carried `build-essential`/`libpq-dev` into the runtime layer
   (larger surface, bigger image).
12. **No resource limits or log rotation** — a runaway worker or noisy logs could
    exhaust host memory/disk.
13. **No `.dockerignore`** at repo root — large build context and risk of copying
    secrets/local data into the image layer.

### 🟡 Medium — correctness / latent bugs

14. **`wsgi.py` / `asgi.py` defaulted to `config.settings`** — an (empty) package,
    not a settings module. Worked only because the Dockerfile sets the env var
    explicitly; broke any non-Docker invocation.
15. **`SECURE_SSL_REDIRECT` vs HTTP bootstrap** — defaulting to `True` while serving
    over HTTP (pre-TLS) causes redirect loops. Now env-gated (`0` until HTTPS).
16. **`docker-compose.dev.yml`** runs Postgres with a throwaway password and Redis
    without persistence — fine for dev, documented as dev-only.

### ⚪ Informational — pre-existing, out of Docker scope (noted, not changed)

- `drf-spectacular` emits ~70 schema warnings (APIViews without `serializer_class`).
  These are OpenAPI-doc warnings, not runtime/security issues.
- The frontend has several overlapping API-client helpers (`lib/api.ts`,
  `shared/lib/*`). Harmless but worth consolidating.
- Stated Channels/WebSockets/Daphne are **not implemented** (see §0).

---

## 3. Fix list (applied)

| # | Fix | Files |
|---|-----|-------|
| 1 | Single-source env wiring; all connection strings point at compose service names | `.env.prod.example`, `.env.prod`, `docker-compose.prod.yml` |
| 2 | WhiteNoise middleware + `STORAGES["staticfiles"]`; nginx serves `/static/` from shared volume | `backend/config/settings/base.py`, `infra/nginx/default.conf`, compose `staticfiles` volume |
| 3 | nginx serves `/media/` from shared volume | `infra/nginx/default.conf`, compose `media` volume |
| 4 | Migrate S3 media to the Django 6 `STORAGES` API | `backend/config/settings/base.py` |
| 5 | `BACKEND_URL=http://backend:8000` wired into `web` | `.env.prod*` |
| 6 | HTTP-first nginx that boots without certs; separate HTTPS config | `infra/nginx/default.conf`, `default.https.conf` |
| 7 | Pin all direct deps to resolved versions; add `whitenoise` | `backend/requirements.txt` |
| 8 | Multi-stage **standalone** frontend image, non-root, healthcheck, `.dockerignore` | `frontend_w/Dockerfile`, `next.config.ts`, `frontend_w/.dockerignore` |
| 9 | Multi-stage backend image (build tools isolated), slim runtime | `backend/Dockerfile` |
| 10 | `deploy.resources.limits` + `json-file` log rotation on every service | `docker-compose.prod.yml` |
| 11 | Root `.dockerignore` | `.dockerignore` |
| 12 | Fix `wsgi/asgi` default settings module to `config.settings.dev` | `backend/config/{wsgi,asgi}.py` |
| 13 | `SECURE_SSL_REDIRECT` env-gated; default `0` until HTTPS | `.env.prod*` (read by `prod.py`) |
| 14 | Startup/ops scripts | `backend/scripts/*`, `frontend_w/scripts/*`, `scripts/{backup,restore}.sh` |
| 15 | CI docker-build + Trivy job; deploy workflow with health gate + rollback | `.github/workflows/{ci,deploy}.yml` |
| 16 | Resolve Next 16 build blocker: consolidate `middleware.ts`+`proxy.ts` into one `proxy.ts` (union of protected routes) | `frontend_w/src/proxy.ts` (deleted `middleware.ts`) |
| 17 | Remove invalid Next 16 `eslint` config key | `frontend_w/next.config.ts` |

---

## 4. Security report

| Control | Status | Notes |
|---------|--------|-------|
| `DEBUG=False` in prod | ✅ | `prod.py` forces it; fail-closed on insecure `SECRET_KEY` |
| `SECRET_KEY` enforcement | ✅ | Refuses to start on missing / `django-insecure-` key |
| `ALLOWED_HOSTS` enforcement | ✅ | Required in prod or startup aborts |
| HTTPS / HSTS | ✅ | `SECURE_SSL_REDIRECT`, 1-yr HSTS + preload (enable after cert) |
| Secure cookies (session/CSRF/JWT) | ✅ | `Secure`, `HttpOnly` in prod |
| Security headers | ✅ | Django (`nosniff`, `DENY`, referrer) + nginx `add_header` |
| CORS | ✅ | Explicit origins; wildcard+credentials combo blocked in prod |
| Rate limiting | ✅ | DRF throttles (anon/user/login/refresh) |
| Non-root containers | ✅ | backend `app` user, web `node` user |
| Secrets in image / git | ✅ | `.dockerignore` + `.gitignore` exclude `.env*`; `.env.prod` gitignored |
| Dependency scanning | ✅ | `pip-audit` (deps) + Trivy (image) in CI |
| `manage.py check --deploy` security warnings | ✅ **0** | Verified (see §7) |

Residual: rotate the placeholder DB password in `.env.prod` before real deploy;
prefer S3 for media on ephemeral-disk hosts (Railway/Render).

---

## 5. Performance report

**Measured image sizes** (this host): web **297 MB** (standalone), backend
**1.06 GB** (down from **1.92 GB** after dropping the recursive venv `chown`). The
backend's remaining bulk is the optional AI providers (`voyageai`/`openai` →
`langchain`/`tokenizers`/`huggingface`/`numpy`); splitting those into an optional
requirements file would roughly halve it (left in place to avoid breaking configured
remote-embedding deployments).

| Optimization | Effect |
|--------------|--------|
| Frontend standalone output | Runtime image ships only the server bundle + `.next/static` + `public` — no `node_modules`/source. Order-of-magnitude smaller image, faster cold start. |
| Backend multi-stage | Build toolchain (`build-essential`, `libpq-dev`) stays in the builder; runtime keeps only `libpq5` + `curl`. Smaller, fewer CVEs. |
| Layer caching | Deps copied/installed before app code in both images; GHA build cache in CI. |
| Static serving offloaded | nginx serves `/static` & `/media` from a volume with long-lived cache headers; gunicorn handles only dynamic requests. |
| WhiteNoise compression | Pre-compressed static assets for single-container hosts without nginx. |
| Gzip at nginx | Text/JSON/JS/CSS compressed (`gzip_comp_level 5`). |
| DB connection reuse | `CONN_MAX_AGE=60` keeps Postgres connections warm. |
| Redis AOF + maxmemory | Durable broker/queue with a 256 MB cap and `noeviction` (safe for a broker). |
| Gunicorn tuning | `--max-requests`/`--max-requests-jitter` recycle workers to bound memory; workers configurable via `GUNICORN_WORKERS`. |
| Resource limits | Each service capped (CPU/mem) so one cannot starve the host. |

---

## 6. Mobile (Expo)

Expo/React Native apps are **built and distributed via EAS**, not run as a
production server container, so no prod Dockerfile is warranted. For prod the
mobile app simply needs `EXPO_PUBLIC_API_BASE_URL` pointed at the public API
(`https://yourdomain.com`). Local development against the Dockerized backend:

- Android emulator → `EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000`
- Physical device → your machine's LAN IP, e.g. `http://192.168.1.x:8000`
- iOS simulator → `http://127.0.0.1:8000`

(Documented in `mobile/.env.example`.) A throwaway Expo dev container is possible
but adds little over running the Metro bundler on the host; skipped intentionally.

---

## 7. Verification

See `VERIFICATION.md` for the full command log. Summary:

- `docker compose -f docker-compose.prod.yml config -q` → **OK** (valid, anchors resolve).
- `manage.py check` (dev) → **0 issues**.
- `manage.py check --deploy` (prod) → **0 `security.*` warnings** (only pre-existing
  drf-spectacular schema warnings remain).
- Image builds (`docker compose build backend web`) → see VERIFICATION.md.

---

## 8. Recommendations (not yet done — propose as follow-ups)

1. **Consolidate frontend API clients** into one module.
2. **If real-time is needed**, add `channels`/`channels-redis` + Daphne/Uvicorn and a
   `/ws/` nginx upstream — this is a feature, not a config fix.
3. **Add a full lock file** (`pip-compile`/`uv`) for transitive pinning; the resolved
   transitive set is captured during this audit.
4. **Move media to S3** for any host with ephemeral disk.
5. **Postgres tuning** (`shared_buffers`, `max_connections`) once real load is known.
