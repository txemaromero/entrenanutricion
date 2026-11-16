from django.db.models import Exists, OuterRef, Q, QuerySet

from apps.accounts.models import Role, User
from apps.nutrition.models import UserNutritionPlan
from apps.training.models import UserTrainingPlan


def clients_with_plan_flags() -> QuerySet:
    """Active onboarded clients annotated with `has_training` / `has_nutrition`."""
    return (
        User.objects.filter(role=Role.CLIENT, is_active=True, details__isnull=False)
        .select_related("details")
        .annotate(
            has_training=Exists(
                UserTrainingPlan.objects.filter(user=OuterRef("pk"), is_current=True)
            ),
            has_nutrition=Exists(
                UserNutritionPlan.objects.filter(user=OuterRef("pk"), is_current=True)
            ),
        )
    )


def pending_clients(role: str) -> QuerySet:
    queryset = clients_with_plan_flags()
    if role == Role.TRAINER:
        return queryset.filter(has_training=False)
    if role == Role.NUTRITIONIST:
        return queryset.filter(has_nutrition=False)
    return queryset.filter(Q(has_training=False) | Q(has_nutrition=False))
