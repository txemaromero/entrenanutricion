"""Macronutrient calculations (kcal per macro, ±10 % check) and nutrition plan operations."""

from decimal import ROUND_HALF_UP, Decimal

from apps.core.exceptions import ConflictError
from apps.core.translation import localized_value
from apps.nutrition.models import MEALS, MealPlan, UserNutritionPlan

KCAL_PER_GRAM = {"proteins": 4, "carbs": 4, "fats": 9}
CALORIES_TOLERANCE = Decimal("0.10")


def _round(value, places: str = "0.1") -> float:
    return float(Decimal(value).quantize(Decimal(places), rounding=ROUND_HALF_UP))


def macro_kcal(proteins_g, carbs_g, fats_g) -> dict[str, Decimal]:
    grams = {"proteins": proteins_g, "carbs": carbs_g, "fats": fats_g}
    return {macro: Decimal(grams[macro]) * KCAL_PER_GRAM[macro] for macro in grams}


def macros_total_kcal(proteins_g, carbs_g, fats_g) -> Decimal:
    return sum(macro_kcal(proteins_g, carbs_g, fats_g).values(), Decimal(0))


def calories_within_tolerance(calories, proteins_g, carbs_g, fats_g) -> bool:
    total = macros_total_kcal(proteins_g, carbs_g, fats_g)
    return total > 0 and abs(Decimal(calories) - total) <= total * CALORIES_TOLERANCE


def macro_breakdown(plan: MealPlan) -> dict:
    """Grams, kcal and percentage of each macro; percentages are over the macros' kcal sum."""
    kcal = macro_kcal(plan.proteins_g, plan.carbs_g, plan.fats_g)
    total = sum(kcal.values(), Decimal(0))
    grams = {"proteins": plan.proteins_g, "carbs": plan.carbs_g, "fats": plan.fats_g}
    return {
        macro: {
            "grams": _round(grams[macro]),
            "kcal": _round(kcal[macro], "1"),
            "pct": _round(kcal[macro] * 100 / total) if total else 0.0,
        }
        for macro in kcal
    } | {"total_kcal": _round(total, "1")}


def meal_breakdown(plan: MealPlan) -> list[dict]:
    """Declared calories and macro grams split by meal according to the plan's distribution."""
    rows = []
    for meal in MEALS:
        share = Decimal(str(plan.meal_distribution.get(meal, 0))) / 100
        rows.append(
            {
                "meal": meal,
                "pct": _round(share * 100),
                "kcal": _round(Decimal(plan.calories) * share, "1"),
                "proteins_g": _round(plan.proteins_g * share),
                "carbs_g": _round(plan.carbs_g * share),
                "fats_g": _round(plan.fats_g * share),
            }
        )
    return rows


def delete_food(food) -> None:
    """Foods in a menu cannot be deleted; the diary keeps its own copy of the values."""
    plans = list(
        MealPlan.objects.filter(menu_items__food=food)
        .distinct()
        .order_by("name")
        .values("id", "name", "translations")
    )
    plans = [
        {"id": plan["id"], "name": localized_value(plan["name"], plan["translations"], "name")}
        for plan in plans
    ]
    if plans:
        names = ", ".join(plan["name"] for plan in plans)
        raise ConflictError(
            f"This food cannot be deleted because it is in the menu of: {names}.",
            code="food_in_use",
            extra={"plans": plans},
        )
    food.delete()


def delete_meal_plan(plan: MealPlan) -> None:
    """Nutrition plans are always soft-deleted: assigned clients keep theirs."""
    plan.is_active = False
    plan.save(update_fields=["is_active", "updated_at"])


def current_assignment(user) -> UserNutritionPlan | None:
    return (
        UserNutritionPlan.objects.select_related("plan").filter(user=user, is_current=True).first()
    )


def get_current_assignment(user) -> UserNutritionPlan:
    assignment = current_assignment(user)
    if assignment is None:
        raise ConflictError(
            "No nutrition plan has been assigned yet.", code="nutrition_plan_not_assigned"
        )
    return assignment
