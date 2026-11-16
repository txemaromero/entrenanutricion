"""Training business rules: catalog writes, delete policy, locked sequence, completion and cycles."""

from datetime import date, timedelta

from django.db import transaction
from django.db.models import Case, FloatField, Max, Prefetch, Value, When
from django.db.models.functions import Cast
from django.utils import timezone

from apps.accounts.models import UserDetails
from apps.core.exceptions import ConflictError, DomainError, ForbiddenError, NotFoundError
from apps.core.translation import localized, localized_value
from apps.progress.badges import sync_badges
from apps.progress.motivation import motivation_for
from apps.training import schedule
from apps.training.constants import SECONDS_PER_REP
from apps.training.models import (
    Exercise,
    ExerciseCompletion,
    ExerciseLog,
    ExerciseMedia,
    ExerciseSet,
    ExerciseStep,
    TrainingPlan,
    TrainingPlanWorkout,
    UserPlanWorkout,
    UserTrainingPlan,
    UserWorkoutStatus,
    Workout,
    WorkoutExercise,
    WorkoutSession,
)

MAX_EXERCISE_MEDIA = 10


# --- Calculations --------------------------------------------------------------------------------


def estimate_duration_minutes(items) -> int:
    """Σ sets × (reps × 3 s + rest), rounded to the nearest minute."""
    seconds = sum(item.sets * (item.reps * SECONDS_PER_REP + item.rest_seconds) for item in items)
    return int((seconds + 30) // 60)


def workout_summary(workout: Workout, items=None) -> dict:
    items = list(workout.items.all() if items is None else items)
    return {
        "estimated_duration_minutes": workout.duration_minutes or estimate_duration_minutes(items),
        "total_sets": sum(item.sets for item in items),
        "total_reps": sum(item.sets * item.reps for item in items),
        "exercise_count": len(items),
    }


def day_progress(items, completed_ids: set[int]) -> dict:
    total = len(items)
    done = sum(1 for item in items if item.id in completed_ids)
    return {"completed": done, "total": total, "percent": round(done * 100 / total) if total else 0}


# --- Catalog writes ------------------------------------------------------------------------------


def _assign_fields(instance, data: dict) -> None:
    for field, value in data.items():
        setattr(instance, field, value)


@transaction.atomic
def save_exercise(data: dict, exercise: Exercise | None = None) -> Exercise:
    data = dict(data)
    steps = data.pop("steps", None)
    muscle_groups = data.pop("muscle_groups", None)
    exercise = exercise or Exercise()
    _assign_fields(exercise, data)
    exercise.save()
    if muscle_groups is not None:
        exercise.muscle_groups.set(muscle_groups)
    if steps is not None:
        exercise.steps.all().delete()
        ExerciseStep.objects.bulk_create(
            ExerciseStep(exercise=exercise, order=position, text=text)
            for position, text in enumerate(steps, start=1)
        )
    return exercise


def _sync_ordered(model, parent_field: str, parent, rows: list[dict], fields: tuple[str, ...]):
    """Create/update/delete the ordered children of `parent`; position in `rows` sets `order`."""
    existing = {child.id: child for child in model.objects.filter(**{parent_field: parent})}
    kept: list[int] = []
    for position, row in enumerate(rows, start=1):
        child = existing.get(row.get("id")) or model(**{parent_field: parent})
        child.order = position
        for field in fields:
            setattr(child, field, row[field])
        child.save()
        kept.append(child.id)
    model.objects.filter(**{parent_field: parent}).exclude(id__in=kept).delete()


@transaction.atomic
def save_workout(data: dict, workout: Workout | None = None) -> Workout:
    data = dict(data)
    items = data.pop("items", None)
    workout = workout or Workout()
    _assign_fields(workout, data)
    workout.save()
    if items is not None:
        _sync_ordered(
            WorkoutExercise, "workout", workout, items, ("exercise", "sets", "reps", "rest_seconds")
        )
    return workout


@transaction.atomic
def save_training_plan(data: dict, plan: TrainingPlan | None = None) -> TrainingPlan:
    data = dict(data)
    plan_workouts = data.pop("plan_workouts", None)
    plan = plan or TrainingPlan()
    _assign_fields(plan, data)
    plan.save()
    if plan_workouts is not None:
        _sync_ordered(TrainingPlanWorkout, "plan", plan, plan_workouts, ("workout",))
        for assignment in plan.assignments.filter(is_current=True):
            sync_user_plan(assignment)
    return plan


def set_media(instance, file) -> None:
    """Replace (or remove, with `file=None`) the media of a workout or training plan."""
    instance.media = file
    instance.save()


@transaction.atomic
def add_exercise_media(exercise: Exercise, file, caption: str = "") -> ExerciseMedia:
    # Two uploads at once must not both see room for one more.
    exercise = Exercise.objects.select_for_update().get(pk=exercise.pk)
    count = exercise.media.count()
    if count >= MAX_EXERCISE_MEDIA:
        raise DomainError(
            f"An exercise can have at most {MAX_EXERCISE_MEDIA} images or videos.",
            code="too_many_media",
        )
    return ExerciseMedia.objects.create(
        exercise=exercise, file=file, caption=caption, order=count + 1
    )


# --- Delete policy -----------------------------------------------------------------------------


def delete_exercise(exercise: Exercise) -> str:
    """Soft delete when workouts or history reference the exercise; hard delete otherwise."""
    if exercise.workout_items.exists() or exercise.logs.exists():
        exercise.is_active = False
        exercise.save(update_fields=["is_active", "updated_at"])
        return "deactivated"
    exercise.delete()
    return "deleted"


def delete_workout(workout: Workout) -> None:
    plans = list(
        TrainingPlan.objects.filter(plan_workouts__workout=workout)
        .distinct()
        .order_by("name")
        .values("id", "name", "translations")
    )
    plans = [
        {"id": plan["id"], "name": localized_value(plan["name"], plan["translations"], "name")}
        for plan in plans
    ]
    if plans:
        names = ", ".join(plan["name"] for plan in plans)
        raise ConflictError(
            f"This workout cannot be deleted because it is used by: {names}.",
            code="workout_in_use",
            extra={"plans": plans},
        )
    workout.delete()


def delete_training_plan(plan: TrainingPlan) -> str:
    """Plans that were ever assigned are deactivated (clients keep them); others are deleted."""
    if plan.assignments.exists():
        plan.is_active = False
        plan.save(update_fields=["is_active", "updated_at"])
        return "deactivated"
    plan.delete()
    return "deleted"


# --- Assigned plan: locked sequence -------------------------------------------------------------


def _ordered_rows(user_plan: UserTrainingPlan) -> list[UserPlanWorkout]:
    return list(
        UserPlanWorkout.objects.filter(user_plan=user_plan)
        .select_related("plan_workout")
        .order_by("plan_workout__order", "plan_workout_id")
    )


def _normalize(rows: list[UserPlanWorkout]) -> None:
    """Completed rows stay; the first pending one is available and the rest are locked."""
    changed = []
    first_pending = True
    for row in rows:
        if row.status == UserWorkoutStatus.COMPLETED:
            continue
        desired = UserWorkoutStatus.AVAILABLE if first_pending else UserWorkoutStatus.LOCKED
        first_pending = False
        if row.status != desired:
            row.status = desired
            changed.append(row)
    UserPlanWorkout.objects.bulk_update(changed, ["status"])


def _close_cycle(user_plan: UserTrainingPlan, rows: list[UserPlanWorkout], today: date) -> None:
    ExerciseCompletion.objects.filter(user_plan_workout__user_plan=user_plan).delete()
    for position, row in enumerate(rows):
        row.status = UserWorkoutStatus.AVAILABLE if position == 0 else UserWorkoutStatus.LOCKED
        row.completed_at = None
    UserPlanWorkout.objects.bulk_update(rows, ["status", "completed_at"])
    user_plan.cycle += 1
    user_plan.progress = 0
    user_plan.date_completed = today
    user_plan.save(update_fields=["cycle", "progress", "date_completed", "updated_at"])


def _refresh_progress(
    user_plan: UserTrainingPlan, rows: list[UserPlanWorkout], today: date
) -> bool:
    """Recompute the plan percentage; close the cycle when every workout is done."""
    completed = sum(1 for row in rows if row.status == UserWorkoutStatus.COMPLETED)
    if rows and completed == len(rows):
        _close_cycle(user_plan, rows, today)
        return True
    user_plan.progress = round(completed * 100 / len(rows)) if rows else 0
    user_plan.save(update_fields=["progress", "updated_at"])
    return False


@transaction.atomic
def sync_user_plan(user_plan: UserTrainingPlan) -> None:
    """Create missing per-user rows for the plan's workouts and normalize the locked sequence."""
    existing = set(
        UserPlanWorkout.objects.filter(user_plan=user_plan).values_list(
            "plan_workout_id", flat=True
        )
    )
    # Query the table directly: the plan instance may carry a stale prefetch of `plan_workouts`.
    UserPlanWorkout.objects.bulk_create(
        UserPlanWorkout(user_plan=user_plan, plan_workout_id=plan_workout_id)
        for plan_workout_id in TrainingPlanWorkout.objects.filter(
            plan_id=user_plan.plan_id
        ).values_list("id", flat=True)
        if plan_workout_id not in existing
    )
    rows = _ordered_rows(user_plan)
    _normalize(rows)
    _refresh_progress(user_plan, rows, timezone.localdate())


# --- Client operations ---------------------------------------------------------------------------


def current_assignment(user) -> UserTrainingPlan | None:
    return (
        UserTrainingPlan.objects.select_related("plan").filter(user=user, is_current=True).first()
    )


def get_current_assignment(user) -> UserTrainingPlan:
    assignment = current_assignment(user)
    if assignment is None:
        raise ConflictError(
            "No training plan has been assigned yet.", code="training_plan_not_assigned"
        )
    return assignment


def get_user_workout(user, user_workout_id: int, *, for_update: bool = False) -> UserPlanWorkout:
    """A workout of the client's current plan; 404 if it is not theirs, 403 while locked."""
    assignment = get_current_assignment(user)
    queryset = UserPlanWorkout.objects.select_related("user_plan", "plan_workout__workout").filter(
        user_plan=assignment, pk=user_workout_id
    )
    if for_update:
        queryset = queryset.select_for_update(of=("self",))
    row = queryset.first()
    if row is None:
        raise NotFoundError()
    if row.status == UserWorkoutStatus.LOCKED:
        raise ForbiddenError(
            "This workout is locked until you complete the previous one.", code="workout_locked"
        )
    return row


def completed_item_ids(row: UserPlanWorkout) -> set[int]:
    if row.status == UserWorkoutStatus.COMPLETED:
        return set(row.plan_workout.workout.items.values_list("id", flat=True))
    return set(
        ExerciseCompletion.objects.filter(user_plan_workout=row, completed=True).values_list(
            "workout_exercise_id", flat=True
        )
    )


@transaction.atomic
def set_exercise_completion(
    user, user_workout_id: int, item_id: int, completed: bool, sets: list[dict] | None = None
) -> dict:
    row = get_user_workout(user, user_workout_id, for_update=True)
    if row.status == UserWorkoutStatus.COMPLETED:
        raise ConflictError("This workout is already completed.", code="workout_already_completed")
    item = WorkoutExercise.objects.filter(
        pk=item_id, workout_id=row.plan_workout.workout_id
    ).first()
    if item is None:
        raise NotFoundError()
    defaults = {"completed": completed}
    if sets is not None:
        defaults["sets"] = [_json_set(entry) for entry in sets]
    completion, _ = ExerciseCompletion.objects.update_or_create(
        user_plan_workout=row, workout_exercise=item, defaults=defaults
    )
    items = list(row.plan_workout.workout.items.all())
    return {
        "workout_exercise_id": item.id,
        "completed": completed,
        "logged_sets": completion.sets,
        "progress": day_progress(items, completed_item_ids(row)),
    }


def _json_set(entry: dict) -> dict:
    weight = entry.get("weight_kg")
    return {"reps": int(entry["reps"]), "weight_kg": float(weight) if weight is not None else None}


@transaction.atomic
def complete_workout(user, user_workout_id: int, now=None) -> dict:
    """Session + logs, unlock the next workout, update progress and close the cycle."""
    now = now or timezone.now()
    today = timezone.localdate(now)
    row = get_user_workout(user, user_workout_id, for_update=True)
    if row.status == UserWorkoutStatus.COMPLETED:
        raise ConflictError("This workout is already completed.", code="workout_already_completed")
    workout = row.plan_workout.workout
    items = list(workout.items.select_related("exercise"))
    done = completed_item_ids(row)
    if not items or any(item.id not in done for item in items):
        raise ConflictError(
            "Mark every exercise as done before completing the workout.",
            code="workout_not_finished",
        )

    assignment = UserTrainingPlan.objects.select_for_update().get(pk=row.user_plan_id)
    summary = workout_summary(workout, items)
    session = WorkoutSession.objects.create(
        user=user,
        user_plan=assignment,
        workout=workout,
        workout_name=workout.name,
        cycle=assignment.cycle,
        completed_at=now,
        total_sets=summary["total_sets"],
        total_reps=summary["total_reps"],
        duration_minutes=summary["estimated_duration_minutes"],
    )
    logged = dict(
        ExerciseCompletion.objects.filter(user_plan_workout=row).values_list(
            "workout_exercise_id", "sets"
        )
    )
    previous_bests = best_weights(user, [item.exercise_id for item in items])
    done_sets = {item.id: sets_done(item, logged.get(item.id)) for item in items}
    logs = ExerciseLog.objects.bulk_create(
        ExerciseLog(
            user=user,
            workout=workout,
            exercise=item.exercise,
            session=session,
            date=today,
            sets_completed=len(done_sets[item.id]),
            reps_completed=sum(entry["reps"] for entry in done_sets[item.id]),
            rest_time=item.rest_seconds,
        )
        for item in items
    )
    ExerciseSet.objects.bulk_create(
        ExerciseSet(log=log, number=number, reps=entry["reps"], weight_kg=entry["weight_kg"])
        for log, item in zip(logs, items, strict=True)
        for number, entry in enumerate(done_sets[item.id], start=1)
    )
    session.total_sets = sum(len(entries) for entries in done_sets.values())
    session.total_reps = sum(entry["reps"] for entries in done_sets.values() for entry in entries)
    session.save(update_fields=["total_sets", "total_reps", "updated_at"])
    new_records = _beaten_records(items, done_sets, previous_bests)
    row.status = UserWorkoutStatus.COMPLETED
    row.completed_at = now
    row.save(update_fields=["status", "completed_at", "updated_at"])

    rows = _ordered_rows(assignment)
    _normalize(rows)
    cycle_completed = _refresh_progress(assignment, rows, today)
    next_row = next((r for r in rows if r.status == UserWorkoutStatus.AVAILABLE), None)
    return {
        "session": session,
        "cycle_completed": cycle_completed,
        "cycle": assignment.cycle,
        "plan_progress": assignment.progress,
        "next_workout_id": next_row.id if next_row else None,
        "motivation": motivation_for(user),
        "new_badges": sync_badges(user),
        "new_records": new_records,
    }


def get_accessible_exercise(user, exercise_id: int) -> Exercise:
    """Exercise detail for a client: only when it belongs to an unlocked workout of their plan."""
    assignment = get_current_assignment(user)
    statuses = set(
        UserPlanWorkout.objects.filter(
            user_plan=assignment, plan_workout__workout__items__exercise_id=exercise_id
        ).values_list("status", flat=True)
    )
    if not statuses:
        raise NotFoundError()
    if statuses == {UserWorkoutStatus.LOCKED}:
        raise ForbiddenError("This exercise belongs to a locked workout.", code="workout_locked")
    return Exercise.objects.prefetch_related("muscle_groups", "steps", "media").get(pk=exercise_id)


# --- Schedule ----------------------------------------------------------------------------------


def weekly_training_days(user) -> int | None:
    return (
        UserDetails.objects.filter(user=user).values_list("weekly_training_days", flat=True).first()
    )


def training_weekdays_for(user) -> tuple[int, ...]:
    """Weekdays the client trains on: their own choice or the default calendar."""
    row = (
        UserDetails.objects.filter(user=user)
        .values_list("weekly_training_days", "training_days")
        .first()
    )
    return schedule.training_weekdays(*row) if row else schedule.training_weekdays(None)


def training_time_for(user):
    """Time of day the client trains (None: the default of the settings)."""
    return UserDetails.objects.filter(user=user).values_list("training_time", flat=True).first()


def get_training_days(user) -> dict:
    details = _client_details(user)
    return {
        "days": list(
            schedule.training_weekdays(details.weekly_training_days, details.training_days)
        ),
        "custom": bool(details.training_days),
        "weekly_training_days": details.weekly_training_days,
    }


@transaction.atomic
def set_training_days(user, days: list[int]) -> dict:
    """Pick the weekdays to train on (their count becomes the weekly days); [] restores the default."""
    details = _client_details(user)
    details.training_days = sorted(days)
    if days:
        details.weekly_training_days = len(days)
    details.save()
    return get_training_days(user)


def _client_details(user) -> UserDetails:
    details = UserDetails.objects.filter(user=user).first()
    if details is None:
        raise ConflictError(
            "The onboarding form has not been completed yet.", code="onboarding_not_completed"
        )
    return details


def trained_on(user, day: date) -> bool:
    return WorkoutSession.objects.filter(user=user, completed_at__date=day).exists()


def schedule_rows(user, rows: list[UserPlanWorkout], today: date | None = None) -> dict[int, date]:
    """Scheduled date of every pending workout, in sequence over the default weekly calendar."""
    today = today or timezone.localdate()
    weekdays = training_weekdays_for(user)
    start = today + timedelta(days=1) if trained_on(user, today) else today
    pending = [row for row in rows if row.status != UserWorkoutStatus.COMPLETED]
    dates = schedule.training_dates_from(start, weekdays, len(pending))
    return {row.id: day for row, day in zip(pending, dates, strict=True)}


def plan_rows_for_display(assignment: UserTrainingPlan) -> list[UserPlanWorkout]:
    return list(
        UserPlanWorkout.objects.filter(user_plan=assignment)
        .select_related("plan_workout__workout")
        .prefetch_related(
            Prefetch("plan_workout__workout__items", queryset=WorkoutExercise.objects.all())
        )
        .order_by("plan_workout__order", "plan_workout_id")
    )


# --- Logged sets and personal records (phase 12) ------------------------------------------------

MAX_SETS = 20


def sets_done(item: WorkoutExercise, logged: list[dict] | None) -> list[dict]:
    """The sets the client logged or, if none, the planned ones (no load)."""
    if logged:
        return [_json_set(entry) for entry in logged]
    return [{"reps": item.reps, "weight_kg": None} for _ in range(item.sets)]


def estimated_one_rep_max(weight_kg: float, reps: int) -> float:
    """Epley formula; a single repetition is the weight itself."""
    if reps <= 1:
        return round(weight_kg, 1)
    return round(weight_kg * (1 + reps / 30), 1)


def best_weights(user, exercise_ids: list[int]) -> dict[int, float]:
    return {
        exercise_id: float(weight)
        for exercise_id, weight in ExerciseSet.objects.filter(
            log__user=user, log__exercise_id__in=exercise_ids, weight_kg__isnull=False
        )
        .values("log__exercise_id")
        .annotate(best=Max("weight_kg"))
        .values_list("log__exercise_id", "best")
    }


def _beaten_records(items, done_sets: dict, previous: dict[int, float]) -> list[dict]:
    """Exercises whose heaviest set beats an earlier best (a first weighted session is no record)."""
    records = []
    for item in items:
        weighted = [entry for entry in done_sets[item.id] if entry["weight_kg"]]
        if not weighted or item.exercise_id not in previous:
            continue
        top = max(weighted, key=lambda entry: (entry["weight_kg"], entry["reps"]))
        if top["weight_kg"] > previous[item.exercise_id]:
            records.append(
                {
                    "exercise_id": item.exercise_id,
                    "exercise_name": localized(item.exercise, "name"),
                    "weight_kg": top["weight_kg"],
                    "reps": top["reps"],
                }
            )
    return records


def last_sets(user, exercise_ids: list[int]) -> dict[int, list[dict]]:
    """Sets of the latest completed session of each exercise (a hint for the next one)."""
    latest = (
        ExerciseLog.objects.filter(user=user, exercise_id__in=exercise_ids)
        .order_by("exercise_id", "-date", "-id")
        .distinct("exercise_id")
        .values_list("id", flat=True)
    )
    result: dict[int, list[dict]] = {}
    for entry in (
        ExerciseSet.objects.filter(log_id__in=list(latest))
        .order_by("log_id", "number")
        .values("log__exercise_id", "reps", "weight_kg")
    ):
        weight = entry["weight_kg"]
        result.setdefault(entry["log__exercise_id"], []).append(
            {"reps": entry["reps"], "weight_kg": float(weight) if weight is not None else None}
        )
    return result


def personal_records(user) -> list[dict]:
    """Per exercise: heaviest set (with its reps and its first date) and best estimated 1RM.

    Worked out by the database (one row per exercise), not by loading every set of the user.
    """
    sets = ExerciseSet.objects.filter(log__user=user, weight_kg__isnull=False)
    heaviest = (
        sets.order_by("log__exercise_id", "-weight_kg", "-reps", "log__date", "id")
        .distinct("log__exercise_id")
        .values(
            "log__exercise_id",
            "log__exercise__name",
            "log__exercise__translations",
            "log__date",
            "reps",
            "weight_kg",
        )
    )
    weight = Cast("weight_kg", FloatField())
    # Same Epley formula as estimated_one_rep_max(), in double precision like Python's floats.
    epley = Case(
        When(reps__lte=1, then=weight),
        default=weight * (Value(1.0) + Cast("reps", FloatField()) / Value(30.0)),
        output_field=FloatField(),
    )
    best_one_rm = dict(
        sets.values("log__exercise_id")
        .annotate(best=Max(epley))
        .values_list("log__exercise_id", "best")
    )
    records = [
        {
            "exercise": {
                "id": row["log__exercise_id"],
                "name": localized_value(
                    row["log__exercise__name"], row["log__exercise__translations"], "name"
                ),
            },
            "best_weight_kg": float(row["weight_kg"]),
            "best_weight_reps": row["reps"],
            "best_weight_date": row["log__date"],
            "estimated_one_rm_kg": round(best_one_rm[row["log__exercise_id"]], 1),
        }
        for row in heaviest
    ]
    return sorted(records, key=lambda record: record["exercise"]["name"].lower())


def exercise_history(user, exercise_id: int, limit: int = 30) -> list[dict]:
    """The latest sessions of one exercise with their sets, heaviest load and volume."""
    logs = (
        ExerciseLog.objects.filter(user=user, exercise_id=exercise_id)
        .prefetch_related("sets")
        .order_by("-date", "-id")[:limit]
    )
    entries = []
    for log in logs:
        sets = [
            {
                "reps": entry.reps,
                "weight_kg": float(entry.weight_kg) if entry.weight_kg is not None else None,
            }
            for entry in log.sets.all()
        ]
        weights = [entry["weight_kg"] for entry in sets if entry["weight_kg"]]
        entries.append(
            {
                "date": log.date,
                "sets": sets,
                "max_weight_kg": max(weights) if weights else None,
                "volume_kg": round(
                    sum((entry["weight_kg"] or 0) * entry["reps"] for entry in sets), 1
                ),
            }
        )
    return entries
