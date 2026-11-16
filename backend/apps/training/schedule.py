"""Weekly training calendar: the days picked by the client or, if none, the default for their days.

Weekdays follow Python's convention: Monday = 0 … Sunday = 6.
"""

import calendar
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

DEFAULT_WEEKDAYS = {
    1: (0,),  # L
    2: (0, 3),  # L, J
    3: (0, 2, 4),  # L, X, V
    4: (0, 1, 3, 4),  # L, M, J, V
    5: (0, 1, 2, 3, 4),  # L–V
    6: (0, 1, 2, 3, 4, 5),  # L–S
}
FALLBACK_DAYS_PER_WEEK = 3


def training_weekdays(
    days_per_week: int | None, chosen: list[int] | None = None
) -> tuple[int, ...]:
    if chosen:
        return tuple(sorted(set(chosen)))
    return DEFAULT_WEEKDAYS.get(days_per_week or FALLBACK_DAYS_PER_WEEK, DEFAULT_WEEKDAYS[3])


def training_dates_from(start: date, weekdays: tuple[int, ...], count: int) -> list[date]:
    """The first `count` training dates on or after `start`."""
    dates: list[date] = []
    current = start
    while len(dates) < count:
        if current.weekday() in weekdays:
            dates.append(current)
        current += timedelta(days=1)
    return dates


def scheduled_dates_in_month(
    year: int, month: int, weekdays: tuple[int, ...], since: date | None = None
) -> list[date]:
    last_day = calendar.monthrange(year, month)[1]
    days = (date(year, month, day) for day in range(1, last_day + 1))
    return [d for d in days if d.weekday() in weekdays and (since is None or d >= since)]


def default_training_time() -> time:
    hour, minute = (int(part) for part in settings.DEFAULT_TRAINING_TIME.split(":"))
    return time(hour, minute)


def target_datetime(on_date: date, at: time | None = None) -> datetime:
    """Countdown target for a scheduled workout: the client's training time (or the default)."""
    return timezone.make_aware(datetime.combine(on_date, at or default_training_time()))
