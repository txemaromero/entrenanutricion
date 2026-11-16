"""Request and response guards (phase 15): size limit of the requests, no caching of the API.

Requests bigger than any allowed upload are refused before their body is read.

The upload limits (5 MB images, 50 MB videos) are checked by the serializers, once Django has
received the whole body into a temporary file. Without this, a client could send gigabytes first.
"""

from django.conf import settings
from django.http import JsonResponse


class RequestSizeLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            length = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        # Without Content-Length (chunked), Django reads no body at all: nothing to check.
        if length > settings.MAX_REQUEST_BODY_BYTES:
            return JsonResponse(
                {"code": "request_too_large", "message": "The request is too large.", "fields": {}},
                status=413,
            )
        return self.get_response(request)


class ApiNoStoreMiddleware:
    """`Cache-Control: no-store` on every API answer (unless a view chose its own policy).

    They hold personal and health data: no browser disk cache, back/forward cache nor shared proxy
    may keep a copy (e.g. on a shared computer after signing out).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/api/") and not response.has_header("Cache-Control"):
            response["Cache-Control"] = "no-store"
        return response
