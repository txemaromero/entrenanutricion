"""Upload limits (phase 15): decoded pixels, body size and rate of the requests with files."""

from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.core.files import validate_image_file
from apps.core.images import PHOTO_MAX_PX, optimize_image
from apps.core.throttling import UploadRateThrottle
from tests.factories import UserFactory, image_upload

PHOTO = "/api/v1/me/photo"
HEALTH = "/api/v1/health"


def bomb(size, name="bomb.png") -> SimpleUploadedFile:
    """A plain 1-bit PNG: a few kB on disk, `width × height` pixels once decoded."""
    buffer = BytesIO()
    Image.new("1", size).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class TestPixels:
    @pytest.mark.parametrize(
        "size",
        [
            (8_000, 6_000),  # above our limit, below Pillow's
            (10_000, 10_000),  # Pillow only warns
            (15_000, 15_000),  # Pillow refuses it
        ],
    )
    def test_decompression_bombs_are_refused(self, size):
        upload = bomb(size)
        assert upload.size < 1024 * 1024  # far below the 5 MB limit

        with pytest.raises(ValidationError) as error:
            validate_image_file(upload)

        assert error.value.code == "image_too_large"

    def test_the_limit_is_a_setting(self, settings):
        settings.MAX_IMAGE_PIXELS = 100

        with pytest.raises(ValidationError) as error:
            validate_image_file(image_upload(size=(16, 16)))

        assert error.value.code == "image_too_large"

    def test_the_re_encoding_checks_it_too(self, settings):
        settings.MAX_IMAGE_PIXELS = 100

        with pytest.raises(ValidationError) as error:
            optimize_image(image_upload(size=(16, 16)), PHOTO_MAX_PX)

        assert error.value.code == "image_too_large"

    @pytest.mark.django_db
    def test_the_api_answers_with_the_field_code(self, auth_api, client_user):
        response = auth_api(client_user).put(
            PHOTO, {"photo": bomb((10_000, 10_000))}, format="multipart"
        )

        assert response.status_code == 400
        assert response.json()["field_codes"]["photo"] == ["image_too_large"]


@pytest.mark.django_db
class TestRequestSize:
    def test_bodies_bigger_than_any_upload_are_refused_unread(self, client, settings):
        response = client.put(
            PHOTO,
            data=b"",
            content_type="multipart/form-data; boundary=x",
            CONTENT_LENGTH=str(settings.MAX_REQUEST_BODY_BYTES + 1),
        )

        assert response.status_code == 413
        assert response.json()["code"] == "request_too_large"

    def test_up_to_the_limit_the_request_goes_on(self, client, settings):
        response = client.get(HEALTH, CONTENT_LENGTH=str(settings.MAX_REQUEST_BODY_BYTES))

        assert response.status_code == 200


@pytest.mark.django_db
class TestUploadRate:
    def test_requests_with_files_have_a_budget_per_user(self, auth_api, client_user, monkeypatch):
        monkeypatch.setattr(UploadRateThrottle, "THROTTLE_RATES", {"uploads": "2/min"})
        api = auth_api(client_user)
        for _ in range(2):
            assert api.put(PHOTO, {"photo": image_upload()}, format="multipart").status_code == 200

        response = api.put(PHOTO, {"photo": image_upload()}, format="multipart")

        assert response.status_code == 429
        assert response.json()["code"] == "throttled"
        # Requests without files are not counted, and each user has their own budget.
        assert api.get("/api/v1/me").status_code == 200
        assert api.delete(PHOTO).status_code == 200
        other = auth_api(UserFactory())
        assert other.put(PHOTO, {"photo": image_upload()}, format="multipart").status_code == 200
