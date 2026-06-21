# EduPlatform — Production Deployment & Launch Guide

Ties together the hardening/recovery work (Phases 1–9). The platform is a Django
+ DRF backend, a Next.js web app, and an Expo React Native mobile app, backed by
PostgreSQL + Redis + Celery.

> Status at time of writing: backend **35/35 tests green**, `check --deploy` → **0
> security warnings**, web `tsc` clean. Two blockers remain before launch (below).

---

## 0. 🚨 LAUNCH BLOCKERS (do these first)

1. **Rotate & purge committed secrets.** `backend/.env` and `.env.prod` were
   committed in history (commit `9fe5556`) containing a real `SECRET_KEY` and DB
   password. `.gitignore` now blocks them, but history still leaks them.
   - Generate a fresh `SECRET_KEY` and a new DB password.
   - Purge from history: `git filter-repo --path backend/.env --path .env.prod --invert-paths` (or BFG), then force-push.
   - The production settings **refuse to boot** on the old insecure key (`prod.py` fails closed).

2. **Install mobile dependencies.** Phases 6 + 9 added declared deps (push,
   offline cache, AI screens). Run `cd mobile && npm install` — this resolves
   `expo-notifications`, `expo-device`, `@react-native-async-storage/async-storage`,
   `@tanstack/react-query-persist-client` (the only outstanding mobile `tsc` errors).

---

## 1. Architecture (post-consolidation)

```
Web (Next.js)  ─┐                        ┌─ PostgreSQL 16
Mobile (Expo)  ─┼─► Django/DRF API ─────►├─ Redis 7  (cache + Celery broker)
                │   (gunicorn)            └─ Celery worker + beat
                └─► Next.js BFF proxy (/api/backend) injects JWT from httpOnly cookies
```

**Canonical Django apps (10):** `accounts, academics, content, assessment,
progress, gamification, institutions, notifications, moderation, ai, ai_learning`.
(`mcq`, `leaderboards`, `billing`, `practice`, `social` were removed in Phase 7.)

Ownership: curriculum → `academics`; questions/quizzes → `assessment`; XP/badges/
leaderboard → `gamification`; institutions/batches → `institutions`; AI
personalization → `ai_learning` (reads the others, owns no source data).

---

## 2. Environment variables

### Backend (`.env.prod`, loaded by the backend + worker + beat containers)
| Var | Required | Notes |
|---|---|---|
| `SECRET_KEY` (or `DJANGO_SECRET_KEY`) | ✅ | Prod refuses insecure/`django-insecure*` values |
| `DEBUG` | ✅ | Must be `False` in prod |
| `ALLOWED_HOSTS` | ✅ | Comma-separated, e.g. `edu.example.com` (localhost auto-added for health checks) |
| `DB_NAME` `DB_USER` `DB_PASSWORD` `DB_HOST` `DB_PORT` | ✅ | `DB_HOST=db`, `DB_PORT=5432`; `DB_PASSWORD` must equal `POSTGRES_PASSWORD` |
| `USE_REDIS` `USE_CELERY` | ✅ | `True` in prod |
| `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | ✅ | e.g. `redis://redis:6379/1` |
| `CORS_ALLOWED_ORIGINS` | ✅ | Web origin(s), e.g. `https://edu.example.com` |
| `CSRF_TRUSTED_ORIGINS` | ✅ | Same origin(s) |
| `JWT_ACCESS_MINUTES` `JWT_REFRESH_DAYS` | — | Defaults 15 / 30 |
| `EMAIL_BACKEND` `DEFAULT_FROM_EMAIL` | ✅ | SMTP backend for OTP/verification/reset emails |
| `ANTHROPIC_API_KEY` `AI_CHAT_MODEL` | ✅ (for RAG chat) | `claude-opus-4-8` etc. |
| `AI_EMBEDDING_PROVIDER` (+ `VOYAGE_API_KEY`/`OPENAI_API_KEY`) | — | `local` works keyless |
| `GOOGLE_OAUTH_CLIENT_IDS` | — | Comma-separated client IDs for Google sign-in |
| `SENTRY_DSN` | recommended | Enables error tracking automatically |
| `USE_S3` + `AWS_*` | recommended | Offload media to S3-compatible storage |
| `LOG_LEVEL` `PASSWORD_MIN_LENGTH` `SECURE_HSTS_SECONDS` | — | Sensible defaults set |

### Postgres / backup (`.env.prod`, same file)
`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` — the `db` service reads these
via `env_file` (no separate `.env` needed), and the `backup` service reuses them.
`POSTGRES_PASSWORD` **must equal** `DB_PASSWORD`. A fully documented template lives
at **`.env.prod.example`** — copy it to `.env.prod` and fill in the `<CHANGE ME>` values.

### Web (`frontend_w`, build/runtime env)
| Var | Notes |
|---|---|
| `BACKEND_URL` (or `NEXT_PUBLIC_BACKEND_URL`) | Internal URL the BFF proxies to, e.g. `http://backend:8000` |
| `NODE_ENV=production` | Enables `Secure` cookies in the auth routes |

### Mobile (`mobile`, via `eas.json` build profiles)
| Var | Notes |
|---|---|
| `EXPO_PUBLIC_API_BASE_URL` | **HTTPS** public API URL (preview/production profiles in `eas.json`) |
| `EXPO_PUBLIC_GOOGLE_*_CLIENT_ID` | Google OAuth client IDs (optional) |

---

## 3. Deploy (Docker Compose)

`docker-compose.prod.yml` defines: `nginx`, `backend`, `worker`, `beat`, `web`,
`db`, `redis`, `certbot`, `backup`. The backend image runs as non-root and its
entrypoint auto-runs `migrate` + `collectstatic` (`RUN_MIGRATIONS=1`; worker/beat
set `0`).

```bash
# 1. Configure — ONE file is the source of truth for every service.
cp .env.prod.example .env.prod       # fill in the <CHANGE ME> values (§2)
$EDITOR .env.prod

# 2. Build + launch everything. The stack boots over HTTP with no manual fixes;
#    nginx serves on :80 (HTTP-first config), static/media from shared volumes.
docker compose -f docker-compose.prod.yml up -d --build

# 3. Watch health
docker compose -f docker-compose.prod.yml ps        # backend/db/redis/web healthy
docker compose -f docker-compose.prod.yml logs -f backend worker beat

# 4. (First-time HTTPS) Issue a cert, then switch nginx to the HTTPS config.
#    Point your domain's A record at the host first, then:
docker compose -f docker-compose.prod.yml run --rm certbot \
  certonly --webroot -w /var/www/certbot -d yourdomain.com -d www.yourdomain.com
$EDITOR infra/nginx/default.https.conf               # set your real domain + cert paths
#    Mount the HTTPS config (edit the nginx volume in docker-compose.prod.yml to use
#    default.https.conf), set SECURE_SSL_REDIRECT=1 in .env.prod, then:
docker compose -f docker-compose.prod.yml up -d nginx backend
```

- **Migrations & static**: handled by the backend entrypoint on boot.
- **Background jobs**: `worker` consumes the queue; `beat` runs
  `send-scheduled-notifications` (every minute). The learning loop fires inline
  via `transaction.on_commit`.
- **Backups**: the `backup` service runs a daily `pg_dump` to `./backups`
  (7-day retention). Verify a restore before launch.
- **Certbot**: auto-renew loop runs after the first manual issuance.

### Create the first admin
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### Mobile build/submit
```bash
cd mobile && npm install
npx eas build --profile production --platform all
npx eas submit --profile production --platform all
```

---

## 4. CI/CD

`.github/workflows/ci.yml` runs on push/PR to `main`:
- **backend** — `check`, migration-drift check, `test apps`
- **web** — `tsc`, `eslint`, `build`
- **security** — `pip-audit` (non-blocking)
- **docker** — builds the backend + web images and runs a Trivy scan (non-blocking)

`.github/workflows/deploy.yml` (manual dispatch) builds the stack on a VPS over SSH
with a `/healthz/` gate. Needs secrets `SSH_HOST`, `SSH_USER`, `SSH_KEY`,
`DEPLOY_PATH`. **Rollback:** re-run it with `ref` set to a previous tag/SHA.

---

## 5. Post-deploy smoke test

```bash
curl -f https://edu.example.com/healthz/                 # → {"status":"ok"}
curl -sf https://edu.example.com/api/academics/levels/   # public catalogue (200)
curl -si https://edu.example.com/api/progress/dashboard/ # → 401 (auth required)
```
Then via the web app: register → verify email (OTP) → browse academics → take a
quiz → confirm XP/leaderboard/notification update → open **AI Coach** → Generate
plan → see recommendations + study plan.

---

## 6. Launch checklist

**Security**
- [ ] Secrets rotated + purged from git history (Blocker #1)
- [ ] `DEBUG=False`, `ALLOWED_HOSTS` set, prod boots (fails closed otherwise)
- [ ] `check --deploy` clean (HSTS, SSL redirect, secure cookies — already wired)
- [ ] DRF default permission `IsAuthenticated`; answer-keys/PII gated (Phase 2)
- [ ] CORS/CSRF origins restricted to the real web origin

**Infrastructure**
- [ ] Postgres + Redis healthy; `worker` + `beat` running
- [ ] Daily `pg_dump` backup verified (restore tested)
- [ ] TLS issued + auto-renew confirmed; nginx domain not placeholder
- [ ] Sentry `SENTRY_DSN` set; logs visible (`docker compose logs`)
- [ ] Media on S3 (`USE_S3`) or persistent volume

**Application**
- [ ] Superuser created; seed curriculum (Level→Subject→Chapter→Topic) + questions
- [ ] Email (SMTP) verified: registration OTP + password reset arrive
- [ ] Web smoke test (§5) passes end-to-end incl. AI Coach
- [ ] Mobile: `npm install`, `EXPO_PUBLIC_API_BASE_URL` → HTTPS, store build green

---

## 7. Phase summary (what shipped)

| Phase | Outcome |
|---|---|
| 1 | Celery revived; quiz → XP → progress → leaderboard → notification loop wired (`on_commit`) |
| 2a | Secure-by-default perms, password validators, HSTS/SSL/cookies, logging + Sentry |
| 2b | Content IDOR, institutions grade-auth, accounts PII/answer-key leaks fixed |
| 3 | Password reset (OTP), Expo push (Device + sender), event notifications |
| 4 | Leaderboard caching + caps, N+1 fixes |
| 5 | Web route-protection middleware + leaderboard/badges/notifications pages |
| 6 | Docker (non-root, entrypoint, worker/beat/healthchecks/backup), CI/CD; mobile login/refresh/eas fixes |
| 7 | Schema consolidation: 13→10 apps, single source of truth per entity, FK-based curriculum |
| 9 | AI Learning engine: mastery bands, weak-topic scoring, forgetting curve, recommendations, study plans (web + mobile) |

---

## 8. Rollback

- App rollback: redeploy the previous image tag (`docker compose ... up -d`).
- DB: restore the latest `./backups/edu-*.sql.gz` via `gunzip | psql`.
- Migrations are reversible per app; avoid destructive data migrations without a
  fresh backup.
