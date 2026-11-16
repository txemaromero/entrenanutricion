from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.models import TRAINING_DAYS_RANGE
from apps.core.files import media_kind, validate_media_file
from apps.core.images import MEDIA_MAX_PX, optimize_image
from apps.core.translation import TranslatedMixin, TranslationsField, localized_value
from apps.core.utils import FileUrlField, file_url
from apps.training import services
from apps.training.models import (
    Exercise,
    ExerciseMedia,
    MuscleGroup,
    TrainingPlan,
    TrainingPlanWorkout,
    Workout,
    WorkoutExercise,
)


class MuscleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuscleGroup
        fields = ["id", "name", "slug"]


def first_image_url(exercise: Exercise, request) -> str | None:
    image = next((media for media in exercise.media.all() if media.kind == "image"), None)
    return file_url(image.file, request) if image else None


class MediaFieldsMixin(serializers.Serializer):
    media_url = FileUrlField(source="media")
    media_kind = serializers.SerializerMethodField()

    def get_media_kind(self, obj) -> str | None:
        return media_kind(obj.media.name) if obj.media else None


def optimized_media(upload):
    """Images are re-encoded (WebP, 1600 px, no metadata); videos are stored as they are."""
    return optimize_image(upload, MEDIA_MAX_PX) if media_kind(upload.name) == "image" else upload


class MediaUploadSerializer(serializers.Serializer):
    media = serializers.FileField(validators=[validate_media_file])

    def validate_media(self, value):
        return optimized_media(value)


# --- Exercises -----------------------------------------------------------------------------------


class ExerciseMediaSerializer(serializers.ModelSerializer):
    url = FileUrlField(source="file")
    kind = serializers.CharField(read_only=True)

    class Meta:
        model = ExerciseMedia
        fields = ["id", "url", "kind", "caption", "order"]


class ExerciseMediaUploadSerializer(serializers.Serializer):
    file = serializers.FileField(validators=[validate_media_file])
    caption = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")

    def validate_file(self, value):
        return optimized_media(value)


@extend_schema_field(serializers.ListField(child=serializers.CharField()))
class StepsField(serializers.ListField):
    """Ordered instructions, exchanged as a plain list of strings."""

    def __init__(self, **kwargs):
        super().__init__(child=serializers.CharField(max_length=1000), **kwargs)

    def to_representation(self, value):
        return [step.text for step in value.all()]


TEXT = 5000
EXERCISE_TEXTS = {
    "name": 120,
    "description": TEXT,
    "technique": TEXT,
    "common_mistakes": TEXT,
    "benefits": TEXT,
}
NAME_AND_DESCRIPTION = {"name": 120, "description": TEXT}


class ExerciseListSerializer(TranslatedMixin, serializers.ModelSerializer):
    translated_fields = ("name", "description")
    muscle_groups = MuscleGroupSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = ["id", "name", "description", "muscle_groups", "thumbnail_url", "is_active"]

    def get_thumbnail_url(self, exercise) -> str | None:
        return first_image_url(exercise, self.context.get("request"))


class ExerciseSerializer(TranslatedMixin, serializers.ModelSerializer):
    translated_fields = tuple(EXERCISE_TEXTS)
    translated_steps = True
    translations = TranslationsField(EXERCISE_TEXTS, steps=True)
    muscle_groups = MuscleGroupSerializer(many=True, read_only=True)
    muscle_group_ids = serializers.PrimaryKeyRelatedField(
        queryset=MuscleGroup.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source="muscle_groups",
    )
    steps = StepsField(required=False)
    media = ExerciseMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = [
            "id",
            "name",
            "description",
            "technique",
            "common_mistakes",
            "benefits",
            "muscle_groups",
            "muscle_group_ids",
            "steps",
            "media",
            "is_active",
            "translations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["is_active", "created_at", "updated_at"]

    def create(self, validated_data):
        return services.save_exercise(validated_data)

    def update(self, instance, validated_data):
        return services.save_exercise(validated_data, instance)


class ExerciseBriefSerializer(TranslatedMixin, serializers.ModelSerializer):
    translated_fields = ("name",)
    muscle_groups = MuscleGroupSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = ["id", "name", "muscle_groups", "thumbnail_url", "is_active"]

    def get_thumbnail_url(self, exercise) -> str | None:
        return first_image_url(exercise, self.context.get("request"))


# --- Workouts ------------------------------------------------------------------------------------


class SummaryMixin:
    """Adds the computed duration, sets, reps and exercise count of a workout."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(services.workout_summary(instance, instance.items.all()))
        return data


class WorkoutItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    exercise_id = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(), source="exercise", write_only=True
    )
    exercise = ExerciseBriefSerializer(read_only=True)

    class Meta:
        model = WorkoutExercise
        fields = ["id", "exercise_id", "exercise", "order", "sets", "reps", "rest_seconds"]
        read_only_fields = ["order"]


class WorkoutListSerializer(
    TranslatedMixin, SummaryMixin, MediaFieldsMixin, serializers.ModelSerializer
):
    translated_fields = ("name", "description")

    class Meta:
        model = Workout
        fields = ["id", "name", "description", "media_url", "media_kind", "duration_minutes"]


def _validate_children(serializer, rows, related_name: str, empty_code: str, empty_message: str):
    if not rows:
        raise serializers.ValidationError(empty_message, code=empty_code)
    instance = serializer.instance
    allowed = (
        set(getattr(instance, related_name).values_list("id", flat=True)) if instance else set()
    )
    errors = {}
    for index, row in enumerate(rows):
        if row.get("id") is not None and row["id"] not in allowed:
            errors[index] = {"id": [serializers.ErrorDetail("Unknown item.", code="invalid_item")]}
    if errors:
        raise serializers.ValidationError(errors)
    return rows


class WorkoutSerializer(
    TranslatedMixin, SummaryMixin, MediaFieldsMixin, serializers.ModelSerializer
):
    translated_fields = ("name", "description")
    translations = TranslationsField(NAME_AND_DESCRIPTION)
    exercises = WorkoutItemSerializer(many=True, source="items")

    class Meta:
        model = Workout
        fields = [
            "id",
            "name",
            "description",
            "media_url",
            "media_kind",
            "duration_minutes",
            "exercises",
            "translations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_exercises(self, rows):
        _validate_children(self, rows, "items", "exercises_required", "Add at least one exercise.")
        current = set()
        if self.instance:
            current = set(self.instance.items.values_list("exercise_id", flat=True))
        errors = {}
        for index, row in enumerate(rows):
            exercise = row["exercise"]
            if not exercise.is_active and exercise.id not in current:
                errors[index] = {
                    "exercise_id": [
                        serializers.ErrorDetail(
                            "This exercise is no longer available.", code="exercise_inactive"
                        )
                    ]
                }
        if errors:
            raise serializers.ValidationError(errors)
        return rows

    def create(self, validated_data):
        return services.save_workout(validated_data)

    def update(self, instance, validated_data):
        return services.save_workout(validated_data, instance)


class WorkoutBriefSerializer(
    TranslatedMixin, SummaryMixin, MediaFieldsMixin, serializers.ModelSerializer
):
    translated_fields = ("name", "description")

    class Meta:
        model = Workout
        fields = ["id", "name", "description", "media_url", "media_kind"]


# --- Training plans ------------------------------------------------------------------------------


class PlanWorkoutItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    workout_id = serializers.PrimaryKeyRelatedField(
        queryset=Workout.objects.all(), source="workout", write_only=True
    )
    workout = WorkoutBriefSerializer(read_only=True)

    class Meta:
        model = TrainingPlanWorkout
        fields = ["id", "workout_id", "workout", "order"]
        read_only_fields = ["order"]


class TrainingPlanListSerializer(TranslatedMixin, MediaFieldsMixin, serializers.ModelSerializer):
    translated_fields = ("name", "description")
    workout_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TrainingPlan
        fields = [
            "id",
            "name",
            "description",
            "media_url",
            "media_kind",
            "goal",
            "difficulty",
            "equipment",
            "duration_weeks",
            "is_active",
            "workout_count",
        ]


class TrainingPlanSerializer(TranslatedMixin, MediaFieldsMixin, serializers.ModelSerializer):
    translated_fields = ("name", "description")
    translations = TranslationsField(NAME_AND_DESCRIPTION)
    workouts = PlanWorkoutItemSerializer(many=True, source="plan_workouts")
    sessions_per_week = serializers.SerializerMethodField()

    class Meta:
        model = TrainingPlan
        fields = [
            "id",
            "name",
            "description",
            "media_url",
            "media_kind",
            "goal",
            "difficulty",
            "equipment",
            "duration_weeks",
            "is_active",
            "workouts",
            "sessions_per_week",
            "translations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["is_active", "created_at", "updated_at"]

    def get_sessions_per_week(self, plan) -> int:
        """Recommended frequency: one session per workout in the weekly sequence."""
        return len(plan.plan_workouts.all())

    def validate_workouts(self, rows):
        return _validate_children(
            self, rows, "plan_workouts", "workouts_required", "Add at least one workout."
        )

    def create(self, validated_data):
        return services.save_training_plan(validated_data)

    def update(self, instance, validated_data):
        return services.save_training_plan(validated_data, instance)


# --- Client views (shapes of dict payloads built by the views) -----------------------------------


class DayProgressSerializer(serializers.Serializer):
    completed = serializers.IntegerField()
    total = serializers.IntegerField()
    percent = serializers.IntegerField()


class WorkoutSummarySerializer(serializers.Serializer):
    estimated_duration_minutes = serializers.IntegerField()
    total_sets = serializers.IntegerField()
    total_reps = serializers.IntegerField()
    exercise_count = serializers.IntegerField()


class ClientWorkoutRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    media_url = serializers.URLField(allow_null=True)
    media_kind = serializers.CharField(allow_null=True)


class ClientPlanWorkoutSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="Id of the user's workout (UserPlanWorkout).")
    order = serializers.IntegerField()
    status = serializers.CharField()
    completed_at = serializers.DateTimeField(allow_null=True)
    scheduled_date = serializers.DateField(allow_null=True)
    workout = ClientWorkoutRefSerializer()
    summary = WorkoutSummarySerializer()


class ClientPlanRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    media_url = serializers.URLField(allow_null=True)
    media_kind = serializers.CharField(allow_null=True)
    goal = serializers.CharField()
    difficulty = serializers.CharField()
    equipment = serializers.CharField()
    duration_weeks = serializers.IntegerField()


class TrainingDaysInputSerializer(serializers.Serializer):
    days = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        max_length=TRAINING_DAYS_RANGE[1],
        allow_empty=True,
        help_text="Weekdays (Monday = 0). An empty list restores the default calendar.",
    )

    def validate_days(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError(
                "Each day can be chosen only once.", code="duplicated_choice"
            )
        return value


class TrainingDaysSerializer(serializers.Serializer):
    days = serializers.ListField(child=serializers.IntegerField())
    custom = serializers.BooleanField(help_text="False when the default calendar is used.")
    weekly_training_days = serializers.IntegerField()


class MyTrainingPlanSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    cycle = serializers.IntegerField()
    progress = serializers.IntegerField()
    date_started = serializers.DateField()
    weekly_training_days = serializers.IntegerField(allow_null=True)
    training_days = serializers.ListField(child=serializers.IntegerField())
    custom_training_days = serializers.BooleanField()
    plan = ClientPlanRefSerializer()
    workouts = ClientPlanWorkoutSerializer(many=True)
    next_workout_id = serializers.IntegerField(allow_null=True)


class SetEntrySerializer(serializers.Serializer):
    """One set: repetitions done and, for weighted exercises, the load."""

    reps = serializers.IntegerField(min_value=0, max_value=200)
    weight_kg = serializers.DecimalField(
        max_digits=5,
        decimal_places=1,
        min_value=0,
        max_value=500,
        allow_null=True,
        required=False,
        coerce_to_string=False,
    )


class ClientWorkoutItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="WorkoutExercise id.")
    order = serializers.IntegerField()
    sets = serializers.IntegerField(help_text="Planned sets.")
    reps = serializers.IntegerField(help_text="Planned repetitions per set.")
    rest_seconds = serializers.IntegerField()
    completed = serializers.BooleanField()
    logged_sets = SetEntrySerializer(many=True, help_text="Sets logged so far in this workout.")
    last_sets = SetEntrySerializer(
        many=True, allow_null=True, help_text="Sets of the last session of this exercise."
    )
    exercise = ExerciseBriefSerializer()


class MyWorkoutDaySerializer(ClientPlanWorkoutSerializer):
    progress = DayProgressSerializer()
    exercises = ClientWorkoutItemSerializer(many=True)


class ExerciseCompletionInputSerializer(serializers.Serializer):
    completed = serializers.BooleanField()
    sets = serializers.ListField(
        child=SetEntrySerializer(),
        max_length=services.MAX_SETS,
        required=False,
        help_text="Sets done so far; omitted keeps the ones already logged.",
    )


class ExerciseCompletionResultSerializer(serializers.Serializer):
    workout_exercise_id = serializers.IntegerField()
    completed = serializers.BooleanField()
    logged_sets = SetEntrySerializer(many=True)
    progress = DayProgressSerializer()


class NewRecordSerializer(serializers.Serializer):
    exercise_id = serializers.IntegerField()
    exercise_name = serializers.CharField()
    weight_kg = serializers.FloatField()
    reps = serializers.IntegerField()


class ExerciseRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class PersonalRecordSerializer(serializers.Serializer):
    exercise = ExerciseRefSerializer()
    best_weight_kg = serializers.FloatField()
    best_weight_reps = serializers.IntegerField()
    best_weight_date = serializers.DateField()
    estimated_one_rm_kg = serializers.FloatField(help_text="Epley formula.")


class ExerciseHistoryEntrySerializer(serializers.Serializer):
    date = serializers.DateField()
    sets = SetEntrySerializer(many=True)
    max_weight_kg = serializers.FloatField(allow_null=True)
    volume_kg = serializers.FloatField()


class ExerciseHistorySerializer(serializers.Serializer):
    record = PersonalRecordSerializer(allow_null=True)
    entries = ExerciseHistoryEntrySerializer(many=True)


class MotivationSerializer(serializers.Serializer):
    keys = serializers.ListField(child=serializers.CharField())
    params = serializers.DictField()


class SessionWorkoutNameMixin:
    """The name stored with the session (it does not change if the workout is renamed) or, in
    another language, the workout's translation while the workout exists."""

    def to_representation(self, session):
        data = super().to_representation(session)
        if getattr(session, "workout", None) is not None:
            data["workout_name"] = localized_value(
                data["workout_name"], session.workout.translations, "name"
            )
        return data


class WorkoutSessionSerializer(SessionWorkoutNameMixin, serializers.Serializer):
    id = serializers.IntegerField()
    workout_id = serializers.IntegerField(allow_null=True)
    workout_name = serializers.CharField()
    cycle = serializers.IntegerField()
    completed_at = serializers.DateTimeField()
    total_sets = serializers.IntegerField()
    total_reps = serializers.IntegerField()
    duration_minutes = serializers.IntegerField()


class CompleteWorkoutResultSerializer(serializers.Serializer):
    session = WorkoutSessionSerializer()
    cycle_completed = serializers.BooleanField()
    cycle = serializers.IntegerField()
    plan_progress = serializers.IntegerField()
    next_workout_id = serializers.IntegerField(allow_null=True)
    motivation = MotivationSerializer()
    new_records = NewRecordSerializer(many=True)
    new_badges = serializers.ListField(
        child=serializers.CharField(), help_text="Codes of the badges awarded by this workout."
    )


class ClientExerciseDetailSerializer(TranslatedMixin, serializers.ModelSerializer):
    translated_fields = tuple(EXERCISE_TEXTS)
    translated_steps = True

    muscle_groups = MuscleGroupSerializer(many=True, read_only=True)
    steps = StepsField(read_only=True)
    media = ExerciseMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = [
            "id",
            "name",
            "description",
            "technique",
            "common_mistakes",
            "benefits",
            "muscle_groups",
            "steps",
            "media",
        ]


class RemindersSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    training_time = serializers.TimeField(format="%H:%M")
    custom_time = serializers.BooleanField(help_text="False while the default time is used.")
    default_training_time = serializers.TimeField(format="%H:%M")


class RemindersInputSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    training_time = serializers.TimeField(
        input_formats=["%H:%M"],
        allow_null=True,
        required=False,
        help_text="HH:MM; null or omitted restores the default time.",
    )
