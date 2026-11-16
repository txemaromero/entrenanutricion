"""Email verification of self-registered accounts (phase 12)."""

import re
from datetime import datetime, timedelta

import pytest
from django.core import mail
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts.models import User
from apps.accounts.services import email_verification_token
from apps.training.reminders import send_due_reminders
from tests.factories import UserFactory, active_client

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/auth/register"
VERIFY = "/api/v1/auth/verify-email"
RESEND = "/api/v1/me/verify-email/resend"
PAYLOAD = {
    "first_name": "Laura",
    "last_name": "Nueva",
    "email": "laura@example.com",
    "password": "Str0ng#Pass",
    "birth_date": "1992-04-12",
    "gender": "F",
    "terms_accepted": True,
    "health_data_consent": True,
}


def token_in(message) -> str:
    return re.search(r"/verify-email\?token=(\S+)", message.body).group(1)


class TestRegistration:
    def test_a_new_account_gets_the_link_in_its_language(self, api_client):
        response = api_client.post(REGISTER, PAYLOAD, format="json", HTTP_ACCEPT_LANGUAGE="ca")

        assert response.status_code == 201
        assert response.json()["user"]["email_verified"] is False
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == ["laura@example.com"]
        assert message.subject == "Confirma el teu correu d'entrenanutricion"
        assert "http://localhost:5173/verify-email?token=" in message.body
        assert User.objects.get(email="laura@example.com").language == "ca"

    def test_the_link_verifies_the_address(self, api_client, auth_api):
        api_client.post(REGISTER, PAYLOAD, format="json")
        token = token_in(mail.outbox[0])

        response = api_client.post(VERIFY, {"token": token})

        assert response.json() == {"email_verified": True}
        user = User.objects.get(email="laura@example.com")
        assert user.email_verified_at is not None
        assert auth_api(user).get("/api/v1/me").json()["email_verified"] is True
        # Opening it again changes nothing.
        assert api_client.post(VERIFY, {"token": token}).status_code == 200

    def test_staff_created_and_demo_accounts_are_verified(self, auth_api, admin_user):
        body = auth_api(admin_user).post(
            "/api/v1/users",
            {**PAYLOAD, "email": "staff-made@example.com", "role": "client"},
            format="json",
        )

        assert body.status_code == 201
        assert User.objects.get(email="staff-made@example.com").email_verified_at is not None
        assert mail.outbox == []


class TestLink:
    @pytest.mark.parametrize("token", ["nope", "a" * 60])
    def test_invalid_link(self, api_client, token):
        response = api_client.post(VERIFY, {"token": token})

        assert response.status_code == 400
        assert response.json()["code"] == "verification_link_invalid"

    def test_expired_link(self, api_client, settings):
        user = UserFactory(email_verified_at=None)
        with freeze_time(timezone.now() - timedelta(days=8)):
            token = email_verification_token(user)

        response = api_client.post(VERIFY, {"token": token})

        assert response.json()["code"] == "verification_link_expired"

    def test_a_deactivated_account(self, api_client):
        user = UserFactory(email_verified_at=None, is_active=False)

        response = api_client.post(VERIFY, {"token": email_verification_token(user)})

        assert response.json()["code"] == "verification_link_invalid"


class TestResend:
    def test_resend_while_not_verified(self, auth_api):
        user = UserFactory(email_verified_at=None)

        response = auth_api(user).post(RESEND, HTTP_ACCEPT_LANGUAGE="en")

        assert response.status_code == 202
        assert mail.outbox[0].subject == "Confirm your entrenanutricion email"
        assert email_verification_token(user)[:10] in mail.outbox[0].body

    def test_already_verified(self, auth_api):
        response = auth_api(UserFactory()).post(RESEND)

        assert response.status_code == 409
        assert response.json()["code"] == "email_already_verified"

    def test_resending_is_throttled(self, auth_api, monkeypatch):
        monkeypatch.setattr(
            ScopedRateThrottle, "THROTTLE_RATES", {"email_verification_resend": "1/hour"}
        )
        api = auth_api(UserFactory(email_verified_at=None))

        assert [api.post(RESEND).status_code for _ in range(2)] == [202, 429]

    def test_needs_a_session(self, api_client):
        assert api_client.post(RESEND).status_code == 401


class TestEffects:
    def test_a_password_reset_by_email_verifies_the_address(self, api_client):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = UserFactory(email_verified_at=None)

        response = api_client.post(
            "/api/v1/auth/password-reset/confirm",
            {
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user),
                "new_password": "N3w#Password",
                "confirm_password": "N3w#Password",
            },
        )

        assert response.status_code == 204
        user.refresh_from_db()
        assert user.email_verified_at is not None

    def test_no_reminders_to_an_unconfirmed_address(self):
        client = active_client(email_verified_at=None)
        client.details.reminders_enabled = True
        client.details.save()
        monday_evening = timezone.make_aware(
            datetime(2026, 3, 2, 17, 10)  # one hour before the default 18:00
        )

        assert send_due_reminders(monday_evening) == 0
        client.email_verified_at = timezone.now()
        client.save()
        assert send_due_reminders(monday_evening) == 1
