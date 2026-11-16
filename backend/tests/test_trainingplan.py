import pytest

from apps.training.models import TrainingPlan, UserPlanWorkout, UserWorkoutStatus
from tests.factories import (
    TrainingPlanFactory,
    WorkoutFactory,
    assign_plan,
    image_upload,
    plan_with_workouts,
    workout_with_exercises,
)

URL = "/api/v1/training-plans"

pytestmark = pytest.mark.django_db


def payload(workout_list, **overrides):
    data = {
        "name": "Fuerza 3 días",
        "description": "Plan de fuerza general",
        "goal": "gain_muscle",
        "difficulty": "intermediate",
        "equipment": "full_gym",
        "duration_weeks": 12,
        "workouts": [{"workout_id": workout.id} for workout in workout_list],
    }
    data.update(overrides)
    return data


class TestTrainingPlanCrud:
    def test_create_with_ordered_workouts(self, auth_api, trainer):
        core, legs = workout_with_exercises(2, name="Core"), workout_with_exercises(
            3, name="Piernas"
        )

        response = auth_api(trainer).post(URL, payload([legs, core, legs]))

        assert response.status_code == 201
        body = response.json()
        assert [row["workout"]["name"] for row in body["workouts"]] == [
            "Piernas",
            "Core",
            "Piernas",
        ]
        assert [row["order"] for row in body["workouts"]] == [1, 2, 3]
        assert body["workouts"][0]["workout"]["exercise_count"] == 3
        assert body["sessions_per_week"] == 3
        assert body["is_active"] is True

    @pytest.mark.parametrize(
        ("changes", "field", "code"),
        [
            ({"goal": "fly"}, "goal", "invalid_choice"),
            ({"difficulty": "legend"}, "difficulty", "invalid_choice"),
            ({"equipment": "spaceship"}, "equipment", "invalid_choice"),
            ({"duration_weeks": 0}, "duration_weeks", "min_value"),
            ({"duration_weeks": 53}, "duration_weeks", "max_value"),
            ({"workouts": []}, "workouts", "workouts_required"),
            ({"workouts": [{"workout_id": 999999}]}, "workouts.0.workout_id", "does_not_exist"),
        ],
    )
    def test_validation(self, auth_api, trainer, changes, field, code):
        response = auth_api(trainer).post(URL, payload([WorkoutFactory()], **changes))

        assert response.status_code == 400
        assert response.json()["field_codes"][field] == [code]

    def test_update_reorders_and_removes(self, auth_api, trainer):
        api = auth_api(trainer)
        a, b, c = (workout_with_exercises(1, name=name) for name in "ABC")
        created = api.post(URL, payload([a, b, c])).json()
        rows = {row["workout"]["name"]: row["id"] for row in created["workouts"]}

        response = api.patch(
            f"{URL}/{created['id']}",
            {
                "workouts": [
                    {"id": rows["C"], "workout_id": c.id},
                    {"id": rows["A"], "workout_id": a.id},
                ]
            },
        )

        assert [row["workout"]["name"] for row in response.json()["workouts"]] == ["C", "A"]

    def test_list_filters_and_hides_inactive(
        self, auth_api, admin_user, django_assert_max_num_queries
    ):
        plan_with_workouts(2, name="Perder grasa", goal="lose_weight", difficulty="beginner")
        plan_with_workouts(1, name="Hipertrofia", goal="gain_muscle", difficulty="advanced")
        TrainingPlanFactory(name="Antiguo", is_active=False)
        api = auth_api(admin_user)

        with django_assert_max_num_queries(4):
            listed = api.get(URL).json()
        by_goal = api.get(URL, {"goal": "gain_muscle"}).json()
        everything = api.get(URL, {"include_inactive": "1"}).json()

        assert [plan["name"] for plan in listed["results"]] == ["Hipertrofia", "Perder grasa"]
        assert listed["results"][1]["workout_count"] == 2
        assert [plan["name"] for plan in by_goal["results"]] == ["Hipertrofia"]
        assert everything["count"] == 3

    def test_detail_avoids_n_plus_one(self, auth_api, trainer, django_assert_max_num_queries):
        plan = plan_with_workouts(6, exercises=4)

        with django_assert_max_num_queries(6):
            response = auth_api(trainer).get(f"{URL}/{plan.id}")

        assert len(response.json()["workouts"]) == 6

    def test_media(self, auth_api, trainer):
        plan = plan_with_workouts(1)

        response = auth_api(trainer).put(
            f"{URL}/{plan.id}/media", {"media": image_upload()}, format="multipart"
        )

        assert response.status_code == 200
        assert response.json()["media_kind"] == "image"
        assert response.json()["workouts"][0]["workout"]["name"]


class TestTrainingPlanUpdatesAssignedUsers:
    def test_new_workouts_reach_assigned_clients_locked(self, auth_api, trainer, onboarded_client):
        plan = plan_with_workouts(2)
        assignment = assign_plan(onboarded_client, plan)
        rows = [{"id": row.id, "workout_id": row.workout_id} for row in plan.plan_workouts.all()]
        extra = workout_with_exercises(1)

        auth_api(trainer).patch(f"{URL}/{plan.id}", {"workouts": [*rows, {"workout_id": extra.id}]})

        statuses = list(
            UserPlanWorkout.objects.filter(user_plan=assignment)
            .order_by("plan_workout__order")
            .values_list("status", flat=True)
        )
        assert statuses == ["available", "locked", "locked"]

    def test_removing_the_available_workout_unlocks_the_next(
        self, auth_api, trainer, onboarded_client
    ):
        plan = plan_with_workouts(3)
        assignment = assign_plan(onboarded_client, plan)
        rows = list(plan.plan_workouts.all())

        auth_api(trainer).patch(
            f"{URL}/{plan.id}",
            {"workouts": [{"id": row.id, "workout_id": row.workout_id} for row in rows[1:]]},
        )

        first = UserPlanWorkout.objects.filter(user_plan=assignment).order_by(
            "plan_workout__order"
        )[0]
        assert first.plan_workout_id == rows[1].id
        assert first.status == UserWorkoutStatus.AVAILABLE


class TestTrainingPlanDelete:
    def test_unassigned_plan_is_deleted(self, auth_api, trainer):
        plan = plan_with_workouts(1)

        assert auth_api(trainer).delete(f"{URL}/{plan.id}").status_code == 204
        assert not TrainingPlan.objects.filter(pk=plan.id).exists()

    def test_assigned_plan_is_deactivated_and_kept_by_clients(
        self, auth_api, trainer, onboarded_client
    ):
        plan = plan_with_workouts(1)
        assign_plan(onboarded_client, plan)

        response = auth_api(trainer).delete(f"{URL}/{plan.id}")

        assert response.status_code == 204
        plan.refresh_from_db()
        assert plan.is_active is False
        assert auth_api(onboarded_client).get("/api/v1/me/training-plan").status_code == 200

    def test_nutritionist_cannot_delete(self, auth_api, nutritionist):
        plan = plan_with_workouts(1)

        assert auth_api(nutritionist).delete(f"{URL}/{plan.id}").status_code == 403
