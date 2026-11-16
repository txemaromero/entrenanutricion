"""Refresh token in an httpOnly cookie (phase 10): JavaScript never sees it, so an XSS cannot steal it.

The access token (15 min) still travels in the Authorization header and lives in memory. Endpoints
that read the cookie (refresh, logout) also require the X-Requested-With header: a cross-site page
cannot send it without a CORS preflight, which only the allowed origins pass.
"""

from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError

from apps.accounts.tokens import REMEMBER_CLAIM, SessionRefreshToken
from apps.core.exceptions import ForbiddenError

CSRF_HEADER = "X-Requested-With"


def _is_remembered(refresh: str) -> bool:
    try:
        return bool(SessionRefreshToken(refresh, verify=False).payload.get(REMEMBER_CLAIM))
    except TokenError:
        return False


def set_refresh_cookie(response, refresh: str) -> None:
    """Remembered sessions get a 7-day cookie; the others end when the browser closes."""
    max_age = (
        int(settings.REMEMBER_ME_REFRESH_LIFETIME.total_seconds())
        if _is_remembered(refresh)
        else None
    )
    response.set_cookie(
        settings.AUTH_COOKIE_NAME,
        refresh,
        max_age=max_age,
        path=settings.AUTH_COOKIE_PATH,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def clear_refresh_cookie(response) -> None:
    response.delete_cookie(
        settings.AUTH_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def refresh_from_request(request) -> str | None:
    """The refresh token of the cookie. Only there (phase 15): a token copied out of the browser
    cannot be used from elsewhere by sending it in the body."""
    token = request.COOKIES.get(settings.AUTH_COOKIE_NAME)
    if token:
        require_csrf_header(request)
    return token


def require_csrf_header(request) -> None:
    if request.headers.get(CSRF_HEADER) != settings.AUTH_CSRF_HEADER_VALUE:
        raise ForbiddenError(
            "Missing the X-Requested-With header of the application.", code="csrf_failed"
        )
