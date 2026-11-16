"""Right of access and portability (GDPR arts. 15 and 20): every personal record of a user as JSON."""

from django.db.models import Prefetch
from django.utils import timezone

from apps.accounts.models import HealthDataAccess, User, UserDetails
from apps.accounts.serializers import OnboardingSerializer
from apps.core.utils import file_url
from apps.notes.models import Note
from apps.nutrition.models import FoodLogEntry, UserNutritionPlan
from apps.progress.models import UserBadge, WeightRecord
from apps.training.models import ExerciseLog, UserTrainingPlan, WorkoutSession

FORMAT_VERSION = 1


def _iso(value):
    return value.isoformat() if value else None


def export_user_data(user: User, request=None) -> dict:
    details = (
        UserDetails.objects.select_related("user__diet_preferences", "user__health_info")
        .filter(user=user)
        .first()
    )
    sessions = (
        WorkoutSession.objects.filter(user=user)
        .order_by("completed_at")
        .prefetch_related(
            Prefetch(
                "logs",
                queryset=ExerciseLog.objects.select_related("exercise")
                .prefetch_related("sets")
                .order_by("id"),
            )
        )
    )
    return {
        "format_version": FORMAT_VERSION,
        "exported_at": timezone.now().isoformat(),
        "account": {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "birth_date": _iso(user.birth_date),
            "gender": user.gender,
            "role": user.role,
            "status": user.status,
            "date_joined": _iso(user.date_joined),
            "last_login": _iso(user.last_login),
            "profile_photo_url": file_url(user.profile_photo, request),
            "terms_accepted_at": _iso(user.terms_accepted_at),
            "privacy_policy_version": user.privacy_policy_version,
            "privacy_accepted_at": _iso(user.privacy_accepted_at),
            "health_consent_at": _iso(user.health_consent_at),
            "language": user.language,
            "email_verified_at": _iso(user.email_verified_at),
        },
        "reminders": (
            {
                "enabled": details.reminders_enabled,
                "training_time": (
                    details.training_time.strftime("%H:%M") if details.training_time else None
                ),
            }
            if details
            else None
        ),
        "onboarding": OnboardingSerializer(details).data if details else None,
        "weight_records": [
            {"date": _iso(record.date), "weight_kg": float(record.weight_kg)}
            for record in WeightRecord.objects.filter(user=user).order_by("date")
        ],
        "training_plans": [
            {
                "plan": assignment.plan.name,
                "date_started": _iso(assignment.date_started),
                "date_completed": _iso(assignment.date_completed),
                "cycle": assignment.cycle,
                "progress": assignment.progress,
                "is_current": assignment.is_current,
            }
            for assignment in UserTrainingPlan.objects.filter(user=user)
            .select_related("plan")
            .order_by("date_started", "id")
        ],
        "nutrition_plans": [
            {
                "plan": assignment.plan.name,
                "category": assignment.plan.category,
                "calories": assignment.plan.calories,
                "date_assigned": _iso(assignment.date_assigned),
                "is_current": assignment.is_current,
            }
            for assignment in UserNutritionPlan.objects.filter(user=user)
            .select_related("plan")
            .order_by("date_assigned", "id")
        ],
        "workout_sessions": [
            {
                "workout": session.workout_name,
                "completed_at": _iso(session.completed_at),
                "cycle": session.cycle,
                "total_sets": session.total_sets,
                "total_reps": session.total_reps,
                "duration_minutes": session.duration_minutes,
                "exercises": [
                    {
                        "exercise": log.exercise.name,
                        "sets_completed": log.sets_completed,
                        "reps_completed": log.reps_completed,
                        "rest_seconds": log.rest_time,
                        "sets": [
                            {
                                "reps": entry.reps,
                                "weight_kg": (
                                    float(entry.weight_kg) if entry.weight_kg is not None else None
                                ),
                            }
                            for entry in log.sets.all()
                        ],
                    }
                    for log in session.logs.all()
                ],
            }
            for session in sessions
        ],
        "badges": [
            {"code": badge.code, "awarded_at": _iso(badge.created_at)}
            for badge in UserBadge.objects.filter(user=user).order_by("created_at")
        ],
        "food_log": [
            {
                "date": _iso(entry.date),
                "meal": entry.meal,
                "food": entry.food_name,
                "grams": entry.grams,
                "calories": float(entry.calories),
                "proteins_g": float(entry.proteins_g),
                "carbs_g": float(entry.carbs_g),
                "fats_g": float(entry.fats_g),
            }
            for entry in FoodLogEntry.objects.filter(user=user).order_by("date", "id")
        ],
        "notes": [
            {
                "created_at": _iso(note.created_at),
                "author": note.author_name,
                "author_role": note.author_role,
                "body": note.body,
                "read_at": _iso(note.read_at),
            }
            for note in Note.objects.filter(client=user).order_by("created_at", "id")
        ],
        # Who of the team was shown the health answers, and when (GDPR art. 15.1.c).
        "health_data_accesses": [
            {
                "accessed_at": _iso(access.created_at),
                "staff": access.staff_name,
                "staff_role": access.staff_role,
            }
            for access in HealthDataAccess.objects.filter(client=user).order_by("created_at", "id")
        ],
    }
