import tempfile

from .base import *  # noqa: F403
from .base import MIDDLEWARE, REST_FRAMEWORK, SIMPLE_JWT

DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production-use-0123456789"
# Background work (apps/core/background.py) runs inline, so tests see its effect at once.
BACKGROUND_TASKS_INLINE = True
SIMPLE_JWT = {**SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}
ALLOWED_HOSTS = ["testserver", "localhost"]
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m]

# Fast hashing keeps the suite quick; Argon2 is covered by a dedicated test.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

MEDIA_ROOT = tempfile.mkdtemp(prefix="entrenanutricion-test-media-")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Per process is fine here (conftest clears it between tests) and needs no table.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "login": "1000/min",
    "login_account": "1000/min",
    "register": "1000/min",
    "password": "1000/min",
    "email_exists": "1000/min",
    "session": "1000/min",
    "data_export": "1000/min",
    "password_reset": "1000/min",
    "notes": "1000/min",
    "email_verification": "1000/min",
    "email_verification_resend": "1000/min",
    "uploads": "1000/min",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"], "level": "CRITICAL"},
}
