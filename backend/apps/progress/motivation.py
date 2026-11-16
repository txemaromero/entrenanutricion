"""Motivational messages. Only i18n keys and parameters are returned; the frontend translates."""

from decimal import Decimal

from apps.accounts.models import Goal, UserDetails
from apps.accounts.selectors import current_weight_kg
from apps.training.models import WorkoutSession

SESSION_THRESHOLDS = (0, 1, 5, 10, 25, 50, 100)
MAINTAIN_TOLERANCE_KG = Decimal("1.0")


def session_milestone(sessions: int) -> int:
    return max(threshold for threshold in SESSION_THRESHOLDS if threshold <= sessions)


def weight_progress_pct(goal: str, initial, target, current) -> int | None:
    """Percentage of the way from the initial weight to the target weight (0–100)."""
    if goal == Goal.MAINTAIN or current is None or initial == target:
        return None
    done = (initial - current) if goal == Goal.LOSE_WEIGHT else (current - initial)
    total = abs(initial - target)
    return int(max(Decimal(0), min(Decimal(100), done / total * 100)))


def weight_key(goal: str, initial, target, current) -> str | None:
    if current is None:
        return None
    if goal == Goal.MAINTAIN:
        on_track = abs(current - initial) <= MAINTAIN_TOLERANCE_KG
        return f"motivation.weight.{'maintain_on_track' if on_track else 'maintain_off_track'}"
    pct = weight_progress_pct(goal, initial, target, current)
    if pct >= 100:
        stage = "reached"
    elif pct >= 50:
        stage = "halfway"
    elif pct > 0:
        stage = "started"
    else:
        stage = "not_started"
    return f"motivation.weight.{stage}"


def build_motivation(sessions: int, details=None, current_weight=None) -> dict:
    keys = [f"motivation.sessions.t{session_milestone(sessions)}"]
    params: dict = {"sessions": sessions}
    if details is not None:
        initial, target = details.initial_weight_kg, details.target_weight_kg
        key = weight_key(details.goal, initial, target, current_weight)
        if key:
            keys.append(key)
            remaining = abs(target - current_weight)
            params["remaining_kg"] = float(remaining)
            pct = weight_progress_pct(details.goal, initial, target, current_weight)
            if pct is not None:
                params["weight_progress_pct"] = pct
    return {"keys": keys, "params": params}


def motivation_for(user) -> dict:
    sessions = WorkoutSession.objects.filter(user=user).count()
    details = UserDetails.objects.filter(user=user).first()
    return build_motivation(sessions, details, current_weight_kg(user) if details else None)
