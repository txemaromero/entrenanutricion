"""Admin statistics. Dates are bucketed in the configured local time zone."""

from datetime import date, timedelta

from django.db.models import Count, Q
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone

from apps.accounts.models import Goal, Role, User, UserDetails, UserStatus
from apps.core.translation import localized_value
from apps.nutrition.models import UserNutritionPlan
from apps.training.models import ExerciseLog, UserTrainingPlan, WorkoutSession


def exercise_popularity(year: int, limit: int = 10) -> list[dict]:
    rows = (
        ExerciseLog.objects.filter(date__year=year)
        .values("exercise_id", "exercise__name", "exercise__translations")
        .annotate(count=Count("id"))
        .order_by("-count", "exercise__name")[:limit]
    )
    return [
        {
            "exercise_id": row["exercise_id"],
            "name": localized_value(row["exercise__name"], row["exercise__translations"], "name"),
            "count": row["count"],
        }
        for row in rows
    ]


def platform_growth(year: int) -> list[dict]:
    """New clients per month (always 12 buckets)."""
    counts = dict(
        User.objects.filter(role=Role.CLIENT, date_joined__year=year)
        .annotate(month=ExtractMonth("date_joined"))
        .values("month")
        .annotate(count=Count("id"))
        .values_list("month", "count")
    )
    return [{"month": month, "count": counts.get(month, 0)} for month in range(1, 13)]


def sessions_per_month(year: int) -> list[dict]:
    """Completed workouts per month (always 12 buckets)."""
    counts = dict(
        WorkoutSession.objects.filter(completed_at__year=year)
        .annotate(month=ExtractMonth("completed_at"))
        .values("month")
        .annotate(count=Count("id"))
        .values_list("month", "count")
    )
    return [{"month": month, "count": counts.get(month, 0)} for month in range(1, 13)]


def plan_popularity(limit: int = 10) -> dict:
    """Plans with the most clients right now (current assignments of active accounts)."""

    def ranking(model) -> list[dict]:
        rows = (
            model.objects.filter(is_current=True, user__is_active=True)
            .values("plan_id", "plan__name", "plan__translations")
            .annotate(count=Count("id"))
            .order_by("-count", "plan__name")[:limit]
        )
        return [
            {
                "plan_id": row["plan_id"],
                "name": localized_value(row["plan__name"], row["plan__translations"], "name"),
                "count": row["count"],
            }
            for row in rows
        ]

    return {"training": ranking(UserTrainingPlan), "nutrition": ranking(UserNutritionPlan)}


def previous_period(today: date) -> tuple[date, date]:
    """The same days of the previous month: from the 1st to today's day (or that month's end)."""
    last_of_previous = today.replace(day=1) - timedelta(days=1)
    return last_of_previous.replace(day=1), last_of_previous.replace(
        day=min(today.day, last_of_previous.day)
    )


def summary(today=None) -> dict:
    today = today or timezone.localdate()
    active_users = User.objects.filter(is_active=True)
    by_role = dict(active_users.values("role").annotate(n=Count("id")).values_list("role", "n"))
    clients = active_users.filter(role=Role.CLIENT)
    by_status = dict(clients.values("status").annotate(n=Count("id")).values_list("status", "n"))
    goals = dict(
        UserDetails.objects.filter(user__in=clients)
        .values("goal")
        .annotate(n=Count("id"))
        .values_list("goal", "n")
    )
    # The month to date against the same days of the previous month, one query for each.
    previous_start, previous_end = previous_period(today)
    month_start = today.replace(day=1)
    sessions = WorkoutSession.objects.filter(completed_at__date__gte=previous_start).aggregate(
        this_month=Count("id", filter=Q(completed_at__date__gte=month_start)),
        previous=Count("id", filter=Q(completed_at__date__lte=previous_end)),
    )
    # Sign-ups, also of accounts closed since (like the growth chart).
    signups = User.objects.filter(
        role=Role.CLIENT, date_joined__date__gte=previous_start, date_joined__date__lte=today
    ).aggregate(
        this_month=Count("id", filter=Q(date_joined__date__gte=month_start)),
        previous=Count("id", filter=Q(date_joined__date__lte=previous_end)),
    )
    return {
        "users_by_role": {role: by_role.get(role, 0) for role in Role.values},
        "active_clients": by_status.get(UserStatus.ACTIVE, 0),
        "pending_assignment": by_status.get(UserStatus.PENDING_ASSIGNMENT, 0),
        "pending_onboarding": by_status.get(UserStatus.PENDING_ONBOARDING, 0),
        "sessions_this_month": sessions["this_month"],
        "sessions_previous_period": sessions["previous"],
        "new_clients_this_month": signups["this_month"],
        "new_clients_previous_period": signups["previous"],
        "clients_by_goal": {goal: goals.get(goal, 0) for goal in Goal.values},
    }


def years_with_data(today=None) -> list[int]:
    today = today or timezone.localdate()
    joined = User.objects.filter(role=Role.CLIENT).annotate(year=ExtractYear("date_joined"))
    logged = ExerciseLog.objects.annotate(year=ExtractYear("date"))
    years = set(joined.values_list("year", flat=True)) | set(logged.values_list("year", flat=True))
    years.add(today.year)
    return sorted(years, reverse=True)
