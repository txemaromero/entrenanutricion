import pytest
from django.utils import timezone

from apps.accounts.models import User, UserStatus
from apps.progress.models import WeightRecord
from tests.factories import (
    DEFAULT_PASSWORD,
    AdminFactory,
    TrainerFactory,
    UserFactory,
    active_client,
    image_upload,
    onboarded_client,
    refresh_with,
)

URL = "/api/v1/users"

pytestmark = pytest.mark.django_db


def create_payload(**overrides):
    data = {
        "first_name": "Núria",
        "last_name": "Vidal",
        "email": "nuria@example.com",
        "password": "Str0ng#Pass",
        "gender": "F",
        "role": "client",
        "birth_date": "1990-02-02",
    }
    data.update(overrides)
    return data


class TestUserList:
    def test_alphabetical_by_last_and_first_name(self, auth_api, trainer):
        UserFactory(first_name="Bea", last_name="Zapata")
        UserFactory(first_name="Ana", last_name="Abad")
        UserFactory(first_name="Carla", last_name="Abad")

        body = auth_api(trainer).get(URL, {"role": "client"}).json()

        assert [user["full_name"] for user in body["results"]] == [
            "Ana Abad",
            "Carla Abad",
            "Bea Zapata",
        ]

    def test_search_and_role_filter(self, auth_api, nutritionist):
        UserFactory(first_name="Ana", last_name="Pérez", email="ana@x.com")
        TrainerFactory(first_name="Ana", last_name="Coach")
        api = auth_api(nutritionist)

        by_search = api.get(URL, {"search": "pérez"}).json()
        by_role = api.get(URL, {"role": "client", "search": "ana"}).json()

        assert [user["email"] for user in by_search["results"]] == ["ana@x.com"]
        assert [user["last_name"] for user in by_role["results"]] == ["Pérez"]

    def test_trainers_and_nutritionists_only_see_clients(self, auth_api, trainer, nutritionist):
        client = UserFactory()
        colleague = TrainerFactory()
        boss = AdminFactory()

        for staff in (trainer, nutritionist):
            api = auth_api(staff)
            assert [user["id"] for user in api.get(URL).json()["results"]] == [client.id]
            assert api.get(URL, {"role": "trainer"}).json()["count"] == 0
            assert api.get(f"{URL}/{client.id}").status_code == 200
            assert api.get(f"{URL}/{colleague.id}").status_code == 404
            assert api.get(f"{URL}/{boss.id}").status_code == 404

    def test_admins_see_everybody(self, auth_api, admin_user, trainer):
        api = auth_api(admin_user)
        client = UserFactory()

        ids = {user["id"] for user in api.get(URL).json()["results"]}

        assert ids == {admin_user.id, trainer.id, client.id}
        assert api.get(f"{URL}/{trainer.id}").status_code == 200

    def test_shows_current_plans(self, auth_api, admin_user, django_assert_max_num_queries):
        client = active_client()
        for _ in range(5):
            active_client()
        api = auth_api(admin_user)

        with django_assert_max_num_queries(6):
            body = api.get(URL, {"role": "client"}).json()

        row = next(user for user in body["results"] if user["id"] == client.id)
        assert row["training_plan"]["name"]
        assert row["nutrition_plan"]["name"]
        assert row["status"] == UserStatus.ACTIVE

    def test_hides_deleted_users(self, auth_api, admin_user):
        UserFactory(is_active=False, status=UserStatus.INACTIVE)

        assert auth_api(admin_user).get(URL, {"role": "client"}).json()["count"] == 0

    def test_clients_cannot_list_users(self, auth_api, client_user):
        assert auth_api(client_user).get(URL).status_code == 403


class TestUserDetail:
    def test_full_profile_for_staff(self, auth_api, trainer):
        client = active_client()

        body = auth_api(trainer).get(f"{URL}/{client.id}").json()

        assert body["onboarding"]["diet"]["diet_type"] == "omnivore"
        assert body["details"]["target_weight_kg"] == 75.0
        assert body["weight_records"][0]["weight_kg"] == 80.0
        assert body["training_assignment"]["cycle"] == 1
        assert body["nutrition_assignment"]["plan"]["name"]
        assert body["age"] >= 18

    def test_pending_client_has_no_plans(self, auth_api, trainer, client_user):
        body = auth_api(trainer).get(f"{URL}/{client_user.id}").json()

        assert body["onboarding"] is None
        assert body["training_assignment"] is None
        assert body["nutrition_assignment"] is None


class TestUserAdministration:
    def test_admin_creates_a_client_pending_onboarding(self, auth_api, admin_user):
        response = auth_api(admin_user).post(URL, create_payload())

        assert response.status_code == 201
        assert response.json()["status"] == UserStatus.PENDING_ONBOARDING
        login = auth_api(admin_user).post(
            "/api/v1/auth/login", {"email": "nuria@example.com", "password": "Str0ng#Pass"}
        )
        assert login.json()["user"]["onboarding_completed"] is False

    def test_admin_creates_staff_active(self, auth_api, admin_user):
        body = auth_api(admin_user).post(URL, create_payload(role="nutritionist")).json()

        assert body["role"] == "nutritionist"
        assert body["status"] == UserStatus.ACTIVE

    @pytest.mark.parametrize(
        "field", ["first_name", "last_name", "email", "password", "gender", "role", "birth_date"]
    )
    def test_every_field_is_required(self, auth_api, admin_user, field):
        data = create_payload()
        del data[field]

        response = auth_api(admin_user).post(URL, data)

        assert response.status_code == 400
        assert response.json()["field_codes"][field] == ["required"]

    def test_create_validates_like_registration(self, auth_api, admin_user):
        UserFactory(email="taken@example.com")

        response = auth_api(admin_user).post(
            URL, create_payload(email="TAKEN@example.com", password="weak", birth_date="2015-01-01")
        )

        codes = response.json()["field_codes"]
        assert codes["email"] == ["email_taken"]
        assert "password_too_short" in codes["password"]
        assert codes["birth_date"] == ["too_young"]

    def test_patch_persists_and_returns_new_data(self, auth_api, admin_user):
        """Regression #2: changes made to a user were not saved."""
        client = onboarded_client()

        response = auth_api(admin_user).patch(
            f"{URL}/{client.id}",
            {
                "first_name": "Rosa",
                "last_name": "Mas",
                "current_weight_kg": 77.0,
                "goal": "maintain",
                "physical_activity_level": "intense",
                "weekly_training_days": 5,
            },
        )

        body = response.json()
        assert response.status_code == 200
        assert body["full_name"] == "Rosa Mas"
        assert body["details"]["current_weight_kg"] == 77.0
        assert body["details"]["goal"] == "maintain"
        client.refresh_from_db()
        assert client.first_name == "Rosa"
        assert client.details.weekly_training_days == 5
        assert WeightRecord.objects.filter(user=client, date=timezone.localdate()).exists()

    def test_put_behaves_like_patch(self, auth_api, admin_user, client_user):
        response = auth_api(admin_user).put(f"{URL}/{client_user.id}", {"first_name": "Teo"})

        assert response.json()["first_name"] == "Teo"

    def test_change_role_recomputes_status(self, auth_api, admin_user, client_user):
        api = auth_api(admin_user)

        to_trainer = api.patch(f"{URL}/{client_user.id}", {"role": "trainer"}).json()
        back = api.patch(f"{URL}/{client_user.id}", {"role": "client"}).json()

        assert to_trainer["role"] == "trainer"
        assert to_trainer["status"] == UserStatus.ACTIVE
        assert back["status"] == UserStatus.PENDING_ONBOARDING

    def test_admin_cannot_change_own_role(self, auth_api, admin_user):
        response = auth_api(admin_user).patch(f"{URL}/{admin_user.id}", {"role": "client"})

        assert response.status_code == 409
        assert response.json()["code"] == "cannot_change_own_role"

    def test_sport_fields_require_onboarding(self, auth_api, admin_user, client_user):
        response = auth_api(admin_user).patch(f"{URL}/{client_user.id}", {"goal": "maintain"})

        assert response.status_code == 409

    def test_photo_upload_with_multipart(self, auth_api, admin_user, client_user):
        response = auth_api(admin_user).patch(
            f"{URL}/{client_user.id}",
            {"photo": image_upload(), "first_name": "Iris"},
            format="multipart",
        )

        assert response.status_code == 200
        assert response.json()["profile_photo_url"].endswith(".webp")
        assert response.json()["first_name"] == "Iris"

    def test_delete_is_logical_and_closes_sessions(self, auth_api, api_client, admin_user):
        user = UserFactory(email="bye@example.com")
        refresh = (
            api_client.post(
                "/api/v1/auth/login", {"email": "bye@example.com", "password": DEFAULT_PASSWORD}
            )
            .cookies["entrenanutricion_refresh"]
            .value
        )

        response = auth_api(admin_user).delete(f"{URL}/{user.id}")

        assert response.status_code == 204
        user.refresh_from_db()
        assert user.is_active is False
        assert user.status == UserStatus.INACTIVE
        assert User.objects.filter(pk=user.id).exists()
        assert refresh_with(api_client, refresh).status_code == 401
        assert auth_api(admin_user).get(f"{URL}/{user.id}").status_code == 404

    def test_admin_cannot_delete_self(self, auth_api, admin_user):
        response = auth_api(admin_user).delete(f"{URL}/{admin_user.id}")

        assert response.status_code == 409
        assert response.json()["code"] == "cannot_delete_self"


class TestStaffCannotManageUsers:
    """Regression #11: trainers and nutritionists could create, edit or delete users."""

    @pytest.mark.parametrize("role", ["trainer", "nutritionist"])
    def test_write_operations_are_forbidden(self, request, auth_api, client_user, role):
        api = auth_api(request.getfixturevalue(role))

        assert api.post(URL, create_payload()).status_code == 403
        assert api.patch(f"{URL}/{client_user.id}", {"first_name": "X"}).status_code == 403
        assert api.put(f"{URL}/{client_user.id}", {"first_name": "X"}).status_code == 403
        assert api.delete(f"{URL}/{client_user.id}").status_code == 403
        client_user.refresh_from_db()
        assert client_user.is_active and client_user.first_name == "Ana"
