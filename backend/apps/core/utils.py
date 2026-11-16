from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

# What a user logs by hand (weights, diary) can go back this many years: a bounded history.
HISTORY_YEARS = 5


def years_before(day, years: int):
    """The same day `years` years earlier (28 February for a 29 February)."""
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, day=28)


def file_url(file, request=None) -> str | None:
    """Absolute URL of a stored file. With GCS this is a short-lived signed URL."""
    if not file:
        return None
    url = file.url
    if request is not None and url.startswith("/"):
        return request.build_absolute_uri(url)
    return url


@extend_schema_field({"type": "string", "format": "uri", "nullable": True})
class FileUrlField(serializers.Field):
    """Read-only serializer field rendering a FileField as its (signed) absolute URL."""

    def __init__(self, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, value):
        return file_url(value, self.context.get("request"))
