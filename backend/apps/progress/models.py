from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class WeightRecord(TimeStampedModel):
    """Body-weight history. The latest record by date is the user's current weight."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weight_records"
    )
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(30), MaxValueValidator(300)],
    )
    date = models.DateField()

    class Meta:
        ordering = ["date", "id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="progress_weight_one_per_day"),
        ]
        indexes = [models.Index(fields=["user", "-date"])]

    def __str__(self) -> str:
        return f"{self.user_id} {self.date}: {self.weight_kg} kg"


class BadgeCode(models.TextChoices):
    """Achievements (phase 9). The order is the display order; texts are translated in the app."""

    FIRST_WORKOUT = "first_workout", "First workout"
    WORKOUTS_10 = "workouts_10", "10 workouts"
    WORKOUTS_50 = "workouts_50", "50 workouts"
    WORKOUTS_100 = "workouts_100", "100 workouts"
    PERFECT_WEEK = "perfect_week", "Perfect week"
    FIRST_CYCLE = "first_cycle", "First full plan"
    WEIGHT_LOGS_10 = "weight_logs_10", "10 weigh-ins"
    GOAL_REACHED = "goal_reached", "Target weight reached"


class UserBadge(TimeStampedModel):
    """A badge earned by a client; `created_at` is when it was awarded. Never taken away."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges"
    )
    code = models.CharField(max_length=30, choices=BadgeCode.choices)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "code"], name="progress_badge_once"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}: {self.code}"
