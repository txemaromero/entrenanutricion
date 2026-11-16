"""Settings shared by every environment. Environment-specific modules import * from here."""

import json
import os
from datetime import timedelta
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-secret-key-change-me-in-production")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
# Render exposes the service hostname; accept it without hard-coding the URL.
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "apps.core",
    "apps.accounts",
    "apps.training",
    "apps.nutrition",
    "apps.progress",
    "apps.assignments",
    "apps.statistics",
    "apps.notes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # API answers (personal and health data) are never kept by browsers nor shared caches.
    "apps.core.middleware.ApiNoStoreMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    # After CORS, so the 413 carries its headers too.
    "apps.core.middleware.RequestSizeLimitMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": dj_database_url.config(
        default="postgres://entrenanutricion:entrenanutricion@localhost:5432/entrenanutricion",
        conn_max_age=int(env("DB_CONN_MAX_AGE", "60")),
    )
}

# Shared by every gunicorn worker and restart: the rate limits count across all of them (with the
# default per-process memory cache, 3 workers meant 3 times each limit). The table is created by a
# migration (core.0001). Plenty of entries, so flooding new keys cannot evict real counters.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
        "OPTIONS": {"MAX_ENTRIES": 50_000},
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "apps.accounts.validators.PasswordComplexityValidator"},
    # Phase 15: none of the 20 000 most common passwords, nor one that looks like the name or email.
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"user_attributes": ("email", "first_name", "last_name")},
    },
]

LANGUAGE_CODE = "es"
LANGUAGES = [("es", "Español"), ("en", "English"), ("ca", "Català")]
TIME_ZONE = env("TIME_ZONE", "Europe/Madrid")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", str(BASE_DIR / "media")))

# --- File storage: local filesystem by default, private Google Cloud Storage bucket when USE_GCS ---
USE_GCS = env_bool("USE_GCS", False)
GS_BUCKET_NAME = env("GS_BUCKET_NAME", "")
GS_EXPIRATION_MINUTES = int(env("GS_EXPIRATION_MINUTES", "15"))

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


def gcs_credentials(variable: str):
    """Service account key from a one-line JSON variable, or None (Google's default credentials)."""
    if not env(variable):
        return None
    from google.oauth2 import service_account

    return service_account.Credentials.from_service_account_info(json.loads(env(variable)))


# Service account of the media bucket. The backups use another one (GS_BACKUP_CREDENTIALS_JSON):
# whoever gets hold of the API's key must not be able to read nor delete the database dumps.
GS_CREDENTIALS = gcs_credentials("GS_CREDENTIALS_JSON")

if USE_GCS:
    _gcs_options = {
        "bucket_name": GS_BUCKET_NAME,
        "querystring_auth": True,
        "default_acl": None,
        "file_overwrite": False,
        "expiration": timedelta(minutes=GS_EXPIRATION_MINUTES),
    }
    if GS_CREDENTIALS is not None:
        _gcs_options["credentials"] = GS_CREDENTIALS
    STORAGES["default"] = {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": _gcs_options,
    }

MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_VIDEO_UPLOAD_BYTES = 50 * 1024 * 1024
# A small, very compressed image can decode into gigabytes: the limit is on the pixels too.
MAX_IMAGE_PIXELS = 40_000_000
# Bodies bigger than the biggest upload (plus the form fields) are refused before being read.
MAX_REQUEST_BODY_BYTES = MAX_VIDEO_UPLOAD_BYTES + 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# --- REST framework ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # simplejwt's, plus: access tokens issued before the last password change are refused.
        "apps.accounts.authentication.SessionJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.DefaultLimitOffsetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    # Only counts requests that carry files; views with their own throttles (auth) keep those.
    "DEFAULT_THROTTLE_CLASSES": ["apps.core.throttling.UploadRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "login": env("THROTTLE_LOGIN", "10/min"),
        # Failed sign-ins per account, whatever the IP (apps/accounts/login_attempts.py).
        "login_account": env("THROTTLE_LOGIN_ACCOUNT", "10/hour"),
        "register": env("THROTTLE_REGISTER", "10/min"),
        "password": env("THROTTLE_PASSWORD", "5/min"),
        # The sign-up form asks once per address typed: a lower limit slows down discovering accounts.
        "email_exists": env("THROTTLE_EMAIL_EXISTS", "10/min"),
        # Generous: one IP can be a whole office, and a 429 here must not end sessions.
        "session": env("THROTTLE_SESSION", "120/min"),
        "data_export": env("THROTTLE_DATA_EXPORT", "5/hour"),
        "password_reset": env("THROTTLE_PASSWORD_RESET", "5/min"),
        "notes": env("THROTTLE_NOTES", "30/min"),
        "email_verification": env("THROTTLE_EMAIL_VERIFICATION", "10/min"),
        "email_verification_resend": env("THROTTLE_EMAIL_VERIFICATION_RESEND", "3/hour"),
        "uploads": env("THROTTLE_UPLOADS", "100/hour"),
    },
    # Proxies in front of Django that append to X-Forwarded-For (Render, nginx: 1). With 0 the
    # header is ignored, so a client cannot dodge the rate limits by sending a fake one.
    "NUM_PROXIES": int(env("NUM_PROXIES", "0")),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "COERCE_DECIMAL_TO_STRING": False,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=12),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    # A key of its own lets the sessions be revoked (by changing it) without touching SECRET_KEY.
    "SIGNING_KEY": env("JWT_SIGNING_KEY") or SECRET_KEY,
}
REMEMBER_ME_REFRESH_LIFETIME = timedelta(days=7)

# Refresh token cookie (httpOnly). Lax works when the app and the API share a site (same origin,
# the Render rewrite or app./api. subdomains); "None" is only for APIs on another site.
AUTH_COOKIE_NAME = "entrenanutricion_refresh"
AUTH_COOKIE_PATH = "/api/v1/auth/"
AUTH_COOKIE_SECURE = env_bool("AUTH_COOKIE_SECURE", True)
AUTH_COOKIE_SAMESITE = env("AUTH_COOKIE_SAMESITE", "Lax")
# Value of the X-Requested-With header the app sends (CSRF defence of the cookie endpoints).
AUTH_CSRF_HEADER_VALUE = "entrenanutricion"

SPECTACULAR_SETTINGS = {
    "TITLE": "entrenanutricion API",
    "DESCRIPTION": "Training and nutrition plans management (clients, trainers, nutritionists, admins).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "ENUM_NAME_OVERRIDES": {
        "EquipmentEnum": "apps.accounts.models.Equipment",
        "GoalEnum": "apps.accounts.models.Goal",
        "MealPlanCategoryEnum": "apps.nutrition.models.MealPlanCategory",
        "FoodCategoryEnum": "apps.nutrition.models.FoodCategory",
        "BadgeCodeEnum": "apps.progress.models.BadgeCode",
        "AdherenceStatusEnum": "apps.progress.adherence.STATUSES",
        "UserStatusEnum": "apps.accounts.models.UserStatus",
        "RoleEnum": "apps.accounts.models.Role",
    },
}

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)
# The refresh cookie must reach the API from the allowed origins (cross-site deployments).
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# Serve uploaded files from Django (local production-like stack only; real deploys use GCS).
SERVE_MEDIA = env_bool("SERVE_MEDIA", False)

# Django's admin site and the interactive API docs (/api/docs/, /api/schema/). On for development;
# production turns both off (config/settings/prod.py): the app and the commands manage everything.
ADMIN_ENABLED = env_bool("ADMIN_ENABLED", True)
API_DOCS_PUBLIC = env_bool("API_DOCS_PUBLIC", True)

# --- Email (password recovery). Console backend unless an SMTP server is configured ---
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "localhost")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "entrenanutricion <no-reply@entrenanutricion.dev>")
# Public URL of the frontend, used to build the links sent by email.
FRONTEND_URL = env("FRONTEND_URL", "http://localhost:5173").rstrip("/")
# Reset links are single use (they depend on the password hash) and expire after this time.
EMAIL_VERIFICATION_MAX_AGE = int(env("EMAIL_VERIFICATION_MAX_AGE_DAYS", "7")) * 86400
PASSWORD_RESET_TIMEOUT = int(env("PASSWORD_RESET_TIMEOUT_MINUTES", "60")) * 60
# Emails whose sending time would reveal something (the password reset) go out in a thread;
# the tests run them inline (apps/core/background.py).
BACKGROUND_TASKS_INLINE = False

# --- Database backups (manage.py backup_database / restore_drill) ---
# Private bucket for the dumps (they contain health data); without one they go to BACKUP_DIR.
GS_BACKUP_BUCKET_NAME = env("GS_BACKUP_BUCKET_NAME", "")
# Its own service account, allowed only to create objects in that bucket (docs/OPERATIONS.md).
GS_BACKUP_CREDENTIALS = gcs_credentials("GS_BACKUP_CREDENTIALS_JSON")
BACKUP_DIR = env("BACKUP_DIR", str(BASE_DIR / "backups"))
BACKUP_RETENTION_DAYS = int(env("BACKUP_RETENTION_DAYS", "14"))
# 0 leaves the old dumps to the bucket's lifecycle rule: the job then needs no right to delete.
BACKUP_PRUNE = env_bool("BACKUP_PRUNE", True)
# Folder with pg_dump / pg_restore when they are not on the PATH.
PG_BIN_DIR = env("PG_BIN_DIR", "")

# --- Error monitoring (Sentry). Disabled unless SENTRY_DSN is set ---
SENTRY_DSN = env("SENTRY_DSN", "")
SENTRY_ENVIRONMENT = env("SENTRY_ENVIRONMENT", "development")
# Render exposes the deployed commit; any other host can set SENTRY_RELEASE.
SENTRY_RELEASE = env("SENTRY_RELEASE") or env("RENDER_GIT_COMMIT")
SENTRY_TRACES_SAMPLE_RATE = float(env("SENTRY_TRACES_SAMPLE_RATE", "0"))

# --- Data protection (GDPR) ---
# Version of the privacy policy shown in the app; changing it asks every user to accept it again.
PRIVACY_POLICY_VERSION = env("PRIVACY_POLICY_VERSION", "2026-11")
# Accounts deactivated by an admin are deleted for good after this many days.
ACCOUNT_RETENTION_DAYS = int(env("ACCOUNT_RETENTION_DAYS", "365"))

# Password of the demo accounts (seed_demo). Development uses the one in the README; anywhere else
# (seed_demo --allow-production) it must be set, and not to that public one.
DEMO_PASSWORD = env("DEMO_PASSWORD", "")

# --- Business settings ---
# Time of day used as countdown target for the next scheduled workout (see DECISIONS.md).
DEFAULT_TRAINING_TIME = env("DEFAULT_TRAINING_TIME", "18:00")
# Training reminders are emailed within this many minutes before the client's training time; the
# job runs every hour, so keep it at 60 or more.
REMINDER_LEAD_MINUTES = int(env("REMINDER_LEAD_MINUTES", "60"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "apps.core.logging.JsonFormatter"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "json"},
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
    "loggers": {
        "django.db.backends": {"level": "WARNING"},
    },
}
