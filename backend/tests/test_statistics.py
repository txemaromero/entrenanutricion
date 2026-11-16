from datetime import date, datetime

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.accounts.models import Goal
from apps.statistics.services import previous_period
from apps.training.models import ExerciseLog, WorkoutSession
from tests.factories import (
    ExerciseFactory,
    MealPlanFactory,
    UserFactory,
    active_client,
    assign_meal_plan,
    assign_plan,
    onboarded_client,
    plan_with_workouts,
)

BASE = "/api/v1/statistics"

pytestmark = pytest.mark.django_db


def log(user, exercise, day: date, times: int = 1):
    session = WorkoutSession.objects.create(
        user=user,
        workout_name="W",
        completed_at=timezone.make_aware(datetime.combine(day, datetime.min.time())),
    )
    for _ in range(times):
        ExerciseLog.objects.create(
            user=user,
            exercise=exercise,
            session=session,
            date=day,
            sets_completed=3,
            reps_completed=10,
            rest_time=60,
        )


def joined(year, month):
    return timezone.make_aware(datetime(year, month, 15, 12))


class TestExercisePopularity:
    def test_counts_logs_of_the_year_descending(self, auth_api, admin_user):
        user = UserFactory()
        squat, press, row = (ExerciseFactory(name=name) for name in ("Sentadilla", "Press", "Remo"))
        log(user, press, date(2026, 3, 1), times=2)
        log(user, squat, date(2026, 4, 1), times=3)
        log(user, row, date(2026, 5, 1), times=1)
        log(user, row, date(2025, 5, 1), times=9)

        body = auth_api(admin_user).get(f"{BASE}/exercise-popularity", {"year": 2026}).json()

        assert body["year"] == 2026
        assert [(row["name"], row["count"]) for row in body["results"]] == [
            ("Sentadilla", 3),
            ("Press", 2),
            ("Remo", 1),
        ]

    def test_limit(self, auth_api, admin_user):
        user = UserFactory()
        for index in range(5):
            log(user, ExerciseFactory(), date(2026, 1, 1), times=index + 1)

        body = (
            auth_api(admin_user)
            .get(f"{BASE}/exercise-popularity", {"year": 2026, "limit": 2})
            .json()
        )

        assert [row["count"] for row in body["results"]] == [5, 4]

    @pytest.mark.parametrize(
        "params", [{"year": 1999}, {"year": "abc"}, {"limit": 0}, {"limit": 51}]
    )
    def test_invalid_parameters(self, auth_api, admin_user, params):
        response = auth_api(admin_user).get(f"{BASE}/exercise-popularity", params)

        assert response.status_code == 400


class TestPlatformGrowth:
    def test_new_clients_per_month(self, auth_api, admin_user):
        UserFactory(date_joined=joined(2026, 1))
        UserFactory(date_joined=joined(2026, 1))
        UserFactory(date_joined=joined(2026, 7))
        UserFactory(date_joined=joined(2025, 7))

        body = auth_api(admin_user).get(f"{BASE}/platform-growth", {"year": 2026}).json()

        assert body["year"] == 2026
        assert len(body["months"]) == 12
        assert body["months"][0] == {"month": 1, "count": 2}
        assert body["months"][6] == {"month": 7, "count": 1}
        assert sum(row["count"] for row in body["months"]) == 3

    @freeze_time("2026-05-05")
    def test_defaults_to_the_current_year(self, auth_api, admin_user):
        body = auth_api(admin_user).get(f"{BASE}/platform-growth").json()

        assert body["year"] == 2026


class TestSummaryAndYears:
    @freeze_time("2026-05-20 12:00:00")
    def test_kpis(self, auth_api, admin_user, trainer, nutritionist):
        active = active_client()
        onboarded_client()
        UserFactory()
        UserFactory(is_active=False, status="inactive")
        log(active, ExerciseFactory(), date(2026, 5, 3))
        log(active, ExerciseFactory(), date(2026, 4, 30))

        body = auth_api(admin_user).get(f"{BASE}/summary").json()

        assert body["users_by_role"] == {"client": 3, "admin": 1, "trainer": 2, "nutritionist": 2}
        assert body["active_clients"] == 1
        assert body["pending_assignment"] == 1
        assert body["pending_onboarding"] == 1
        assert body["sessions_this_month"] == 1

    @freeze_time("2026-05-20 12:00:00")
    def test_month_to_date_against_the_same_days_before(self, auth_api, admin_user):
        client = active_client()  # signs up now, this month
        for day in (date(2026, 5, 2), date(2026, 5, 19)):
            log(client, ExerciseFactory(), day)
        for day in (date(2026, 4, 3), date(2026, 4, 20), date(2026, 4, 21)):  # 21: after the 20th
            log(client, ExerciseFactory(), day)
        UserFactory(date_joined=joined(2026, 5))
        UserFactory(date_joined=joined(2026, 4), is_active=False, status="inactive")  # counts
        UserFactory(date_joined=timezone.make_aware(datetime(2026, 4, 25)))  # after the 20th

        body = auth_api(admin_user).get(f"{BASE}/summary").json()

        assert (body["sessions_this_month"], body["sessions_previous_period"]) == (2, 2)
        assert (body["new_clients_this_month"], body["new_clients_previous_period"]) == (2, 1)

    def test_previous_period_of_a_longer_month(self):
        assert previous_period(date(2026, 3, 31)) == (date(2026, 2, 1), date(2026, 2, 28))
        assert previous_period(date(2026, 1, 10)) == (date(2025, 12, 1), date(2025, 12, 10))

    def test_active_clients_per_goal(self, auth_api, admin_user):
        for goal in (Goal.LOSE_WEIGHT, Goal.LOSE_WEIGHT, Goal.MAINTAIN):
            client = onboarded_client()
            client.details.goal = goal
            client.details.save()
        gone = onboarded_client(is_active=False)  # closed account: not counted
        gone.details.goal = Goal.GAIN_MUSCLE
        gone.details.save()

        goals = auth_api(admin_user).get(f"{BASE}/summary").json()["clients_by_goal"]

        assert goals == {"lose_weight": 2, "gain_muscle": 0, "maintain": 1}

    @freeze_time("2026-05-20")
    def test_years_with_data(self, auth_api, admin_user):
        user = UserFactory(date_joined=joined(2024, 3))
        log(user, ExerciseFactory(), date(2023, 6, 1))

        body = auth_api(admin_user).get(f"{BASE}/years").json()

        assert body == {"years": [2026, 2024, 2023]}


class TestSessionsAndPlans:
    def test_sessions_per_month(self, auth_api, admin_user):
        client = active_client()
        log(client, ExerciseFactory(), date(2025, 3, 2))
        log(client, ExerciseFactory(), date(2025, 3, 20))
        log(client, ExerciseFactory(), date(2025, 11, 5))
        log(client, ExerciseFactory(), date(2024, 3, 2))  # another year

        body = auth_api(admin_user).get(f"{BASE}/sessions", {"year": 2025}).json()

        assert body["year"] == 2025
        assert [row["count"] for row in body["months"]] == [0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1, 0]

    def test_plans_with_most_clients_now(self, auth_api, admin_user):
        strength = plan_with_workouts(name="Fuerza")
        cardio = plan_with_workouts(name="Cardio")
        diet = MealPlanFactory(name="Mediterránea")
        for plan in (strength, strength, cardio):
            client = onboarded_client()
            assign_plan(client, plan)
            assign_meal_plan(client, diet)
        gone = onboarded_client(is_active=False)  # closed account: not counted
        assign_plan(gone, cardio)

        body = auth_api(admin_user).get(f"{BASE}/plan-popularity").json()

        assert [(row["name"], row["count"]) for row in body["training"]] == [
            ("Fuerza", 2),
            ("Cardio", 1),
        ]
        assert [(row["name"], row["count"]) for row in body["nutrition"]] == [("Mediterránea", 3)]


class TestAdminOnly:
    @pytest.mark.parametrize(
        "path",
        [
            "exercise-popularity",
            "platform-growth",
            "sessions",
            "plan-popularity",
            "summary",
            "years",
        ],
    )
    @pytest.mark.parametrize("role", ["trainer", "nutritionist", "client_user"])
    def test_other_roles_are_forbidden(self, request, auth_api, path, role):
        response = auth_api(request.getfixturevalue(role)).get(f"{BASE}/{path}")

        assert response.status_code == 403
