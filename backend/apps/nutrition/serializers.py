from decimal import Decimal

from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.translation import TranslatedMixin, TranslationsField, localized_value
from apps.core.utils import HISTORY_YEARS, years_before
from apps.nutrition import services
from apps.nutrition.menus import MAX_MENU_ITEMS
from apps.nutrition.models import (
    MAX_PORTION_GRAMS,
    MEAL_CHOICES,
    MEALS,
    MICRONUTRIENTS,
    OTHER_NUTRIENTS,
    Food,
    FoodCategory,
    FoodLogEntry,
    MealPlan,
)


def macro_field(**kwargs):
    return serializers.DecimalField(
        max_digits=6, decimal_places=1, min_value=Decimal("0.1"), **kwargs
    )


class MealDistributionField(serializers.DictField):
    """{breakfast, lunch, dinner, snacks} percentages that must add up to 100."""

    def __init__(self, **kwargs):
        super().__init__(child=serializers.IntegerField(min_value=0, max_value=100), **kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if set(value) != set(MEALS):
            raise serializers.ValidationError(
                "Give a percentage for breakfast, lunch, dinner and snacks.",
                code="invalid_meals",
            )
        if sum(value.values()) != 100:
            raise serializers.ValidationError(
                "The meal percentages must add up to 100.", code="distribution_sum"
            )
        return {meal: value[meal] for meal in MEALS}


class MealPlanSerializer(TranslatedMixin, serializers.ModelSerializer):
    translated_fields = ("name", "description")
    translations = TranslationsField({"name": 120, "description": 5000})
    proteins_g = macro_field()
    carbs_g = macro_field()
    fats_g = macro_field()
    meal_distribution = MealDistributionField(required=False)
    macros = serializers.SerializerMethodField()
    meals = serializers.SerializerMethodField()

    class Meta:
        model = MealPlan
        fields = [
            "id",
            "name",
            "category",
            "diet_label",
            "calories",
            "proteins_g",
            "carbs_g",
            "fats_g",
            "meal_distribution",
            "description",
            "is_active",
            "macros",
            "meals",
            "translations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["is_active", "created_at", "updated_at"]
        extra_kwargs = {"calories": {"min_value": 1}, "description": {"required": False}}

    def get_macros(self, plan) -> dict:
        return services.macro_breakdown(plan)

    def get_meals(self, plan) -> list[dict]:
        return services.meal_breakdown(plan)

    def validate(self, attrs):
        def current(field):
            if field in attrs:
                return attrs[field]
            return getattr(self.instance, field) if self.instance else None

        calories, proteins, carbs, fats = (
            current(field) for field in ("calories", "proteins_g", "carbs_g", "fats_g")
        )
        if None not in (calories, proteins, carbs, fats) and not (
            services.calories_within_tolerance(calories, proteins, carbs, fats)
        ):
            total = services.macros_total_kcal(proteins, carbs, fats)
            raise serializers.ValidationError(
                {
                    "calories": serializers.ErrorDetail(
                        f"Declared calories differ more than 10% from the macros total "
                        f"({total:.0f} kcal).",
                        code="calories_mismatch",
                    )
                }
            )
        return attrs


class MealPlanListSerializer(TranslatedMixin, serializers.ModelSerializer):
    translated_fields = ("name",)

    class Meta:
        model = MealPlan
        fields = [
            "id",
            "name",
            "category",
            "diet_label",
            "calories",
            "proteins_g",
            "carbs_g",
            "fats_g",
            "is_active",
        ]


class MacroValueSerializer(serializers.Serializer):
    grams = serializers.FloatField()
    kcal = serializers.FloatField()
    pct = serializers.FloatField()


class MacrosSerializer(serializers.Serializer):
    proteins = MacroValueSerializer()
    carbs = MacroValueSerializer()
    fats = MacroValueSerializer()
    total_kcal = serializers.FloatField()


class MealRowSerializer(serializers.Serializer):
    meal = serializers.CharField()
    pct = serializers.FloatField()
    kcal = serializers.FloatField()
    proteins_g = serializers.FloatField()
    carbs_g = serializers.FloatField()
    fats_g = serializers.FloatField()


class MyNutritionPlanSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="Plan id.")
    name = serializers.CharField()
    category = serializers.CharField()
    diet_label = serializers.CharField()
    description = serializers.CharField()
    calories = serializers.IntegerField()
    date_assigned = serializers.DateField()
    macros = MacrosSerializer()
    meals = MealRowSerializer(many=True)


class FoodSerializer(TranslatedMixin, serializers.ModelSerializer):
    """Values per 100 g. Macros are also returned as grams, kcal and %."""

    translated_fields = ("name",)
    translations = TranslationsField({"name": 120})
    macros = serializers.SerializerMethodField()

    class Meta:
        model = Food
        fields = [
            "id",
            "name",
            "category",
            "calories",
            "proteins_g",
            "carbs_g",
            "fats_g",
            *(field for field, _ in OTHER_NUTRIENTS),
            *(field for field, _ in MICRONUTRIENTS),
            "macros",
            "translations",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(MacrosSerializer)
    def get_macros(self, food) -> dict:
        return services.macro_breakdown(food)

    def validate_name(self, value: str) -> str:
        value = value.strip()
        duplicates = Food.objects.filter(name__iexact=value)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                "There is already a food with this name.", code="food_name_taken"
            )
        return value

    def validate(self, attrs):
        def value(field):
            return attrs[field] if field in attrs else getattr(self.instance, field, None)

        if sum(value(field) or 0 for field in ("proteins_g", "carbs_g", "fats_g")) > 100:
            raise serializers.ValidationError(
                "Proteins, carbohydrates and fats cannot add up to more than 100 g per 100 g.",
                code="macros_exceed_100g",
            )
        errors = {}
        for part, whole, code in (
            ("sugars_g", "carbs_g", "sugars_exceed_carbs"),
            ("saturated_fat_g", "fats_g", "saturated_exceed_fats"),
        ):
            if value(part) is not None and value(whole) is not None and value(part) > value(whole):
                errors[part] = serializers.ErrorDetail(f"Cannot be more than {whole}.", code=code)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


# --- Menus, shopping list and food diary (phase 13) ----------------------------------------------


class FoodRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.ChoiceField(choices=FoodCategory.choices)


class NutrientsSerializer(serializers.Serializer):
    calories = serializers.FloatField()
    proteins_g = serializers.FloatField()
    carbs_g = serializers.FloatField()
    fats_g = serializers.FloatField()


class MenuItemSerializer(NutrientsSerializer):
    id = serializers.IntegerField()
    food = FoodRefSerializer()
    grams = serializers.IntegerField()


class MenuMealSerializer(serializers.Serializer):
    meal = serializers.ChoiceField(choices=MEAL_CHOICES)
    items = MenuItemSerializer(many=True)
    totals = NutrientsSerializer()
    target = NutrientsSerializer(help_text="The plan's targets for this meal.")


class MenuSerializer(serializers.Serializer):
    has_menu = serializers.BooleanField()
    meals = MenuMealSerializer(many=True)
    totals = NutrientsSerializer()
    target = NutrientsSerializer()
    calories_deviation_pct = serializers.FloatField(
        allow_null=True, help_text="Menu calories against the plan's, in %."
    )
    within_tolerance = serializers.BooleanField(help_text="Within ±10 % of the plan's calories.")


class MenuItemInputSerializer(serializers.Serializer):
    meal = serializers.ChoiceField(choices=MEAL_CHOICES)
    food_id = serializers.PrimaryKeyRelatedField(queryset=Food.objects.all(), source="food")
    grams = serializers.IntegerField(min_value=1, max_value=MAX_PORTION_GRAMS)


class MenuInputSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=MenuItemInputSerializer(), max_length=MAX_MENU_ITEMS, allow_empty=True
    )


class ShoppingItemSerializer(serializers.Serializer):
    food = FoodRefSerializer()
    grams = serializers.IntegerField()


class ShoppingListSerializer(serializers.Serializer):
    days = serializers.IntegerField()
    has_menu = serializers.BooleanField()
    items = ShoppingItemSerializer(many=True)


class ShoppingListQuerySerializer(serializers.Serializer):
    days = serializers.IntegerField(min_value=1, max_value=14, default=7)


def not_in_the_future(value):
    if value > timezone.localdate():
        raise serializers.ValidationError("The date cannot be in the future.", code="future_date")
    return value


class FoodLogEntrySerializer(serializers.ModelSerializer):
    food_id = serializers.IntegerField(allow_null=True, read_only=True)
    calories = serializers.FloatField()
    proteins_g = serializers.FloatField()
    carbs_g = serializers.FloatField()
    fats_g = serializers.FloatField()

    class Meta:
        model = FoodLogEntry
        fields = [
            "id",
            "date",
            "meal",
            "food_id",
            "food_name",
            "grams",
            "calories",
            "proteins_g",
            "carbs_g",
            "fats_g",
        ]
        read_only_fields = fields

    def to_representation(self, entry):
        data = super().to_representation(entry)
        # The stored name or, in another language, the food's translation while it exists.
        if entry.food is not None:
            data["food_name"] = localized_value(entry.food_name, entry.food.translations, "name")
        return data


def loggable_date(value):
    """Not in the future and within the last years: the diary stays bounded, like the weights."""
    not_in_the_future(value)
    if value < years_before(timezone.localdate(), HISTORY_YEARS):
        raise serializers.ValidationError(
            f"The date cannot be more than {HISTORY_YEARS} years ago.", code="date_too_old"
        )
    return value


class FoodLogEntryInputSerializer(serializers.Serializer):
    date = serializers.DateField(validators=[loggable_date])
    meal = serializers.ChoiceField(choices=MEAL_CHOICES)
    food_id = serializers.PrimaryKeyRelatedField(queryset=Food.objects.all(), source="food")
    grams = serializers.IntegerField(min_value=1, max_value=MAX_PORTION_GRAMS)


class FoodLogEntryUpdateSerializer(serializers.Serializer):
    meal = serializers.ChoiceField(choices=MEAL_CHOICES, required=False)
    grams = serializers.IntegerField(min_value=1, max_value=MAX_PORTION_GRAMS, required=False)


class DiaryQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False, validators=[not_in_the_future])


class CopyMenuInputSerializer(serializers.Serializer):
    date = serializers.DateField(validators=[loggable_date])
    meal = serializers.ChoiceField(choices=MEAL_CHOICES, required=False, allow_null=True)


class DiaryMealSerializer(serializers.Serializer):
    meal = serializers.ChoiceField(choices=MEAL_CHOICES)
    target_calories = serializers.FloatField(allow_null=True)
    totals = NutrientsSerializer()
    entries = FoodLogEntrySerializer(many=True)


class DiaryDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    target = NutrientsSerializer(allow_null=True, help_text="Daily targets of the current plan.")
    totals = NutrientsSerializer()
    meals = DiaryMealSerializer(many=True)


class DiarySummaryQuerySerializer(serializers.Serializer):
    days = serializers.IntegerField(min_value=1, max_value=31, default=7)


class DiarySummaryDaySerializer(NutrientsSerializer):
    date = serializers.DateField()
    entries = serializers.IntegerField()


class DiarySummarySerializer(serializers.Serializer):
    target_calories = serializers.FloatField(allow_null=True)
    days_logged = serializers.IntegerField()
    average_calories = serializers.FloatField(
        allow_null=True, help_text="Over the days with something logged."
    )
    days = DiarySummaryDaySerializer(many=True, help_text="Oldest first, today last.")
