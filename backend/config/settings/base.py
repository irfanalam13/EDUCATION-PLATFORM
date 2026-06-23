from __future__ import annotations

import os
from pathlib import Path
from datetime import timedelta


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _load_dotenv() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name)
    if not value:
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]


_load_dotenv()

DEBUG = env_bool("DEBUG", env_bool("DJANGO_DEBUG", True))
DEV_MODE = env_bool("DEV_MODE", DEBUG)

# Accept either SECRET_KEY or DJANGO_SECRET_KEY (the .env files historically used
# both). The insecure fallback is only ever used in DEBUG; prod.py hard-fails if
# a real key is missing or left at the insecure default.
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("DJANGO_SECRET_KEY") or "django-insecure-dev-only-change-me"
# ---- AI / RAG (chat answer generation) ----
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_CHAT_MODEL = os.getenv("AI_CHAT_MODEL", "claude-opus-4-8")
AI_CHAT_MAX_TOKENS = int(os.getenv("AI_CHAT_MAX_TOKENS", "2000"))
AI_RAG_TOP_K = int(os.getenv("AI_RAG_TOP_K", "5"))
AI_MAX_UPLOAD_MB = int(os.getenv("AI_MAX_UPLOAD_MB", "20"))

# Google Gemini chat provider. The platform ships without preloaded RAG data, so
# answers are generated from the model's general knowledge (RAG context is still
# used when a user uploads PDFs/notes). AI_CHAT_PROVIDER picks the primary LLM
# ("gemini" | "claude"); the other is used as fallback if the primary fails.
# Defaults to Gemini whenever a GEMINI_API_KEY is configured.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
AI_CHAT_PROVIDER = os.getenv("AI_CHAT_PROVIDER", "gemini" if GEMINI_API_KEY else "claude").lower()

# Embeddings are retrieval-only (Anthropic has no embeddings endpoint).
# Provider: "local" (hash fallback, no key) | "voyage" | "openai".
AI_EMBEDDING_PROVIDER = os.getenv("AI_EMBEDDING_PROVIDER", "local").lower()
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")
VOYAGE_EMBEDDING_MODEL = os.getenv("VOYAGE_EMBEDDING_MODEL", "voyage-3.5")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_EMBEDDING_MODEL = os.getenv("AI_EMBEDDING_MODEL", "text-embedding-3-small")
ACCOUNT_EMAIL_VERIFICATION_REQUIRED = env_bool("ACCOUNT_EMAIL_VERIFICATION_REQUIRED", True)
EMAIL_OTP_EXPIRY_MINUTES = int(os.getenv("EMAIL_OTP_EXPIRY_MINUTES", "10"))
GOOGLE_OAUTH_CLIENT_IDS = env_list("GOOGLE_OAUTH_CLIENT_IDS", env_list("GOOGLE_OAUTH_CLIENT_ID", []))

# ---- Billing / payments (apps.billing) ----
# Nepal-focused: prices default to NPR; Khalti/eSewa are the local gateways and
# Stripe covers international cards. With no keys configured the MANUAL gateway
# (offline confirmation via MANUAL_WEBHOOK_TOKEN) keeps the flow working.
BILLING_DEFAULT_CURRENCY = os.getenv("BILLING_DEFAULT_CURRENCY", "NPR")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
KHALTI_SECRET_KEY = os.getenv("KHALTI_SECRET_KEY", "")
KHALTI_SANDBOX = env_bool("KHALTI_SANDBOX", True)
ESEWA_SECRET_KEY = os.getenv("ESEWA_SECRET_KEY", "")
ESEWA_PRODUCT_CODE = os.getenv("ESEWA_PRODUCT_CODE", "EPAYTEST")
ESEWA_SANDBOX = env_bool("ESEWA_SANDBOX", True)
MANUAL_WEBHOOK_TOKEN = os.getenv("MANUAL_WEBHOOK_TOKEN", "")

# In prod, operators must set ALLOWED_HOSTS (enforced in prod.py). We always keep
# localhost/127.0.0.1 so in-container health checks work regardless. The deployed
# origins (Render host, Vercel frontend) are supplied via env on the platform —
# see backend/.env.example for the variable names.
# Render injects RENDER_EXTERNAL_HOSTNAME for every service; auto-trusting it
# means a Render deploy works without hand-copying the *.onrender.com host into
# ALLOWED_HOSTS. Operators can still add custom domains via the ALLOWED_HOSTS env.
_RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
ALLOWED_HOSTS = (
    ["*"]
    if DEBUG
    else list(
        dict.fromkeys(
            env_list("ALLOWED_HOSTS", [])
            + ([_RENDER_HOST] if _RENDER_HOST else [])
            + ["localhost", "127.0.0.1"]
        )
    )
)
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
)
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8081",  # Added for Expo Web view
        "http://127.0.0.1:8081",  # Added for Expo Web view
    ]
)
# In dev, Expo Web picks whatever port is free (8081, 8082, 19006, ...), so we
# allow any localhost/127.0.0.1 port rather than chasing the number each run.
# Prod overrides CORS_ALLOWED_ORIGINS via env and never sets DEBUG, so this
# regex is dev-only. (Native React Native has no Origin header, so CORS never
# applies there — this only matters for the Expo Web build in a browser.)
if DEBUG:
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^http://localhost:\d+$",
        r"^http://127\.0\.0\.1:\d+$",
    ]
# config/settings/base.py

# 1. Explicitly allow the HTTP methods your frontend will use
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# 2. Explicitly allow the headers your React Native app sends
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", False)
CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    "django_extensions",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_filters",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "apps.academics",
    "apps.accounts",
    "apps.ai",
    "apps.ai_learning",
    "apps.analytics",
    "apps.assessment",
    "apps.billing",
    "apps.content",
    "apps.gamification",
    "apps.institutions",
    "apps.moderation",
    "apps.notifications",
    "apps.progress",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Serve hashed/compressed static files directly from the app server so the
    # admin and DRF assets work with DEBUG=False even without nginx (e.g. on
    # Railway/Render single-container deploys). Must sit right after Security.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Wires request.entitlements (feature gating) — must run after auth so the
    # user is resolved. Cheap: no DB work until an entitlement is queried.
    "apps.billing.middleware.FeatureGateMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTH_USER_MODEL = "accounts.User"

# Database choice is decoupled from DEV_MODE: prod always uses Postgres, but dev
# can opt into Postgres (USE_POSTGRES=True in .env) while keeping DEBUG/DEV_MODE on.
# Managed platforms (Render, Railway, Heroku, Fly) expose a single DATABASE_URL
# connection string instead of discrete DB_* vars — if it is set we parse it and
# use Postgres regardless of USE_POSTGRES, so the operator only has to wire one var.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def _database_from_url(url: str) -> dict:
    """Parse a postgres://user:pass@host:port/name URL into a Django DB config."""
    from urllib.parse import unquote, urlparse

    parsed = urlparse(url)
    # Render's managed Postgres requires SSL. Allow opt-out via DB_SSLMODE for
    # providers/local proxies that don't (e.g. DB_SSLMODE=disable).
    sslmode = os.getenv("DB_SSLMODE", "require")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or "5432"),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": {"sslmode": sslmode} if sslmode else {},
    }


USE_POSTGRES = env_bool("USE_POSTGRES", not DEV_MODE) or bool(DATABASE_URL)

if DATABASE_URL:
    DATABASES = {"default": _database_from_url(DATABASE_URL)}
elif USE_POSTGRES:
    DATABASES = {
        "default": {
            "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
            "NAME": os.getenv("DB_NAME", "edu_platform"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

USE_REDIS = env_bool("USE_REDIS", not DEV_MODE)
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1")

if USE_REDIS:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "edu-platform",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "edu-platform",
        }
    }

USE_CELERY = env_bool("USE_CELERY", not DEV_MODE)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", "Asia/Kathmandu")

# When Celery/Redis are disabled (local dev), run tasks inline in-process so
# that .delay() calls in the learning loop still execute. In prod USE_CELERY is
# true and a real worker consumes the queue.
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", not USE_CELERY)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Periodic jobs. Times are in CELERY_TIMEZONE. Requires `celery beat`.
CELERY_BEAT_SCHEDULE = {
    "send-scheduled-notifications": {
        "task": "apps.notifications.tasks.send_scheduled_notifications",
        "schedule": 60.0,  # every minute
    },
    "snapshot-institution-analytics": {
        "task": "apps.analytics.tasks.snapshot_institutions",
        "schedule": 6 * 60 * 60.0,  # every 6 hours; persists a daily metrics row
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        # Secure by default. Genuinely public endpoints (e.g. the academics
        # catalogue) opt into AllowAny explicitly on the view.
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/min",
        "user": "120/min",
        "login": "10/min",
        "refresh": "20/min",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": (
        ("rest_framework.renderers.JSONRenderer",)
        + (("rest_framework.renderers.BrowsableAPIRenderer",) if DEBUG else ())
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Edu Platform API",
    "DESCRIPTION": "Backend API for the Nepal-focused educational platform.",
    "VERSION": "1.0.0",
    'SERVE_INCLUDE_SCHEMA': False,
    # Optional: If you use JWT or Token auth, add security definitions here
    'COMPONENT_SPLIT_REQUEST': True,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "30"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

JWT_COOKIE_SECURE = env_bool("JWT_COOKIE_SECURE", not DEBUG)
JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")
JWT_ACCESS_COOKIE_NAME = os.getenv("JWT_ACCESS_COOKIE_NAME", "access_token")
JWT_REFRESH_COOKIE_NAME = os.getenv("JWT_REFRESH_COOKIE_NAME", "refresh_token")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": int(os.getenv("PASSWORD_MIN_LENGTH", "8"))},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Structured logging to stdout (container-friendly). Level via LOG_LEVEL env.
# Default to INFO even in dev so the terminal shows requests/errors, not a flood
# of file-watch + SQL DEBUG lines. Set LOG_LEVEL=DEBUG to opt into verbose logs.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(name)s %(process)d %(message)s",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose" if not DEBUG else "simple",
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        # Always silence these two firehoses, even when LOG_LEVEL=DEBUG:
        # the dev auto-reloader logs every watched file, and the DB backend logs
        # every SQL query — both bury real logs.
        "django.utils.autoreload": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "celery": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "apps": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

# Optional Sentry error tracking (no-op unless SENTRY_DSN is set and SDK installed).
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    try:  # pragma: no cover - only when sentry-sdk is installed
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration(), CeleryIntegration()],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            send_default_pii=False,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        )
    except Exception:
        pass



LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Django 5.1+ / 6.0 storage backends. WhiteNoise compresses static assets and
# serves them straight from the app server. The `default` (media) backend is
# swapped to S3 below when USE_S3 is enabled.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
WHITENOISE_MAX_AGE = int(os.getenv("WHITENOISE_MAX_AGE", "31536000"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "EduPlatform <no-reply@edu-platform.local>")

SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

USE_S3 = env_bool("USE_S3", False)
if USE_S3:
    INSTALLED_APPS += ["storages"]
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
    AWS_S3_ADDRESSING_STYLE = "path"
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    # Django 6.0 removed DEFAULT_FILE_STORAGE; route media through STORAGES.
    STORAGES["default"] = {"BACKEND": "apps.common.storage_backends.MediaStorage"}
