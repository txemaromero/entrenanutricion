from datetime import UTC, datetime

import pytest
from freezegun import freeze_time

from apps.training.models import (
    ExerciseCompletion,
    ExerciseLog,
    UserPlanWorkout,
    UserTrainingPlan,
    WorkoutSession,
)
from tests.factories import assign_plan, onboarded_client, plan_with_workouts

PLAN = "/api/v1/me/training-plan"

pytestmark = pytest.mark.django_db

MONDAY = "2026-11-02 09:00:00"


def workout_url(row_id):
    return f"{PLAN}/workouts/{row_id}"


def rows_of(assignment):
    return list(
        UserPlanWorkout.objects.filter(user_plan=assignment).order_by("plan_workout__order")
    )


def finish_all_exercises(api, row_id):
    for item in api.get(workout_url(row_id)).json()["exercises"]:
        api.put(f"{workout_url(row_id)}/exercises/{item['id']}", {"completed": True})


@pytest.fixture
def setup(auth_api, onboarded_client):
    assignment = assign_plan(onboarded_client, plan_with_workouts(3, exercises=2))
    return auth_api(onboarded_client), assignment


class TestMyTrainingPlan:
    def test_requires_an_assigned_plan(self, auth_api, onboarded_client):
        response = auth_api(onboarded_client).get(PLAN)

        assert response.status_code == 409
        assert response.json()["code"] == "training_plan_not_assigned"

    def test_staff_cannot_use_client_endpoints(self, auth_api, trainer):
        assert auth_api(trainer).get(PLAN).status_code == 403

    @freeze_time(MONDAY)
    def test_sequence_with_lock_and_schedule(self, setup, django_assert_max_num_queries):
        api, assignment = setup

        with django_assert_max_num_queries(12):
            body = api.get(PLAN).json()

        assert body["cycle"] == 1
        assert body["progress"] == 0
        assert body["weekly_training_days"] == 3
        assert [row["status"] for row in body["workouts"]] == ["available", "locked", "locked"]
        assert [row["scheduled_date"] for row in body["workouts"]] == [
            "2026-11-02",
            "2026-11-04",
            "2026-11-06",
        ]
        assert body["next_workout_id"] == body["workouts"][0]["id"]
        assert body["workouts"][0]["summary"]["exercise_count"] == 2
        assert body["plan"]["name"] == assignment.plan.name

    def test_assignment_starts_with_first_available(self, setup):
        _, assignment = setup

        assert [row.status for row in rows_of(assignment)] == ["available", "locked", "locked"]


class TestWorkoutDay:
    def test_day_view_with_summary_and_progress(self, setup):
        api, assignment = setup
        first = rows_of(assignment)[0]

        body = api.get(workout_url(first.id)).json()

        assert len(body["exercises"]) == 2
        assert body["summary"] == {
            "estimated_duration_minutes": 9,  # 2 × 3 × (30 + 60) = 540 s
            "total_sets": 6,
            "total_reps": 60,
            "exercise_count": 2,
        }
        assert body["progress"] == {"completed": 0, "total": 2, "percent": 0}
        assert body["exercises"][0]["completed"] is False

    def test_locked_workout_is_forbidden(self, setup):
        api, assignment = setup
        locked = rows_of(assignment)[1]

        response = api.get(workout_url(locked.id))

        assert response.status_code == 403
        assert response.json()["code"] == "workout_locked"

    def test_other_users_workout_is_not_found(self, setup, auth_api):
        _, assignment = setup
        stranger = onboarded_client()
        assign_plan(stranger)

        response = auth_api(stranger).get(workout_url(rows_of(assignment)[0].id))

        assert response.status_code == 404

    def test_checkbox_state_is_persisted_and_rehydrated(self, setup):
        """Regression #4: checkboxes were unticked when coming back to the workout."""
        api, assignment = setup
        row = rows_of(assignment)[0]
        item_id = api.get(workout_url(row.id)).json()["exercises"][0]["id"]

        marked = api.put(f"{workout_url(row.id)}/exercises/{item_id}", {"completed": True})
        again = api.get(workout_url(row.id)).json()

        assert marked.json()["progress"] == {"completed": 1, "total": 2, "percent": 50}
        assert again["exercises"][0]["completed"] is True
        assert again["progress"]["percent"] == 50

        api.put(f"{workout_url(row.id)}/exercises/{item_id}", {"completed": False})
        assert api.get(workout_url(row.id)).json()["exercises"][0]["completed"] is False

    def test_cannot_mark_exercises_of_locked_workouts(self, setup):
        api, assignment = setup
        locked = rows_of(assignment)[1]
        item = locked.plan_workout.workout.items.first()

        response = api.put(f"{workout_url(locked.id)}/exercises/{item.id}", {"completed": True})

        assert response.status_code == 403

    def test_unknown_exercise_row_is_not_found(self, setup):
        api, assignment = setup
        foreign_item = rows_of(assignment)[1].plan_workout.workout.items.first()

        response = api.put(
            f"{workout_url(rows_of(assignment)[0].id)}/exercises/{foreign_item.id}",
            {"completed": True},
        )

        assert response.status_code == 404


class TestCompleteWorkout:
    def test_requires_every_exercise_marked(self, setup):
        api, assignment = setup

        response = api.post(f"{workout_url(rows_of(assignment)[0].id)}/complete")

        assert response.status_code == 409
        assert response.json()["code"] == "workout_not_finished"

    @freeze_time(MONDAY)
    def test_completes_logs_and_unlocks_the_next(self, setup):
        api, assignment = setup
        first, second, _ = rows_of(assignment)
        finish_all_exercises(api, first.id)

        response = api.post(f"{workout_url(first.id)}/complete")

        body = response.json()
        assert response.status_code == 200
        assert body["cycle_completed"] is False
        assert body["plan_progress"] == 33
        assert body["next_workout_id"] == second.id
        assert body["session"]["total_sets"] == 6
        assert body["motivation"]["keys"][0] == "motivation.sessions.t1"
        assert [row.status for row in rows_of(assignment)] == ["completed", "available", "locked"]
        session = WorkoutSession.objects.get(user=assignment.user)
        assert session.workout_name == first.plan_workout.workout.name
        assert ExerciseLog.objects.filter(session=session).count() == 2

        plan = api.get(PLAN).json()
        # Trained today, so the remaining workouts move to the next scheduled days.
        assert [row["scheduled_date"] for row in plan["workouts"]] == [
            None,
            "2026-11-04",
            "2026-11-06",
        ]
        completed_day = api.get(workout_url(first.id)).json()
        assert completed_day["progress"]["percent"] == 100

    def test_completed_workout_cannot_be_completed_or_edited_again(self, setup):
        api, assignment = setup
        first = rows_of(assignment)[0]
        finish_all_exercises(api, first.id)
        api.post(f"{workout_url(first.id)}/complete")
        item = first.plan_workout.workout.items.first()

        again = api.post(f"{workout_url(first.id)}/complete")
        toggle = api.put(f"{workout_url(first.id)}/exercises/{item.id}", {"completed": False})

        assert again.status_code == 409
        assert again.json()["code"] == "workout_already_completed"
        assert toggle.status_code == 409

    def test_locked_workout_cannot_be_completed(self, setup):
        api, assignment = setup

        response = api.post(f"{workout_url(rows_of(assignment)[2].id)}/complete")

        assert response.status_code == 403

    def test_completing_every_workout_closes_the_cycle(self, setup):
        api, assignment = setup
        with freeze_time("2026-11-06 19:00:00"):
            for row in rows_of(assignment):
                finish_all_exercises(api, row.id)
                last = api.post(f"{workout_url(row.id)}/complete").json()

        assignment.refresh_from_db()
        assert last["cycle_completed"] is True
        assert last["cycle"] == 2
        assert last["plan_progress"] == 0
        assert last["next_workout_id"] == rows_of(assignment)[0].id
        assert assignment.cycle == 2
        assert assignment.progress == 0
        assert str(assignment.date_completed) == "2026-11-06"
        assert [row.status for row in rows_of(assignment)] == ["available", "locked", "locked"]
        assert not ExerciseCompletion.objects.filter(
            user_plan_workout__user_plan=assignment
        ).exists()
        # History is preserved across cycles.
        assert WorkoutSession.objects.filter(user=assignment.user, cycle=1).count() == 3
        first_again = api.get(workout_url(rows_of(assignment)[0].id)).json()
        assert first_again["progress"]["percent"] == 0

    def test_session_timestamp(self, setup):
        api, assignment = setup
        row = rows_of(assignment)[0]
        finish_all_exercises(api, row.id)

        with freeze_time("2026-11-02 18:30:00"):
            api.post(f"{workout_url(row.id)}/complete")

        session = WorkoutSession.objects.get(user=assignment.user)
        assert session.completed_at == datetime(2026, 11, 2, 18, 30, tzinfo=UTC)


class TestExerciseDetail:
    def test_exercise_of_available_workout(self, setup):
        api, assignment = setup
        exercise = rows_of(assignment)[0].plan_workout.workout.items.first().exercise
        exercise.steps.create(order=1, text="Paso")

        response = api.get(f"/api/v1/me/exercises/{exercise.id}")

        assert response.status_code == 200
        assert response.json()["name"] == exercise.name
        assert response.json()["steps"] == ["Paso"]

    def test_exercise_only_in_locked_workouts_is_forbidden(self, setup):
        """Regression #5: clients could open exercises of locked workouts."""
        api, assignment = setup
        exercise = rows_of(assignment)[2].plan_workout.workout.items.first().exercise

        response = api.get(f"/api/v1/me/exercises/{exercise.id}")

        assert response.status_code == 403
        assert response.json()["code"] == "workout_locked"

    def test_exercise_outside_the_plan_is_not_found(self, setup):
        api, _ = setup
        other = plan_with_workouts(1).plan_workouts.first().workout.items.first().exercise

        assert api.get(f"/api/v1/me/exercises/{other.id}").status_code == 404


class TestAssignmentState:
    def test_replacing_keeps_one_current_assignment(self, onboarded_client):
        assign_plan(onboarded_client)
        from apps.assignments.services import assign_training_plan

        assign_training_plan(onboarded_client, plan_with_workouts(1), None, replace=True)

        assert UserTrainingPlan.objects.filter(user=onboarded_client, is_current=True).count() == 1
        assert UserTrainingPlan.objects.filter(user=onboarded_client).count() == 2
