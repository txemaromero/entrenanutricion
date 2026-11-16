from datetime import timedelta

import pytest
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.settings import api_settings
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts import login_attempts
from apps.accounts.models import Role, User, UserStatus
from apps.accounts.tokens import SessionRefreshToken, issue_tokens
from config.settings import base as base_settings
from tests.factories import DEFAULT_PASSWORD, UserFactory, refresh_with

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
EMAIL_EXISTS = "/api/v1/auth/email-exists"
COOKIE = "entrenanutricion_refresh"
APP_HEADER = "entrenanutricion"

pytestmark = pytest.mark.django_db


def register_payload(**overrides):
    payload = {
        "first_name": "María José",
        "last_name": "Núñez-Çelik",
        "email": "Maria@Example.com",
        "password": "Str0ng#Pass",
        "birth_date": "1995-03-10",
        "gender": "F",
        "terms_accepted": True,
        "health_data_consent": True,
    }
    payload.update(overrides)
    return payload


def cookie_of(response):
    return response.cookies[COOKIE]


def lifetime(token: str) -> timedelta:
    payload = SessionRefreshToken(token, verify=False).payload
    return timedelta(seconds=payload["exp"] - payload["iat"])


class TestRegister:
    def test_creates_pending_client_and_returns_tokens(self, api_client):
        response = api_client.post(REGISTER, register_payload())

        assert response.status_code == 201
        body = response.json()
        assert body["access"] and "refresh" not in body
        assert cookie_of(response).value
        assert body["user"]["email"] == "maria@example.com"
        assert body["user"]["role"] == Role.CLIENT
        assert body["user"]["status"] == UserStatus.PENDING_ONBOARDING
        assert body["user"]["onboarding_completed"] is False
        user = User.objects.get(email="maria@example.com")
        assert user.terms_accepted_at is not None
        assert user.check_password("Str0ng#Pass")

    def test_rejects_duplicated_email_case_insensitive(self, api_client):
        UserFactory(email="maria@example.com")

        response = api_client.post(REGISTER, register_payload(email="MARIA@example.COM"))

        assert response.status_code == 400
        assert response.json()["field_codes"]["email"] == ["email_taken"]

    @pytest.mark.parametrize(
        ("password", "code"),
        [
            ("Ab1#xyz", "password_too_short"),
            ("lowercase1#", "password_no_upper"),
            ("UPPERCASE1#", "password_no_lower"),
            ("NoDigits#ab", "password_no_digit"),
            ("NoSymbol123", "password_no_symbol"),
        ],
    )
    def test_password_policy(self, api_client, password, code):
        response = api_client.post(REGISTER, register_payload(password=password))

        assert response.status_code == 400
        assert code in response.json()["field_codes"]["password"]

    @pytest.mark.parametrize(
        "name", ["Ana", "María José", "O'Connor", "Jean-Luc", "Çelik", "Núñez"]
    )
    def test_accepts_valid_names(self, api_client, name):
        response = api_client.post(REGISTER, register_payload(first_name=name))

        assert response.status_code == 201

    @pytest.mark.parametrize("name", ["Ana3", "Ana!", "Ana  María", "-Ana", "Ana_"])
    def test_rejects_invalid_names(self, api_client, name):
        response = api_client.post(REGISTER, register_payload(last_name=name))

        assert response.status_code == 400
        assert response.json()["field_codes"]["last_name"] == ["invalid_name"]

    @freeze_time("2026-06-15")
    @pytest.mark.parametrize(
        ("birth_date", "status_code", "code"),
        [
            ("2008-06-15", 201, None),  # exactly 18 today
            ("2008-06-16", 400, "too_young"),
            ("1906-06-15", 201, None),  # exactly 120
            ("1905-06-15", 400, "too_old"),  # 121 today
        ],
    )
    def test_age_limits(self, api_client, birth_date, status_code, code):
        response = api_client.post(REGISTER, register_payload(birth_date=birth_date))

        assert response.status_code == status_code
        if code:
            assert response.json()["field_codes"]["birth_date"] == [code]

    def test_terms_must_be_accepted(self, api_client):
        response = api_client.post(REGISTER, register_payload(terms_accepted=False))

        assert response.status_code == 400
        assert response.json()["field_codes"]["terms_accepted"] == ["terms_required"]

    def test_reports_every_missing_field(self, api_client):
        response = api_client.post(REGISTER, {})

        body = response.json()
        assert response.status_code == 400
        assert body["code"] == "validation_error"
        assert set(body["fields"]) == {
            "first_name",
            "last_name",
            "email",
            "password",
            "birth_date",
            "gender",
            "terms_accepted",
            "health_data_consent",
        }

    def test_rejects_unknown_gender(self, api_client):
        response = api_client.post(REGISTER, register_payload(gender="X"))

        assert response.status_code == 400
        assert response.json()["field_codes"]["gender"] == ["invalid_choice"]


class TestEmailExists:
    def test_reports_existing_email_case_insensitive(self, api_client):
        UserFactory(email="taken@example.com")

        response = api_client.get(EMAIL_EXISTS, {"email": "TAKEN@example.com"})

        assert response.status_code == 200
        assert response.json() == {"exists": True}

    def test_reports_free_email(self, api_client):
        response = api_client.get(EMAIL_EXISTS, {"email": "free@example.com"})

        assert response.json() == {"exists": False}

    def test_requires_a_valid_email(self, api_client):
        response = api_client.get(EMAIL_EXISTS, {"email": "not-an-email"})

        assert response.status_code == 400
        assert "email" in response.json()["fields"]


class TestLogin:
    def test_returns_tokens_and_user(self, api_client):
        user = UserFactory(email="ana@example.com")

        response = api_client.post(
            LOGIN, {"email": "ANA@example.com", "password": DEFAULT_PASSWORD}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["user"]["id"] == user.id
        assert body.keys() == {"access", "user"}

    def test_the_refresh_token_is_an_http_only_cookie(self, api_client, settings):
        settings.AUTH_COOKIE_SECURE = True
        UserFactory(email="ana@example.com")

        response = api_client.post(
            LOGIN, {"email": "ana@example.com", "password": DEFAULT_PASSWORD}
        )

        cookie = cookie_of(response)
        assert cookie["httponly"] is True
        assert cookie["secure"] is True
        assert cookie["samesite"] == "Lax"
        assert cookie["path"] == "/api/v1/auth/"

    @pytest.mark.parametrize(
        "credentials",
        [
            {"email": "ana@example.com", "password": "Wrong#Pass1"},
            {"email": "nobody@example.com", "password": DEFAULT_PASSWORD},
        ],
    )
    def test_rejects_bad_credentials_with_specific_code(self, api_client, credentials):
        UserFactory(email="ana@example.com")

        response = api_client.post(LOGIN, credentials)

        assert response.status_code == 401
        assert response.json()["code"] == "invalid_credentials"

    def test_rejects_inactive_user(self, api_client):
        UserFactory(email="gone@example.com", is_active=False, status=UserStatus.INACTIVE)

        response = api_client.post(
            LOGIN, {"email": "gone@example.com", "password": DEFAULT_PASSWORD}
        )

        assert response.status_code == 401
        assert response.json()["code"] == "invalid_credentials"

    def test_refresh_lifetime_is_12_hours_without_remember_me(self, api_client):
        UserFactory(email="ana@example.com")

        response = api_client.post(
            LOGIN, {"email": "ana@example.com", "password": DEFAULT_PASSWORD}
        )

        assert lifetime(cookie_of(response).value) == timedelta(hours=12)
        assert cookie_of(response)["max-age"] == ""  # session cookie: gone with the browser

    def test_refresh_lifetime_is_7_days_with_remember_me(self, api_client):
        UserFactory(email="ana@example.com")

        response = api_client.post(
            LOGIN, {"email": "ana@example.com", "password": DEFAULT_PASSWORD, "remember_me": True}
        )

        assert lifetime(cookie_of(response).value) == timedelta(days=7)
        assert cookie_of(response)["max-age"] == 7 * 24 * 3600

    def test_access_token_lasts_15_minutes(self, api_client):
        UserFactory(email="ana@example.com")
        with freeze_time("2026-03-01 10:00:00") as frozen:
            access = api_client.post(
                LOGIN, {"email": "ana@example.com", "password": DEFAULT_PASSWORD}
            ).json()["access"]
            api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
            assert api_client.get("/api/v1/me").status_code == 200

            frozen.tick(timedelta(minutes=16))
            response = api_client.get("/api/v1/me")

        assert response.status_code == 401
        assert response.json()["code"] == "token_not_valid"


class TestRefreshAndLogout:
    """The refresh token lives in an httpOnly cookie; the app sends X-Requested-With."""

    def login(self, api_client, remember=False):
        UserFactory(email="ana@example.com")
        return api_client.post(
            LOGIN,
            {"email": "ana@example.com", "password": DEFAULT_PASSWORD, "remember_me": remember},
        )

    def refresh(self, api_client, **extra):
        return api_client.post(REFRESH, {}, HTTP_X_REQUESTED_WITH=APP_HEADER, **extra)

    def test_rotates_the_cookie_and_blacklists_the_old_token(self, api_client):
        first = cookie_of(self.login(api_client)).value

        rotated = self.refresh(api_client)

        assert rotated.status_code == 200
        assert rotated.json().keys() == {"access"}
        assert cookie_of(rotated).value != first
        reused = refresh_with(api_client, first)
        assert reused.status_code == 401
        assert reused.json()["code"] == "token_not_valid"

    def test_the_cookie_needs_the_application_header(self, api_client):
        self.login(api_client)

        response = api_client.post(REFRESH, {})

        assert response.status_code == 403
        assert response.json()["code"] == "csrf_failed"

    def test_without_a_session(self, api_client):
        response = api_client.post(REFRESH, {}, HTTP_X_REQUESTED_WITH=APP_HEADER)

        assert response.status_code == 401
        assert response.json()["code"] == "not_authenticated"

    def test_remembered_session_keeps_long_lifetime_after_rotation(self, api_client):
        self.login(api_client, remember=True)

        cookie = cookie_of(self.refresh(api_client))

        assert lifetime(cookie.value) == timedelta(days=7)
        assert cookie["max-age"] == 7 * 24 * 3600

    def test_a_token_in_the_body_is_ignored(self, api_client):
        # Only the httpOnly cookie counts: a token copied out of the browser is useless elsewhere.
        user = UserFactory(email="ana@example.com")
        token = issue_tokens(user, remember=True)["refresh"]

        response = api_client.post(REFRESH, {"refresh": token}, HTTP_X_REQUESTED_WITH=APP_HEADER)

        assert response.status_code == 401
        assert response.json()["code"] == "not_authenticated"

    def test_refresh_fails_for_deactivated_user(self, api_client):
        self.login(api_client)
        User.objects.filter(email="ana@example.com").update(is_active=False)

        assert self.refresh(api_client).status_code == 401

    def test_refresh_fails_for_deleted_user(self, api_client):
        self.login(api_client)
        User.objects.filter(email="ana@example.com").delete()

        assert self.refresh(api_client).status_code == 401

    def test_logout_blacklists_the_token_and_deletes_the_cookie(self, api_client):
        token = cookie_of(self.login(api_client)).value

        logout = api_client.post(LOGOUT, {}, HTTP_X_REQUESTED_WITH=APP_HEADER)

        assert logout.status_code == 204
        assert cookie_of(logout).value == ""
        assert cookie_of(logout)["max-age"] == 0
        assert refresh_with(api_client, token).status_code == 401

    def test_logout_always_ends_the_session(self, api_client):
        api_client.cookies[COOKIE] = "garbage"
        assert api_client.post(LOGOUT, {}, HTTP_X_REQUESTED_WITH=APP_HEADER).status_code == 204
        assert api_client.post(LOGOUT, {}).status_code == 204


class TestSecurity:
    def test_protected_endpoint_requires_authentication(self, api_client):
        response = api_client.get("/api/v1/me")

        assert response.status_code == 401
        assert response.json()["code"] == "not_authenticated"

    def test_login_is_throttled(self, api_client, monkeypatch):
        monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"login": "2/min"})
        payload = {"email": "x@example.com", "password": "Wrong#Pass1"}

        codes = [api_client.post(LOGIN, payload).status_code for _ in range(3)]

        assert codes == [401, 401, 429]
        assert api_client.post(LOGIN, payload).json()["code"] == "throttled"

    def test_a_fake_forwarded_for_header_does_not_dodge_the_limit(self, api_client, monkeypatch):
        monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"login": "2/min"})
        payload = {"email": "x@example.com", "password": "Wrong#Pass1"}

        codes = [
            api_client.post(LOGIN, payload, HTTP_X_FORWARDED_FOR=f"10.0.0.{n}").status_code
            for n in range(3)
        ]

        assert codes == [401, 401, 429]

    def test_behind_a_proxy_the_address_it_appends_is_the_client(
        self, api_client, monkeypatch, settings
    ):
        settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "NUM_PROXIES": 1}
        monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"login": "2/min"})
        payload = {"email": "x@example.com", "password": "Wrong#Pass1"}

        def attempt(forwarded_for):
            return api_client.post(LOGIN, payload, HTTP_X_FORWARDED_FOR=forwarded_for).status_code

        # Whatever the client writes first, the proxy appends the real address at the end.
        assert [attempt(f"6.6.6.{n}, 203.0.113.7") for n in range(3)] == [401, 401, 429]
        assert attempt("198.51.100.4") == 401

    def test_argon2_is_the_production_hasher(self, settings):
        assert base_settings.PASSWORD_HASHERS[0].endswith("Argon2PasswordHasher")
        settings.PASSWORD_HASHERS = base_settings.PASSWORD_HASHERS
        assert make_password("Secret#1a", hasher="argon2").startswith("argon2")


class TestPasswordPolicy:
    @pytest.mark.parametrize(
        ("overrides", "code"),
        [
            ({"password": "P@ssw0rd"}, "password_too_common"),
            ({"first_name": "Valentina", "password": "Valentina#1"}, "password_too_similar"),
            ({"email": "valentina@example.com", "password": "Valentina#1"}, "password_too_similar"),
        ],
    )
    def test_common_or_personal_passwords_are_refused(self, api_client, overrides, code):
        response = api_client.post(REGISTER, register_payload(**overrides))

        assert response.status_code == 400
        assert code in response.json()["field_codes"]["password"]
        assert not User.objects.exists()

    def test_accounts_created_by_an_admin_too(self, auth_api, admin_user):
        payload = register_payload(first_name="Valentina", password="Valentina#1", role="trainer")

        response = auth_api(admin_user).post("/api/v1/users", payload)

        assert response.status_code == 400
        assert response.json()["field_codes"]["password"] == ["password_too_similar"]


class TestLoginPerAccount:
    """Failed sign-ins are limited per account and machine, with a higher total per account."""

    @pytest.fixture(autouse=True)
    def three_failures_per_hour(self, monkeypatch):
        monkeypatch.setitem(api_settings.DEFAULT_THROTTLE_RATES, "login_account", "3/hour")

    def attempt(self, api_client, password="Wrong#Pass1", email="ana@example.com", ip="10.0.0.1"):
        return api_client.post(LOGIN, {"email": email, "password": password}, REMOTE_ADDR=ip)

    def test_one_machine_only_pauses_itself(self, api_client):
        UserFactory(email="ana@example.com")
        for _ in range(3):
            assert self.attempt(api_client, ip="10.0.0.9").status_code == 401

        # Not even the right password from that machine, until the period is over...
        response = self.attempt(api_client, password=DEFAULT_PASSWORD, ip="10.0.0.9")
        assert response.status_code == 429
        assert response.json()["code"] == "throttled"
        assert 0 < int(response["Retry-After"]) <= 3600
        # ...but the owner, from their own, is not locked out.
        assert self.attempt(api_client, password=DEFAULT_PASSWORD).status_code == 200

    def test_the_pause_ends_with_the_period(self, api_client):
        UserFactory(email="ana@example.com")
        for _ in range(3):
            self.attempt(api_client)
        assert self.attempt(api_client, password=DEFAULT_PASSWORD).status_code == 429

        with freeze_time(timezone.now() + timedelta(hours=1, seconds=1)):
            assert self.attempt(api_client, password=DEFAULT_PASSWORD).status_code == 200

    def test_many_machines_have_a_total(self, api_client):
        UserFactory(email="ana@example.com")
        total = 3 * login_attempts.ACCOUNT_TOTAL_FACTOR
        for number in range(total):
            assert self.attempt(api_client, ip=f"10.0.{number}.1").status_code == 401

        response = self.attempt(api_client, password=DEFAULT_PASSWORD, ip="10.1.1.1")

        assert response.status_code == 429

    def test_signing_in_starts_the_count_again(self, api_client):
        UserFactory(email="ana@example.com")
        self.attempt(api_client)
        self.attempt(api_client)

        assert (
            self.attempt(api_client, password=DEFAULT_PASSWORD, email="Ana@Example.com").status_code
            == 200
        )
        for _ in range(3):
            assert self.attempt(api_client).status_code == 401

    def test_unknown_addresses_answer_the_same(self, api_client):
        for _ in range(3):
            assert self.attempt(api_client, email="nadie@example.com").status_code == 401

        assert self.attempt(api_client, email="nadie@example.com").status_code == 429

    def test_the_cache_keeps_hashes_not_the_address_nor_the_ip(self):
        key = login_attempts._key("Ana@Example.com")

        assert "@" not in key and "ana" not in key.lower()
        assert key == login_attempts._key(" ana@example.com ")
        login_attempts.record_failure("ana@example.com", "10.0.0.7")
        assert "10.0.0.7" not in str(cache.get(key))


class TestSameEmailAtOnce:
    """The serializer checks the email first; a double submit can pass that check twice."""

    @pytest.fixture
    def check_passes(self, monkeypatch):
        from apps.accounts import serializers

        monkeypatch.setattr(serializers, "email_is_taken", lambda *args, **kwargs: False)

    def test_registration_answers_like_the_form(self, api_client, check_passes):
        UserFactory(email="ana@example.com")

        response = api_client.post(REGISTER, register_payload(email="Ana@example.com"))

        assert response.status_code == 400
        assert response.json()["field_codes"] == {"email": ["email_taken"]}
        assert User.objects.filter(email__iexact="ana@example.com").count() == 1

    def test_accounts_created_by_an_admin_too(self, auth_api, admin_user, check_passes):
        UserFactory(email="ana@example.com")

        response = auth_api(admin_user).post(
            "/api/v1/users", register_payload(email="ana@example.com", role="trainer")
        )

        assert response.status_code == 400
        assert response.json()["field_codes"] == {"email": ["email_taken"]}


class TestPasswordLength:
    TOO_LONG = "Aa1#" * 33

    def test_login_and_registration_refuse_it(self, api_client):
        login = api_client.post(LOGIN, {"email": "ana@example.com", "password": self.TOO_LONG})
        register = api_client.post(REGISTER, register_payload(password=self.TOO_LONG))

        assert login.status_code == register.status_code == 400
        assert login.json()["field_codes"] == {"password": ["max_length"]}
        assert "max_length" in register.json()["field_codes"]["password"]

    def test_128_characters_are_accepted(self, api_client):
        password = ("Aa1#Zy9$" * 16)[:128]

        response = api_client.post(REGISTER, register_payload(password=password))

        assert response.status_code == 201


class TestSessionRateLimit:
    def test_refresh_and_logout_are_limited(self, api_client, monkeypatch):
        monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"session": "2/min"})
        headers = {"HTTP_X_REQUESTED_WITH": base_settings.AUTH_CSRF_HEADER_VALUE}
        urls = ["/api/v1/auth/refresh", "/api/v1/auth/logout", "/api/v1/auth/refresh"]

        codes = [api_client.post(url, **headers).status_code for url in urls]

        assert codes[2] == 429
