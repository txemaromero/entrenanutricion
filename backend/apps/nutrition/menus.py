"""Sample day menu of a nutrition plan and the shopping list built from it (phase 13)."""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction

from apps.core.translation import localized
from apps.nutrition.models import MEALS, Food, FoodCategory, MealPlan, MealPlanItem
from apps.nutrition.services import CALORIES_TOLERANCE, meal_breakdown

MAX_MENU_ITEMS = 60
NUTRIENTS = ("calories", "proteins_g", "carbs_g", "fats_g")


def _one_decimal(value) -> Decimal:
    return Decimal(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def portion(food: Food, grams: int) -> dict[str, Decimal]:
    """Calories and macros of `grams` of a food (the library gives them per 100 g)."""
    return {field: _one_decimal(getattr(food, field) * grams / 100) for field in NUTRIENTS}


def _sum(rows) -> dict[str, float]:
    return {field: float(sum((row[field] for row in rows), Decimal(0))) for field in NUTRIENTS}


def _food_ref(food: Food) -> dict:
    return {"id": food.id, "name": localized(food, "name"), "category": food.category}


def menu_of(plan: MealPlan) -> dict:
    """The menu by meal with the totals of each meal and of the day against the plan's targets."""
    items = list(plan.menu_items.select_related("food"))
    targets = {row["meal"]: row for row in meal_breakdown(plan)}
    meals = []
    all_rows = []
    for meal in MEALS:
        rows = [
            {
                "id": item.id,
                "food": _food_ref(item.food),
                "grams": item.grams,
                **portion(item.food, item.grams),
            }
            for item in items
            if item.meal == meal
        ]
        all_rows.extend(rows)
        target = targets[meal]
        meals.append(
            {
                "meal": meal,
                "items": [{**row, **{f: float(row[f]) for f in NUTRIENTS}} for row in rows],
                "totals": _sum(rows),
                "target": {
                    "calories": target["kcal"],
                    "proteins_g": target["proteins_g"],
                    "carbs_g": target["carbs_g"],
                    "fats_g": target["fats_g"],
                },
            }
        )
    totals = _sum(all_rows)
    deviation = (
        round((totals["calories"] - plan.calories) * 100 / plan.calories, 1) if all_rows else None
    )
    return {
        "has_menu": bool(all_rows),
        "meals": meals,
        "totals": totals,
        "target": {
            "calories": float(plan.calories),
            "proteins_g": float(plan.proteins_g),
            "carbs_g": float(plan.carbs_g),
            "fats_g": float(plan.fats_g),
        },
        "calories_deviation_pct": deviation,
        "within_tolerance": deviation is not None
        and abs(Decimal(str(deviation))) <= CALORIES_TOLERANCE * 100,
    }


@transaction.atomic
def set_menu(plan: MealPlan, rows: list[dict]) -> dict:
    """Replace the whole menu (the order of `rows` is kept within each meal)."""
    plan.menu_items.all().delete()
    MealPlanItem.objects.bulk_create(
        MealPlanItem(
            meal_plan=plan, meal=row["meal"], food=row["food"], grams=row["grams"], order=index
        )
        for index, row in enumerate(rows)
    )
    return menu_of(plan)


def shopping_list(plan: MealPlan, days: int) -> dict:
    """Grams of each food of the menu for `days` days, by category and name."""
    grams: dict[int, int] = defaultdict(int)
    foods: dict[int, Food] = {}
    for item in plan.menu_items.select_related("food"):
        grams[item.food_id] += item.grams * days
        foods[item.food_id] = item.food
    order = {category: index for index, category in enumerate(FoodCategory.values)}
    items = sorted(
        ({"food": _food_ref(food), "grams": grams[food_id]} for food_id, food in foods.items()),
        key=lambda row: (order[row["food"]["category"]], row["food"]["name"].lower()),
    )
    return {"days": days, "has_menu": bool(items), "items": items}
