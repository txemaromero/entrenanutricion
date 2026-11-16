import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import UserStatus
from apps.assignments.services import compute_user_status, recompute_user_status
from apps.training.models import UserTrainingPlan
from tests.factories import (
    TrainingPlanFactory,
    UserFactory,
    assign_meal_plan,
    assign_plan,
    onboarded_client,
    plan_with_workouts,
)

pytestmark = pytest.mark.django_db

PENDING = "/api/v1/assignments/pending"


class TestPendingAssignments:
    @pytest.fixture
    def clients(self):
        nothing = onboarded_client(first_name="Nada")
        only_training = onboarded_client(first_name="Entreno")
        assign_plan(only_training)
        only_nutrition = onboarded_client(first_name="Dieta")
        assign_meal_plan(only_nutrition)
        both = onboarded_client(first_name="Ambos")
        assign_plan(both)
        assign_meal_plan(both)
        UserFactory(first_name="SinOnboarding")
        onboarded_client(first_name="Borrado", is_active=False, status=UserStatus.INACTIVE)
        return {"nothing": nothing, "training": only_training, "nutrition": only_nutrition}

    def ids(self, response):
        return {row["id"]: row["missing"] for row in response.json()["results"]}

    def test_trainer_sees_clients_without_training(self, auth_api, trainer, clients):
        rows = self.ids(auth_api(trainer).get(PENDING))

        assert set(rows) == {clients["nothing"].id, clients["nutrition"].id}

    def test_nutritionist_sees_clients_without_nutrition(self, auth_api, nutritionist, clients):
        rows = self.ids(auth_api(nutritionist).get(PENDING))

        assert set(rows) == {clients["nothing"].id, clients["training"].id}

    def test_admin_sees_every_missing_plan(
        self, auth_api, admin_user, clients, django_assert_max_num_queries
    ):
        with django_assert_max_num_queries(4):
            response = auth_api(admin_user).get(PENDING)

        assert self.ids(response) == {
            clients["nothing"].id: ["training", "nutrition"],
            clients["training"].id: ["nutrition"],
            clients["nutrition"].id: ["training"],
        }
        row = response.json()["results"][0]
        assert row["goal"] == "lose_weight"
        assert row["weekly_training_days"] == 3

    def test_clients_cannot_see_it(self, auth_api, client_user):
        assert auth_api(client_user).get(PENDING).status_code == 403


class TestUserStatus:
    def test_full_lifecycle(self):
        user = UserFactory()
        assert compute_user_status(user) == UserStatus.PENDING_ONBOARDING

        user = onboarded_client(status=UserStatus.PENDING_ONBOARDING)
        assert recompute_user_status(user) == UserStatus.PENDING_ASSIGNMENT

        assign_plan(user)
        user.refresh_from_db()
        assert user.status == UserStatus.PENDING_ASSIGNMENT

        assign_meal_plan(user)
        user.refresh_from_db()
        assert user.status == UserStatus.ACTIVE

        user.is_active = False
        assert recompute_user_status(user) == UserStatus.INACTIVE

    def test_staff_are_always_active(self, trainer):
        assert compute_user_status(trainer) == UserStatus.ACTIVE

    def test_activation_unlocks_client_endpoints(self, auth_api):
        user = onboarded_client()
        api = auth_api(user)
        assert api.get("/api/v1/me").json()["status"] == UserStatus.PENDING_ASSIGNMENT

        assign_plan(user)
        assign_meal_plan(user)

        me = api.get("/api/v1/me").json()
        assert me["status"] == UserStatus.ACTIVE
        assert me["has_training_plan"] and me["has_nutrition_plan"]
        assert api.get("/api/v1/me/training-plan").status_code == 200
        assert api.get("/api/v1/me/nutrition-plan").status_code == 200
        assert api.get("/api/v1/me/progress/dashboard").status_code == 200


def assign_url(user_id):
    return f"/api/v1/users/{user_id}/assign-training-plan"


class TestAssignTrainingPlan:
    @pytest.mark.parametrize("role", ["trainer", "admin_user"])
    def test_trainer_and_admin_assign(self, request, auth_api, onboarded_client, role):
        staff = request.getfixturevalue(role)
        plan = plan_with_workouts(2)

        response = auth_api(staff).post(assign_url(onboarded_client.id), {"plan_id": plan.id})

        assert response.status_code == 201
        body = response.json()
        assert body["plan"] == {"id": plan.id, "name": plan.name}
        assert body["assigned_by_id"] == staff.id
        assert body["is_current"] is True
        # Only the training plan is assigned so far.
        assert body["user_status"] == UserStatus.PENDING_ASSIGNMENT

    @pytest.mark.parametrize("role", ["nutritionist", "onboarded_client"])
    def test_other_roles_cannot_assign(self, request, auth_api, onboarded_client, role):
        actor = request.getfixturevalue(role)

        response = auth_api(actor).post(
            assign_url(onboarded_client.id), {"plan_id": plan_with_workouts(1).id}
        )

        assert response.status_code == 403

    def test_second_assignment_requires_replace(self, auth_api, trainer, onboarded_client):
        """Regression #9: a generic error was shown when the user already had a plan."""
        current = assign_plan(onboarded_client, plan_with_workouts(1, name="Fuerza"))
        new_plan = plan_with_workouts(1)

        response = auth_api(trainer).post(assign_url(onboarded_client.id), {"plan_id": new_plan.id})

        assert response.status_code == 409
        body = response.json()
        assert body["code"] == "training_plan_already_assigned"
        assert "Fuerza" in body["message"]
        assert body["current_plan"] == {"id": current.plan_id, "name": "Fuerza"}

    def test_replace_moves_the_current_assignment(self, auth_api, trainer, onboarded_client):
        old = assign_plan(onboarded_client)
        new_plan = plan_with_workouts(2)

        response = auth_api(trainer).post(
            assign_url(onboarded_client.id), {"plan_id": new_plan.id, "replace": True}
        )

        assert response.status_code == 201
        old.refresh_from_db()
        assert old.is_current is False
        current = UserTrainingPlan.objects.get(user=onboarded_client, is_current=True)
        assert current.plan_id == new_plan.id
        assert current.cycle == 1

    def test_client_must_complete_onboarding(self, auth_api, trainer, client_user):
        response = auth_api(trainer).post(
            assign_url(client_user.id), {"plan_id": plan_with_workouts(1).id}
        )

        assert response.status_code == 409
        assert response.json()["code"] == "onboarding_not_completed"

    def test_only_clients_can_receive_plans(self, auth_api, trainer, nutritionist):
        response = auth_api(trainer).post(
            assign_url(nutritionist.id), {"plan_id": plan_with_workouts(1).id}
        )

        assert response.status_code == 404

    def test_inactive_plan_cannot_be_assigned(self, auth_api, trainer, onboarded_client):
        plan = TrainingPlanFactory(is_active=False)

        response = auth_api(trainer).post(assign_url(onboarded_client.id), {"plan_id": plan.id})

        assert response.status_code == 400
        assert response.json()["code"] == "plan_inactive"

    def test_unknown_plan(self, auth_api, trainer, onboarded_client):
        response = auth_api(trainer).post(assign_url(onboarded_client.id), {"plan_id": 999999})

        assert response.status_code == 400
        assert response.json()["field_codes"]["plan_id"] == ["does_not_exist"]

    def test_database_enforces_a_single_current_plan(self, onboarded_client):
        assignment = assign_plan(onboarded_client)

        with pytest.raises(IntegrityError), transaction.atomic():
            UserTrainingPlan.objects.create(user=onboarded_client, plan=assignment.plan)
