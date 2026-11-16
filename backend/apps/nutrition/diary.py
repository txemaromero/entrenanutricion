"""Food diary of the client (phase 13): what they ate against the targets of their plan."""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from apps.core.exceptions import ConflictError
from apps.nutrition.menus import NUTRIENTS, portion
from apps.nutrition.models import MEALS, Food, FoodLogEntry
from apps.nutrition.services import current_assignment, meal_breakdown

SUMMARY_DAYS = 7
# Entries of one day: far more than anyone eats, but a limit (and a double "copy the menu"
# cannot grow a day without end).
MAX_ENTRIES_PER_DAY = 60


def _floats(values: dict) -> dict[str, float]:
    return {field: float(values.get(field) or 0) for field in NUTRIENTS}


def _ensure_room(user, on_date: date, adding: int) -> None:
    """Lock the user's row (one diary change at a time) and check the day keeps under the limit."""
    type(user).objects.select_for_update().filter(pk=user.pk).first()
    logged = FoodLogEntry.objects.filter(user=user, date=on_date).count()
    if logged + adding > MAX_ENTRIES_PER_DAY:
        raise ConflictError(
            f"A day can have at most {MAX_ENTRIES_PER_DAY} entries.",
            code="food_log_day_full",
            extra={"max": MAX_ENTRIES_PER_DAY},
        )


@transaction.atomic
def add_entry(user, on_date: date, meal: str, food: Food, grams: int) -> FoodLogEntry:
    _ensure_room(user, on_date, 1)
    return _create_entry(user, on_date, meal, food, grams)


def _create_entry(user, on_date: date, meal: str, food: Food, grams: int) -> FoodLogEntry:
    return FoodLogEntry.objects.create(
        user=user,
        date=on_date,
        meal=meal,
        food=food,
        food_name=food.name,
        grams=grams,
        **portion(food, grams),
    )


def update_entry(entry: FoodLogEntry, *, grams: int | None = None, meal: str | None = None):
    """New grams keep the composition logged at the time (values scale with the grams)."""
    if grams is not None and grams != entry.grams:
        for field in NUTRIENTS:
            scaled = getattr(entry, field) * grams / entry.grams
            setattr(entry, field, scaled.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
        entry.grams = grams
    if meal is not None:
        entry.meal = meal
    entry.save()
    return entry


def _targets(user):
    assignment = current_assignment(user)
    if assignment is None:
        return None, {}
    plan = assignment.plan
    day = {
        "calories": float(plan.calories),
        "proteins_g": float(plan.proteins_g),
        "carbs_g": float(plan.carbs_g),
        "fats_g": float(plan.fats_g),
    }
    meals = {row["meal"]: row["kcal"] for row in meal_breakdown(plan)}
    return day, meals


def day_log(user, on_date: date) -> dict:
    entries = list(FoodLogEntry.objects.filter(user=user, date=on_date).select_related("food"))
    target, meal_targets = _targets(user)
    meals = []
    for meal in MEALS:
        rows = [entry for entry in entries if entry.meal == meal]
        meals.append(
            {
                "meal": meal,
                "target_calories": meal_targets.get(meal),
                "totals": _floats(
                    {field: sum(getattr(entry, field) for entry in rows) for field in NUTRIENTS}
                ),
                "entries": rows,
            }
        )
    return {
        "date": on_date,
        "target": target,
        "totals": _floats(
            {field: sum(getattr(entry, field) for entry in entries) for field in NUTRIENTS}
        ),
        "meals": meals,
    }


@transaction.atomic
def copy_menu(user, on_date: date, meal: str | None = None) -> int:
    """Log the foods of the plan's menu (one meal or the whole day); returns how many."""
    assignment = current_assignment(user)
    items = (
        list(assignment.plan.menu_items.select_related("food")) if assignment is not None else []
    )
    if meal is not None:
        items = [item for item in items if item.meal == meal]
    if not items:
        raise ConflictError("The plan has no menu to copy.", code="menu_empty")
    _ensure_room(user, on_date, len(items))
    for item in items:
        _create_entry(user, on_date, item.meal, item.food, item.grams)
    return len(items)


def summary(user, days: int = SUMMARY_DAYS, today: date | None = None) -> dict:
    """Totals of the last `days` days (today included) and the daily calorie target."""
    today = today or timezone.localdate()
    start = today - timedelta(days=days - 1)
    rows = {
        row["date"]: row
        for row in FoodLogEntry.objects.filter(user=user, date__gte=start, date__lte=today)
        .values("date")
        .annotate(
            entries=Count("id"),
            **{field: Sum(field) for field in NUTRIENTS},
        )
    }
    target, _ = _targets(user)
    series = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        row = rows.get(day, {})
        series.append({"date": day, "entries": row.get("entries", 0), **_floats(row)})
    logged = [row for row in series if row["entries"]]
    return {
        "target_calories": target["calories"] if target else None,
        "days_logged": len(logged),
        "average_calories": (
            round(sum(row["calories"] for row in logged) / len(logged), 1) if logged else None
        ),
        "days": series,
    }
