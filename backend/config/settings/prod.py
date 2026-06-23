import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa

DEBUG = False

# --- Fail closed on insecure secrets -------------------------------------
if not (os.environ.get("SECRET_KEY") or os.environ.get("DJANGO_SECRET_KEY")):
    raise ImproperlyConfigured(
        "SECRET_KEY (or DJANGO_SECRET_KEY) must be set in production."
    )
if SECRET_KEY.startswith("django-insecure"):  # noqa: F405
    raise ImproperlyConfigured(
        "Refusing to start with an insecure SECRET_KEY in production."
    )

# ALLOWED_HOSTS must be provided via env in prod (base appends localhost for
# in-container health checks, so we validate the env var itself). On Render the
# platform-injected RENDER_EXTERNAL_HOSTNAME satisfies this, so no manual host
# config is required there.
if not (
    (os.environ.get("ALLOWED_HOSTS") or "").strip()
    or (os.environ.get("RENDER_EXTERNAL_HOSTNAME") or "").strip()
):
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set explicitly in production.")

# --- HTTPS / transport security ------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)  # noqa: F405
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# --- Cookies --------------------------------------------------------------
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
JWT_COOKIE_SECURE = True  # noqa: F405

# --- Content / header hardening ------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# --- Never allow wildcard CORS with credentials in prod ------------------
if CORS_ALLOW_ALL_ORIGINS and CORS_ALLOW_CREDENTIALS:  # noqa: F405
    raise ImproperlyConfigured(
        "CORS_ALLOW_ALL_ORIGINS cannot be combined with CORS_ALLOW_CREDENTIALS."
    )
