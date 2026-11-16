import pytest
from django.core.files.storage import default_storage

from apps.training.models import TrainingPlanWorkout, Workout, WorkoutExercise
from apps.training.services import estimate_duration_minutes, workout_summary
from tests.factories import (
    ExerciseFactory,
    TrainingPlanFactory,
    WorkoutFactory,
    image_upload,
    mp4_upload,
    workout_with_exercises,
)

URL = "/api/v1/workouts"

pytestmark = pytest.mark.django_db


def payload(exercises, **overrides):
    data = {
        "name": "Piernas",
        "description": "Tren inferior",
        "exercises": [
            {"exercise_id": exercise.id, "sets": 4, "reps": 8, "rest_seconds": 90}
            for exercise in exercises
        ],
    }
    data.update(overrides)
    return data


class TestDuration:
    def test_estimate_formula(self):
        items = [
            WorkoutExercise(sets=3, reps=10, rest_seconds=60),  # 3 × (30 + 60) = 270 s
            WorkoutExercise(sets=4, reps=8, rest_seconds=90),  # 4 × (24 + 90) = 456 s
        ]

        assert estimate_duration_minutes(items) == 12  # 726 s ≈ 12.1 min
        assert estimate_duration_minutes([]) == 0

    def test_declared_duration_wins(self):
        workout = Workout(name="x", duration_minutes=50)
        items = [WorkoutExercise(sets=3, reps=10, rest_seconds=60)]

        summary = workout_summary(workout, items)

        assert summary == {
            "estimated_duration_minutes": 50,
            "total_sets": 3,
            "total_reps": 30,
            "exercise_count": 1,
        }


class TestWorkoutCrud:
    def test_create_with_ordered_exercises(self, auth_api, trainer):
        squat, lunge = ExerciseFactory(name="Sentadilla"), ExerciseFactory(name="Zancada")

        response = auth_api(trainer).post(URL, payload([squat, lunge]))

        assert response.status_code == 201
        body = response.json()
        assert [item["exercise"]["name"] for item in body["exercises"]] == ["Sentadilla", "Zancada"]
        assert [item["order"] for item in body["exercises"]] == [1, 2]
        assert body["total_sets"] == 8
        assert body["total_reps"] == 64
        assert body["exercise_count"] == 2
        assert body["estimated_duration_minutes"] == 15  # 2 × 4 × (24 + 90) = 912 s
        assert body["media_url"] is None

    def test_description_is_optional(self, auth_api, trainer):
        data = payload([ExerciseFactory()])
        del data["description"]

        assert auth_api(trainer).post(URL, data).status_code == 201

    @pytest.mark.parametrize(
        ("row", "field", "code"),
        [
            ({"sets": 0}, "sets", "min_value"),
            ({"sets": 21}, "sets", "max_value"),
            ({"reps": 0}, "reps", "min_value"),
            ({"reps": 101}, "reps", "max_value"),
            ({"rest_seconds": -1}, "rest_seconds", "min_value"),
            ({"rest_seconds": 601}, "rest_seconds", "max_value"),
            ({"exercise_id": 999999}, "exercise_id", "does_not_exist"),
        ],
    )
    def test_validates_exercise_rows(self, auth_api, trainer, row, field, code):
        data = payload([ExerciseFactory()])
        data["exercises"][0].update(row)

        response = auth_api(trainer).post(URL, data)

        assert response.status_code == 400
        assert response.json()["field_codes"][f"exercises.0.{field}"] == [code]

    def test_requires_at_least_one_exercise(self, auth_api, trainer):
        response = auth_api(trainer).post(URL, payload([]))

        assert response.json()["field_codes"]["exercises"] == ["exercises_required"]

    def test_rejects_inactive_exercises(self, auth_api, trainer):
        response = auth_api(trainer).post(URL, payload([ExerciseFactory(is_active=False)]))

        assert response.json()["field_codes"]["exercises.0.exercise_id"] == ["exercise_inactive"]

    def test_update_diffs_rows_by_id(self, auth_api, trainer):
        api = auth_api(trainer)
        first, second, third = ExerciseFactory.create_batch(3)
        created = api.post(URL, payload([first, second])).json()
        kept_id = created["exercises"][1]["id"]

        response = api.put(
            f"{URL}/{created['id']}",
            {
                "name": "Piernas v2",
                "exercises": [
                    {
                        "id": kept_id,
                        "exercise_id": second.id,
                        "sets": 5,
                        "reps": 5,
                        "rest_seconds": 120,
                    },
                    {"exercise_id": third.id, "sets": 3, "reps": 12, "rest_seconds": 45},
                ],
            },
        )

        body = response.json()
        assert response.status_code == 200
        assert body["exercises"][0]["id"] == kept_id
        assert body["exercises"][0]["sets"] == 5
        assert body["exercises"][0]["order"] == 1
        assert body["exercises"][1]["exercise"]["id"] == third.id
        assert WorkoutExercise.objects.filter(workout_id=created["id"]).count() == 2

    def test_update_rejects_rows_of_other_workouts(self, auth_api, trainer):
        foreign = workout_with_exercises(1).items.first()
        workout = workout_with_exercises(1)
        data = payload([ExerciseFactory()])
        data["exercises"][0]["id"] = foreign.id

        response = auth_api(trainer).put(f"{URL}/{workout.id}", data)

        assert response.json()["field_codes"]["exercises.0.id"] == ["invalid_item"]

    def test_inactive_exercise_already_in_workout_can_stay(self, auth_api, trainer):
        workout = workout_with_exercises(1)
        item = workout.items.first()
        item.exercise.is_active = False
        item.exercise.save()

        response = auth_api(trainer).patch(
            f"{URL}/{workout.id}",
            {
                "exercises": [
                    {
                        "id": item.id,
                        "exercise_id": item.exercise_id,
                        "sets": 2,
                        "reps": 5,
                        "rest_seconds": 30,
                    }
                ]
            },
        )

        assert response.status_code == 200

    def test_patch_without_exercises_keeps_them(self, auth_api, trainer):
        workout = workout_with_exercises(3)

        response = auth_api(trainer).patch(f"{URL}/{workout.id}", {"duration_minutes": 40})

        assert response.json()["exercise_count"] == 3
        assert response.json()["estimated_duration_minutes"] == 40

    def test_list_and_search(self, auth_api, nutritionist, django_assert_max_num_queries):
        for name in ["Core", "Espalda y bíceps", "Pecho y tríceps"]:
            workout_with_exercises(2, name=name)
        api = auth_api(nutritionist)

        with django_assert_max_num_queries(5):
            listed = api.get(URL).json()
        searched = api.get(URL, {"search": "bíceps"}).json()

        assert [item["name"] for item in listed["results"]] == [
            "Core",
            "Espalda y bíceps",
            "Pecho y tríceps",
        ]
        assert listed["results"][0]["exercise_count"] == 2
        assert [item["name"] for item in searched["results"]] == ["Espalda y bíceps"]


class TestWorkoutDelete:
    def test_unused_workout_is_deleted(self, auth_api, trainer):
        workout = workout_with_exercises(2)

        response = auth_api(trainer).delete(f"{URL}/{workout.id}")

        assert response.status_code == 204
        assert not Workout.objects.filter(pk=workout.id).exists()

    def test_workout_in_a_plan_cannot_be_deleted(self, auth_api, trainer):
        workout = workout_with_exercises(1)
        plan = TrainingPlanFactory(name="Fuerza 3 días")
        TrainingPlanWorkout.objects.create(plan=plan, workout=workout, order=1)

        response = auth_api(trainer).delete(f"{URL}/{workout.id}")

        assert response.status_code == 409
        body = response.json()
        assert body["code"] == "workout_in_use"
        assert body["plans"] == [{"id": plan.id, "name": "Fuerza 3 días"}]
        assert Workout.objects.filter(pk=workout.id).exists()


class TestWorkoutMedia:
    def test_upload_replace_and_delete(self, auth_api, trainer, django_capture_on_commit_callbacks):
        workout = WorkoutFactory()
        api = auth_api(trainer)

        image = api.put(f"{URL}/{workout.id}/media", {"media": image_upload()}, format="multipart")
        workout.refresh_from_db()
        first = workout.media.name
        with django_capture_on_commit_callbacks(execute=True):
            video = api.put(
                f"{URL}/{workout.id}/media", {"media": mp4_upload()}, format="multipart"
            )
        with django_capture_on_commit_callbacks(execute=True):
            removed = api.delete(f"{URL}/{workout.id}/media")

        assert image.json()["media_kind"] == "image"
        assert video.json()["media_kind"] == "video"
        assert not default_storage.exists(first)
        assert removed.json()["media_url"] is None

    def test_rejects_invalid_media(self, auth_api, trainer):
        workout = WorkoutFactory()

        response = auth_api(trainer).put(
            f"{URL}/{workout.id}/media", {"media": image_upload("x.bmp")}, format="multipart"
        )

        assert response.status_code == 400

    def test_nutritionist_cannot_change_media(self, auth_api, nutritionist):
        workout = WorkoutFactory()

        response = auth_api(nutritionist).delete(f"{URL}/{workout.id}/media")

        assert response.status_code == 403
