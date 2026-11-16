"""JWT authentication of the API: simplejwt's, plus the cut-off of the last password change."""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class SessionJWTAuthentication(JWTAuthentication):
    """Refuses access tokens issued before the user's last password change (phase 15).

    The refresh tokens are blacklisted at that moment; without this, an access token already handed
    out (a stolen one, say) would keep working until it expires. Whole seconds are compared, because
    `iat` has no fractions: a token issued right after the change, in the same second, is valid.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        changed = user.password_changed_at
        if changed is not None and validated_token.get("iat", 0) < int(changed.timestamp()):
            raise InvalidToken("The session ended when the password was changed.")
        return user
