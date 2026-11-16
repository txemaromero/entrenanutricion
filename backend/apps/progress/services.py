import calendar
from collections import Counter
from datetime import date, datetime, time, timedelta

from django.utils import timezone

from apps.accounts.models import UserDetails
from apps.core.exceptions import ConflictError
from apps.core.translation import localized
from apps.progress.models import WeightRecord
from apps.progress.motivation import motivation_for
from apps.training import schedule
from apps.training import services as training
from apps.training.models import UserWorkoutStatus, WorkoutSession


def record_weight(user, weight_kg, on_date: date | None = None) -> WeightRecord:
    """Create the weight record of a day, or update it if that day already has one."""
    record, _ = WeightRecord.objects.update_or_create(
        user=user,
        date=on_date or timezone.localdate(),
        defaults={"weight_kg": weight_kg},
    )
    return record


def require_details(user) -> UserDetails:
    details = UserDetails.objects.filter(user=user).first()
    if details is None:
        raise ConflictError(
            "The onboarding form has not been completed yet.", code="onboarding_not_completed"
        )
    return details


def weight_summary(user) -> dict:
    """Weight history plus the initial and target lines of the chart."""
    details = require_details(user)
    records = list(WeightRecord.objects.filter(user=user).order_by("date", "id"))
    return {
        "goal": details.goal,
        "initial_weight_kg": float(details.initial_weight_kg),
        "target_weight_kg": float(details.target_weight_kg),
        "current_weight_kg": float(records[-1].weight_kg) if records else None,
        "records": [
            {"id": record.id, "date": record.date, "weight_kg": float(record.weight_kg)}
            for record in records
        ],
    }


STREAK_MAX_WEEKS = 52


def week_progress(user, date_started: date, weekdays: tuple[int, ...], today: date):
    """This week day by day (scheduled, trained) and the streak: weeks in a row, within the current
    plan, with every scheduled session done. The current week counts once it is complete; while it
    is under way it does not break the streak. One query."""
    this_monday = today - timedelta(days=today.weekday())
    plan_monday = date_started - timedelta(days=date_started.weekday())
    first_monday = max(plan_monday, this_monday - timedelta(weeks=STREAK_MAX_WEEKS))

    sessions_per_week: Counter[date] = Counter()
    trained_days: set[date] = set()
    since = timezone.make_aware(datetime.combine(first_monday, time.min))
    for completed_at in WorkoutSession.objects.filter(
        user=user, completed_at__gte=since
    ).values_list("completed_at", flat=True):
        day = timezone.localdate(completed_at)
        sessions_per_week[day - timedelta(days=day.weekday())] += 1
        trained_days.add(day)

    def scheduled(day: date) -> bool:
        return day.weekday() in weekdays and day >= date_started

    def week_done(monday: date) -> bool:
        target = sum(scheduled(monday + timedelta(days=offset)) for offset in range(7))
        return target > 0 and sessions_per_week[monday] >= target

    week_days = [this_monday + timedelta(days=offset) for offset in range(7)]
    week = [
        {"date": day, "scheduled": scheduled(day), "completed": day in trained_days}
        for day in week_days
    ]

    streak = 1 if week_done(this_monday) else 0
    monday = this_monday - timedelta(weeks=1)
    while monday >= first_monday and week_done(monday):
        streak += 1
        monday -= timedelta(weeks=1)
    return week, streak


def dashboard(user, year: int | None = None, month: int | None = None, today=None) -> dict:
    """Monthly calendar, this week and the streak, next scheduled workout with countdown target,
    plan % and motivation."""
    assignment = training.get_current_assignment(user)
    today = today or timezone.localdate()
    year, month = year or today.year, month or today.month
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    completed_days = list(
        WorkoutSession.objects.filter(
            user=user, completed_at__date__gte=first_day, completed_at__date__lte=last_day
        ).dates("completed_at", "day")
    )
    weekdays = training.training_weekdays_for(user)
    scheduled_days = schedule.scheduled_dates_in_month(
        year, month, weekdays, since=assignment.date_started
    )

    rows = training.plan_rows_for_display(assignment)
    scheduled = training.schedule_rows(user, rows, today)
    next_row = next((row for row in rows if row.status == UserWorkoutStatus.AVAILABLE), None)
    week, streak_weeks = week_progress(user, assignment.date_started, weekdays, today)
    next_workout = None
    if next_row is not None:
        next_date = scheduled[next_row.id]
        next_workout = {
            "id": next_row.id,
            "workout_name": localized(next_row.plan_workout.workout, "name"),
            "scheduled_date": next_date,
            "target_datetime": schedule.target_datetime(
                next_date, training.training_time_for(user)
            ),
        }

    return {
        "month": f"{year:04d}-{month:02d}",
        "completed_days": completed_days,
        "scheduled_days": scheduled_days,
        "next_workout": next_workout,
        "plan_name": localized(assignment.plan, "name"),
        "plan_progress": assignment.progress,
        "cycle": assignment.cycle,
        "total_sessions": WorkoutSession.objects.filter(user=user).count(),
        "week": week,
        "streak_weeks": streak_weeks,
        "motivation": motivation_for(user),
    }


def session_history(user):
    training.get_current_assignment(user)
    return (
        WorkoutSession.objects.filter(user=user)
        .select_related("workout")
        .order_by("-completed_at", "-id")
    )
