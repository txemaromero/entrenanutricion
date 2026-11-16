"""Query budgets of the key read endpoints: the number of queries must not grow with the data."""

from datetime import date, datetime

import pytest
from django.utils import timezone

from apps.progress.models import WeightRecord
from apps.training.models import WorkoutSession
from tests.factories import active_client, plan_with_workouts

pytestmark = pytest.mark.django_db


def add_history(user, sessions: int):
    assignment = user.training_plans.get(is_current=True)
    workout = assignment.plan.plan_workouts.first().workout
    for day in range(1, sessions + 1):
        WorkoutSession.objects.create(
            user=user,
            user_plan=assignment,
            workout=workout,
            workout_name=workout.name,
            completed_at=timezone.make_aware(datetime(2026, 10, day, 18)),
        )
        WeightRecord.objects.create(user=user, weight_kg=80 - day / 10, date=date(2026, 10, day))


@pytest.mark.parametrize("sessions", [2, 20])
def test_dashboard_query_budget(auth_api, sessions, django_assert_max_num_queries):
    client = active_client()
    add_history(client, sessions)
    api = auth_api(client)

    with django_assert_max_num_queries(16):
        assert api.get("/api/v1/me/progress/dashboard", {"month": "2026-10"}).status_code == 200


def test_history_query_budget(auth_api, django_assert_max_num_queries):
    client = active_client()
    add_history(client, 25)

    with django_assert_max_num_queries(5):
        response = auth_api(client).get("/api/v1/me/progress/history")

    assert response.json()["count"] == 25


def test_my_nutrition_plan_query_budget(auth_api, django_assert_max_num_queries):
    api = auth_api(active_client())

    with django_assert_max_num_queries(2):
        assert api.get("/api/v1/me/nutrition-plan").status_code == 200


def test_user_detail_query_budget(auth_api, admin_user, django_assert_max_num_queries):
    client = active_client()
    add_history(client, 20)
    api = auth_api(admin_user)

    with django_assert_max_num_queries(8):
        body = api.get(f"/api/v1/users/{client.id}").json()

    assert len(body["weight_records"]) == 21


def test_training_plan_detail_for_client_query_budget(auth_api, django_assert_max_num_queries):
    client = active_client()
    from apps.assignments.services import assign_training_plan

    assign_training_plan(client, plan_with_workouts(6, exercises=5), None, replace=True)

    with django_assert_max_num_queries(12):
        assert auth_api(client).get("/api/v1/me/training-plan").status_code == 200


def test_statistics_query_budget(auth_api, admin_user, django_assert_max_num_queries):
    for _ in range(5):
        add_history(active_client(), 3)
    api = auth_api(admin_user)

    # Roles, statuses, goals, and one query each for the sessions and the sign-ups of both periods.
    with django_assert_max_num_queries(6):
        api.get("/api/v1/statistics/summary")
    with django_assert_max_num_queries(2):
        api.get("/api/v1/statistics/exercise-popularity", {"year": 2026})
    with django_assert_max_num_queries(2):
        api.get("/api/v1/statistics/platform-growth", {"year": 2026})
    with django_assert_max_num_queries(2):
        api.get("/api/v1/statistics/sessions", {"year": 2026})
    with django_assert_max_num_queries(3):
        api.get("/api/v1/statistics/plan-popularity")
