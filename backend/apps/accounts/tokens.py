"""JWT helpers: refresh tokens remember whether the session is long-lived ("Recordar sesión")."""

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import datetime_from_epoch

REMEMBER_CLAIM = "remember"


class SessionRefreshToken(RefreshToken):
    """Refresh token whose lifetime is 7 days when `remember` is set, 12 hours otherwise.

    The claim survives rotation, so a remembered session stays remembered.
    """

    def set_exp(self, claim="exp", from_time=None, lifetime=None):
        if claim == "exp" and lifetime is None and self.payload.get(REMEMBER_CLAIM):
            lifetime = settings.REMEMBER_ME_REFRESH_LIFETIME
        super().set_exp(claim=claim, from_time=from_time, lifetime=lifetime)


def issue_tokens(user, remember: bool = False) -> dict[str, str]:
    refresh = SessionRefreshToken.for_user(user)
    if remember:
        refresh[REMEMBER_CLAIM] = True
        refresh.set_exp()
        OutstandingToken.objects.filter(jti=refresh["jti"]).update(
            token=str(refresh), expires_at=datetime_from_epoch(refresh["exp"])
        )
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def blacklist_all_tokens(user) -> None:
    """Invalidate every outstanding refresh token of `user` (e.g. after a password change)."""
    pending = OutstandingToken.objects.filter(user=user, blacklistedtoken__isnull=True)
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=token) for token in pending], ignore_conflicts=True
    )


class SessionTokenRefreshSerializer(TokenRefreshSerializer):
    token_class = SessionRefreshToken

    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except get_user_model().DoesNotExist as exc:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"], "no_active_account"
            ) from exc
