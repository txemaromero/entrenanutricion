from django.core.exceptions import ValidationError


class PasswordComplexityValidator:
    """At least one uppercase letter, one lowercase letter, one digit and one symbol.

    Mirrors `passwordSchema` in frontend/src/validation/schemas.ts.
    """

    def validate(self, password, user=None):
        errors = []
        if not any(c.isupper() for c in password):
            errors.append(
                ValidationError("Must contain an uppercase letter.", code="password_no_upper")
            )
        if not any(c.islower() for c in password):
            errors.append(
                ValidationError("Must contain a lowercase letter.", code="password_no_lower")
            )
        if not any(c in "0123456789" for c in password):
            errors.append(ValidationError("Must contain a number.", code="password_no_digit"))
        if not any(not c.isalnum() and not c.isspace() for c in password):
            errors.append(ValidationError("Must contain a symbol.", code="password_no_symbol"))
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return "Your password must contain uppercase and lowercase letters, a number and a symbol."
