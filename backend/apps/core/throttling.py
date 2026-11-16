"""Rate limit of uploads (phase 15): validating and re-encoding images costs memory and CPU."""

from rest_framework.throttling import SimpleRateThrottle

UPLOAD_METHODS = {"POST", "PUT", "PATCH"}


class UploadRateThrottle(SimpleRateThrottle):
    """Counts only the requests that carry files (multipart), whatever the view; per user or IP."""

    scope = "uploads"

    def allow_request(self, request, view):
        if request.method not in UPLOAD_METHODS:
            return True
        if not (request.content_type or "").startswith("multipart/"):
            return True
        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        ident = user.pk if user and user.is_authenticated else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
