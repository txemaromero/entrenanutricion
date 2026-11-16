"""Gamification (phase 9): badges computed from the data the client already produces.

A badge is awarded the first time its goal is met and is kept even if the figure later drops
(for example, gaining weight back after reaching the target).
"""

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncWeek

from apps.accounts.models import Goal, UserDetails
from apps.accounts.selectors import current_weight_kg
from apps.progress.models import BadgeCode, UserBadge, WeightRecord
from apps.training.models import UserTrainingPlan, WorkoutSession

DEFAULT_WEEKLY_DAYS = 3


def _goal_reached(details: UserDetails | None, weight) -> bool:
    if details is None or weight is None or details.target_weight_change_kg <= 0:
        return False
    if details.goal == Goal.LOSE_WEIGHT:
        return weight <= details.target_weight_kg
    if details.goal == Goal.GAIN_MUSCLE:
        return weight >= details.target_weight_kg
    return False  # "maintain" has no target to reach


def badge_progress(user) -> dict[str, tuple[int, int]]:
    """(current, target) of every badge; a badge is earned when current reaches target."""
    sessions = WorkoutSession.objects.filter(user=user)
    count = sessions.count()
    details = UserDetails.objects.filter(user=user).first()
    weekly = details.weekly_training_days if details else DEFAULT_WEEKLY_DAYS
    best_week = (
        sessions.annotate(week=TruncWeek("completed_at"))
        .values("week")
        .annotate(total=Count("id"))
        .order_by("-total")
        .values_list("total", flat=True)
        .first()
    ) or 0
    cycles = (
        UserTrainingPlan.objects.filter(user=user).aggregate(done=Sum(F("cycle") - 1))["done"] or 0
    )
    weigh_ins = WeightRecord.objects.filter(user=user).count()
    reached = _goal_reached(details, current_weight_kg(user))

    def capped(value: int, target: int) -> tuple[int, int]:
        return min(value, target), target

    return {
        BadgeCode.FIRST_WORKOUT: capped(count, 1),
        BadgeCode.WORKOUTS_10: capped(count, 10),
        BadgeCode.WORKOUTS_50: capped(count, 50),
        BadgeCode.WORKOUTS_100: capped(count, 100),
        BadgeCode.PERFECT_WEEK: capped(best_week, weekly),
        BadgeCode.FIRST_CYCLE: capped(cycles, 1),
        BadgeCode.WEIGHT_LOGS_10: capped(weigh_ins, 10),
        BadgeCode.GOAL_REACHED: (int(reached), 1),
    }


def sync_badges(user, progress: dict[str, tuple[int, int]] | None = None) -> list[str]:
    """Award the badges whose goal is met for the first time; return their codes."""
    progress = progress or badge_progress(user)
    earned = set(UserBadge.objects.filter(user=user).values_list("code", flat=True))
    new = [
        code
        for code in BadgeCode.values
        if code not in earned and progress[code][0] >= progress[code][1]
    ]
    UserBadge.objects.bulk_create(
        [UserBadge(user=user, code=code) for code in new], ignore_conflicts=True
    )
    return new


def badges_overview(user) -> dict:
    """Every badge with its progress and award date (awarding any pending one first)."""
    progress = badge_progress(user)
    new = sync_badges(user, progress)
    awarded = dict(UserBadge.objects.filter(user=user).values_list("code", "created_at"))
    return {
        "earned_count": len(awarded),
        "total": len(BadgeCode.values),
        "new_badges": new,
        "badges": [
            {
                "code": code,
                "earned": code in awarded,
                "awarded_at": awarded.get(code),
                "current": progress[code][0],
                "target": progress[code][1],
            }
            for code in BadgeCode.values
        ],
    }
