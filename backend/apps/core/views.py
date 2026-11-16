from django.conf import settings
from django.db import connection
from django.views.static import serve
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(
        responses=inline_serializer(
            "Health",
            fields={"status": serializers.CharField(), "database": serializers.CharField()},
        )
    )
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return Response({"status": "ok", "database": "ok"})


def serve_media(request, path):
    """Uploads served by Django (local production stack, without GCS).

    Never rendered as a page: `nosniff` keeps the browser to the declared type, and anything that is
    not an image (videos) is an attachment if opened directly. `<video>` ignores the disposition.
    """
    response = serve(request, path, document_root=settings.MEDIA_ROOT)
    response["X-Content-Type-Options"] = "nosniff"
    if not response.get("Content-Type", "").startswith("image/"):
        # FileResponse sends `inline; filename="…"`: keep the name.
        disposition = response.get("Content-Disposition", "inline")
        response["Content-Disposition"] = "attachment" + disposition.removeprefix("inline")
    return response
