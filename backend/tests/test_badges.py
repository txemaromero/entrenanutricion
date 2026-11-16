"""Gamification (phase 9): badges earned from workouts, plan cycles and weigh-ins."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.models import Goal, UserDetails
from apps.progress.badges import badge_progress, sync_badges
from apps.progress.models import BadgeCode, UserBadge, WeightRecord
from apps.training.models import UserPlanWorkout, WorkoutSession
from tests.factories import UserFactory, active_client

BADGES = "/api/v1/me/badges"
WEIGHTS = "/api/v1/me/weight-records"

pytestmark = pytest.mark.django_db


def add_sessions(user, days: list[date]) -> None:
    assignment = user.training_plans.get(is_current=True)
    workout = assignment.plan.plan_workouts.first().workout
    WorkoutSession.objects.bulk_create(
        WorkoutSession(
            user=user,
            user_plan=assignment,
            workout=workout,
            workout_name=workout.name,
            completed_at=timezone.make_aware(datetime.combine(day, datetime.min.time())),
        )
        for day in days
    )


def earned(user) -> set[str]:
    return set(UserBadge.objects.filter(user=user).values_list("code", flat=True))


def set_goal(user, goal, change_kg="5.0", initial="80.0"):
    UserDetails.objects.filter(user=user).update(
        goal=goal, target_weight_change_kg=Decimal(change_kg), initial_weight_kg=Decimal(initial)
    )


def weigh(user, kg: str, day: date):
    WeightRecord.objects.update_or_create(user=user, date=day, defaults={"weight_kg": Decimal(kg)})


class TestRules:
    def test_a_new_client_has_no_badges(self):
        client = active_client()

        assert sync_badges(client) == []
        progress = badge_progress(client)
        assert progress[BadgeCode.FIRST_WORKOUT] == (0, 1)
        assert progress[BadgeCode.WEIGHT_LOGS_10] == (1, 10)  # the onboarding weight

    @pytest.mark.parametrize(
        ("sessions", "expected"),
        [
            (1, {"first_workout"}),
            (10, {"first_workout", "workouts_10"}),
            (50, {"first_workout", "workouts_10", "workouts_50"}),
        ],
    )
    def test_workout_milestones(self, sessions, expected):
        client = active_client()
        start = date(2026, 1, 5)
        # One workout a week, so the perfect week does not interfere.
        add_sessions(client, [start + timedelta(weeks=n) for n in range(sessions)])

        assert set(sync_badges(client)) == expected
        assert badge_progress(client)[BadgeCode.WORKOUTS_100] == (sessions, 100)

    def test_perfect_week_needs_every_weekly_workout_in_the_same_week(self):
        client = active_client()  # 3 weekly days
        add_sessions(client, [date(2026, 3, 2), date(2026, 3, 4), date(2026, 3, 9)])
        assert BadgeCode.PERFECT_WEEK not in sync_badges(client)
        assert badge_progress(client)[BadgeCode.PERFECT_WEEK] == (2, 3)

        add_sessions(client, [date(2026, 3, 6)])  # Mon, Wed and Fri of the same week

        assert BadgeCode.PERFECT_WEEK in sync_badges(client)

    def test_first_full_plan(self):
        client = active_client()
        assignment = client.training_plans.get(is_current=True)
        assert BadgeCode.FIRST_CYCLE not in sync_badges(client)

        assignment.cycle = 2
        assignment.save()

        assert BadgeCode.FIRST_CYCLE in sync_badges(client)

    def test_ten_weigh_ins(self):
        client = active_client()
        for n in range(1, 10):
            weigh(client, "79.0", date(2026, 2, n))

        assert BadgeCode.WEIGHT_LOGS_10 in sync_badges(client)

    @pytest.mark.parametrize(
        ("goal", "weight", "reached"),
        [
            (Goal.LOSE_WEIGHT, "75.0", True),
            (Goal.LOSE_WEIGHT, "75.1", False),
            (Goal.GAIN_MUSCLE, "85.0", True),
            (Goal.GAIN_MUSCLE, "84.0", False),
            (Goal.MAINTAIN, "80.0", False),
        ],
    )
    def test_target_weight(self, goal, weight, reached):
        client = active_client()
        set_goal(client, goal, change_kg="0" if goal == Goal.MAINTAIN else "5.0")
        weigh(client, weight, date(2026, 6, 1))

        assert (BadgeCode.GOAL_REACHED in sync_badges(client)) is reached

    def test_badges_are_awarded_once_and_kept(self):
        client = active_client()
        set_goal(client, Goal.LOSE_WEIGHT)
        weigh(client, "74.0", date(2026, 6, 1))
        assert BadgeCode.GOAL_REACHED in sync_badges(client)

        weigh(client, "79.0", date(2026, 6, 2))

        assert sync_badges(client) == []
        assert BadgeCode.GOAL_REACHED in earned(client)
        assert UserBadge.objects.filter(user=client).count() == 1


class TestApi:
    def test_overview_lists_every_badge_with_its_progress(self, auth_api):
        client = active_client()
        add_sessions(client, [date(2026, 1, 5)])

        body = auth_api(client).get(BADGES).json()

        assert body["total"] == len(BadgeCode.values) == 8
        assert body["earned_count"] == 1
        assert body["new_badges"] == ["first_workout"]
        badges = {badge["code"]: badge for badge in body["badges"]}
        assert [badge["code"] for badge in body["badges"]] == BadgeCode.values
        assert badges["first_workout"]["earned"] is True
        assert badges["first_workout"]["awarded_at"] is not None
        assert badges["workouts_10"] == {
            "code": "workouts_10",
            "earned": False,
            "awarded_at": None,
            "current": 1,
            "target": 10,
        }

        again = auth_api(client).get(BADGES).json()
        assert again["new_badges"] == []
        assert again["earned_count"] == 1

    def test_completing_a_workout_reports_new_badges(self, auth_api):
        client = active_client()
        api = auth_api(client)
        row = UserPlanWorkout.objects.filter(user_plan__user=client, status="available").first()
        for item in row.plan_workout.workout.items.all():
            api.put(
                f"/api/v1/me/training-plan/workouts/{row.id}/exercises/{item.id}",
                {"completed": True},
                format="json",
            )

        body = api.post(f"/api/v1/me/training-plan/workouts/{row.id}/complete").json()

        assert body["new_badges"] == ["first_workout"]
        assert earned(client) == {"first_workout"}

    def test_recording_the_weight_reports_new_badges(self, auth_api):
        client = active_client()
        set_goal(client, Goal.LOSE_WEIGHT)

        response = auth_api(client).post(
            WEIGHTS, {"weight_kg": 74.5, "date": "2026-06-01"}, format="json"
        )

        assert response.status_code == 201
        assert response.json()["new_badges"] == ["goal_reached"]
        assert response.json()["current_weight_kg"] == 74.5

    def test_only_clients(self, auth_api, trainer, api_client):
        assert auth_api(trainer).get(BADGES).status_code == 403
        assert api_client.get(BADGES).status_code == 401

    def test_works_before_the_onboarding_form(self, auth_api):
        body = auth_api(UserFactory()).get(BADGES).json()

        assert body["earned_count"] == 0
        assert {badge["target"] for badge in body["badges"] if badge["code"] == "perfect_week"} == {
            3
        }

    def test_query_budget(self, auth_api, django_assert_max_num_queries):
        client = active_client()
        add_sessions(client, [date(2026, 1, 5), date(2026, 1, 6)])
        api = auth_api(client)

        with django_assert_max_num_queries(10):
            api.get(BADGES)
