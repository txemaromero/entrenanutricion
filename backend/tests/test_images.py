"""Uploaded images are re-encoded: WebP, bounded size and no metadata (phase 11)."""

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from PIL.JpegImagePlugin import JpegImageFile

from apps.core.images import MEDIA_MAX_PX, PHOTO_MAX_PX, optimize_image
from apps.training.models import ExerciseMedia
from tests.factories import ExerciseFactory, mp4_upload

pytestmark = pytest.mark.django_db

GPS_IFD = 0x8825
ORIENTATION = 0x0112
MAKE = 0x010F


def jpeg_upload(size=(3000, 2000), orientation=None, name="phone.jpg") -> SimpleUploadedFile:
    image = Image.new("RGB", size, (200, 60, 60))
    exif = Image.Exif()
    exif[MAKE] = "PhoneMaker"
    exif.get_ifd(GPS_IFD)[2] = (41.0, 23.0, 0.0)  # latitude
    if orientation:
        exif[ORIENTATION] = orientation
    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


def opened(content) -> Image.Image:
    return Image.open(BytesIO(content.read() if hasattr(content, "read") else content))


class TestOptimizeImage:
    def test_webp_within_the_size_and_without_metadata(self):
        upload = jpeg_upload()
        assert opened(upload).getexif()[MAKE] == "PhoneMaker"

        result = optimize_image(upload, MEDIA_MAX_PX)

        image = opened(result)
        assert result.name == "phone.webp"
        assert image.format == "WEBP"
        assert max(image.size) == MEDIA_MAX_PX
        assert image.size == (1600, 1067)
        assert len(image.getexif()) == 0
        assert "exif" not in image.info

    def test_the_photo_orientation_is_applied(self):
        result = optimize_image(jpeg_upload(size=(300, 100), orientation=6), MEDIA_MAX_PX)

        assert opened(result).size == (100, 300)

    def test_small_images_are_not_enlarged(self):
        result = optimize_image(jpeg_upload(size=(200, 120)), PHOTO_MAX_PX)

        assert opened(result).size == (200, 120)

    def test_transparency_is_kept(self):
        buffer = BytesIO()
        Image.new("RGBA", (64, 64), (0, 0, 0, 0)).save(buffer, format="PNG")
        upload = SimpleUploadedFile("logo.png", buffer.getvalue(), content_type="image/png")

        image = opened(optimize_image(upload, PHOTO_MAX_PX))

        assert image.mode == "RGBA"
        assert image.getpixel((0, 0))[3] == 0

    def test_big_jpegs_are_decoded_at_a_reduced_scale(self, monkeypatch):
        decoded = []
        load = JpegImageFile.load

        def spy(image):
            decoded.append(image.size)
            return load(image)

        monkeypatch.setattr(JpegImageFile, "load", spy)

        result = optimize_image(jpeg_upload(size=(4000, 3000)), PHOTO_MAX_PX)

        assert opened(result).size == (512, 384)
        # 1/4 of the photo (0.75 MP) is decoded, not its 12 MP.
        assert decoded and set(decoded) == {(1000, 750)}


class TestUploads:
    def test_profile_photos_are_small_webp_files(self, auth_api, client_user):
        response = auth_api(client_user).put(
            "/api/v1/me/photo", {"photo": jpeg_upload()}, format="multipart"
        )

        assert response.status_code == 200
        client_user.refresh_from_db()
        assert client_user.profile_photo.name.endswith(".webp")
        with client_user.profile_photo.open("rb") as stored:
            image = Image.open(stored)
            assert max(image.size) == PHOTO_MAX_PX
            assert len(image.getexif()) == 0

    def test_exercise_images_are_optimized_and_videos_kept(self, auth_api, trainer):
        exercise = ExerciseFactory()
        api = auth_api(trainer)

        api.post(
            f"/api/v1/exercises/{exercise.id}/media", {"file": jpeg_upload()}, format="multipart"
        )
        api.post(
            f"/api/v1/exercises/{exercise.id}/media", {"file": mp4_upload()}, format="multipart"
        )

        image, video = ExerciseMedia.objects.filter(exercise=exercise).order_by("id")
        assert image.file.name.endswith(".webp")
        assert video.file.name.endswith(".mp4")
        with image.file.open("rb") as stored:
            assert max(Image.open(stored).size) == MEDIA_MAX_PX

    def test_workout_cover_images_are_optimized(self, auth_api, trainer):
        from tests.factories import workout_with_exercises

        workout = workout_with_exercises(1)

        response = auth_api(trainer).put(
            f"/api/v1/workouts/{workout.id}/media", {"media": jpeg_upload()}, format="multipart"
        )

        assert response.status_code in (200, 204)
        workout.refresh_from_db()
        assert workout.media.name.endswith(".webp")
