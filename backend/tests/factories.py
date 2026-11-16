from datetime import date
from decimal import Decimal
from io import BytesIO

import factory
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from factory.django import DjangoModelFactory
from PIL import Image

from apps.accounts.models import (
    ActivityLevel,
    DailyTrainingTime,
    DietPreferences,
    DietType,
    Goal,
    HealthInfo,
    MacroSelfAssessment,
    Role,
    User,
    UserDetails,
    UserStatus,
)
from apps.progress.models import WeightRecord

DEFAULT_PASSWORD = "Secret#2025a"


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = "Ana"
    last_name = factory.Sequence(lambda n: f"Garcia {n}")
    birth_date = date(1990, 5, 17)
    gender = "F"
    role = Role.CLIENT
    status = UserStatus.PENDING_ONBOARDING
    privacy_policy_version = factory.LazyFunction(lambda: settings.PRIVACY_POLICY_VERSION)
    privacy_accepted_at = factory.LazyFunction(timezone.now)
    health_consent_at = factory.LazyFunction(timezone.now)
    email_verified_at = factory.LazyFunction(timezone.now)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", DEFAULT_PASSWORD)
        return model_class.objects.create_user(*args, password=password, **kwargs)


class TrainerFactory(UserFactory):
    role = Role.TRAINER
    status = UserStatus.ACTIVE
    email = factory.Sequence(lambda n: f"trainer{n}@example.com")


class NutritionistFactory(UserFactory):
    role = Role.NUTRITIONIST
    status = UserStatus.ACTIVE
    email = factory.Sequence(lambda n: f"nutri{n}@example.com")


class AdminFactory(UserFactory):
    role = Role.ADMIN
    status = UserStatus.ACTIVE
    email = factory.Sequence(lambda n: f"admin{n}@example.com")


class UserDetailsFactory(DjangoModelFactory):
    class Meta:
        model = UserDetails

    user = factory.SubFactory(UserFactory)
    height_cm = 170
    initial_weight_kg = Decimal("80.0")
    goal = Goal.LOSE_WEIGHT
    target_weight_change_kg = Decimal("5.0")
    weekly_training_days = 3
    daily_training_time = DailyTrainingTime.ONE_TO_TWO_HOURS
    physical_activity_level = ActivityLevel.MODERATE
    usual_exercise_types = factory.LazyFunction(lambda: ["strength"])
    available_equipment = factory.LazyFunction(lambda: ["full_gym"])
    training_preference = "gym"


class DietPreferencesFactory(DjangoModelFactory):
    class Meta:
        model = DietPreferences

    user = factory.SubFactory(UserFactory)
    diet_type = DietType.OMNIVORE
    food_restrictions = factory.LazyFunction(lambda: ["none"])
    meals_per_day = 4
    macronutrient_intake_self_assessment = MacroSelfAssessment.BALANCED


class HealthInfoFactory(DjangoModelFactory):
    class Meta:
        model = HealthInfo

    user = factory.SubFactory(UserFactory)
    medical_conditions = factory.LazyFunction(lambda: ["none"])
    supplements = factory.LazyFunction(lambda: ["none"])


class WeightRecordFactory(DjangoModelFactory):
    class Meta:
        model = WeightRecord

    user = factory.SubFactory(UserFactory)
    weight_kg = Decimal("80.0")
    date = factory.LazyFunction(date.today)


def onboarded_client(**user_kwargs) -> User:
    """A client that completed the onboarding form (status pending_assignment)."""
    user_kwargs.setdefault("status", UserStatus.PENDING_ASSIGNMENT)
    user = UserFactory(**user_kwargs)
    details = UserDetailsFactory(user=user)
    DietPreferencesFactory(user=user)
    HealthInfoFactory(user=user)
    WeightRecordFactory(user=user, weight_kg=details.initial_weight_kg, date=date(2026, 1, 1))
    return User.objects.select_related("details").get(pk=user.pk)


def image_upload(name="photo.png", image_format="PNG", size=(16, 16)) -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", size, color=(31, 138, 76)).save(buffer, format=image_format)
    content_type = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}.get(
        image_format, "application/octet-stream"
    )
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


def mp4_upload(name="clip.mp4", valid=True) -> SimpleUploadedFile:
    header = b"\x00\x00\x00\x18ftypmp42" if valid else b"not a real video file"
    return SimpleUploadedFile(name, header + b"\x00" * 64, content_type="video/mp4")


# --- Training ------------------------------------------------------------------------------------


class ExerciseFactory(DjangoModelFactory):
    class Meta:
        model = "training.Exercise"

    name = factory.Sequence(lambda n: f"Exercise {n}")
    description = "Description"
    technique = "Technique"
    common_mistakes = "Mistakes"
    benefits = "Benefits"


class WorkoutFactory(DjangoModelFactory):
    class Meta:
        model = "training.Workout"

    name = factory.Sequence(lambda n: f"Workout {n}")
    description = "Workout description"


class WorkoutExerciseFactory(DjangoModelFactory):
    class Meta:
        model = "training.WorkoutExercise"

    workout = factory.SubFactory(WorkoutFactory)
    exercise = factory.SubFactory(ExerciseFactory)
    order = factory.Sequence(lambda n: n + 1)
    sets = 3
    reps = 10
    rest_seconds = 60


class TrainingPlanFactory(DjangoModelFactory):
    class Meta:
        model = "training.TrainingPlan"

    name = factory.Sequence(lambda n: f"Plan {n}")
    description = "Plan description"
    goal = Goal.LOSE_WEIGHT
    difficulty = "beginner"
    equipment = "full_gym"
    duration_weeks = 8


def workout_with_exercises(exercises: int = 2, **kwargs):
    workout = WorkoutFactory(**kwargs)
    for position in range(1, exercises + 1):
        WorkoutExerciseFactory(workout=workout, order=position)
    return workout


def plan_with_workouts(workouts: int = 3, exercises: int = 2, **kwargs):
    from apps.training.models import TrainingPlanWorkout

    plan = TrainingPlanFactory(**kwargs)
    for position in range(1, workouts + 1):
        TrainingPlanWorkout.objects.create(
            plan=plan, workout=workout_with_exercises(exercises), order=position
        )
    return plan


def assign_plan(user, plan=None, assigned_by=None):
    from apps.assignments.services import assign_training_plan

    plan = plan or plan_with_workouts()
    assigned_by = assigned_by or TrainerFactory()
    return assign_training_plan(user, plan, assigned_by)


# --- Nutrition -----------------------------------------------------------------------------------


class MealPlanFactory(DjangoModelFactory):
    class Meta:
        model = "nutrition.MealPlan"

    name = factory.Sequence(lambda n: f"Meal plan {n}")
    category = "weight_loss"
    diet_label = "high_protein"
    calories = 1700
    proteins_g = Decimal("150")
    carbs_g = Decimal("150")
    fats_g = Decimal("55")
    description = "Plan description"


class FoodFactory(DjangoModelFactory):
    class Meta:
        model = "nutrition.Food"

    name = factory.Sequence(lambda n: f"Food {n}")
    category = "vegetables"
    calories = Decimal("34")
    proteins_g = Decimal("2.8")
    carbs_g = Decimal("6.6")
    fats_g = Decimal("0.4")
    fiber_g = Decimal("2.6")


def assign_meal_plan(user, plan=None, assigned_by=None):
    from apps.assignments.services import assign_nutrition_plan

    return assign_nutrition_plan(
        user, plan or MealPlanFactory(), assigned_by or NutritionistFactory()
    )


def active_client(**user_kwargs):
    """Onboarded client with both plans assigned (status active)."""
    user = onboarded_client(**user_kwargs)
    assign_plan(user)
    assign_meal_plan(user)
    user.refresh_from_db()
    return user


def refresh_with(client, token: str):
    """Refresh as the app does: the token in the httpOnly cookie, plus the app's header."""
    # A new morsel: the client's may be shared with an earlier response, which would change too.
    client.cookies.pop(settings.AUTH_COOKIE_NAME, None)
    client.cookies[settings.AUTH_COOKIE_NAME] = token
    return client.post(
        "/api/v1/auth/refresh", {}, HTTP_X_REQUESTED_WITH=settings.AUTH_CSRF_HEADER_VALUE
    )
