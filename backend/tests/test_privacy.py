"""Data protection (phase 10): consents, data export, account deletion and retention."""

import json
from datetime import date, timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import User, UserDetails
from apps.notes.models import Note
from apps.notes.services import add_note
from apps.progress.models import UserBadge, WeightRecord
from apps.training.models import WorkoutSession
from tests.factories import DEFAULT_PASSWORD, TrainerFactory, UserFactory, active_client

REGISTER = "/api/v1/auth/register"
ME = "/api/v1/me"
CONSENT = "/api/v1/me/consent"
EXPORT = "/api/v1/me/export"
ACCOUNT = "/api/v1/me/account"

pytestmark = pytest.mark.django_db


def register_payload(**overrides):
    return {
        "first_name": "Laura",
        "last_name": "Privada",
        "email": "laura@example.com",
        "password": "Str0ng#Pass",
        "birth_date": "1991-02-03",
        "gender": "F",
        "terms_accepted": True,
        "health_data_consent": True,
        **overrides,
    }


class TestConsent:
    def test_registration_records_both_consents(self, api_client, settings):
        settings.PRIVACY_POLICY_VERSION = "2026-11"

        response = api_client.post(REGISTER, register_payload())

        assert response.status_code == 201
        assert response.json()["user"]["consent_required"] is False
        user = User.objects.get(email="laura@example.com")
        assert user.privacy_policy_version == "2026-11"
        assert user.privacy_accepted_at and user.health_consent_at

    def test_registration_needs_explicit_health_consent(self, api_client):
        response = api_client.post(REGISTER, register_payload(health_data_consent=False))

        assert response.status_code == 400
        assert response.json()["field_codes"] == {
            "health_data_consent": ["health_consent_required"]
        }
        assert not User.objects.exists()

    def test_a_new_policy_version_asks_again(self, auth_api, settings):
        user = UserFactory()
        api = auth_api(user)
        assert api.get(ME).json()["consent_required"] is False

        settings.PRIVACY_POLICY_VERSION = "2027-01"

        assert api.get(ME).json()["consent_required"] is True
        body = api.post(CONSENT, {"privacy_policy": True}, format="json").json()
        assert body["consent_required"] is False
        user.refresh_from_db()
        assert user.privacy_policy_version == "2027-01"

    def test_clients_without_health_consent_must_give_it(self, auth_api):
        user = UserFactory(health_consent_at=None)
        api = auth_api(user)
        assert api.get(ME).json()["consent_required"] is True

        refused = api.post(CONSENT, {"privacy_policy": True}, format="json")
        assert refused.status_code == 400
        assert refused.json()["code"] == "health_consent_required"

        accepted = api.post(CONSENT, {"privacy_policy": True, "health_data": True}, format="json")
        assert accepted.json()["consent_required"] is False

    def test_staff_only_accept_the_policy(self, auth_api, trainer, settings):
        settings.PRIVACY_POLICY_VERSION = "2027-01"

        body = auth_api(trainer).post(CONSENT, {"privacy_policy": True}, format="json").json()

        assert body["consent_required"] is False

    def test_the_policy_must_be_accepted(self, auth_api):
        response = auth_api(UserFactory()).post(CONSENT, {"privacy_policy": False}, format="json")

        assert response.json()["field_codes"] == {"privacy_policy": ["privacy_required"]}


class TestExport:
    def test_downloads_every_personal_record(self, auth_api):
        client = active_client(email="ana@example.com")
        WeightRecord.objects.create(user=client, weight_kg=78.5, date=date(2026, 3, 1))
        UserBadge.objects.create(user=client, code="first_workout")
        add_note(
            client, TrainerFactory(first_name="Pau", last_name="Vidal"), "¿Qué tal la rodilla?"
        )

        response = auth_api(client).get(EXPORT)

        assert response.status_code == 200
        assert response["Content-Disposition"].startswith(
            'attachment; filename="entrenanutricion-datos-'
        )
        body = json.loads(response.content)
        assert body["format_version"] == 1
        assert body["account"]["email"] == "ana@example.com"
        assert body["account"]["health_consent_at"]
        assert body["onboarding"]["health"] is not None
        assert {"date": "2026-03-01", "weight_kg": 78.5} in body["weight_records"]
        assert body["training_plans"][0]["is_current"] is True
        assert body["nutrition_plans"][0]["is_current"] is True
        assert body["badges"][0]["code"] == "first_workout"
        assert body["notes"][0]["author"] == "Pau Vidal"
        assert body["notes"][0]["body"] == "¿Qué tal la rodilla?"

    def test_includes_sessions_with_their_exercises(self, auth_api):
        client = active_client()
        api = auth_api(client)
        row = client.training_plans.get(is_current=True).workouts.order_by("id").first()
        for item in row.plan_workout.workout.items.all():
            api.put(
                f"/api/v1/me/training-plan/workouts/{row.id}/exercises/{item.id}",
                {"completed": True},
                format="json",
            )
        api.post(f"/api/v1/me/training-plan/workouts/{row.id}/complete")

        session = json.loads(api.get(EXPORT).content)["workout_sessions"][0]

        assert session["workout"] == row.plan_workout.workout.name
        assert len(session["exercises"]) == row.plan_workout.workout.items.count()

    def test_works_for_staff_and_before_the_onboarding_form(self, auth_api, trainer):
        for user in (trainer, UserFactory()):
            body = json.loads(auth_api(user).get(EXPORT).content)
            assert body["onboarding"] is None
            assert body["workout_sessions"] == []

    def test_query_budget(self, auth_api, django_assert_max_num_queries):
        api = auth_api(active_client())

        with django_assert_max_num_queries(12):
            api.get(EXPORT)


class TestAccountDeletion:
    def test_a_client_deletes_the_account_and_all_its_data(self, api_client):
        client = active_client(email="bye@example.com")
        WeightRecord.objects.create(user=client, weight_kg=70, date=date(2026, 2, 1))
        add_note(client, client, "Hasta pronto")
        login = api_client.post(
            "/api/v1/auth/login", {"email": "bye@example.com", "password": DEFAULT_PASSWORD}
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")

        response = api_client.delete(ACCOUNT, {"password": DEFAULT_PASSWORD})

        assert response.status_code == 204
        assert response.cookies["entrenanutricion_refresh"]["max-age"] == 0
        assert not User.objects.filter(email="bye@example.com").exists()
        assert not UserDetails.objects.filter(user_id=client.id).exists()
        assert not WeightRecord.objects.filter(user_id=client.id).exists()
        assert not WorkoutSession.objects.filter(user_id=client.id).exists()
        assert not Note.objects.filter(client_id=client.id).exists()

    def test_the_password_is_required(self, auth_api):
        client = active_client()

        response = auth_api(client).delete(ACCOUNT, {"password": "Wrong#Pass1"}, format="json")

        assert response.json()["field_codes"] == {"password": ["current_password_incorrect"]}
        assert User.objects.filter(pk=client.pk).exists()

    def test_staff_accounts_are_managed_by_an_admin(self, auth_api, trainer):
        response = auth_api(trainer).delete(ACCOUNT, {"password": DEFAULT_PASSWORD}, format="json")

        assert response.status_code == 403
        assert response.json()["code"] == "staff_account_managed"
        assert User.objects.filter(pk=trainer.pk).exists()


class TestRetention:
    def test_deactivation_is_dated(self, auth_api, admin_user):
        user = UserFactory()

        auth_api(admin_user).delete(f"/api/v1/users/{user.id}")

        user.refresh_from_db()
        assert user.deactivated_at is not None

    def test_old_deactivated_accounts_are_deleted(self):
        now = timezone.now()
        old = UserFactory(is_active=False, deactivated_at=now - timedelta(days=400))
        recent = UserFactory(is_active=False, deactivated_at=now - timedelta(days=10))
        active = UserFactory()
        out = StringIO()

        call_command("purge_inactive_accounts", "--dry-run", stdout=out)
        assert "1 account(s)" in out.getvalue()
        assert User.objects.filter(pk=old.pk).exists()

        call_command("purge_inactive_accounts", stdout=out)

        assert not User.objects.filter(pk=old.pk).exists()
        assert User.objects.filter(pk__in=[recent.pk, active.pk]).count() == 2
        assert "Deleted 1 account(s) deactivated more than 365 days ago" in out.getvalue()

    def test_custom_retention(self):
        UserFactory(is_active=False, deactivated_at=timezone.now() - timedelta(days=40))

        call_command("purge_inactive_accounts", "--days", "30", stdout=StringIO())

        assert not User.objects.filter(is_active=False).exists()


def test_users_created_by_an_admin_give_their_consent_on_first_use(auth_api, admin_user):
    response = auth_api(admin_user).post(
        "/api/v1/users",
        {
            "first_name": "Sin",
            "last_name": "Consentimiento",
            "email": "nuevo@example.com",
            "password": "Str0ng#Pass",
            "gender": "O",
            "role": "client",
            "birth_date": "1990-01-01",
        },
        format="json",
    )

    assert response.status_code == 201, response.content
    user = User.objects.get(email="nuevo@example.com")
    assert user.consent_required is True
    assert auth_api(user).get(ME).json()["consent_required"] is True


def test_the_data_download_is_limited(auth_api, monkeypatch):
    from rest_framework.throttling import ScopedRateThrottle

    monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"data_export": "2/hour"})
    api = auth_api(active_client())

    codes = [api.get(EXPORT).status_code for _ in range(3)]

    assert codes == [200, 200, 429]
