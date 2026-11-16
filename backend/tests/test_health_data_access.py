"""Who of the team saw a client's health answers, and when (decision 2 of phase 15)."""

import json
from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.accounts.models import HealthDataAccess, Role
from apps.accounts.services import purge_inactive_accounts
from tests.factories import TrainerFactory, onboarded_client

pytestmark = pytest.mark.django_db


def profile(api, user):
    return api.get(f"/api/v1/users/{user.pk}")


def log_url(user) -> str:
    return f"/api/v1/users/{user.pk}/health-data-accesses"


class TestRecording:
    def test_viewing_a_client_profile_is_recorded_without_values(self, auth_api, trainer):
        client = onboarded_client()

        response = profile(auth_api(trainer), client)

        assert response.json()["onboarding"]["health"]  # what the professional was shown
        access = HealthDataAccess.objects.get()
        assert (access.client, access.staff, access.staff_role) == (client, trainer, Role.TRAINER)
        assert access.staff_name == trainer.get_full_name()
        # Who, whom and when: nothing of the answers themselves.
        fields = {field.name for field in HealthDataAccess._meta.get_fields()}
        assert fields == {
            "id",
            "created_at",
            "updated_at",
            "client",
            "staff",
            "staff_role",
            "staff_name",
        }

    def test_one_row_per_professional_client_and_hour(self, auth_api, trainer, nutritionist):
        client = onboarded_client()

        with freeze_time("2026-11-06 10:00:00"):
            profile(auth_api(trainer), client)
            profile(auth_api(trainer), client)
            profile(auth_api(nutritionist), client)
        assert HealthDataAccess.objects.filter(client=client).count() == 2

        with freeze_time("2026-11-06 11:00:01"):
            profile(auth_api(trainer), client)
        assert HealthDataAccess.objects.filter(client=client, staff=trainer).count() == 2

    def test_the_notes_and_the_diary_count_too(self, auth_api, trainer, nutritionist):
        client = onboarded_client()

        assert auth_api(trainer).get(f"/api/v1/users/{client.pk}/notes").status_code == 200
        assert (
            auth_api(nutritionist).get(f"/api/v1/users/{client.pk}/food-log/summary").status_code
            == 200
        )

        assert set(HealthDataAccess.objects.values_list("staff_id", flat=True)) == {
            trainer.pk,
            nutritionist.pk,
        }

    def test_writing_a_note_is_not_a_read(self, auth_api, trainer):
        client = onboarded_client()

        auth_api(trainer).post(f"/api/v1/users/{client.pk}/notes", {"body": "Hola"})

        assert not HealthDataAccess.objects.exists()

    def test_an_admin_editing_the_client_is_shown_them_too(self, auth_api, admin_user):
        client = onboarded_client()

        auth_api(admin_user).patch(f"/api/v1/users/{client.pk}", {"first_name": "Nora"})

        assert HealthDataAccess.objects.get().staff_role == Role.ADMIN

    def test_nothing_to_record_without_health_answers(self, auth_api, trainer, client_user):
        api = auth_api(trainer)

        profile(api, client_user)  # before the onboarding form
        profile(api, TrainerFactory())  # a colleague
        api.get("/api/v1/users", {"role": "client"})  # the list shows no health data

        assert not HealthDataAccess.objects.exists()


class TestAdherenceShowsTheWeight:
    URL = "/api/v1/adherence"

    def test_the_list_logs_the_clients_of_the_page(self, auth_api, nutritionist):
        from tests.factories import active_client

        clients = [active_client() for _ in range(3)]
        api = auth_api(nutritionist)

        with freeze_time("2026-11-10 10:00:00"):
            body = api.get(self.URL, {"limit": 2}).json()
            api.get(self.URL, {"limit": 2})  # again within the hour: nothing new

        shown = {row["user"]["id"] for row in body["results"]}
        assert len(shown) == 2 and shown <= {client.pk for client in clients}
        logged = HealthDataAccess.objects.filter(staff=nutritionist)
        assert set(logged.values_list("client_id", flat=True)) == shown
        assert set(logged.values_list("staff_role", flat=True)) == {Role.NUTRITIONIST}

    def test_one_client(self, auth_api, trainer):
        from tests.factories import active_client

        client = active_client()

        assert auth_api(trainer).get(f"/api/v1/users/{client.pk}/adherence").status_code == 200

        assert HealthDataAccess.objects.get().client == client

    def test_rows_without_a_weight_are_not_logged(self):
        from apps.progress.views import shown_weights

        rows = [
            {"user": "a", "current_weight_kg": 70.0, "weight_change_kg": None},
            {"user": "b", "current_weight_kg": None, "weight_change_kg": None},
        ]

        assert shown_weights(rows) == ["a"]


class TestAdminLog:
    def test_newest_first(self, auth_api, admin_user, trainer, nutritionist):
        client = onboarded_client()
        with freeze_time("2026-11-01 09:00:00"):
            profile(auth_api(trainer), client)
        with freeze_time("2026-11-02 09:00:00"):
            profile(auth_api(nutritionist), client)

        body = auth_api(admin_user).get(log_url(client)).json()

        assert body["count"] == 2
        assert [row["staff_role"] for row in body["results"]] == ["nutritionist", "trainer"]
        assert body["results"][1] == {
            "id": body["results"][1]["id"],
            "staff": trainer.pk,
            "staff_name": trainer.get_full_name(),
            "staff_role": "trainer",
            "accessed_at": "2026-11-01T10:00:00+01:00",
        }

    def test_only_admins(self, request, auth_api):
        client = onboarded_client()
        for role in ("trainer", "nutritionist", "client_user"):
            assert auth_api(request.getfixturevalue(role)).get(log_url(client)).status_code == 403
        assert auth_api(client).get(log_url(client)).status_code == 403

    def test_unknown_user(self, auth_api, admin_user):
        assert (
            auth_api(admin_user).get("/api/v1/users/999999/health-data-accesses").status_code == 404
        )


class TestClientsAndRetention:
    def test_the_client_finds_it_in_the_data_download(self, auth_api, trainer):
        client = onboarded_client()
        with freeze_time("2026-11-06 10:00:00"):
            profile(auth_api(trainer), client)

        body = json.loads(auth_api(client).get("/api/v1/me/export").content)

        assert body["health_data_accesses"] == [
            {
                "accessed_at": "2026-11-06T10:00:00+00:00",
                "staff": trainer.get_full_name(),
                "staff_role": "trainer",
            }
        ]

    def test_it_says_who_after_the_professional_account_is_gone(self, auth_api):
        client = onboarded_client()
        trainer = TrainerFactory(first_name="Marta", last_name="Gil")
        profile(auth_api(trainer), client)

        trainer.delete()

        access = HealthDataAccess.objects.get()
        assert access.staff is None
        assert (access.staff_name, access.staff_role) == ("Marta Gil", Role.TRAINER)

    def test_it_goes_with_the_client_account(self, auth_api, trainer):
        client = onboarded_client()
        other = onboarded_client()
        profile(auth_api(trainer), client)
        profile(auth_api(trainer), other)
        client.is_active = False
        client.deactivated_at = timezone.now() - timedelta(days=400)
        client.save()

        purge_inactive_accounts(365)

        assert list(HealthDataAccess.objects.values_list("client_id", flat=True)) == [other.pk]

    def test_your_own_profile_is_not_an_access(self, auth_api):
        admin = onboarded_client(role=Role.ADMIN)

        response = profile(auth_api(admin), admin)

        assert response.json()["onboarding"]["health"]
        assert not HealthDataAccess.objects.exists()

    def test_changing_the_role_does_not_hide_the_access(self, auth_api, admin_user):
        client = onboarded_client()
        api = auth_api(admin_user)

        with freeze_time("2026-11-09 10:00:00"):
            changed = api.patch(f"/api/v1/users/{client.pk}", {"role": "trainer"})
        with freeze_time("2026-11-09 12:00:00"):
            seen = profile(api, client)

        assert changed.json()["role"] == "trainer"
        assert seen.json()["onboarding"]["health"]
        assert HealthDataAccess.objects.filter(client=client, staff=admin_user).count() == 2
