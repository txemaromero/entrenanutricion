"""A client's training in figures: weeks of sessions, minutes and volume, muscles worked."""

from datetime import date, datetime
from decimal import Decimal

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.training.models import ExerciseLog, ExerciseSet, MuscleGroup, WorkoutSession
from tests.factories import ExerciseFactory, active_client

STATS = "/api/v1/me/progress/stats"

pytestmark = pytest.mark.django_db


def session(user, when: datetime, minutes=30) -> WorkoutSession:
    return WorkoutSession.objects.create(
        user=user,
        workout_name="Sesión",
        completed_at=timezone.make_aware(when),
        duration_minutes=minutes,
    )


def log(user, exercise, day: date, sets=(), sets_completed=None) -> ExerciseLog:
    """An exercise of a completed workout with the sets actually done: (reps, kilos or None)."""
    entry = ExerciseLog.objects.create(
        user=user,
        exercise=exercise,
        session=session(user, datetime.combine(day, datetime.min.time().replace(hour=18))),
        date=day,
        sets_completed=sets_completed if sets_completed is not None else len(sets),
        reps_completed=sum(reps for reps, _ in sets),
        rest_time=60,
    )
    for number, (reps, weight) in enumerate(sets, start=1):
        ExerciseSet.objects.create(log=entry, number=number, reps=reps, weight_kg=weight)
    return entry


def exercise(*slugs):
    item = ExerciseFactory()
    item.muscle_groups.set(MuscleGroup.objects.filter(slug__in=slugs))
    return item


@freeze_time("2026-11-11 10:00:00")  # Wednesday
class TestWeeks:
    def test_twelve_weeks_from_monday_even_without_history(self, auth_api):
        body = auth_api(active_client()).get(STATS).json()

        assert [week["start"] for week in body["weeks"]][:2] == ["2026-08-24", "2026-08-31"]
        assert body["weeks"][-1] == {
            "start": "2026-11-09",
            "sessions": 0,
            "minutes": 0,
            "volume_kg": 0.0,
        }
        assert len(body["weeks"]) == 12
        assert body["muscle_groups"] == []

    def test_sessions_and_minutes_by_week(self, auth_api):
        client = active_client()
        session(client, datetime(2026, 11, 9, 19), minutes=40)  # this Monday
        session(client, datetime(2026, 11, 10, 19), minutes=25)
        session(client, datetime(2026, 11, 8, 23, 30), minutes=30)  # last Sunday, late evening
        session(client, datetime(2026, 8, 23, 19))  # the day before the first week: left out

        weeks = auth_api(client).get(STATS).json()["weeks"]

        assert (weeks[-1]["sessions"], weeks[-1]["minutes"]) == (2, 65)
        assert (weeks[-2]["sessions"], weeks[-2]["minutes"]) == (1, 30)
        assert sum(week["sessions"] for week in weeks) == 3

    def test_volume_counts_the_sets_with_load(self, auth_api):
        client = active_client()
        squat = exercise("quadriceps")
        log(client, squat, date(2026, 11, 10), sets=[(10, Decimal("60")), (8, Decimal("62.5"))])
        log(client, squat, date(2026, 11, 3), sets=[(12, None)])  # bodyweight: no kilos
        log(active_client(), squat, date(2026, 11, 10), sets=[(5, Decimal("100"))])  # someone else

        weeks = auth_api(client).get(STATS).json()["weeks"]

        assert weeks[-1]["volume_kg"] == 1100.0  # 10 × 60 + 8 × 62.5
        assert weeks[-2]["volume_kg"] == 0.0


@freeze_time("2026-11-11 10:00:00")
class TestMuscleGroups:
    def test_sets_of_the_last_four_weeks_most_worked_first(self, auth_api):
        client = active_client()
        bench = exercise("chest", "triceps")
        curl = exercise("biceps")
        log(client, bench, date(2026, 11, 10), sets_completed=4)
        log(client, bench, date(2026, 10, 20), sets_completed=3)
        log(client, curl, date(2026, 11, 9), sets_completed=3)
        log(client, curl, date(2026, 10, 14), sets_completed=5)  # 28 days ago: left out
        log(client, ExerciseFactory(), date(2026, 11, 10), sets_completed=2)  # no muscle group

        groups = auth_api(client).get(STATS).json()["muscle_groups"]

        assert [(group["slug"], group["sets"]) for group in groups] == [
            ("chest", 7),
            ("triceps", 7),
            ("biceps", 3),
        ]
        assert all(group["name"] for group in groups)


class TestAccess:
    def test_only_clients(self, auth_api, trainer, nutritionist, admin_user):
        for user in (trainer, nutritionist, admin_user):
            assert auth_api(user).get(STATS).status_code == 403

    def test_query_budget(self, auth_api, django_assert_max_num_queries):
        client = active_client()
        squat = exercise("quadriceps", "glutes")
        for day in (date(2026, 11, 2), date(2026, 11, 4), date(2026, 11, 6)):
            log(client, squat, day, sets=[(10, Decimal("50")), (10, Decimal("50"))])
        api = auth_api(client)

        with freeze_time("2026-11-11 10:00:00"), django_assert_max_num_queries(5):
            assert api.get(STATS).status_code == 200
