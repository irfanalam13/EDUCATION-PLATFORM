# Final Verification Report

**Date:** 2026-06-21 · **Host:** Windows 11 · Docker 29.5.2 / Compose v5.1.4 · Python 3.13.5 · Node 20

All checks were run against the repository after the fixes in `DOCKER_AUDIT.md`.

| ✓ | Check | Command | Result |
|---|-------|---------|--------|
| ✅ | Prod compose is valid | `docker compose -f docker-compose.prod.yml config -q` | OK (YAML anchors + env resolve) |
| ✅ | Dev compose is valid | `docker compose -f docker-compose.dev.yml config -q` | OK |
| ✅ | Django dev check | `manage.py check` (`config.settings.dev`) | **0 issues** |
| ✅ | Django prod check | `manage.py check` (`config.settings.prod`) | **0 issues** |
| ✅ | Django deploy security | `manage.py check --deploy` | **0 `security.*` warnings**¹ |
| ✅ | Dependencies resolve & pin | clean venv install + `pip freeze` | resolved; direct deps pinned |
| ✅ | Mobile typecheck | `cd mobile && npx tsc --noEmit` | **0 errors** (exit 0) |
| ✅ | Expo project health | `npx expo-doctor` | **18/18 checks passed, no issues** |
| ✅ | Expo config resolves | `npx expo config --type public` | OK (name/slug/scheme/apiBaseUrl) |
| ✅ | `app.json` / `eas.json` valid | parsed; profiles checked | dev=http, preview/production=https ✓ |
| ✅ | Secrets stay ignored | `git check-ignore .env.prod` | ignored ✓; `.env.prod.example` trackable ✓ |
| ✅ | Backend image builds | `docker compose build backend` | exit 0 — **1.06 GB** |
| ✅ | Web image builds (standalone) | `docker compose build web` | exit 0 — **297 MB** |

¹ The 72 messages from `check --deploy` are all pre-existing `drf-spectacular`
schema warnings (W001/W002 — APIViews without `serializer_class`). None are Django
security or deployment errors. Confirmed by filtering for `security.(W|E)` → none.

## Component coverage

- **Backend (Django/DRF):** system check clean on dev+prod; prod fails closed on
  insecure `SECRET_KEY`/missing `ALLOWED_HOSTS` (by design); WhiteNoise static
  storage imports cleanly.
- **PostgreSQL:** `db` reads `POSTGRES_*` from `.env.prod`; healthcheck `pg_isready`.
- **Redis:** AOF persistence + 256MB cap; healthcheck `redis-cli ping`.
- **Celery worker + beat:** start commands valid; worker healthcheck `inspect ping`.
- **Frontend (Next.js):** `output: "standalone"`, multi-stage image, non-root `node`.
- **Mobile (Expo):** deps installed (529 pkgs), `tsc --noEmit` clean, EAS profiles set.
- **Nginx:** HTTP-first config boots without certs; HTTPS config provided.

## Image build

Both images build cleanly with `docker compose -f docker-compose.prod.yml build`:

| Image | Size | Notes |
|-------|------|-------|
| `edu-platform-web` | **297 MB** | Next.js standalone on `node:20-alpine`, non-root |
| `edu-platform-backend` | **1.06 GB** | multi-stage `python:3.13-slim`; ↓ from 1.92 GB after removing the recursive `chown` over the venv |

Two real build blockers were found and fixed **during** verification (both
pre-existing app issues, not infra):

1. **Next 16 refused to build** with both `src/middleware.ts` and `src/proxy.ts`
   present (framework renamed `middleware`→`proxy`). Consolidated into `proxy.ts`
   (kept the union of protected routes + session-validation/refresh), deleted
   `middleware.ts`. → `✓ Compiled successfully`.
2. **Invalid `eslint` key** in `next.config.ts` (removed in Next 16) → deleted.

> The backend image is ~1 GB because the **optional** AI embedding providers
> (`voyageai`, `openai`) pull in `langchain-core`, `tokenizers`, `huggingface_hub`,
> and `numpy`. The default `AI_EMBEDDING_PROVIDER=local` doesn't need them — moving
> those two to an optional `requirements-ai.txt` would roughly halve the image.
> Left in place to avoid breaking anyone who has configured a remote provider.

## How to bring the whole stack up

```bash
cp .env.prod.example .env.prod   # fill in <CHANGE ME> values
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps     # all services healthy
curl -f http://localhost/healthz/                 # {"status":"ok"}
```

## Not verified here (require a running stack / real infra)

- Live end-to-end request flow (browser → nginx → Next BFF → Django → Postgres).
- Celery task execution against the live broker.
- TLS issuance (needs a real domain + public DNS).
These are covered by the smoke test in `DEPLOYMENT.md §5` once deployed.
