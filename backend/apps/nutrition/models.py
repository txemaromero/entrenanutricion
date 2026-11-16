from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone

from apps.core.models import TimeStampedModel

MEALS = ("breakfast", "lunch", "dinner", "snacks")
DEFAULT_MEAL_DISTRIBUTION = {"breakfast": 20, "lunch": 30, "dinner": 30, "snacks": 20}


def default_meal_distribution() -> dict:
    return dict(DEFAULT_MEAL_DISTRIBUTION)


class MealPlanCategory(models.TextChoices):
    WEIGHT_LOSS = "weight_loss", "Weight loss"
    MUSCLE_GAIN = "muscle_gain", "Muscle gain"
    MAINTENANCE = "maintenance", "Maintenance"


class DietLabel(models.TextChoices):
    BALANCED = "balanced", "Balanced"
    HIGH_PROTEIN = "high_protein", "High protein"
    LOW_CARB = "low_carb", "Low carb"
    LOW_FAT = "low_fat", "Low fat"
    MEDITERRANEAN = "mediterranean", "Mediterranean"
    VEGETARIAN = "vegetarian", "Vegetarian"
    VEGAN = "vegan", "Vegan"
    KETO = "keto", "Keto"


class MealPlan(TimeStampedModel):
    """Reusable nutrition plan (catalog). Assignments live in UserNutritionPlan."""

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=MealPlanCategory.choices)
    diet_label = models.CharField(max_length=20, choices=DietLabel.choices)
    calories = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    proteins_g = models.DecimalField(
        max_digits=6, decimal_places=1, validators=[MinValueValidator(Decimal("0.1"))]
    )
    carbs_g = models.DecimalField(
        max_digits=6, decimal_places=1, validators=[MinValueValidator(Decimal("0.1"))]
    )
    fats_g = models.DecimalField(
        max_digits=6, decimal_places=1, validators=[MinValueValidator(Decimal("0.1"))]
    )
    meal_distribution = models.JSONField(default=default_meal_distribution)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    # English and Catalan texts of the catalog item: {"en": {"name": …}, "ca": {…}} (phase 14).
    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name", "id"]
        indexes = [models.Index(fields=["category", "is_active"])]

    def __str__(self) -> str:
        return self.name


class UserNutritionPlan(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="nutrition_plans"
    )
    plan = models.ForeignKey(MealPlan, on_delete=models.PROTECT, related_name="assignments")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    date_assigned = models.DateField(default=timezone.localdate)
    is_current = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_current=True),
                name="nutrition_one_current_plan_per_user",
            ),
        ]
        indexes = [models.Index(fields=["user", "is_current"])]

    def __str__(self) -> str:
        return f"{self.user_id} → {self.plan_id}"


# --- Food library (phase 9) ------------------------------------------------------------------------


class FoodCategory(models.TextChoices):
    VEGETABLES = "vegetables", "Vegetables"
    FRUITS = "fruits", "Fruits"
    GRAINS = "grains", "Grains and cereals"
    LEGUMES = "legumes", "Legumes"
    MEAT = "meat", "Meat"
    FISH = "fish", "Fish and seafood"
    EGGS = "eggs", "Eggs"
    DAIRY = "dairy", "Dairy"
    NUTS_SEEDS = "nuts_seeds", "Nuts and seeds"
    FATS_OILS = "fats_oils", "Fats and oils"
    OTHER = "other", "Other"


# Optional nutrients per 100 g: (field, unit). The frontend shows them in this order.
OTHER_NUTRIENTS = (("fiber_g", "g"), ("sugars_g", "g"), ("saturated_fat_g", "g"))
MICRONUTRIENTS = (
    ("sodium_mg", "mg"),
    ("potassium_mg", "mg"),
    ("calcium_mg", "mg"),
    ("iron_mg", "mg"),
    ("magnesium_mg", "mg"),
    ("vitamin_a_ug", "µg"),
    ("vitamin_c_mg", "mg"),
    ("vitamin_d_ug", "µg"),
    ("vitamin_b12_ug", "µg"),
)


def nutrient_field():
    return models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )


def grams_field(optional: bool = False):
    return models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=optional,
        blank=optional,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )


class Food(TimeStampedModel):
    """Food composition per 100 g (calories, macros and optional micronutrients)."""

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=FoodCategory.choices)
    calories = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("900"))],
        help_text="kcal per 100 g (pure fat is about 900).",
    )
    proteins_g = grams_field()
    carbs_g = grams_field()
    fats_g = grams_field()
    fiber_g = grams_field(optional=True)
    sugars_g = grams_field(optional=True)
    saturated_fat_g = grams_field(optional=True)
    sodium_mg = nutrient_field()
    potassium_mg = nutrient_field()
    calcium_mg = nutrient_field()
    iron_mg = nutrient_field()
    magnesium_mg = nutrient_field()
    vitamin_a_ug = nutrient_field()
    vitamin_c_mg = nutrient_field()
    vitamin_d_ug = nutrient_field()
    vitamin_b12_ug = nutrient_field()
    # English and Catalan texts of the catalog item: {"en": {"name": …}, "ca": {…}} (phase 14).
    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(Lower("name"), name="nutrition_food_name_ci_unique"),
        ]
        indexes = [models.Index(fields=["category"])]

    def __str__(self) -> str:
        return self.name


# --- Menus and food diary (phase 13) -------------------------------------------------------------

MEAL_CHOICES = [(meal, meal) for meal in MEALS]
MAX_PORTION_GRAMS = 2000


def portion_grams_field():
    return models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(MAX_PORTION_GRAMS)]
    )


class MealPlanItem(TimeStampedModel):
    """A food of the plan's sample day menu. Its values come from the food library, live."""

    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name="menu_items")
    meal = models.CharField(max_length=20, choices=MEAL_CHOICES)
    food = models.ForeignKey(Food, on_delete=models.PROTECT, related_name="menu_items")
    grams = portion_grams_field()
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["meal_plan", "order", "id"]

    def __str__(self) -> str:
        return f"{self.meal_plan_id} {self.meal}: {self.grams} g {self.food_id}"


class FoodLogEntry(TimeStampedModel):
    """What a client ate. The values of the portion are copied when it is logged, so the diary
    keeps its history if the food is edited or deleted later."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="food_log"
    )
    date = models.DateField()
    meal = models.CharField(max_length=20, choices=MEAL_CHOICES)
    food = models.ForeignKey(
        Food, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    food_name = models.CharField(max_length=120)
    grams = portion_grams_field()
    calories = models.DecimalField(max_digits=6, decimal_places=1)
    proteins_g = models.DecimalField(max_digits=6, decimal_places=1)
    carbs_g = models.DecimalField(max_digits=6, decimal_places=1)
    fats_g = models.DecimalField(max_digits=6, decimal_places=1)

    class Meta:
        ordering = ["date", "created_at", "id"]
        indexes = [models.Index(fields=["user", "date"])]

    def __str__(self) -> str:
        return f"{self.user_id} {self.date} {self.meal}: {self.grams} g {self.food_name}"
