"""A client's training in figures: sessions, minutes and lifted volume per week, muscles worked."""

from datetime import date, datetime, time, timedelta

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from apps.training.models import ExerciseLog, ExerciseSet, WorkoutSession

WEEKS = 12
MUSCLE_DAYS = 28


def week_start(day: date) -> date:
    """Monday of the week of `day`."""
    return day - timedelta(days=day.weekday())


def training_stats(user, today: date | None = None) -> dict:
    """The last `WEEKS` weeks (Monday to Sunday, the current one included, oldest first) and the
    sets per muscle group of the last `MUSCLE_DAYS` days. Three queries, whatever the history."""
    today = today or timezone.localdate()
    first = week_start(today) - timedelta(weeks=WEEKS - 1)
    weeks = {
        first + timedelta(weeks=index): {"sessions": 0, "minutes": 0, "volume_kg": 0.0}
        for index in range(WEEKS)
    }

    sessions = WorkoutSession.objects.filter(
        user=user, completed_at__gte=timezone.make_aware(datetime.combine(first, time.min))
    ).values_list("completed_at", "duration_minutes")
    for completed_at, minutes in sessions:
        week = weeks.get(week_start(timezone.localdate(completed_at)))
        if week is not None:
            week["sessions"] += 1
            week["minutes"] += minutes

    # Volume = repetitions × kilos of the sets with load (bodyweight sets have no kilos).
    load = ExpressionWrapper(
        F("reps") * F("weight_kg"), output_field=DecimalField(max_digits=12, decimal_places=1)
    )
    volume_per_day = (
        ExerciseSet.objects.filter(
            log__user=user, log__date__gte=first, log__date__lte=today, weight_kg__isnull=False
        )
        .values("log__date")
        .annotate(volume=Sum(load))
        .values_list("log__date", "volume")
    )
    for day, volume in volume_per_day:
        weeks[week_start(day)]["volume_kg"] += float(volume or 0)

    # An exercise that works two muscle groups counts its sets for both.
    muscles = (
        ExerciseLog.objects.filter(
            user=user,
            date__gt=today - timedelta(days=MUSCLE_DAYS),
            date__lte=today,
            exercise__muscle_groups__isnull=False,
        )
        .values("exercise__muscle_groups__slug", "exercise__muscle_groups__name")
        .annotate(sets=Sum("sets_completed"))
        .order_by("-sets", "exercise__muscle_groups__name")
    )

    return {
        "weeks": [
            {"start": start, **values, "volume_kg": round(values["volume_kg"], 1)}
            for start, values in weeks.items()
        ],
        "muscle_groups": [
            {
                "slug": row["exercise__muscle_groups__slug"],
                "name": row["exercise__muscle_groups__name"],
                "sets": row["sets"],
            }
            for row in muscles
        ],
    }
