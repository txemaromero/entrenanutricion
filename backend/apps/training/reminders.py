"""Email reminders on training days (phase 12).

Opt-in per client. The hourly job sends at most one a day, within the hour before the client's
training time, when that day is one of their training days, they have a workout waiting and have
not trained yet.
"""

from datetime import datetime, time, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.emails import send_training_reminder_email
from apps.accounts.models import Role, UserDetails
from apps.core.translation import localized_value
from apps.training import schedule
from apps.training.models import UserPlanWorkout, UserWorkoutStatus, WorkoutSession
from apps.training.services import _client_details


def reminder_settings(user) -> dict:
    details = _client_details(user)
    default = schedule.default_training_time()
    return {
        "enabled": details.reminders_enabled,
        "training_time": details.training_time or default,
        "custom_time": details.training_time is not None,
        "default_training_time": default,
    }


@transaction.atomic
def update_reminders(user, enabled: bool, training_time: time | None) -> dict:
    """Turn the reminders on or off and set the training time (None restores the default)."""
    details = _client_details(user)
    details.reminders_enabled = enabled
    details.training_time = training_time
    details.save(update_fields=["reminders_enabled", "training_time", "updated_at"])
    return reminder_settings(user)


def send_due_reminders(now: datetime | None = None, *, dry_run: bool = False) -> int:
    """Send the reminders due now; returns how many were sent (or would be, with dry_run)."""
    now = now or timezone.now()
    today = timezone.localtime(now).date()
    lead = timedelta(minutes=settings.REMINDER_LEAD_MINUTES)
    candidates = list(
        UserDetails.objects.filter(
            reminders_enabled=True,
            user__is_active=True,
            user__role=Role.CLIENT,
            user__email_verified_at__isnull=False,  # never email an unconfirmed address
        )
        .exclude(last_reminder_on=today)
        .select_related("user")
    )
    ids = [details.user_id for details in candidates]
    trained_today = set(
        WorkoutSession.objects.filter(user_id__in=ids, completed_at__date=today).values_list(
            "user_id", flat=True
        )
    )
    waiting = {
        user_id: (name, translations)
        for user_id, name, translations in UserPlanWorkout.objects.filter(
            user_plan__user_id__in=ids,
            user_plan__is_current=True,
            status=UserWorkoutStatus.AVAILABLE,
        ).values_list(
            "user_plan__user_id",
            "plan_workout__workout__name",
            "plan_workout__workout__translations",
        )
    }
    sent = 0
    for details in candidates:
        weekdays = schedule.training_weekdays(details.weekly_training_days, details.training_days)
        if (
            today.weekday() not in weekdays
            or details.user_id in trained_today
            or details.user_id not in waiting
        ):
            continue
        at = details.training_time or schedule.default_training_time()
        training_at = schedule.target_datetime(today, at)
        if not training_at - lead <= now < training_at:
            continue
        if dry_run:
            sent += 1
            continue
        name, translations = waiting[details.user_id]
        workout = localized_value(name, translations, "name", details.user.language)
        if send_training_reminder_email(details.user, workout, at):
            details.last_reminder_on = today
            details.save(update_fields=["last_reminder_on", "updated_at"])
            sent += 1
    return sent
