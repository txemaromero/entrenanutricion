"""Catalog content in the user's language (phase 14).

The texts of exercises, workouts, plans and foods are written in Spanish (the base language) and
may have English and Catalan translations in a `translations` JSON field:
``{"en": {"name": "Squat", "description": "…"}, "ca": {…}}``. Responses show each text in the
language of the request (`Accept-Language`, activated by LocaleMiddleware) or, if it has no
translation, in Spanish. Exercise steps are translated as a list: ``{"en": {"steps": ["…"]}}``.
"""

from django.db.models import CharField, F, Value
from django.db.models.fields.json import KT
from django.db.models.functions import Coalesce, Lower, NullIf
from django.utils import translation
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

BASE_LANGUAGE = "es"
TRANSLATION_LANGUAGES = ("en", "ca")
LANGUAGES = (BASE_LANGUAGE, *TRANSLATION_LANGUAGES)
MAX_STEPS = 50
MAX_STEP_LENGTH = 1000


def content_language() -> str:
    language = (translation.get_language() or BASE_LANGUAGE)[:2]
    return language if language in LANGUAGES else BASE_LANGUAGE


def localized_value(base, translations: dict | None, field: str, language: str | None = None):
    """`base` in `language` (the request's by default) when there is a translation."""
    language = language or content_language()
    if language != BASE_LANGUAGE and translations:
        value = (translations.get(language) or {}).get(field)
        if value:
            return value
    return base


def localized(obj, field: str, language: str | None = None):
    return localized_value(getattr(obj, field), getattr(obj, "translations", None), field, language)


def localized_steps(exercise, language: str | None = None) -> list[str]:
    """Steps in the language; a step without translation stays in Spanish."""
    base = [step.text for step in exercise.steps.all()]
    language = language or content_language()
    if language == BASE_LANGUAGE:
        return base
    translated = ((exercise.translations or {}).get(language) or {}).get("steps") or []
    return [
        translated[index] if index < len(translated) and translated[index] else text
        for index, text in enumerate(base)
    ]


def order_by_localized_name(queryset):
    """Alphabetical by the name in the request's language (Spanish when not translated)."""
    language = content_language()
    if language == BASE_LANGUAGE:
        name = F("name")
    else:
        name = Coalesce(
            NullIf(KT(f"translations__{language}__name"), Value("")),
            F("name"),
            output_field=CharField(),
        )
    return queryset.annotate(localized_name=Lower(name)).order_by("localized_name", "id")


@extend_schema_field(OpenApiTypes.OBJECT)
class TranslationsField(serializers.Field):
    """All the languages of the translatable texts: `es` (the model fields) plus `en` and `ca`.

    Writing accepts `en` and `ca` (the Spanish text goes in the normal fields); empty texts are
    dropped. Exercise steps are a list in each language.
    """

    def __init__(self, fields: dict[str, int | None], steps: bool = False, **kwargs):
        kwargs.setdefault("source", "*")
        kwargs.setdefault("required", False)
        self.text_fields = fields
        self.steps = steps
        super().__init__(**kwargs)

    def to_representation(self, instance):
        base = {field: getattr(instance, field) for field in self.text_fields}
        if self.steps:
            base["steps"] = [step.text for step in instance.steps.all()]
        stored = instance.translations or {}
        return {
            BASE_LANGUAGE: base,
            **{language: dict(stored.get(language) or {}) for language in TRANSLATION_LANGUAGES},
        }

    def _text(self, value, max_length: int | None):
        if not isinstance(value, str):
            raise serializers.ValidationError("A text is expected.", code="invalid")
        value = value.strip()
        if max_length and len(value) > max_length:
            raise serializers.ValidationError(
                f"Ensure this field has no more than {max_length} characters.", code="max_length"
            )
        return value

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("An object by language is expected.", code="invalid")
        clean: dict[str, dict] = {}
        # Errors by language and field ("translations.en.name"), so forms show them in place.
        errors: dict[str, object] = {}
        for language, values in data.items():
            if language == BASE_LANGUAGE:
                continue  # the Spanish text is written in the model fields
            if language not in TRANSLATION_LANGUAGES:
                errors[language] = [
                    serializers.ErrorDetail(
                        f"Unsupported language: {language}.", code="invalid_language"
                    )
                ]
                continue
            if not isinstance(values, dict):
                errors[language] = [
                    serializers.ErrorDetail("An object is expected.", code="invalid")
                ]
                continue
            row, field_errors = self._language(values)
            if field_errors:
                errors[language] = field_errors
            elif row:
                clean[language] = row
        if errors:
            raise serializers.ValidationError(errors)
        return {"translations": clean}

    def _language(self, values: dict) -> tuple[dict, dict]:
        row: dict = {}
        errors: dict = {}
        for field, value in values.items():
            if value in (None, "", []):
                continue  # nothing to store (a translation left empty)
            try:
                if field == "steps" and self.steps:
                    if not isinstance(value, list) or len(value) > MAX_STEPS:
                        raise serializers.ValidationError(
                            "A list of steps is expected.", code="invalid"
                        )
                    steps = [self._text(step or "", MAX_STEP_LENGTH) for step in value]
                    if any(steps):
                        row["steps"] = steps
                    continue
                if field not in self.text_fields:
                    raise serializers.ValidationError(
                        f"Unknown field: {field}.", code="invalid_field"
                    )
                text = self._text(value, self.text_fields[field])
                if text:
                    row[field] = text
            except serializers.ValidationError as error:
                errors[field] = error.detail
        return row, errors


class TranslatedMixin:
    """Serializers of catalog items: the translatable fields come in the request's language."""

    translated_fields: tuple[str, ...] = ()
    translated_steps = False

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in self.translated_fields:
            if field in data:
                data[field] = localized(instance, field)
        if self.translated_steps and "steps" in data:
            data["steps"] = localized_steps(instance)
        return data
