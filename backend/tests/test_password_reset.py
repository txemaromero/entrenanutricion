import re
import threading
from datetime import timedelta

import pytest
from django.core import mail
from freezegun import freeze_time
from rest_framework.settings import api_settings
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts import emails, services
from apps.accounts.emails import language_from_header
from apps.accounts.tokens import issue_tokens
from tests.factories import DEFAULT_PASSWORD, UserFactory, refresh_with

REQUEST = "/api/v1/auth/password-reset"
CONFIRM = "/api/v1/auth/password-reset/confirm"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
NEW_PASSWORD = "N3w#Password"

pytestmark = pytest.mark.django_db


def link_params(message) -> dict[str, str]:
    match = re.search(r"/reset-password\?uid=([\w-]+)&token=([\w-]+)", message.body)
    assert match, message.body
    return {"uid": match.group(1), "token": match.group(2)}


def request_link(api_client, user, language="es") -> dict[str, str]:
    mail.outbox.clear()
    response = api_client.post(REQUEST, {"email": user.email}, HTTP_ACCEPT_LANGUAGE=language)
    assert response.status_code == 204
    assert len(mail.outbox) == 1
    return link_params(mail.outbox[0])


def confirm(api_client, params, password=NEW_PASSWORD, confirm_password=None):
    return api_client.post(
        CONFIRM,
        {**params, "new_password": password, "confirm_password": confirm_password or password},
    )


class TestRequest:
    def test_sends_a_single_use_link_to_the_account_email(self, api_client, settings):
        settings.FRONTEND_URL = "https://app.example.com"
        user = UserFactory(email="ana@example.com", first_name="Ana")

        response = api_client.post(REQUEST, {"email": "ANA@example.com"})

        assert response.status_code == 204
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == [user.email]
        assert "https://app.example.com/reset-password?uid=" in message.body
        assert "Hola, Ana" in message.body
        assert "60 minutos" in message.body

    @pytest.mark.parametrize(
        ("header", "subject"),
        [
            ("en-GB,en;q=0.9", "Reset your entrenanutricion password"),
            ("ca", "Restableix la contrasenya d'entrenanutricion"),
            ("fr-FR, es;q=0.8", "Restablece tu contraseña de entrenanutricion"),
            ("", "Restablece tu contraseña de entrenanutricion"),
        ],
    )
    def test_email_follows_the_app_language(self, api_client, header, subject):
        user = UserFactory()

        api_client.post(REQUEST, {"email": user.email}, HTTP_ACCEPT_LANGUAGE=header)

        assert mail.outbox[0].subject == subject

    def test_unknown_email_gets_the_same_answer_and_no_email(self, api_client):
        response = api_client.post(REQUEST, {"email": "nobody@example.com"})

        assert response.status_code == 204
        assert mail.outbox == []

    def test_deactivated_accounts_get_no_email(self, api_client):
        user = UserFactory(is_active=False)

        assert api_client.post(REQUEST, {"email": user.email}).status_code == 204
        assert mail.outbox == []

    def test_invalid_email_is_a_validation_error(self, api_client):
        response = api_client.post(REQUEST, {"email": "not-an-email"})

        assert response.status_code == 400
        assert response.json()["field_codes"] == {"email": ["invalid"]}

    def test_mail_server_errors_are_logged_not_leaked(self, api_client, monkeypatch, caplog):
        def broken_send_mail(*args, **kwargs):
            raise OSError("SMTP down")

        monkeypatch.setattr(emails, "send_mail", broken_send_mail)
        user = UserFactory()

        with caplog.at_level("ERROR", logger="apps.api"):
            response = api_client.post(REQUEST, {"email": user.email})

        assert response.status_code == 204
        assert "Could not send the password reset email" in caplog.text

    def test_is_throttled(self, api_client, monkeypatch):
        monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"password_reset": "2/min"})

        codes = [api_client.post(REQUEST, {"email": "x@example.com"}).status_code for _ in range(3)]

        assert codes == [204, 204, 429]


class TestConfirm:
    def test_sets_the_new_password(self, api_client):
        user = UserFactory()
        params = request_link(api_client, user)

        response = confirm(api_client, params)

        assert response.status_code == 204
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)
        login = api_client.post(LOGIN, {"email": user.email, "password": NEW_PASSWORD})
        assert login.status_code == 200
        old_login = api_client.post(LOGIN, {"email": user.email, "password": DEFAULT_PASSWORD})
        assert old_login.status_code == 401

    def test_closes_every_open_session(self, api_client):
        user = UserFactory()
        refresh = issue_tokens(user)["refresh"]
        params = request_link(api_client, user)

        confirm(api_client, params)

        response = refresh_with(api_client, refresh)
        assert response.status_code == 401

    def test_access_tokens_issued_before_the_reset_stop_working(self, api_client):
        user = UserFactory()
        with freeze_time("2026-11-06 10:00:00"):
            access = issue_tokens(user)["access"]
        with freeze_time("2026-11-06 10:05:00"):
            confirm(api_client, request_link(api_client, user))
            api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
            response = api_client.get("/api/v1/me")

        assert response.status_code == 401
        assert response.json()["code"] == "token_not_valid"

    def test_link_works_only_once(self, api_client):
        user = UserFactory()
        params = request_link(api_client, user)
        assert confirm(api_client, params).status_code == 204

        response = confirm(api_client, params, password="Other#Pass9")

        assert response.status_code == 400
        assert response.json()["code"] == "reset_link_invalid"
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)

    @pytest.mark.parametrize(("elapsed", "status_code"), [(3599, 204), (3601, 400)])
    def test_link_expires(self, api_client, settings, elapsed, status_code):
        settings.PASSWORD_RESET_TIMEOUT = 3600
        user = UserFactory()
        with freeze_time("2026-03-02 10:00:00") as clock:
            params = request_link(api_client, user)
            clock.tick(timedelta(seconds=elapsed))
            response = confirm(api_client, params)

        assert response.status_code == status_code
        if status_code == 400:
            assert response.json()["code"] == "reset_link_invalid"

    @pytest.mark.parametrize(
        "params",
        [
            {"uid": "bm90LWEtdXNlcg", "token": "abc-123"},
            {"uid": "!!", "token": "abc-123"},
            {"uid": "OTk5OTk", "token": "abc-123"},
        ],
    )
    def test_tampered_links_are_rejected(self, api_client, params):
        response = confirm(api_client, params)

        assert response.status_code == 400
        assert response.json()["code"] == "reset_link_invalid"

    def test_token_of_another_user_is_rejected(self, api_client):
        first, second = UserFactory(), UserFactory()
        params = request_link(api_client, first)
        other = request_link(api_client, second)

        response = confirm(api_client, {"uid": other["uid"], "token": params["token"]})

        assert response.json()["code"] == "reset_link_invalid"

    def test_deactivated_account_cannot_use_an_old_link(self, api_client):
        user = UserFactory()
        params = request_link(api_client, user)
        user.is_active = False
        user.save()

        assert confirm(api_client, params).json()["code"] == "reset_link_invalid"

    def test_new_password_follows_the_policy(self, api_client):
        user = UserFactory()
        params = request_link(api_client, user)

        response = confirm(api_client, params, password="weakpass")

        assert response.status_code == 400
        codes = response.json()["field_codes"]["new_password"]
        assert {"password_no_upper", "password_no_digit", "password_no_symbol"} <= set(codes)
        user.refresh_from_db()
        assert user.check_password(DEFAULT_PASSWORD)

    def test_passwords_must_match(self, api_client):
        user = UserFactory()
        params = request_link(api_client, user)

        response = confirm(api_client, params, confirm_password="Different#1")

        assert response.json()["field_codes"] == {"confirm_password": ["passwords_do_not_match"]}

    def test_missing_fields_are_required(self, api_client):
        response = api_client.post(CONFIRM, {})

        assert response.status_code == 400
        assert set(response.json()["field_codes"]) == {
            "uid",
            "token",
            "new_password",
            "confirm_password",
        }


@pytest.mark.parametrize(
    ("header", "language"),
    [(None, "es"), ("en", "en"), ("ca-ES,ca;q=0.9", "ca"), ("de, fr", "es"), ("EN-us", "en")],
)
def test_language_from_header(header, language):
    assert language_from_header(header) == language


class TestTiming:
    def test_the_answer_does_not_wait_for_the_email(self, api_client, settings, monkeypatch):
        """Waiting for the mail server only for existing accounts would reveal them."""
        settings.BACKGROUND_TASKS_INLINE = False
        release, sent = threading.Event(), threading.Event()

        def slow_send(user, link, language):
            release.wait(timeout=10)
            sent.set()

        monkeypatch.setattr(services, "send_password_reset_email", slow_send)
        user = UserFactory()

        response = api_client.post(REQUEST, {"email": user.email})

        assert response.status_code == 204
        assert not sent.is_set()  # answered while the email was still on its way
        release.set()
        assert sent.wait(timeout=10)


def test_a_new_password_lifts_the_pause_on_the_account(api_client, monkeypatch):
    monkeypatch.setitem(api_settings.DEFAULT_THROTTLE_RATES, "login_account", "2/hour")
    user = UserFactory()
    wrong = {"email": user.email, "password": "Wrong#Pass1"}
    for _ in range(2):
        assert api_client.post(LOGIN, wrong).status_code == 401
    assert api_client.post(LOGIN, wrong).status_code == 429

    confirm(api_client, request_link(api_client, user))

    response = api_client.post(LOGIN, {"email": user.email, "password": NEW_PASSWORD})
    assert response.status_code == 200


class TestEmailsPerAddress:
    def test_one_email_every_two_minutes_with_the_same_answer(self, api_client):
        user = UserFactory(email="ana@example.com")
        with freeze_time("2026-11-09 10:00:00") as clock:
            first = api_client.post(REQUEST, {"email": user.email})
            second = api_client.post(REQUEST, {"email": "ANA@example.com"})

            assert first.status_code == second.status_code == 204
            assert len(mail.outbox) == 1

            clock.tick(timedelta(seconds=121))
            api_client.post(REQUEST, {"email": user.email})
            assert len(mail.outbox) == 2

    def test_the_cache_keeps_a_hash_not_the_address(self, api_client):
        from django.core.cache import cache

        UserFactory(email="ana@example.com")
        api_client.post(REQUEST, {"email": "ana@example.com"})

        assert "ana@example.com" not in str(cache._cache.keys())
