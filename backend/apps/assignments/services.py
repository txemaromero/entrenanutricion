from django.db import transaction

from apps.accounts.models import Role, User, UserStatus
from apps.accounts.selectors import has_onboarding, plan_flags
from apps.core.exceptions import ConflictError, DomainError
from apps.nutrition.models import MealPlan, UserNutritionPlan
from apps.training.models import TrainingPlan, UserTrainingPlan
from apps.training.services import sync_user_plan


def compute_user_status(user: User) -> str:
    if not user.is_active:
        return UserStatus.INACTIVE
    if user.role != Role.CLIENT:
        return UserStatus.ACTIVE
    if not has_onboarding(user):
        return UserStatus.PENDING_ONBOARDING
    has_training, has_nutrition = plan_flags(user)
    return UserStatus.ACTIVE if has_training and has_nutrition else UserStatus.PENDING_ASSIGNMENT


def recompute_user_status(user: User) -> str:
    """Single source of truth for a user's status; call it after any change that affects it."""
    status = compute_user_status(user)
    if status != user.status:
        user.status = status
        user.save(update_fields=["status", "updated_at"])
    return status


def _ensure_assignable(user: User) -> None:
    if not has_onboarding(user):
        raise ConflictError(
            "The client has not completed the onboarding form yet.",
            code="onboarding_not_completed",
        )


@transaction.atomic
def assign_training_plan(
    user: User, plan: TrainingPlan, assigned_by: User, replace: bool = False
) -> UserTrainingPlan:
    """A second assignment needs `replace=True`; the previous one stops being current."""
    _ensure_assignable(user)
    if not plan.is_active:
        raise DomainError("This training plan is no longer available.", code="plan_inactive")
    User.objects.select_for_update().filter(pk=user.pk).first()
    current = (
        UserTrainingPlan.objects.select_related("plan").filter(user=user, is_current=True).first()
    )
    if current is not None:
        if not replace:
            raise ConflictError(
                f"The user already has the training plan «{current.plan.name}».",
                code="training_plan_already_assigned",
                extra={"current_plan": {"id": current.plan_id, "name": current.plan.name}},
            )
        current.is_current = False
        current.save(update_fields=["is_current", "updated_at"])
    assignment = UserTrainingPlan.objects.create(user=user, plan=plan, assigned_by=assigned_by)
    sync_user_plan(assignment)
    recompute_user_status(user)
    return assignment


@transaction.atomic
def assign_nutrition_plan(
    user: User, plan: MealPlan, assigned_by: User, replace: bool = False
) -> UserNutritionPlan:
    _ensure_assignable(user)
    if not plan.is_active:
        raise DomainError("This nutrition plan is no longer available.", code="plan_inactive")
    User.objects.select_for_update().filter(pk=user.pk).first()
    current = (
        UserNutritionPlan.objects.select_related("plan").filter(user=user, is_current=True).first()
    )
    if current is not None:
        if not replace:
            raise ConflictError(
                f"The user already has the nutrition plan «{current.plan.name}».",
                code="nutrition_plan_already_assigned",
                extra={"current_plan": {"id": current.plan_id, "name": current.plan.name}},
            )
        current.is_current = False
        current.save(update_fields=["is_current", "updated_at"])
    assignment = UserNutritionPlan.objects.create(user=user, plan=plan, assigned_by=assigned_by)
    recompute_user_status(user)
    return assignment
