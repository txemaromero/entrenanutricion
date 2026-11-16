from decimal import Decimal

import pytest
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.utils import timezone
from freezegun import freeze_time

from apps.accounts import login_attempts
from apps.accounts.tokens import issue_tokens
from apps.progress.models import WeightRecord
from tests.factories import DEFAULT_PASSWORD, image_upload, refresh_with

ME = "/api/v1/me"
PROFILE = "/api/v1/me/profile"
PASSWORD = "/api/v1/me/password"
PHOTO = "/api/v1/me/photo"

pytestmark = pytest.mark.django_db


class TestMe:
    def test_pending_client_profile(self, auth_api, client_user):
        response = auth_api(client_user).get(ME)

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == client_user.email
        assert body["role"] == "client"
        assert body["status"] == "pending_onboarding"
        assert body["details"] is None
        assert body["has_training_plan"] is False
        assert body["has_nutrition_plan"] is False
        assert body["profile_photo_url"] is None

    @freeze_time("2026-05-17")
    def test_onboarded_client_profile_includes_weights_and_age(self, auth_api, onboarded_client):
        WeightRecord.objects.create(
            user=onboarded_client, weight_kg=Decimal("78.5"), date=timezone.localdate()
        )

        body = auth_api(onboarded_client).get(ME).json()

        assert body["age"] == 36
        assert body["onboarding_completed"] is True
        assert body["details"]["initial_weight_kg"] == 80.0
        assert body["details"]["current_weight_kg"] == 78.5
        assert body["details"]["target_weight_kg"] == 75.0
        assert body["details"]["goal"] == "lose_weight"

    def test_staff_profile(self, auth_api, trainer):
        body = auth_api(trainer).get(ME).json()

        assert body["role"] == "trainer"
        assert body["status"] == "active"
        assert body["details"] is None


class TestProfileUpdate:
    def test_updates_names(self, auth_api, client_user):
        response = auth_api(client_user).patch(
            PROFILE, {"first_name": "Lucía", "last_name": "Ferrer"}
        )

        assert response.status_code == 200
        assert response.json()["full_name"] == "Lucía Ferrer"
        client_user.refresh_from_db()
        assert client_user.first_name == "Lucía"

    def test_rejects_invalid_name(self, auth_api, client_user):
        response = auth_api(client_user).patch(PROFILE, {"first_name": "L4ura"})

        assert response.status_code == 400
        assert response.json()["field_codes"]["first_name"] == ["invalid_name"]

    def test_current_weight_creates_a_weight_record(self, auth_api, onboarded_client):
        api = auth_api(onboarded_client)

        response = api.patch(PROFILE, {"current_weight_kg": 77.3})

        assert response.status_code == 200
        assert response.json()["details"]["current_weight_kg"] == 77.3
        assert WeightRecord.objects.filter(user=onboarded_client).count() == 2

    def test_second_weight_update_on_the_same_day_overwrites(self, auth_api, onboarded_client):
        api = auth_api(onboarded_client)

        api.patch(PROFILE, {"current_weight_kg": 77.3})
        api.patch(PROFILE, {"current_weight_kg": 76.9})

        today = WeightRecord.objects.get(user=onboarded_client, date=timezone.localdate())
        assert today.weight_kg == Decimal("76.9")

    def test_updates_sport_information(self, auth_api, onboarded_client):
        response = auth_api(onboarded_client).patch(
            PROFILE,
            {
                "goal": "gain_muscle",
                "physical_activity_level": "intense",
                "weekly_training_days": 5,
            },
        )

        details = response.json()["details"]
        assert details["goal"] == "gain_muscle"
        assert details["physical_activity_level"] == "intense"
        assert details["weekly_training_days"] == 5
        assert details["target_weight_kg"] == 85.0

    def test_sport_information_requires_onboarding(self, auth_api, trainer):
        response = auth_api(trainer).patch(PROFILE, {"goal": "maintain"})

        assert response.status_code == 409
        assert response.json()["code"] == "onboarding_not_completed"

    @pytest.mark.parametrize(
        ("payload", "field"),
        [
            ({"weekly_training_days": 0}, "weekly_training_days"),
            ({"weekly_training_days": 7}, "weekly_training_days"),
            ({"current_weight_kg": 29.9}, "current_weight_kg"),
            ({"current_weight_kg": 300.1}, "current_weight_kg"),
            ({"goal": "be_happy"}, "goal"),
        ],
    )
    def test_validates_ranges(self, auth_api, onboarded_client, payload, field):
        response = auth_api(onboarded_client).patch(PROFILE, payload)

        assert response.status_code == 400
        assert field in response.json()["fields"]


class TestPasswordChange:
    def payload(self, **overrides):
        data = {
            "current_password": DEFAULT_PASSWORD,
            "new_password": "N3w#Password",
            "confirm_password": "N3w#Password",
        }
        data.update(overrides)
        return data

    @pytest.mark.parametrize("remember", [False, True])
    def test_changes_password_and_returns_new_tokens(self, api_client, client_user, remember):
        login = api_client.post(
            "/api/v1/auth/login",
            {"email": client_user.email, "password": DEFAULT_PASSWORD, "remember_me": remember},
        )
        old_refresh = login.cookies["entrenanutricion_refresh"].value
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")

        response = api_client.put(PASSWORD, self.payload())

        assert response.status_code == 200
        assert response.json().keys() == {"access"}
        new_cookie = response.cookies["entrenanutricion_refresh"]
        # The session keeps its "remember me" choice.
        assert new_cookie["max-age"] == (7 * 24 * 3600 if remember else "")
        client_user.refresh_from_db()
        assert client_user.check_password("N3w#Password")
        # Every previous session is logged out; the new cookie works.
        assert refresh_with(api_client, old_refresh).status_code == 401
        assert refresh_with(api_client, new_cookie.value).status_code == 200

    def test_access_tokens_issued_before_the_change_stop_working(self, api_client, client_user):
        with freeze_time("2026-11-06 10:00:00"):
            old_access = issue_tokens(client_user)["access"]
        with freeze_time("2026-11-06 10:05:00"):
            api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {old_access}")
            new_access = api_client.put(PASSWORD, self.payload()).json()["access"]

            old = api_client.get(ME)
            api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access}")
            new = api_client.get(ME)

        assert old.status_code == 401
        assert old.json()["code"] == "token_not_valid"
        assert new.status_code == 200

    def test_changing_it_lifts_the_pause_on_the_account(self, auth_api, api_client, client_user):
        login_attempts.record_failure(client_user.email, "10.0.0.9")
        key = login_attempts._key(client_user.email)
        assert cache.get(key)

        assert auth_api(client_user).put(PASSWORD, self.payload()).status_code == 200

        assert cache.get(key) is None

    def test_rejects_wrong_current_password(self, auth_api, client_user):
        response = auth_api(client_user).put(PASSWORD, self.payload(current_password="Wrong#Pass1"))

        assert response.status_code == 400
        assert response.json()["field_codes"]["current_password"] == ["current_password_incorrect"]

    def test_rejects_mismatched_confirmation(self, auth_api, client_user):
        response = auth_api(client_user).put(PASSWORD, self.payload(confirm_password="Other#Pass1"))

        assert response.status_code == 400
        assert response.json()["field_codes"]["confirm_password"] == ["passwords_do_not_match"]

    def test_rejects_weak_new_password(self, auth_api, client_user):
        response = auth_api(client_user).put(
            PASSWORD, self.payload(new_password="weakpass", confirm_password="weakpass")
        )

        assert response.status_code == 400
        assert "password_no_upper" in response.json()["field_codes"]["new_password"]


class TestProfilePhoto:
    def test_uploads_photo_with_uuid_name(self, auth_api, client_user):
        response = auth_api(client_user).put(
            PHOTO, {"photo": image_upload("my face.png")}, format="multipart"
        )

        assert response.status_code == 200
        url = response.json()["profile_photo_url"]
        assert url.startswith("http://testserver/media/profile_photos/")
        assert "my face" not in url
        client_user.refresh_from_db()
        assert default_storage.exists(client_user.profile_photo.name)

    def test_replacing_photo_deletes_previous_file(
        self, auth_api, client_user, django_capture_on_commit_callbacks
    ):
        api = auth_api(client_user)
        api.put(PHOTO, {"photo": image_upload("first.jpg", "JPEG")}, format="multipart")
        client_user.refresh_from_db()
        first = client_user.profile_photo.name

        with django_capture_on_commit_callbacks(execute=True):
            api.put(PHOTO, {"photo": image_upload("second.webp", "WEBP")}, format="multipart")

        client_user.refresh_from_db()
        assert not default_storage.exists(first)
        assert default_storage.exists(client_user.profile_photo.name)

    def test_delete_photo(self, auth_api, client_user, django_capture_on_commit_callbacks):
        api = auth_api(client_user)
        api.put(PHOTO, {"photo": image_upload()}, format="multipart")
        client_user.refresh_from_db()
        name = client_user.profile_photo.name

        with django_capture_on_commit_callbacks(execute=True):
            response = api.delete(PHOTO)

        assert response.json()["profile_photo_url"] is None
        assert not default_storage.exists(name)

    @pytest.mark.parametrize(
        "upload",
        [
            pytest.param(lambda: image_upload("photo.gif"), id="wrong-extension"),
            pytest.param(lambda: image_upload("photo.png", "GIF"), id="gif-content-as-png"),
        ],
    )
    def test_rejects_invalid_types(self, auth_api, client_user, upload):
        response = auth_api(client_user).put(PHOTO, {"photo": upload()}, format="multipart")

        assert response.status_code == 400
        assert response.json()["field_codes"]["photo"] == ["invalid_file_type"]

    def test_rejects_text_disguised_as_image(self, auth_api, client_user):
        from django.core.files.uploadedfile import SimpleUploadedFile

        fake = SimpleUploadedFile("photo.png", b"<?php echo 1; ?>", content_type="image/png")

        response = auth_api(client_user).put(PHOTO, {"photo": fake}, format="multipart")

        assert response.status_code == 400
        assert response.json()["field_codes"]["photo"] == ["invalid_file_type"]

    def test_rejects_images_over_5_mb(self, auth_api, client_user, settings):
        settings.MAX_IMAGE_UPLOAD_BYTES = 10

        response = auth_api(client_user).put(PHOTO, {"photo": image_upload()}, format="multipart")

        assert response.status_code == 400
        assert response.json()["field_codes"]["photo"] == ["file_too_large"]
