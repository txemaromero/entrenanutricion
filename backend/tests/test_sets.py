"""Logged sets, personal records and load history (phase 12)."""

import pytest

from apps.training.models import ExerciseSet, UserPlanWorkout, WorkoutSession
from apps.training.services import estimated_one_rep_max
from tests.factories import active_client

pytestmark = pytest.mark.django_db

RECORDS = "/api/v1/me/records"


def available_row(client) -> UserPlanWorkout:
    return UserPlanWorkout.objects.filter(user_plan__user=client, status="available").first()


def mark(api, row, item, completed=True, sets=None):
    body = {"completed": completed}
    if sets is not None:
        body["sets"] = sets
    return api.put(
        f"/api/v1/me/training-plan/workouts/{row.id}/exercises/{item.id}", body, format="json"
    )


def finish(api, row, sets_by_item=None):
    """Mark every exercise (with the given sets) and complete the workout."""
    for item in row.plan_workout.workout.items.all():
        mark(api, row, item, sets=(sets_by_item or {}).get(item.id))
    return api.post(f"/api/v1/me/training-plan/workouts/{row.id}/complete").json()


class TestLogging:
    def test_sets_are_saved_with_the_mark_and_come_back(self, auth_api):
        client = active_client()
        api = auth_api(client)
        row = available_row(client)
        item = row.plan_workout.workout.items.first()

        response = mark(api, row, item, sets=[{"reps": 10, "weight_kg": 40}, {"reps": 8}])

        assert response.status_code == 200
        assert response.json()["logged_sets"] == [
            {"reps": 10, "weight_kg": 40.0},
            {"reps": 8, "weight_kg": None},
        ]
        day = api.get(f"/api/v1/me/training-plan/workouts/{row.id}").json()
        logged = next(exercise for exercise in day["exercises"] if exercise["id"] == item.id)
        assert logged["logged_sets"] == [
            {"reps": 10, "weight_kg": 40.0},
            {"reps": 8, "weight_kg": None},
        ]

    def test_a_mark_without_sets_keeps_the_logged_ones(self, auth_api):
        client = active_client()
        api = auth_api(client)
        row = available_row(client)
        item = row.plan_workout.workout.items.first()
        mark(api, row, item, completed=False, sets=[{"reps": 12, "weight_kg": 20}])

        response = mark(api, row, item, completed=True)

        assert response.json()["logged_sets"] == [{"reps": 12, "weight_kg": 20.0}]

    @pytest.mark.parametrize(
        ("sets", "field"),
        [
            ([{"reps": 201}], "sets.0.reps"),
            ([{"reps": 10, "weight_kg": -1}], "sets.0.weight_kg"),
            ([{"reps": 10, "weight_kg": 501}], "sets.0.weight_kg"),
            ([{"reps": 10}] * 21, "sets"),
        ],
    )
    def test_invalid_sets(self, auth_api, sets, field):
        client = active_client()
        row = available_row(client)

        response = mark(auth_api(client), row, row.plan_workout.workout.items.first(), sets=sets)

        assert response.status_code == 400
        assert field in response.json()["field_codes"]


class TestCompletion:
    def test_logged_sets_go_to_the_history(self, auth_api):
        client = active_client()
        api = auth_api(client)
        row = available_row(client)
        first, *others = row.plan_workout.workout.items.order_by("order")

        finish(
            api, row, {first.id: [{"reps": 10, "weight_kg": 40}, {"reps": 9, "weight_kg": 42.5}]}
        )

        session = WorkoutSession.objects.get(user=client)
        sets = ExerciseSet.objects.filter(log__session=session, log__exercise=first.exercise)
        assert [(entry.reps, float(entry.weight_kg)) for entry in sets] == [(10, 40.0), (9, 42.5)]
        # Exercises without logged sets keep the planned ones, without load.
        planned = ExerciseSet.objects.filter(log__session=session, log__exercise=others[0].exercise)
        assert planned.count() == others[0].sets
        assert {entry.weight_kg for entry in planned} == {None}
        assert session.total_sets == 2 + sum(item.sets for item in others)
        assert session.total_reps == 19 + sum(item.sets * item.reps for item in others)

    def test_last_sets_are_shown_next_time(self, auth_api):
        client = active_client()
        api = auth_api(client)
        row = available_row(client)
        first, second, *_ = row.plan_workout.workout.items.order_by("order")
        nxt_before = available_row(client)
        day_before = api.get(f"/api/v1/me/training-plan/workouts/{nxt_before.id}").json()
        assert {exercise["last_sets"] is None for exercise in day_before["exercises"]} == {True}

        finish(api, row, {first.id: [{"reps": 10, "weight_kg": 40}]})

        day = api.get(f"/api/v1/me/training-plan/workouts/{row.id}").json()
        by_item = {exercise["id"]: exercise for exercise in day["exercises"]}
        assert by_item[first.id]["last_sets"] == [{"reps": 10, "weight_kg": 40.0}]
        assert (
            by_item[second.id]["last_sets"]
            == [{"reps": second.reps, "weight_kg": None}] * second.sets
        )

    def test_new_records_are_announced(self, auth_api):
        client = active_client()
        api = auth_api(client)
        row = available_row(client)
        item = row.plan_workout.workout.items.order_by("order").first()

        first = finish(api, row, {item.id: [{"reps": 10, "weight_kg": 40}]})
        assert first["new_records"] == []  # the first weighted session is not a record

        # Same workout again in the next cycle(s): heavier.
        while (
            row := available_row(client)
        ).plan_workout_id != item.workout.plan_entries.first().id:
            finish(api, row)
        same_weight = finish(api, row, {item.id: [{"reps": 12, "weight_kg": 40}]})
        assert same_weight["new_records"] == []

        while (
            row := available_row(client)
        ).plan_workout_id != item.workout.plan_entries.first().id:
            finish(api, row)
        heavier = finish(api, row, {item.id: [{"reps": 6, "weight_kg": 45}]})
        assert heavier["new_records"] == [
            {
                "exercise_id": item.exercise_id,
                "exercise_name": item.exercise.name,
                "weight_kg": 45.0,
                "reps": 6,
            }
        ]


class TestRecords:
    def test_epley(self):
        assert estimated_one_rep_max(100, 1) == 100
        assert estimated_one_rep_max(100, 10) == 133.3

    def test_records_and_history(self, auth_api):
        client = active_client()
        api = auth_api(client)
        row = available_row(client)
        item = row.plan_workout.workout.items.order_by("order").first()
        finish(api, row, {item.id: [{"reps": 10, "weight_kg": 40}, {"reps": 5, "weight_kg": 50}]})

        records = api.get(RECORDS).json()
        record = next(r for r in records if r["exercise"]["id"] == item.exercise_id)
        assert record["best_weight_kg"] == 50.0
        assert record["best_weight_reps"] == 5
        assert record["estimated_one_rm_kg"] == estimated_one_rep_max(50, 5) == 58.3
        assert record["best_weight_date"]

        history = api.get(f"/api/v1/me/exercises/{item.exercise_id}/history").json()
        assert history["record"]["best_weight_kg"] == 50.0
        assert history["entries"][0]["max_weight_kg"] == 50.0
        assert history["entries"][0]["volume_kg"] == 650.0
        assert history["entries"][0]["sets"] == [
            {"reps": 10, "weight_kg": 40.0},
            {"reps": 5, "weight_kg": 50.0},
        ]

    def test_exercises_without_load_have_no_record(self, auth_api):
        client = active_client()
        api = auth_api(client)
        finish(api, available_row(client))

        assert api.get(RECORDS).json() == []
        item = available_row(client).plan_workout.workout.items.first()
        history = api.get(f"/api/v1/me/exercises/{item.exercise_id}/history").json()
        assert history["record"] is None

    def test_only_clients(self, auth_api, trainer):
        assert auth_api(trainer).get(RECORDS).status_code == 403


@pytest.mark.django_db
class TestRecordsInTheDatabase:
    def logged(self, user, exercise, day, sets):
        from apps.training.models import ExerciseLog

        session = WorkoutSession.objects.create(user=user, workout_name="Sesión")
        log = ExerciseLog.objects.create(
            user=user,
            exercise=exercise,
            session=session,
            date=day,
            sets_completed=len(sets),
            reps_completed=sum(reps for reps, _ in sets),
            rest_time=60,
        )
        for number, (reps, weight) in enumerate(sets, start=1):
            ExerciseSet.objects.create(log=log, number=number, reps=reps, weight_kg=weight)

    def test_heaviest_set_first_date_and_best_estimate(
        self, auth_api, django_assert_max_num_queries
    ):
        from datetime import date

        from tests.factories import ExerciseFactory

        client = active_client()
        squat, bench = ExerciseFactory(name="Sentadilla"), ExerciseFactory(name="Banca")
        self.logged(client, squat, date(2026, 10, 1), [(5, 100), (12, 90)])
        self.logged(client, squat, date(2026, 10, 8), [(5, 100), (3, 100)])
        self.logged(client, squat, date(2026, 10, 15), [(5, 100)])
        self.logged(client, bench, date(2026, 10, 2), [(1, 70), (10, None)])
        api = auth_api(client)

        with django_assert_max_num_queries(6):
            records = api.get(RECORDS).json()

        assert [record["exercise"]["name"] for record in records] == ["Banca", "Sentadilla"]
        bench_record, squat_record = records
        # Heaviest set: most weight, then most reps, and the first day it was done.
        assert (squat_record["best_weight_kg"], squat_record["best_weight_reps"]) == (100.0, 5)
        assert squat_record["best_weight_date"] == "2026-10-01"
        # The best estimate can come from a lighter set: 90 kg x 12 beats 100 kg x 5.
        assert squat_record["estimated_one_rm_kg"] == estimated_one_rep_max(90, 12) == 126.0
        assert bench_record["estimated_one_rm_kg"] == estimated_one_rep_max(70, 1) == 70.0
