import json
import logging
import sys
from datetime import date
from types import SimpleNamespace

import pytest
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.storage import default_storage
from django.http import Http404
from rest_framework import exceptions

from apps.accounts.models import Role
from apps.core import permissions
from apps.core.exceptions import ConflictError, api_exception_handler
from apps.core.files import (
    UUIDUploadTo,
    media_kind,
    validate_image_file,
    validate_media_file,
    validate_video_file,
)
from apps.core.logging import JsonFormatter
from apps.core.validators import ChoiceListValidator, age_on, validate_person_name
from tests.factories import UserFactory, image_upload, mp4_upload


def handle(exc):
    return api_exception_handler(exc, {})


class TestExceptionHandler:
    def test_flattens_nested_validation_errors(self):
        exc = exceptions.ValidationError(
            {
                "name": [exceptions.ErrorDetail("Required.", code="required")],
                "items": [{}, {"sets": [exceptions.ErrorDetail("Too big.", code="max_value")]}],
                "diet": {"meals": [exceptions.ErrorDetail("Bad.", code="invalid")]},
            }
        )

        body = handle(exc).data

        assert body["code"] == "validation_error"
        assert body["fields"] == {
            "name": ["Required."],
            "items.1.sets": ["Too big."],
            "diet.meals": ["Bad."],
        }
        assert body["field_codes"]["items.1.sets"] == ["max_value"]

    def test_non_field_error_becomes_the_message(self):
        exc = exceptions.ValidationError([exceptions.ErrorDetail("Nope.", code="custom_rule")])

        body = handle(exc).data

        assert body["code"] == "custom_rule"
        assert body["message"] == "Nope."

    def test_scalar_validation_error(self):
        body = handle(exceptions.ValidationError("Plain")).data

        assert body["message"] == "Plain"

    def test_django_validation_error(self):
        response = handle(DjangoValidationError({"email": ["Bad email."]}))

        assert response.status_code == 400
        assert response.data["fields"] == {"email": ["Bad email."]}

    def test_http404_and_permission_denied(self):
        assert handle(Http404()).data["code"] == "not_found"
        assert handle(DjangoPermissionDenied()).data["code"] == "permission_denied"

    def test_domain_error_extra_fields(self):
        response = handle(ConflictError("Busy", code="busy", extra={"current_plan": {"id": 1}}))

        assert response.status_code == 409
        assert response.data == {
            "code": "busy",
            "message": "Busy",
            "fields": {},
            "current_plan": {"id": 1},
        }

    def test_unhandled_error_returns_json_500(self, settings):
        settings.DEBUG = False

        response = handle(RuntimeError("boom"))

        assert response.status_code == 500
        assert response.data["code"] == "server_error"

    def test_unhandled_error_propagates_in_debug(self, settings):
        settings.DEBUG = True

        assert handle(RuntimeError("boom")) is None

    @pytest.mark.django_db
    def test_method_not_allowed_uses_uniform_format(self, auth_api):
        response = auth_api(UserFactory()).post("/api/v1/me")

        assert response.status_code == 405
        assert response.json()["code"] == "method_not_allowed"


def fake_request(role=None, method="GET"):
    user = SimpleNamespace(is_authenticated=role is not None, role=role, id=1)
    return SimpleNamespace(user=user, method=method)


class TestPermissions:
    @pytest.mark.parametrize(
        ("permission", "allowed"),
        [
            (permissions.IsClient, {Role.CLIENT}),
            (permissions.IsAdmin, {Role.ADMIN}),
            (permissions.IsTrainerOrAdmin, {Role.TRAINER, Role.ADMIN}),
            (permissions.IsNutritionistOrAdmin, {Role.NUTRITIONIST, Role.ADMIN}),
            (permissions.IsStaff, {Role.TRAINER, Role.NUTRITIONIST, Role.ADMIN}),
        ],
    )
    def test_role_permissions(self, permission, allowed):
        for role in [*Role.values, None]:
            assert permission().has_permission(fake_request(role), None) is (role in allowed)

    @pytest.mark.parametrize(
        ("permission", "writers"),
        [
            (permissions.StaffReadTrainerWrite, {Role.TRAINER, Role.ADMIN}),
            (permissions.StaffReadNutritionistWrite, {Role.NUTRITIONIST, Role.ADMIN}),
            (permissions.StaffReadAdminWrite, {Role.ADMIN}),
        ],
    )
    def test_staff_read_restricted_write(self, permission, writers):
        staff = {Role.TRAINER, Role.NUTRITIONIST, Role.ADMIN}
        for role in [*Role.values, None]:
            assert permission().has_permission(fake_request(role, "GET"), None) is (role in staff)
            assert permission().has_permission(fake_request(role, "POST"), None) is (
                role in writers
            )

    def test_is_owner(self):
        request = fake_request(Role.CLIENT)
        assert permissions.IsOwner().has_object_permission(
            request, None, SimpleNamespace(user_id=1)
        )
        assert not permissions.IsOwner().has_object_permission(
            request, None, SimpleNamespace(user_id=2)
        )


class TestFiles:
    def test_uuid_upload_to(self):
        name = UUIDUploadTo("photos")(None, "Mi Foto.PNG")

        assert name.startswith("photos/") and name.endswith(".png")
        assert "Mi Foto" not in name
        assert UUIDUploadTo("photos")(None, "script.exe").count(".") == 0
        assert UUIDUploadTo("a") == UUIDUploadTo("a") and UUIDUploadTo("a") != UUIDUploadTo("b")

    @pytest.mark.parametrize(
        ("name", "fmt"), [("a.jpg", "JPEG"), ("b.png", "PNG"), ("c.webp", "WEBP")]
    )
    def test_accepts_supported_images(self, name, fmt):
        validate_image_file(image_upload(name, fmt))

    def test_video_validation(self, settings):
        validate_video_file(mp4_upload())
        assert validate_media_file(mp4_upload()) == "video"
        assert validate_media_file(image_upload()) == "image"
        with pytest.raises(DjangoValidationError):
            validate_video_file(mp4_upload(valid=False))
        settings.MAX_VIDEO_UPLOAD_BYTES = 10
        with pytest.raises(DjangoValidationError) as error:
            validate_video_file(mp4_upload())
        assert error.value.code == "file_too_large"

    def test_media_kind(self):
        assert media_kind("x/y.mp4") == "video"
        assert media_kind("x/y.png") == "image"
        assert media_kind("") == "image"

    @pytest.mark.django_db
    def test_files_are_removed_when_the_owner_is_deleted(self, django_capture_on_commit_callbacks):
        user = UserFactory()
        user.profile_photo = image_upload()
        user.save()
        name = user.profile_photo.name
        assert default_storage.exists(name)

        with django_capture_on_commit_callbacks(execute=True):
            user.delete()

        assert not default_storage.exists(name)


class TestValidators:
    def test_choice_list_validator(self):
        validator = ChoiceListValidator(Role, exclusive=("admin",))
        validator(["client", "trainer"])
        for value, code in [
            ("client", "not_a_list"),
            (["pilot"], "invalid_choice"),
            (["client", "client"], "duplicated_choice"),
            (["admin", "client"], "exclusive_choice"),
        ]:
            with pytest.raises(DjangoValidationError) as error:
                validator(value)
            assert error.value.code == code
        assert validator == ChoiceListValidator(Role, exclusive=("admin",))
        assert validator != ChoiceListValidator(Role)

    def test_person_name(self):
        validate_person_name("Àngel Martí-Puig")
        with pytest.raises(DjangoValidationError):
            validate_person_name("R2D2")

    def test_age_on(self):
        assert age_on(date(2000, 2, 29), date(2018, 2, 28)) == 17
        assert age_on(date(2000, 2, 29), date(2018, 3, 1)) == 18


class TestJsonLogging:
    def test_formats_records_as_json_with_extra_fields(self):
        try:
            raise ValueError("bad")
        except ValueError:
            record = logging.getLogger("x").makeRecord(
                "x", logging.ERROR, "f.py", 1, "hello %s", ("world",), sys.exc_info()
            )
        record.user_id = 7

        payload = json.loads(JsonFormatter().format(record))

        assert payload["message"] == "hello world"
        assert payload["level"] == "ERROR"
        assert payload["user_id"] == 7
        assert "ValueError" in payload["exc_info"]


class TestBackgroundTasks:
    def test_inline_in_tests_and_in_a_thread_otherwise(self, settings):
        import threading

        from apps.core.background import run_in_background

        done = []
        assert run_in_background(done.append, "inline") is None
        assert done == ["inline"]

        settings.BACKGROUND_TASKS_INLINE = False
        thread = run_in_background(done.append, "thread")
        assert isinstance(thread, threading.Thread) and thread.daemon
        thread.join(timeout=5)
        assert done == ["inline", "thread"]

    def test_failures_are_logged(self, settings, caplog):
        from apps.core.background import run_in_background

        def broken():
            raise RuntimeError("SMTP down")

        settings.BACKGROUND_TASKS_INLINE = False
        caplog.set_level(logging.ERROR, logger="apps.api")

        run_in_background(broken).join(timeout=5)

        assert "Background task failed" in caplog.text
