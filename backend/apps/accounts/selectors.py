"""Read-only queries about users shared by several apps."""

from apps.accounts.models import UserDetails
from apps.nutrition.models import UserNutritionPlan
from apps.progress.models import WeightRecord
from apps.training.models import UserTrainingPlan


def has_onboarding(user) -> bool:
    return UserDetails.objects.filter(user=user).exists()


def current_weight_kg(user):
    """Latest recorded weight (the current weight is always the last WeightRecord)."""
    record = WeightRecord.objects.filter(user=user).order_by("-date", "-id").first()
    return record.weight_kg if record else None


def plan_flags(user) -> tuple[bool, bool]:
    """(has_training_plan, has_nutrition_plan) for the user's current assignments."""
    has_training = UserTrainingPlan.objects.filter(user=user, is_current=True).exists()
    has_nutrition = UserNutritionPlan.objects.filter(user=user, is_current=True).exists()
    return has_training, has_nutrition
