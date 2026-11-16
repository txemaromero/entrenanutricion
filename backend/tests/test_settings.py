import base64
import importlib
import importlib.util
import runpy
import secrets
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.conf import settings as django_settings
from django.db import connection
from django.urls import clear_url_caches

STRONG_KEY = secrets.token_urlsafe(50)


def reload_module(name: str):
    return importlib.reload(importlib.import_module(name))


def reload_prod(monkeypatch, **variables):
    """Production settings with a strong key and SMTP unless `variables` say otherwise."""
    for name in ("JWT_SIGNING_KEY", "EMAIL_BACKEND", "ALLOW_CONSOLE_EMAIL"):
        monkeypatch.delenv(name, raising=False)
    for name, value in {"DJANGO_SECRET_KEY": STRONG_KEY, **variables}.items():
        monkeypatch.setenv(name, value)
    return reload_module("config.settings.prod")


def test_render_hostname_is_allowed(monkeypatch):
    monkeypatch.setenv("RENDER_EXTERNAL_HOSTNAME", "entrenanutricion-api.onrender.com")
    try:
        base = reload_module("config.settings.base")
        assert "entrenanutricion-api.onrender.com" in base.ALLOWED_HOSTS
        assert "https://entrenanutricion-api.onrender.com" in base.CSRF_TRUSTED_ORIGINS
    finally:
        monkeypatch.delenv("RENDER_EXTERNAL_HOSTNAME")
        reload_module("config.settings.base")


def test_gcs_storage_uses_a_private_bucket_with_signed_urls(monkeypatch):
    from google.oauth2 import service_account

    received = {}

    def fake_credentials(info):
        received.update(info)
        return "credentials"

    monkeypatch.setattr(service_account.Credentials, "from_service_account_info", fake_credentials)
    monkeypatch.setenv("USE_GCS", "1")
    monkeypatch.setenv("GS_BUCKET_NAME", "entrenanutricion-media")
    monkeypatch.setenv("GS_EXPIRATION_MINUTES", "10")
    monkeypatch.setenv("GS_CREDENTIALS_JSON", '{"type": "service_account", "project_id": "demo"}')
    try:
        storage = reload_module("config.settings.base").STORAGES["default"]
    finally:
        for name in ("USE_GCS", "GS_BUCKET_NAME", "GS_EXPIRATION_MINUTES", "GS_CREDENTIALS_JSON"):
            monkeypatch.delenv(name)
        reload_module("config.settings.base")

    assert storage["BACKEND"] == "storages.backends.gcloud.GoogleCloudStorage"
    options = storage["OPTIONS"]
    assert options["bucket_name"] == "entrenanutricion-media"
    assert options["querystring_auth"] is True
    assert options["default_acl"] is None
    assert options["file_overwrite"] is False
    assert options["expiration"].total_seconds() == 600
    assert options["credentials"] == "credentials"
    assert received == {"type": "service_account", "project_id": "demo"}


def test_production_settings_are_hardened(monkeypatch):
    prod = reload_prod(monkeypatch)

    assert prod.DEBUG is False
    assert prod.SECURE_SSL_REDIRECT is True
    assert prod.SECURE_HSTS_SECONDS >= 31536000
    assert prod.SESSION_COOKIE_SECURE and prod.CSRF_COOKIE_SECURE
    assert prod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
    assert prod.STORAGES["staticfiles"]["BACKEND"].startswith("whitenoise")
    # No Django admin nor public API docs unless a staging environment turns them on.
    assert prod.ADMIN_ENABLED is False
    assert prod.API_DOCS_PUBLIC is False


def test_production_requires_a_secret_key(monkeypatch):
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError):
        reload_module("config.settings.prod")


@pytest.mark.django_db
def test_media_can_be_served_by_django_on_the_local_production_stack(settings, client, tmp_path):
    (tmp_path / "hello.txt").write_text("hi", encoding="utf-8")
    (tmp_path / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "clip.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42")
    settings.MEDIA_ROOT = tmp_path
    settings.SERVE_MEDIA = True
    try:
        reload_module("config.urls")
        clear_url_caches()
        response = client.get("/media/hello.txt")
        assert response.status_code == 200
        # Never rendered as a page: only the declared type, and inline only for images.
        image = client.get("/media/photo.png")
        assert image["X-Content-Type-Options"] == "nosniff"
        assert not image.has_header("Cache-Control")  # no-store is for the API only
        assert image["Content-Disposition"].startswith("inline")
        video = client.get("/media/clip.mp4")
        assert video["X-Content-Type-Options"] == "nosniff"
        assert video["Content-Disposition"] == 'attachment; filename="clip.mp4"'
        for served in (response, image, video):
            served.close()
    finally:
        settings.SERVE_MEDIA = False
        reload_module("config.urls")
        clear_url_caches()

    assert client.get("/media/hello.txt").status_code == 404


class TestMonitoring:
    def test_events_leave_no_personal_data(self):
        from apps.core.monitoring import scrub_event

        event = {
            "user": {"email": "ana@example.com"},
            "request": {
                "url": "https://api.example.com/api/v1/me/onboarding",
                "query_string": "token=abc",
                "data": {"health": {"medical_conditions": ["diabetes"]}},
                "cookies": {"en_refresh": "secret"},
                "env": {"REMOTE_ADDR": "1.2.3.4"},
                "headers": {"Authorization": "Bearer x", "Cookie": "a=b", "User-Agent": "UA"},
            },
        }

        scrubbed = scrub_event(event)

        assert "user" not in scrubbed
        assert scrubbed["request"] == {
            "url": "https://api.example.com/api/v1/me/onboarding",
            "headers": {"User-Agent": "UA"},
        }

    def test_sentry_is_off_without_a_dsn(self, monkeypatch):
        import sentry_sdk

        from apps.core.monitoring import init_sentry

        calls = []
        monkeypatch.setattr(sentry_sdk, "init", lambda **kwargs: calls.append(kwargs))

        assert init_sentry("", environment="production") is False
        assert calls == []

    def test_production_starts_sentry_without_personal_data(self, monkeypatch):
        import sentry_sdk

        calls = []
        monkeypatch.setattr(sentry_sdk, "init", lambda **kwargs: calls.append(kwargs))
        monkeypatch.setenv("SENTRY_DSN", "https://key@o0.ingest.sentry.io/1")
        monkeypatch.setenv("RENDER_GIT_COMMIT", "abc123")
        try:
            reload_module("config.settings.base")
            reload_prod(monkeypatch)
        finally:
            monkeypatch.delenv("SENTRY_DSN")
            monkeypatch.delenv("RENDER_GIT_COMMIT")
            reload_module("config.settings.base")

        assert len(calls) == 1
        options = calls[0]
        assert options["environment"] == "production"
        assert options["release"] == "abc123"
        assert options["send_default_pii"] is False
        assert options["max_request_body_size"] == "never"
        assert options["traces_sample_rate"] == 0.0


@pytest.mark.django_db
def test_without_admin_nor_docs_their_urls_do_not_exist(settings, client):
    settings.ADMIN_ENABLED = False
    settings.API_DOCS_PUBLIC = False
    try:
        reload_module("config.urls")
        clear_url_caches()
        for url in ("/admin/", "/admin/login/", "/api/docs/", "/api/schema/"):
            assert client.get(url).status_code == 404, url
        assert client.get("/api/v1/health").status_code == 200
    finally:
        settings.ADMIN_ENABLED = True
        settings.API_DOCS_PUBLIC = True
        reload_module("config.urls")
        clear_url_caches()

    assert client.get("/api/schema/").status_code == 200


@pytest.mark.django_db
def test_the_rate_limits_share_a_cache_table_created_by_migrate(settings):
    from config.settings import base

    # Every gunicorn worker counts in the same place (not 3 times each limit with 3 workers).
    assert base.CACHES["default"]["BACKEND"] == "django.core.cache.backends.db.DatabaseCache"
    settings.CACHES = base.CACHES
    migration = importlib.import_module("apps.core.migrations.0001_cache_table")
    with connection.schema_editor() as editor:
        migration.create_cache_table(None, editor)

    assert "django_cache" in connection.introspection.table_names()


def test_the_backups_have_a_service_account_of_their_own(monkeypatch):
    from google.oauth2 import service_account

    monkeypatch.setattr(
        service_account.Credentials, "from_service_account_info", lambda info: info["client_email"]
    )
    monkeypatch.delenv("GS_CREDENTIALS_JSON", raising=False)
    monkeypatch.setenv("GS_BACKUP_CREDENTIALS_JSON", '{"client_email": "backups@demo.iam"}')
    try:
        base = reload_module("config.settings.base")
        assert base.GS_BACKUP_CREDENTIALS == "backups@demo.iam"
        assert base.GS_CREDENTIALS is None
    finally:
        monkeypatch.delenv("GS_BACKUP_CREDENTIALS_JSON")
        reload_module("config.settings.base")


class TestProductionKeys:
    @pytest.mark.parametrize(
        "key",
        [
            "dev-insecure-secret-key-change-me-in-production",  # default of base.py
            "change-me-to-a-long-random-string",  # .env.example
            "local-prod-test-key-change-me-0123456789abcdefghijklmnop",  # old compose default
            "test-secret-key-not-for-production-use-0123456789",  # config/settings/test.py
            "an-example-key-for-the-docs-0123456789abcdefghijklmn",
            "x" * 60,
            "Short#Random9",
        ],
    )
    def test_weak_or_published_keys_are_refused(self, monkeypatch, key):
        with pytest.raises(RuntimeError, match="DJANGO_SECRET_KEY is too weak"):
            reload_prod(monkeypatch, DJANGO_SECRET_KEY=key)

    def test_generated_keys_are_accepted(self, monkeypatch):
        # Like Render's generateValue: 256 random bits in base64, shorter than 50 characters.
        generated = base64.b64encode(secrets.token_bytes(32)).decode()

        prod = reload_prod(monkeypatch, DJANGO_SECRET_KEY=generated)  # no RuntimeError

        assert prod.DEBUG is False

    def test_the_session_tokens_can_have_a_key_of_their_own(self, monkeypatch):
        with pytest.raises(RuntimeError, match="JWT_SIGNING_KEY is too weak"):
            reload_prod(monkeypatch, JWT_SIGNING_KEY="change-me")
        assert reload_prod(monkeypatch, JWT_SIGNING_KEY="")  # empty: SECRET_KEY signs them

        jwt_key = secrets.token_urlsafe(50)
        monkeypatch.setenv("JWT_SIGNING_KEY", jwt_key)
        try:
            assert reload_module("config.settings.base").SIMPLE_JWT["SIGNING_KEY"] == jwt_key
        finally:
            monkeypatch.delenv("JWT_SIGNING_KEY")
            base = reload_module("config.settings.base")
        assert base.SIMPLE_JWT["SIGNING_KEY"] == base.SECRET_KEY


class TestProductionEmail:
    def test_smtp_by_default(self, monkeypatch):
        prod = reload_prod(monkeypatch)

        assert prod.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"

    @pytest.mark.parametrize("backend", ["console", "filebased", "locmem", "dummy"])
    def test_backends_that_send_nothing_are_refused(self, monkeypatch, backend):
        # The reset and confirmation links would end up in the logs.
        with pytest.raises(RuntimeError, match="ALLOW_CONSOLE_EMAIL=1"):
            reload_prod(
                monkeypatch, EMAIL_BACKEND=f"django.core.mail.backends.{backend}.EmailBackend"
            )

    def test_unless_a_test_environment_allows_it(self, monkeypatch):
        console = "django.core.mail.backends.console.EmailBackend"

        prod = reload_prod(monkeypatch, EMAIL_BACKEND=console, ALLOW_CONSOLE_EMAIL="1")

        assert console == prod.EMAIL_BACKEND


@pytest.mark.django_db
def test_api_answers_are_never_stored(client, auth_api, client_user):
    for response in (
        client.get("/api/v1/health"),
        client.get("/api/v1/me"),  # 401
        auth_api(client_user).get("/api/v1/me"),
        client.post("/api/v1/auth/login", {}, content_type="application/json"),  # 400
    ):
        assert response["Cache-Control"] == "no-store"


class TestGunicorn:
    CONF = Path(django_settings.BASE_DIR) / "gunicorn.conf.py"

    def load(self, monkeypatch, **variables):
        for name, value in variables.items():
            monkeypatch.setenv(name, value)
        return runpy.run_path(str(self.CONF))

    def test_port_workers_and_logs_from_the_environment(self, monkeypatch):
        conf = self.load(monkeypatch, PORT="10000", WEB_CONCURRENCY="2")

        assert conf["bind"] == "0.0.0.0:10000"
        assert conf["workers"] == 2
        assert conf["accesslog"] == conf["errorlog"] == "-"

    def test_the_access_log_leaves_out_queries_referrers_and_agents(self, monkeypatch):
        log_format = self.load(monkeypatch)["access_log_format"]

        assert "%(U)s" in log_format  # the path, without the query string
        for atom in ("%(r)s", "%(q)s", "%(f)s", "%(a)s", "%(u)s", "{"):
            assert atom not in log_format

    @pytest.mark.skipif(importlib.util.find_spec("fcntl") is None, reason="gunicorn needs Unix")
    def test_a_real_access_line(self, monkeypatch):
        from gunicorn.config import Config
        from gunicorn.glogging import Logger

        referrer = "https://app.example.com/reset-password?uid=MQ&token=secret-token"
        environ = {
            "REQUEST_METHOD": "GET",
            "RAW_URI": "/api/v1/auth/email-exists?email=ana%40example.com",
            "PATH_INFO": "/api/v1/auth/email-exists",
            "QUERY_STRING": "email=ana%40example.com",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "REMOTE_ADDR": "10.0.0.1",
            "HTTP_REFERER": referrer,
            "HTTP_USER_AGENT": "Mozilla/5.0 (Ana's phone)",
        }
        response = SimpleNamespace(status="200 OK", sent=17, headers=[])
        request = SimpleNamespace(headers=[("REFERER", referrer)])
        atoms = Logger(Config()).atoms(response, request, environ, timedelta(milliseconds=12))

        line = self.load(monkeypatch)["access_log_format"] % atoms

        assert '"GET /api/v1/auth/email-exists HTTP/1.1" 200 17 12ms' in line
        for secret in ("ana", "token", "Mozilla"):
            assert secret not in line
