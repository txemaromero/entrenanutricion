from rest_framework import serializers

from apps.core.validators import ChoiceListValidator


class ChoiceListField(serializers.ListField):
    """List of unique enum values (multi-select). Values in `exclusive` cannot be combined."""

    def __init__(self, choices, exclusive=("none",), **kwargs):
        kwargs.setdefault("min_length", 1)
        super().__init__(child=serializers.ChoiceField(choices=choices.choices), **kwargs)
        self.validators.append(ChoiceListValidator(choices, exclusive))
