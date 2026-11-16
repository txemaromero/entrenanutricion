from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Equipment, Goal
from apps.core.files import UUIDUploadTo, media_kind
from apps.core.models import TimeStampedModel

SETS_RANGE = (1, 20)
REPS_RANGE = (1, 100)
REST_SECONDS_RANGE = (0, 600)


class MuscleGroup(TimeStampedModel):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Exercise(TimeStampedModel):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    technique = models.TextField(blank=True)
    common_mistakes = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    muscle_groups = models.ManyToManyField(MuscleGroup, related_name="exercises", blank=True)
    is_active = models.BooleanField(default=True)
    # English and Catalan texts of the exercise (steps as a list): {"en": {"name": …}, "ca": {…}} (phase 14).
    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name", "id"]
        indexes = [models.Index(fields=["is_active", "name"])]

    def __str__(self) -> str:
        return self.name


class ExerciseStep(TimeStampedModel):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveSmallIntegerField()
    text = models.TextField()

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.exercise_id}#{self.order}"


class ExerciseMedia(TimeStampedModel):
    """Image or video of an exercise (the «Imagen» entity); feeds the carousel."""

    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to=UUIDUploadTo("exercises"))
    order = models.PositiveSmallIntegerField(default=0)
    caption = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name_plural = "exercise media"

    def __str__(self) -> str:
        return self.file.name

    @property
    def kind(self) -> str:
        return media_kind(self.file.name)


class Workout(TimeStampedModel):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    media = models.FileField(upload_to=UUIDUploadTo("workouts"), blank=True)
    duration_minutes = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(600)]
    )
    # English and Catalan texts of the catalog item: {"en": {"name": …}, "ca": {…}} (phase 14).
    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return self.name


class WorkoutExercise(TimeStampedModel):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="items")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name="workout_items")
    order = models.PositiveSmallIntegerField()
    sets = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(SETS_RANGE[0]), MaxValueValidator(SETS_RANGE[1])]
    )
    reps = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(REPS_RANGE[0]), MaxValueValidator(REPS_RANGE[1])]
    )
    rest_seconds = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(REST_SECONDS_RANGE[0]),
            MaxValueValidator(REST_SECONDS_RANGE[1]),
        ]
    )

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.workout_id}#{self.order} {self.exercise_id}"


class Difficulty(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"


class TrainingPlan(TimeStampedModel):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    media = models.FileField(upload_to=UUIDUploadTo("training_plans"), blank=True)
    goal = models.CharField(max_length=20, choices=Goal.choices)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices)
    equipment = models.CharField(max_length=20, choices=Equipment.choices)
    duration_weeks = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(52)]
    )
    is_active = models.BooleanField(default=True)
    # English and Catalan texts of the catalog item: {"en": {"name": …}, "ca": {…}} (phase 14).
    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name", "id"]
        indexes = [models.Index(fields=["is_active", "name"])]

    def __str__(self) -> str:
        return self.name


class TrainingPlanWorkout(TimeStampedModel):
    """Ordered sequence of workouts in a plan (a workout may appear more than once)."""

    plan = models.ForeignKey(TrainingPlan, on_delete=models.CASCADE, related_name="plan_workouts")
    workout = models.ForeignKey(Workout, on_delete=models.PROTECT, related_name="plan_entries")
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.plan_id}#{self.order} {self.workout_id}"


class UserTrainingPlan(TimeStampedModel):
    """Assignment of a training plan to a client."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="training_plans"
    )
    plan = models.ForeignKey(TrainingPlan, on_delete=models.PROTECT, related_name="assignments")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    date_started = models.DateField(default=timezone.localdate)
    date_completed = models.DateField(null=True, blank=True)
    cycle = models.PositiveIntegerField(default=1)
    progress = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_current = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_current=True),
                name="training_one_current_plan_per_user",
            ),
        ]
        indexes = [models.Index(fields=["user", "is_current"])]

    def __str__(self) -> str:
        return f"{self.user_id} → {self.plan_id} (cycle {self.cycle})"


class UserWorkoutStatus(models.TextChoices):
    LOCKED = "locked", "Locked"
    AVAILABLE = "available", "Available"
    COMPLETED = "completed", "Completed"


class UserPlanWorkout(TimeStampedModel):
    """State of each workout of an assigned plan for the user («WeeklyWorkout»)."""

    user_plan = models.ForeignKey(
        UserTrainingPlan, on_delete=models.CASCADE, related_name="workouts"
    )
    plan_workout = models.ForeignKey(
        TrainingPlanWorkout, on_delete=models.CASCADE, related_name="user_entries"
    )
    status = models.CharField(
        max_length=10, choices=UserWorkoutStatus.choices, default=UserWorkoutStatus.LOCKED
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["plan_workout__order", "plan_workout_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user_plan", "plan_workout"], name="training_user_plan_workout_unique"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_plan_id}/{self.plan_workout_id}: {self.status}"


class ExerciseCompletion(TimeStampedModel):
    """Server-side state of each exercise checkbox of the day."""

    user_plan_workout = models.ForeignKey(
        UserPlanWorkout, on_delete=models.CASCADE, related_name="completions"
    )
    workout_exercise = models.ForeignKey(
        WorkoutExercise, on_delete=models.CASCADE, related_name="completions"
    )
    completed = models.BooleanField(default=False)
    # Sets done so far ([{"reps": 10, "weight_kg": 40.0}, …]); copied to ExerciseSet on completion.
    sets = models.JSONField(default=list, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_plan_workout", "workout_exercise"],
                name="training_exercise_completion_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_plan_workout_id}/{self.workout_exercise_id}: {self.completed}"


class WorkoutSession(TimeStampedModel):
    """History of completed workouts."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workout_sessions"
    )
    user_plan = models.ForeignKey(
        UserTrainingPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )
    workout = models.ForeignKey(
        Workout, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions"
    )
    # Snapshot so the history stays readable if the workout is renamed or deleted.
    workout_name = models.CharField(max_length=120)
    cycle = models.PositiveIntegerField(default=1)
    completed_at = models.DateTimeField(default=timezone.now)
    total_sets = models.PositiveIntegerField(default=0)
    total_reps = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-completed_at", "-id"]
        indexes = [models.Index(fields=["user", "-completed_at"])]

    def __str__(self) -> str:
        return f"{self.user_id} {self.workout_name} {self.completed_at:%Y-%m-%d}"


class ExerciseLog(TimeStampedModel):
    """One row per exercise of a completed workout; feeds exercise popularity statistics."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exercise_logs"
    )
    workout = models.ForeignKey(
        Workout, on_delete=models.SET_NULL, null=True, blank=True, related_name="exercise_logs"
    )
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name="logs")
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField()
    sets_completed = models.PositiveSmallIntegerField()
    reps_completed = models.PositiveSmallIntegerField()
    rest_time = models.PositiveSmallIntegerField(help_text="Rest between sets, in seconds.")

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["date", "exercise"])]

    def __str__(self) -> str:
        return f"{self.user_id} {self.exercise_id} {self.date}"


class ExerciseSet(TimeStampedModel):
    """A set actually done in a completed workout: repetitions and, if weighted, the load."""

    log = models.ForeignKey(ExerciseLog, on_delete=models.CASCADE, related_name="sets")
    number = models.PositiveSmallIntegerField()
    reps = models.PositiveSmallIntegerField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    class Meta:
        ordering = ["log", "number"]
        constraints = [
            models.UniqueConstraint(fields=["log", "number"], name="training_exercise_set_unique"),
        ]

    def __str__(self) -> str:
        return f"{self.log_id} #{self.number}: {self.reps} × {self.weight_kg}"
