from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.progress.models import WeightRecord
from apps.training.models import UserPlanWorkout, WorkoutSession
from tests.factories import active_client, onboarded_client

DASHBOARD = "/api/v1/me/progress/dashboard"
HISTORY = "/api/v1/me/progress/history"
WEIGHTS = "/api/v1/me/weight-records"

pytestmark = pytest.mark.django_db


def add_session(user, day: date, workout=None, name="Sesión"):
    assignment = user.training_plans.get(is_current=True)
    workout = workout or assignment.plan.plan_workouts.first().workout
    return WorkoutSession.objects.create(
        user=user,
        user_plan=assignment,
        workout=workout,
        workout_name=name,
        completed_at=timezone.make_aware(
            datetime.combine(day, datetime.min.time().replace(hour=19))
        ),
        total_sets=9,
        total_reps=90,
        duration_minutes=30,
    )


class TestDashboard:
    def test_requires_a_training_plan(self, auth_api, onboarded_client):
        response = auth_api(onboarded_client).get(DASHBOARD)

        assert response.status_code == 409
        assert response.json()["code"] == "training_plan_not_assigned"

    @freeze_time("2026-11-04 10:00:00")  # Wednesday
    def test_calendar_next_workout_and_motivation(self, auth_api, settings):
        settings.DEFAULT_TRAINING_TIME = "18:00"
        client = active_client()
        assignment = client.training_plans.get(is_current=True)
        assignment.date_started = date(2026, 11, 1)
        assignment.save()
        add_session(client, date(2026, 11, 2))

        body = auth_api(client).get(DASHBOARD).json()

        assert body["month"] == "2026-11"
        assert body["completed_days"] == ["2026-11-02"]
        assert body["scheduled_days"][:4] == [
            "2026-11-02",
            "2026-11-04",
            "2026-11-06",
            "2026-11-09",
        ]
        assert len(body["scheduled_days"]) == 13
        first = UserPlanWorkout.objects.filter(user_plan=assignment).order_by(
            "plan_workout__order"
        )[0]
        assert body["next_workout"]["id"] == first.id
        assert body["next_workout"]["scheduled_date"] == "2026-11-04"
        assert body["next_workout"]["target_datetime"] == "2026-11-04T18:00:00+01:00"
        assert body["total_sessions"] == 1
        assert body["plan_progress"] == 0
        assert body["motivation"]["keys"][0] == "motivation.sessions.t1"

    @freeze_time("2026-11-11 10:00:00")  # Wednesday; default days: Monday, Wednesday, Friday
    def test_this_week_day_by_day(self, auth_api):
        client = active_client()
        assignment = client.training_plans.get(is_current=True)
        assignment.date_started = date(2026, 10, 12)
        assignment.save()
        add_session(client, date(2026, 11, 9))
        add_session(client, date(2026, 11, 10))  # an extra day also counts as trained

        week = auth_api(client).get(DASHBOARD).json()["week"]

        assert [day["date"] for day in week][::6] == ["2026-11-09", "2026-11-15"]
        assert [(day["scheduled"], day["completed"]) for day in week] == [
            (True, True),
            (False, True),
            (True, False),
            (False, False),
            (True, False),
            (False, False),
            (False, False),
        ]

    @freeze_time("2026-11-11 10:00:00")
    def test_streak_of_complete_weeks(self, auth_api):
        client = active_client()
        assignment = client.training_plans.get(is_current=True)
        assignment.date_started = date(2026, 10, 12)
        assignment.save()
        add_session(client, date(2026, 10, 12))  # 1 of 3: breaks the streak there
        for monday in (date(2026, 10, 19), date(2026, 10, 26), date(2026, 11, 2)):
            for offset in (0, 2, 4):
                add_session(client, monday + timedelta(days=offset))
        add_session(client, date(2026, 11, 9))  # this week, under way: neither counts nor breaks

        assert auth_api(client).get(DASHBOARD).json()["streak_weeks"] == 3

    def test_the_current_week_counts_once_complete(self, auth_api):
        client = active_client()
        assignment = client.training_plans.get(is_current=True)
        assignment.date_started = date(2026, 11, 4)  # a Wednesday: that week only has 2 days
        assignment.save()
        for day in (4, 6, 9, 11, 13):
            add_session(client, date(2026, 11, day))
        add_session(active_client(), date(2026, 11, 2))  # someone else's

        with freeze_time("2026-11-13 21:00:00"):
            body = auth_api(client).get(DASHBOARD).json()

        assert body["streak_weeks"] == 2

    def test_no_streak_without_complete_weeks(self, auth_api):
        client = active_client()

        with freeze_time("2026-11-11 10:00:00"):
            assert auth_api(client).get(DASHBOARD).json()["streak_weeks"] == 0

    @freeze_time("2026-11-04 10:00:00")
    def test_month_parameter(self, auth_api):
        client = active_client()
        assignment = client.training_plans.get(is_current=True)
        assignment.date_started = date(2026, 9, 15)
        assignment.save()
        add_session(client, date(2026, 10, 7))

        body = auth_api(client).get(DASHBOARD, {"month": "2026-10"}).json()

        assert body["month"] == "2026-10"
        assert body["completed_days"] == ["2026-10-07"]
        assert body["scheduled_days"][0] == "2026-10-02"

    @pytest.mark.parametrize("month", ["2026-13", "26-01", "noviembre"])
    def test_invalid_month(self, auth_api, month):
        response = auth_api(active_client()).get(DASHBOARD, {"month": month})

        assert response.status_code == 400
        assert response.json()["field_codes"]["month"] == ["invalid_month"]


class TestHistory:
    def test_requires_a_training_plan(self, auth_api, onboarded_client):
        assert auth_api(onboarded_client).get(HISTORY).status_code == 409

    def test_lists_sessions_newest_first_with_filters(self, auth_api):
        client = active_client()
        plan_workouts = list(client.training_plans.get(is_current=True).plan.plan_workouts.all())
        add_session(client, date(2026, 9, 1), plan_workouts[0].workout, "A")
        add_session(client, date(2026, 9, 10), plan_workouts[1].workout, "B")
        add_session(client, date(2026, 9, 20), plan_workouts[0].workout, "C")
        add_session(active_client(), date(2026, 9, 5))
        api = auth_api(client)

        everything = api.get(HISTORY).json()
        ranged = api.get(HISTORY, {"from": "2026-09-05", "to": "2026-09-20"}).json()
        by_workout = api.get(HISTORY, {"workout": plan_workouts[0].workout_id}).json()

        assert [row["workout_name"] for row in everything["results"]] == ["C", "B", "A"]
        assert everything["count"] == 3
        assert [row["workout_name"] for row in ranged["results"]] == ["C", "B"]
        assert [row["workout_name"] for row in by_workout["results"]] == ["C", "A"]

    def test_is_paginated(self, auth_api):
        client = active_client()
        for day in range(1, 6):
            add_session(client, date(2026, 8, day))

        body = auth_api(client).get(HISTORY, {"limit": 2}).json()

        assert body["count"] == 5
        assert len(body["results"]) == 2


class TestWeightRecords:
    def test_summary_includes_initial_and_target(self, auth_api, onboarded_client):
        body = auth_api(onboarded_client).get(WEIGHTS).json()

        assert body["goal"] == "lose_weight"
        assert body["initial_weight_kg"] == 80.0
        assert body["target_weight_kg"] == 75.0
        assert body["current_weight_kg"] == 80.0
        assert body["records"] == [
            {"id": body["records"][0]["id"], "date": "2026-01-01", "weight_kg": 80.0}
        ]

    def test_post_returns_the_updated_series(self, auth_api, onboarded_client):
        """Regression #7: the weight chart did not refresh after adding a weight."""
        response = auth_api(onboarded_client).post(WEIGHTS, {"weight_kg": 79.2})

        body = response.json()
        assert response.status_code == 201
        assert body["current_weight_kg"] == 79.2
        assert [record["weight_kg"] for record in body["records"]] == [80.0, 79.2]

    def test_same_day_is_updated(self, auth_api, onboarded_client):
        api = auth_api(onboarded_client)

        api.post(WEIGHTS, {"weight_kg": 79.2, "date": "2026-02-01"})
        api.post(WEIGHTS, {"weight_kg": 78.8, "date": "2026-02-01"})

        assert WeightRecord.objects.get(
            user=onboarded_client, date="2026-02-01"
        ).weight_kg == Decimal("78.8")

    @pytest.mark.parametrize(
        ("payload", "field", "code"),
        [
            ({"weight_kg": 29}, "weight_kg", "min_value"),
            ({"weight_kg": 301}, "weight_kg", "max_value"),
            ({"weight_kg": 70, "date": "2999-01-01"}, "date", "future_date"),
            ({"weight_kg": 70, "date": "1990-01-01"}, "date", "date_too_old"),
            ({}, "weight_kg", "required"),
        ],
    )
    def test_validation(self, auth_api, onboarded_client, payload, field, code):
        response = auth_api(onboarded_client).post(WEIGHTS, payload)

        assert response.status_code == 400
        assert response.json()["field_codes"][field] == [code]

    def test_requires_onboarding(self, auth_api, client_user):
        api = auth_api(client_user)

        assert api.get(WEIGHTS).status_code == 409
        assert api.post(WEIGHTS, {"weight_kg": 70}).json()["code"] == "onboarding_not_completed"

    def test_staff_cannot_use_it(self, auth_api, trainer):
        assert auth_api(trainer).get(WEIGHTS).status_code == 403

    def test_other_clients_records_are_not_visible(self, auth_api):
        mine, other = onboarded_client(), onboarded_client()
        WeightRecord.objects.create(user=other, weight_kg=99, date=date(2026, 3, 3))

        records = auth_api(mine).get(WEIGHTS).json()["records"]

        assert [record["weight_kg"] for record in records] == [80.0]


class TestWeightHistoryBound:
    def test_up_to_five_years_back(self, auth_api, onboarded_client):
        from apps.progress.serializers import WEIGHT_HISTORY_YEARS, years_before

        api = auth_api(onboarded_client)
        today = timezone.localdate()
        oldest = years_before(today, WEIGHT_HISTORY_YEARS)

        assert api.post(WEIGHTS, {"weight_kg": 80, "date": str(oldest)}).status_code == 201
        too_old = api.post(WEIGHTS, {"weight_kg": 80, "date": str(oldest - timedelta(days=1))})
        assert too_old.json()["field_codes"] == {"date": ["date_too_old"]}

    def test_years_before_a_29_february(self):
        from apps.progress.serializers import years_before

        assert years_before(date(2028, 2, 29), 5) == date(2023, 2, 28)
        assert years_before(date(2026, 11, 6), 5) == date(2021, 11, 6)
