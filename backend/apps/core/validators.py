import re
from datetime import date

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

# Letters (any script, incl. accents, ñ, ç) separated by single spaces, hyphens or apostrophes.
# Mirrors `nameSchema` in frontend/src/validation/schemas.ts.
PERSON_NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '’-][^\W\d_]+)*$")

MIN_AGE = 18
MAX_AGE = 120


def validate_person_name(value: str) -> None:
    if not PERSON_NAME_RE.match(value or ""):
        raise ValidationError(
            "Only letters, spaces, hyphens and apostrophes are allowed.", code="invalid_name"
        )


def age_on(birth_date: date, today: date) -> int:
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


def validate_adult_age(birth_date: date, today: date | None = None) -> None:
    age = age_on(birth_date, today or date.today())
    if age < MIN_AGE:
        raise ValidationError("You must be at least 18 years old.", code="too_young")
    if age > MAX_AGE:
        raise ValidationError("Age cannot be over 120 years.", code="too_old")


@deconstructible
class ChoiceListValidator:
    """Validate a JSON list of unique enum values; `exclusive` values cannot be combined."""

    def __init__(self, choices, exclusive=("none",)):
        self.choices = choices
        self.exclusive = tuple(exclusive)

    @property
    def allowed(self) -> set[str]:
        return {str(value) for value in self.choices.values}

    def __call__(self, value):
        if not isinstance(value, list):
            raise ValidationError("Expected a list of values.", code="not_a_list")
        invalid = [item for item in value if item not in self.allowed]
        if invalid:
            raise ValidationError(
                "Invalid values: %(values)s.", code="invalid_choice", params={"values": invalid}
            )
        if len(set(value)) != len(value):
            raise ValidationError("Values must not be repeated.", code="duplicated_choice")
        if len(value) > 1 and any(item in self.exclusive for item in value):
            raise ValidationError(
                "This option cannot be combined with others.", code="exclusive_choice"
            )

    def __eq__(self, other):
        return (
            isinstance(other, ChoiceListValidator)
            and other.choices == self.choices
            and other.exclusive == self.exclusive
        )
