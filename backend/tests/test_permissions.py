"""Role × endpoint permission matrix. Allowed calls must not fail on permissions;
forbidden ones return 401 (anonymous) or 403. Validation errors (400) or business conflicts
(404/409) count as "allowed" because the permission layer let the request through."""

import pytest

from tests.factories import (
    AdminFactory,
    FoodFactory,
    MealPlanFactory,
    NutritionistFactory,
    TrainerFactory,
    UserFactory,
    active_client,
    plan_with_workouts,
    workout_with_exercises,
)

pytestmark = pytest.mark.django_db

ROLES = ["anonymous", "client", "trainer", "nutritionist", "admin"]
STAFF = {"trainer", "nutritionist", "admin"}
CLIENT = {"client"}
EVERYONE_AUTHENTICATED = CLIENT | STAFF
PUBLIC = set(ROLES)


@pytest.fixture
def world(db):
    client = active_client()
    plan = plan_with_workouts(1)
    return {
        "client": client,
        "target": UserFactory(),
        "exercise": plan.plan_workouts.first().workout.items.first().exercise,
        "workout": workout_with_exercises(1),
        "plan": plan,
        "meal_plan": MealPlanFactory(),
        "food": FoodFactory(),
        "actors": {
            "anonymous": None,
            "client": client,
            "trainer": TrainerFactory(),
            "nutritionist": NutritionistFactory(),
            "admin": AdminFactory(),
        },
    }


# (method, path template, allowed roles)
MATRIX = [
    ("post", "/api/v1/auth/password-reset", PUBLIC),
    ("post", "/api/v1/auth/password-reset/confirm", PUBLIC),
    ("post", "/api/v1/auth/verify-email", PUBLIC),
    ("post", "/api/v1/me/verify-email/resend", EVERYONE_AUTHENTICATED),
    ("get", "/api/v1/me", EVERYONE_AUTHENTICATED),
    ("patch", "/api/v1/me/profile", EVERYONE_AUTHENTICATED),
    ("put", "/api/v1/me/password", EVERYONE_AUTHENTICATED),
    ("get", "/api/v1/me/onboarding", CLIENT),
    ("get", "/api/v1/me/training-plan", CLIENT),
    ("get", "/api/v1/me/training-days", CLIENT),
    ("put", "/api/v1/me/training-days", CLIENT),
    ("get", "/api/v1/me/nutrition-plan", CLIENT),
    ("get", "/api/v1/me/progress/dashboard", CLIENT),
    ("get", "/api/v1/me/progress/history", CLIENT),
    ("get", "/api/v1/me/weight-records", CLIENT),
    ("get", "/api/v1/me/badges", CLIENT),
    ("get", "/api/v1/me/exercises/{exercise}", CLIENT),
    ("get", "/api/v1/me/exercises/{exercise}/history", CLIENT),
    ("get", "/api/v1/me/records", CLIENT),
    ("get", "/api/v1/me/reminders", CLIENT),
    ("put", "/api/v1/me/reminders", CLIENT),
    ("get", "/api/v1/muscle-groups", STAFF),
    ("get", "/api/v1/exercises", STAFF),
    ("post", "/api/v1/exercises", {"trainer", "admin"}),
    ("patch", "/api/v1/exercises/{exercise}", {"trainer", "admin"}),
    ("delete", "/api/v1/exercises/{exercise}", {"trainer", "admin"}),
    ("get", "/api/v1/workouts", STAFF),
    ("post", "/api/v1/workouts", {"trainer", "admin"}),
    ("patch", "/api/v1/workouts/{workout}", {"trainer", "admin"}),
    ("delete", "/api/v1/workouts/{workout}", {"trainer", "admin"}),
    ("get", "/api/v1/training-plans", STAFF),
    ("post", "/api/v1/training-plans", {"trainer", "admin"}),
    ("patch", "/api/v1/training-plans/{plan}", {"trainer", "admin"}),
    ("get", "/api/v1/meal-plans", STAFF),
    ("post", "/api/v1/meal-plans", {"nutritionist", "admin"}),
    ("put", "/api/v1/meal-plans/{meal_plan}", {"nutritionist", "admin"}),
    ("delete", "/api/v1/meal-plans/{meal_plan}", {"nutritionist", "admin"}),
    ("get", "/api/v1/foods", EVERYONE_AUTHENTICATED),
    ("get", "/api/v1/foods/{food}", EVERYONE_AUTHENTICATED),
    ("get", "/api/v1/meal-plans/{meal_plan}/menu", STAFF),
    ("put", "/api/v1/meal-plans/{meal_plan}/menu", {"nutritionist", "admin"}),
    ("get", "/api/v1/me/nutrition-plan/menu", CLIENT),
    ("get", "/api/v1/me/shopping-list", CLIENT),
    ("get", "/api/v1/me/food-log", CLIENT),
    ("post", "/api/v1/me/food-log", CLIENT),
    ("post", "/api/v1/me/food-log/copy-menu", CLIENT),
    ("get", "/api/v1/me/food-log/summary", CLIENT),
    ("patch", "/api/v1/me/food-log/999999", CLIENT),
    ("delete", "/api/v1/me/food-log/999999", CLIENT),
    ("get", "/api/v1/users/{target}/food-log/summary", STAFF),
    ("post", "/api/v1/foods", {"nutritionist", "admin"}),
    ("patch", "/api/v1/foods/{food}", {"nutritionist", "admin"}),
    ("delete", "/api/v1/foods/{food}", {"nutritionist", "admin"}),
    ("get", "/api/v1/users", STAFF),
    ("get", "/api/v1/users/{target}", STAFF),
    ("post", "/api/v1/users", {"admin"}),
    ("patch", "/api/v1/users/{target}", {"admin"}),
    ("delete", "/api/v1/users/{target}", {"admin"}),
    ("get", "/api/v1/assignments/pending", STAFF),
    ("get", "/api/v1/adherence", STAFF),
    ("get", "/api/v1/me/notes", CLIENT),
    ("post", "/api/v1/me/notes", CLIENT),
    ("get", "/api/v1/me/notes/unread", CLIENT),
    ("post", "/api/v1/me/notes/read", CLIENT),
    ("get", "/api/v1/notes/inbox", STAFF),
    ("get", "/api/v1/users/{target}/notes", STAFF),
    ("post", "/api/v1/users/{target}/notes", STAFF),
    ("post", "/api/v1/users/{target}/notes/read", STAFF),
    ("get", "/api/v1/users/{target}/adherence", STAFF),
    ("post", "/api/v1/users/{target}/assign-training-plan", {"trainer", "admin"}),
    ("post", "/api/v1/users/{target}/assign-nutrition-plan", {"nutritionist", "admin"}),
    ("get", "/api/v1/statistics/summary", {"admin"}),
    ("get", "/api/v1/statistics/exercise-popularity", {"admin"}),
    ("get", "/api/v1/statistics/platform-growth", {"admin"}),
    ("get", "/api/v1/statistics/years", {"admin"}),
]


def build_path(template: str, world) -> str:
    return template.format(
        exercise=world["exercise"].id,
        workout=world["workout"].id,
        plan=world["plan"].id,
        meal_plan=world["meal_plan"].id,
        food=world["food"].id,
        target=world["target"].id,
    )


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize(("method", "template", "allowed"), MATRIX, ids=lambda v: str(v))
def test_permission_matrix(api_client, world, role, method, template, allowed):
    actor = world["actors"][role]
    if actor is not None:
        api_client.force_authenticate(actor)

    response = getattr(api_client, method)(build_path(template, world), {})

    if role in allowed:
        assert response.status_code not in (401, 403), response.content
    elif role == "anonymous":
        assert response.status_code == 401
    else:
        assert response.status_code == 403


def test_clients_never_see_other_users_resources(auth_api):
    """A client asking for someone else's workout gets 404, not 403 (no existence leak)."""
    owner, intruder = active_client(), active_client()
    row = owner.training_plans.get(is_current=True).workouts.first()

    response = auth_api(intruder).get(f"/api/v1/me/training-plan/workouts/{row.id}")

    assert response.status_code == 404
