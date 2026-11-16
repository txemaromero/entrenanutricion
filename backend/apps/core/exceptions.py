"""Uniform API error format: {"code": str, "message": str, "fields": {name: [msg]}, "field_codes": {...}}."""

import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("apps.api")


class DomainError(exceptions.APIException):
    """Business-rule violation carrying a stable, machine-readable code the frontend translates."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "domain_error"
    default_detail = "The request could not be processed."

    def __init__(self, message=None, code=None, extra=None, status_code=None):
        super().__init__(detail=message or self.default_detail, code=code or self.default_code)
        self.code = code or self.default_code
        self.extra = extra or {}
        if status_code is not None:
            self.status_code = status_code


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"
    default_detail = "The request conflicts with the current state of the resource."


class ForbiddenError(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "permission_denied"
    default_detail = "You do not have permission to perform this action."


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "not_found"
    default_detail = "Not found."


def _flatten(detail, prefix=""):
    """Flatten nested DRF error details into {"a.b.0.c": [ErrorDetail, ...]}."""
    flat = {}
    if isinstance(detail, dict):
        for key, value in detail.items():
            flat.update(_flatten(value, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(detail, list):
        if all(not isinstance(item, (dict, list)) for item in detail):
            if detail:
                flat[prefix or "non_field_errors"] = list(detail)
        else:
            for index, item in enumerate(detail):
                if item:
                    flat.update(_flatten(item, f"{prefix}.{index}" if prefix else str(index)))
    else:
        flat[prefix or "non_field_errors"] = [detail]
    return flat


def _validation_payload(exc: exceptions.ValidationError) -> dict:
    flat = _flatten(exc.detail)
    non_field = flat.pop("non_field_errors", [])
    fields = {name: [str(err) for err in errs] for name, errs in flat.items()}
    field_codes = {
        name: [getattr(err, "code", "invalid") for err in errs] for name, errs in flat.items()
    }
    if non_field:
        code = getattr(non_field[0], "code", "invalid")
        message = str(non_field[0])
    else:
        code = "validation_error"
        message = "Some fields are not valid."
    return {"code": code, "message": message, "fields": fields, "field_codes": field_codes}


def _generic_payload(exc: exceptions.APIException) -> dict:
    detail = exc.detail
    if isinstance(detail, dict):  # e.g. simplejwt InvalidToken
        code = str(detail.get("code", exc.default_code))
        message = str(detail.get("detail", exc.default_detail))
    else:
        codes = exc.get_codes()
        code = codes if isinstance(codes, str) else exc.default_code
        message = str(detail)
    return {"code": code, "message": message, "fields": {}}


def api_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))
    elif isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)
    if response is None:
        if settings.DEBUG:
            return None
        logger.exception("Unhandled API error", exc_info=exc)
        return Response(
            {"code": "server_error", "message": "Internal server error.", "fields": {}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, DomainError):
        payload = {"code": exc.code, "message": str(exc.detail), "fields": {}, **exc.extra}
    elif isinstance(exc, exceptions.ValidationError):
        payload = _validation_payload(exc)
    else:
        payload = _generic_payload(exc)
    response.data = payload
    return response
