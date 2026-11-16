import pytest
from django.core.files.storage import default_storage

from apps.training.models import Exercise, ExerciseMedia, MuscleGroup
from apps.training.services import MAX_EXERCISE_MEDIA
from tests.factories import (
    ExerciseFactory,
    WorkoutExerciseFactory,
    image_upload,
    mp4_upload,
)

URL = "/api/v1/exercises"

pytestmark = pytest.mark.django_db


def payload(**overrides):
    groups = list(
        MuscleGroup.objects.filter(slug__in=["chest", "triceps"]).values_list("id", flat=True)
    )
    data = {
        "name": "Press de banca",
        "description": "Empuje horizontal",
        "technique": "Escápulas retraídas",
        "common_mistakes": "Rebotar la barra",
        "benefits": "Fuerza de pecho",
        "muscle_group_ids": groups,
        "steps": ["Túmbate en el banco", "Baja la barra", "Empuja"],
    }
    data.update(overrides)
    return data


class TestMuscleGroups:
    def test_staff_lists_seeded_groups(self, auth_api, trainer):
        response = auth_api(trainer).get("/api/v1/muscle-groups")

        assert response.status_code == 200
        slugs = {group["slug"] for group in response.json()}
        assert len(slugs) == 13
        assert {"biceps", "lats", "lower_back", "forearms"} <= slugs

    def test_clients_cannot_list(self, auth_api, client_user):
        assert auth_api(client_user).get("/api/v1/muscle-groups").status_code == 403


class TestExerciseCrud:
    def test_create_with_steps_and_muscle_groups(self, auth_api, trainer):
        response = auth_api(trainer).post(URL, payload())

        assert response.status_code == 201
        body = response.json()
        assert body["steps"] == ["Túmbate en el banco", "Baja la barra", "Empuja"]
        assert {group["slug"] for group in body["muscle_groups"]} == {"chest", "triceps"}
        assert body["is_active"] is True
        exercise = Exercise.objects.get(pk=body["id"])
        assert [step.order for step in exercise.steps.all()] == [1, 2, 3]

    def test_name_is_required(self, auth_api, trainer):
        response = auth_api(trainer).post(URL, payload(name=""))

        assert response.status_code == 400
        assert response.json()["field_codes"]["name"] == ["blank"]

    def test_retrieve(self, auth_api, nutritionist):
        exercise = ExerciseFactory(name="Sentadilla")

        response = auth_api(nutritionist).get(f"{URL}/{exercise.id}")

        assert response.status_code == 200
        assert response.json()["name"] == "Sentadilla"

    def test_update_replaces_steps_and_groups(self, auth_api, trainer):
        api = auth_api(trainer)
        exercise_id = api.post(URL, payload()).json()["id"]
        biceps = MuscleGroup.objects.get(slug="biceps")

        response = api.put(
            f"{URL}/{exercise_id}",
            payload(name="Curl", steps=["Sube", "Baja"], muscle_group_ids=[biceps.id]),
        )

        body = response.json()
        assert response.status_code == 200
        assert body["name"] == "Curl"
        assert body["steps"] == ["Sube", "Baja"]
        assert [group["slug"] for group in body["muscle_groups"]] == ["biceps"]

    def test_partial_update_keeps_steps(self, auth_api, trainer):
        api = auth_api(trainer)
        exercise_id = api.post(URL, payload()).json()["id"]

        response = api.patch(f"{URL}/{exercise_id}", {"benefits": "Más fuerza"})

        assert response.json()["benefits"] == "Más fuerza"
        assert len(response.json()["steps"]) == 3

    def test_list_search_and_filter(self, auth_api, trainer):
        api = auth_api(trainer)
        api.post(URL, payload(name="Press de banca"))
        api.post(URL, payload(name="Remo con barra", muscle_group_ids=[]))

        by_search = api.get(URL, {"search": "remo"}).json()
        by_group = api.get(URL, {"muscle_group": "chest"}).json()

        assert [item["name"] for item in by_search["results"]] == ["Remo con barra"]
        assert [item["name"] for item in by_group["results"]] == ["Press de banca"]
        assert by_group["count"] == 1

    def test_list_is_paginated_with_limit_offset(self, auth_api, trainer):
        ExerciseFactory.create_batch(5)

        body = auth_api(trainer).get(URL, {"limit": 2, "offset": 1}).json()

        assert body["count"] == 5
        assert len(body["results"]) == 2
        assert body["next"] and body["previous"]

    def test_list_avoids_n_plus_one(self, auth_api, trainer, django_assert_max_num_queries):
        for exercise in ExerciseFactory.create_batch(10):
            exercise.muscle_groups.set(MuscleGroup.objects.all()[:2])
        api = auth_api(trainer)

        with django_assert_max_num_queries(5):
            api.get(URL)


class TestExerciseDelete:
    def test_unused_exercise_is_deleted(self, auth_api, trainer):
        exercise = ExerciseFactory()

        response = auth_api(trainer).delete(f"{URL}/{exercise.id}")

        assert response.status_code == 204
        assert not Exercise.objects.filter(pk=exercise.id).exists()

    def test_exercise_in_use_is_deactivated(self, auth_api, trainer):
        item = WorkoutExerciseFactory()
        api = auth_api(trainer)

        response = api.delete(f"{URL}/{item.exercise_id}")

        assert response.status_code == 204
        item.exercise.refresh_from_db()
        assert item.exercise.is_active is False
        assert api.get(URL).json()["count"] == 0
        assert api.get(URL, {"include_inactive": "true"}).json()["count"] == 1
        assert api.get(f"{URL}/{item.exercise_id}").status_code == 200


class TestExerciseMedia:
    def test_add_image_and_video(self, auth_api, trainer):
        exercise = ExerciseFactory()
        api = auth_api(trainer)

        image = api.post(
            f"{URL}/{exercise.id}/media",
            {"file": image_upload(), "caption": "Inicio"},
            format="multipart",
        )
        video = api.post(f"{URL}/{exercise.id}/media", {"file": mp4_upload()}, format="multipart")

        assert image.status_code == 201
        assert image.json()["kind"] == "image"
        assert image.json()["caption"] == "Inicio"
        assert video.json()["kind"] == "video"
        assert video.json()["order"] == 2
        detail = api.get(f"{URL}/{exercise.id}").json()
        assert [media["kind"] for media in detail["media"]] == ["image", "video"]
        listed = api.get(URL).json()["results"][0]
        assert listed["thumbnail_url"] == image.json()["url"]

    def test_rejects_unsupported_files(self, auth_api, trainer):
        exercise = ExerciseFactory()

        response = auth_api(trainer).post(
            f"{URL}/{exercise.id}/media", {"file": mp4_upload(valid=False)}, format="multipart"
        )

        assert response.status_code == 400
        assert response.json()["field_codes"]["file"] == ["invalid_file_type"]

    def test_limits_the_number_of_files(self, auth_api, trainer):
        exercise = ExerciseFactory()
        for position in range(MAX_EXERCISE_MEDIA):
            ExerciseMedia.objects.create(exercise=exercise, file=image_upload(), order=position)

        response = auth_api(trainer).post(
            f"{URL}/{exercise.id}/media", {"file": image_upload()}, format="multipart"
        )

        assert response.status_code == 400
        assert response.json()["code"] == "too_many_media"

    @pytest.mark.django_db(transaction=True)
    def test_two_uploads_at_once_respect_the_limit(self, auth_api):
        from tests.concurrency import while_locked
        from tests.factories import TrainerFactory

        exercise = ExerciseFactory()
        for position in range(MAX_EXERCISE_MEDIA - 1):
            ExerciseMedia.objects.create(exercise=exercise, file=image_upload(), order=position)
        trainer = TrainerFactory()
        first_api, second_api = auth_api(trainer), auth_api(trainer)
        url = f"{URL}/{exercise.id}/media"

        first, second = while_locked(
            Exercise,
            exercise.pk,
            first=lambda: first_api.post(url, {"file": image_upload()}, format="multipart"),
            second=lambda: second_api.post(url, {"file": image_upload()}, format="multipart"),
        )

        assert first.status_code == 201
        assert second.status_code == 400
        assert second.json()["code"] == "too_many_media"
        assert exercise.media.count() == MAX_EXERCISE_MEDIA

    def test_delete_media_removes_the_file(
        self, auth_api, trainer, django_capture_on_commit_callbacks
    ):
        exercise = ExerciseFactory()
        media = ExerciseMedia.objects.create(exercise=exercise, file=image_upload())
        name = media.file.name

        with django_capture_on_commit_callbacks(execute=True):
            response = auth_api(trainer).delete(f"{URL}/{exercise.id}/media/{media.id}")

        assert response.status_code == 204
        assert not default_storage.exists(name)

    def test_deleting_an_exercise_removes_its_files(
        self, auth_api, trainer, django_capture_on_commit_callbacks
    ):
        exercise = ExerciseFactory()
        media = ExerciseMedia.objects.create(exercise=exercise, file=image_upload())

        with django_capture_on_commit_callbacks(execute=True):
            auth_api(trainer).delete(f"{URL}/{exercise.id}")

        assert not default_storage.exists(media.file.name)


class TestExercisePermissions:
    @pytest.mark.parametrize("role", ["trainer", "admin_user"])
    def test_trainer_and_admin_can_write(self, request, auth_api, role):
        user = request.getfixturevalue(role)

        assert auth_api(user).post(URL, payload()).status_code == 201

    def test_nutritionist_reads_but_cannot_write(self, auth_api, nutritionist):
        exercise = ExerciseFactory()
        api = auth_api(nutritionist)

        assert api.get(URL).status_code == 200
        assert api.post(URL, payload()).status_code == 403
        assert api.delete(f"{URL}/{exercise.id}").status_code == 403

    def test_clients_cannot_access_the_catalog(self, auth_api, client_user):
        assert auth_api(client_user).get(URL).status_code == 403

    def test_anonymous_gets_401(self, api_client):
        assert api_client.get(URL).status_code == 401
