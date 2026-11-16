"""Adherence of clients to their training plan (phase 12), for the staff.

For each client with a current plan: sessions done in the last 28 days against the sessions their
weekly calendar scheduled since the plan started, days without training and weight change. Today
only counts as scheduled once the client has trained (the day is not over yet).
"""

from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Exists, Max, OuterRef, Q, QuerySet, Subquery
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.core.exceptions import ConflictError, NotFoundError
from apps.core.translation import localized_value
from apps.progress.models import WeightRecord
from apps.training import schedule
from apps.training.models import UserTrainingPlan, WorkoutSession

WINDOW_DAYS = 28
WEEKS = 4
INACTIVE_DAYS = 7  # this many days without training (since the plan started) is "inactive"
AT_RISK_PERCENT = 60  # below this adherence the client is "at risk"

INACTIVE, AT_RISK, ON_TRACK = "inactive", "at_risk", "on_track"
STATUSES = (INACTIVE, AT_RISK, ON_TRACK)


def scheduled_between(weekdays: tuple[int, ...], start: date, end: date) -> int:
    """Training days of the weekly calendar from `start` to `end`, both included."""
    if end < start:
        return 0
    return sum(
        1
        for offset in range((end - start).days + 1)
        if (start + timedelta(days=offset)).weekday() in weekdays
    )


def clients_with_plan(search: str = "") -> QuerySet[User]:
    current = UserTrainingPlan.objects.filter(user=OuterRef("pk"), is_current=True)
    queryset = (
        User.objects.filter(role=Role.CLIENT, is_active=True)
        .filter(Exists(current))
        .annotate(
            plan_started=Subquery(current.values("date_started")[:1]),
            plan_name=Subquery(current.values("plan__name")[:1]),
            plan_translations=Subquery(current.values("plan__translations")[:1]),
        )
        .select_related("details")
    )
    for term in search.split():
        queryset = queryset.filter(
            Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(email__icontains=term)
        )
    return queryset


def _latest_weights(user_ids: list[int], until: date | None = None) -> dict[int, Decimal]:
    records = WeightRecord.objects.filter(user_id__in=user_ids)
    if until is not None:
        records = records.filter(date__lte=until)
    return dict(
        records.order_by("user_id", "-date", "-id")
        .distinct("user_id")
        .values_list("user_id", "weight_kg")
    )


def _weekdays(user: User) -> tuple[int, ...]:
    details = getattr(user, "details", None)
    if details is None:
        return schedule.training_weekdays(None)
    return schedule.training_weekdays(details.weekly_training_days, details.training_days)


def _initial_weight(user: User) -> Decimal | None:
    details = getattr(user, "details", None)
    return details.initial_weight_kg if details else None


def _period(user, days: list[date], weekdays, start: date, end: date, today: date) -> dict:
    """Days trained and training days scheduled between two dates, never before the plan."""
    start = max(start, user.plan_started)
    last_scheduled = end if end < today or today in days else today - timedelta(days=1)
    sessions = len({day for day in days if start <= day <= end})  # days trained
    scheduled = scheduled_between(weekdays, start, last_scheduled)
    return {"sessions": sessions, "scheduled": scheduled}


def _percent(sessions: int, scheduled: int) -> int | None:
    return round(min(sessions, scheduled) * 100 / scheduled) if scheduled else None


BAND = 20  # width of each band of the distribution, in points


def distribution(rows: list[dict]) -> list[dict]:
    """Clients per band of adherence (0–19 %, 20–39 %, …, 80–100 %). Clients with nothing
    scheduled yet are left out."""
    bands = Counter(
        min(row["adherence_percent"] // BAND, 100 // BAND - 1)
        for row in rows
        if row["adherence_percent"] is not None
    )
    last = 100 // BAND - 1
    return [
        {
            "low": band * BAND,
            "high": 100 if band == last else band * BAND + BAND - 1,
            "count": bands[band],
        }
        for band in range(last + 1)
    ]


def average_percent(rows: list[dict]) -> int | None:
    values = [row["adherence_percent"] for row in rows if row["adherence_percent"] is not None]
    return round(sum(values) / len(values)) if values else None


def adherence_rows(users, today: date | None = None, *, weeks: bool = False) -> list[dict]:
    """One row per client (worst first); `weeks` adds the breakdown of the last four weeks."""
    today = today or timezone.localdate()
    users = list(users)
    ids = [user.id for user in users]
    window_start = today - timedelta(days=WINDOW_DAYS - 1)

    session_days: dict[int, list[date]] = defaultdict(list)
    for user_id, completed_at in WorkoutSession.objects.filter(
        user_id__in=ids, completed_at__date__gte=window_start
    ).values_list("user_id", "completed_at"):
        session_days[user_id].append(timezone.localdate(completed_at))
    last_sessions = dict(
        WorkoutSession.objects.filter(user_id__in=ids)
        .values("user_id")
        .annotate(last=Max("completed_at"))
        .values_list("user_id", "last")
    )
    current_weights = _latest_weights(ids)
    reference_weights = _latest_weights(ids, until=today - timedelta(days=WINDOW_DAYS))

    rows = []
    for user in users:
        days = session_days.get(user.id, [])
        weekdays = _weekdays(user)
        window = _period(user, days, weekdays, window_start, today, today)
        last_at = last_sessions.get(user.id)
        last_date = timezone.localdate(last_at) if last_at else None
        idle_since = max(last_date, user.plan_started) if last_date else user.plan_started
        idle_days = (today - idle_since).days
        percent = _percent(window["sessions"], window["scheduled"])
        if idle_days >= INACTIVE_DAYS:
            status = INACTIVE
        elif percent is not None and percent < AT_RISK_PERCENT:
            status = AT_RISK
        else:
            status = ON_TRACK
        current = current_weights.get(user.id)
        reference = reference_weights.get(user.id) or _initial_weight(user)
        row = {
            "user": user,
            "plan_name": localized_value(user.plan_name, user.plan_translations, "name"),
            "plan_started": user.plan_started,
            "sessions": window["sessions"],
            "scheduled": window["scheduled"],
            "adherence_percent": percent,
            "last_session_date": last_date,
            "days_since_last_session": (today - last_date).days if last_date else None,
            "current_weight_kg": float(current) if current is not None else None,
            "weight_change_kg": (
                round(float(current - reference), 1)
                if current is not None and reference is not None
                else None
            ),
            "status": status,
        }
        if weeks:
            row["weeks"] = []
            for index in reversed(range(WEEKS)):
                end = today - timedelta(days=7 * index)
                start = end - timedelta(days=6)
                period = _period(user, days, weekdays, start, end, today)
                row["weeks"].append({"start": start, "end": end, **period})
        rows.append(row)

    order = {status: index for index, status in enumerate(STATUSES)}
    rows.sort(
        key=lambda row: (
            order[row["status"]],
            row["adherence_percent"] if row["adherence_percent"] is not None else 101,
            row["user"].last_name,
            row["user"].first_name,
            row["user"].id,
        )
    )
    return rows


def client_adherence(user_id: int, today: date | None = None) -> dict:
    """Adherence of one client with the last four weeks (staff view of a user)."""
    user = clients_with_plan().filter(pk=user_id).first()
    if user is None:
        if not User.objects.filter(pk=user_id, role=Role.CLIENT, is_active=True).exists():
            raise NotFoundError("Client not found.")
        raise ConflictError(
            "No training plan has been assigned yet.", code="training_plan_not_assigned"
        )
    return adherence_rows([user], today, weeks=True)[0]
