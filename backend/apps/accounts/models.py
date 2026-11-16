from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from apps.core.files import UUIDUploadTo
from apps.core.models import TimeStampedModel
from apps.core.validators import ChoiceListValidator


class Role(models.TextChoices):
    CLIENT = "client", "Client"
    ADMIN = "admin", "Admin"
    TRAINER = "trainer", "Trainer"
    NUTRITIONIST = "nutritionist", "Nutritionist"


STAFF_ROLES = (Role.ADMIN, Role.TRAINER, Role.NUTRITIONIST)


class Language(models.TextChoices):
    """Languages of the app; emails are sent in the user's one."""

    ES = "es", "Español"
    EN = "en", "English"
    CA = "ca", "Català"


class UserStatus(models.TextChoices):
    PENDING_ONBOARDING = "pending_onboarding", "Pending onboarding"
    PENDING_ASSIGNMENT = "pending_assignment", "Pending assignment"
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class Gender(models.TextChoices):
    MALE = "M", "Male"
    FEMALE = "F", "Female"
    OTHER = "O", "Other"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email must be set")
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.CLIENT)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault(
            "status",
            (
                UserStatus.PENDING_ONBOARDING
                if extra_fields["role"] == Role.CLIENT
                else UserStatus.ACTIVE
            ),
        )
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        extra_fields.setdefault("status", UserStatus.ACTIVE)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("email_verified_at", timezone.now())
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    profile_photo = models.ImageField(upload_to=UUIDUploadTo("profile_photos"), blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    status = models.CharField(
        max_length=20, choices=UserStatus.choices, default=UserStatus.PENDING_ONBOARDING
    )
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    # GDPR: accepted privacy policy version and explicit consent for health data (clients).
    privacy_policy_version = models.CharField(max_length=20, blank=True)
    privacy_accepted_at = models.DateTimeField(null=True, blank=True)
    health_consent_at = models.DateTimeField(null=True, blank=True)
    # When an admin deactivated the account (deleted after ACCOUNT_RETENTION_DAYS).
    deactivated_at = models.DateTimeField(null=True, blank=True)
    # Language of the app the last time the user signed in or changed it (for the emails).
    language = models.CharField(max_length=2, choices=Language.choices, default=Language.ES)
    # Self-registered accounts confirm their email with a signed link (phase 12); accounts created
    # by an administrator, and the ones that existed before, count as verified.
    email_verified_at = models.DateTimeField(null=True, blank=True)
    # Access tokens issued before it are refused (phase 15): changing or resetting the password
    # ends every session at once, not when their access token expires.
    password_changed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # Grants access to the Django admin site only; API permissions are driven by `role`.
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    @property
    def consent_required(self) -> bool:
        """The current privacy policy (and, for clients, the health data consent) is pending."""
        from django.conf import settings

        if self.privacy_policy_version != settings.PRIVACY_POLICY_VERSION:
            return True
        return self.role == Role.CLIENT and self.health_consent_at is None

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ["last_name", "first_name", "id"]
        constraints = [
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_unique"),
        ]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["status"]),
            models.Index(fields=["date_joined"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_full_name()} <{self.email}>"

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        return self.first_name

    @property
    def is_client(self) -> bool:
        return self.role == Role.CLIENT

    @property
    def is_staff_member(self) -> bool:
        return self.role in STAFF_ROLES


# --- Onboarding answers -------------------------------------------------------------------------


class Goal(models.TextChoices):
    LOSE_WEIGHT = "lose_weight", "Lose weight"
    GAIN_MUSCLE = "gain_muscle", "Gain muscle"
    MAINTAIN = "maintain", "Maintain"


class DailyTrainingTime(models.TextChoices):
    LESS_THAN_1H = "lt_1h", "Less than 1 hour"
    ONE_TO_TWO_HOURS = "1_2h", "1 to 2 hours"
    MORE_THAN_2H = "gt_2h", "More than 2 hours"


class ActivityLevel(models.TextChoices):
    SEDENTARY = "sedentary", "Sedentary"
    LIGHT = "light", "Light"
    MODERATE = "moderate", "Moderate"
    INTENSE = "intense", "Intense"


class ExerciseType(models.TextChoices):
    CARDIO = "cardio", "Cardio"
    STRENGTH = "strength", "Strength"
    FLEXIBILITY = "flexibility", "Flexibility"
    CIRCUIT = "circuit", "Circuit"
    OTHER = "other", "Other"


class Equipment(models.TextChoices):
    FULL_GYM = "full_gym", "Full gym"
    FREE_WEIGHTS = "free_weights", "Free weights"
    CARDIO_MACHINES = "cardio_machines", "Cardio machines"
    NO_EQUIPMENT = "no_equipment", "No equipment"
    OTHER = "other", "Other"


class TrainingPreference(models.TextChoices):
    HOME = "home", "Home"
    GYM = "gym", "Gym"
    OUTDOOR = "outdoor", "Outdoor"
    GROUP_CLASSES = "group_classes", "Group classes"
    OTHER = "other", "Other"


class DietType(models.TextChoices):
    OMNIVORE = "omnivore", "Omnivore"
    VEGETARIAN = "vegetarian", "Vegetarian"
    VEGAN = "vegan", "Vegan"
    LOW_CARB = "low_carb", "Low carb"
    HIGH_PROTEIN = "high_protein", "High protein"
    OTHER = "other", "Other"


class FoodRestriction(models.TextChoices):
    ALLERGIES = "allergies", "Allergies"
    INTOLERANCES = "intolerances", "Intolerances"
    DIETARY_PREFERENCES = "dietary_preferences", "Dietary preferences"
    NONE = "none", "None"


class MacroSelfAssessment(models.TextChoices):
    LOW_PROTEIN = "low_protein", "Low in protein"
    LOW_CARBS = "low_carbs", "Low in carbohydrates"
    LOW_FATS = "low_fats", "Low in fats"
    BALANCED = "balanced", "Balanced"
    UNKNOWN = "unknown", "I don't know"


class MedicalCondition(models.TextChoices):
    DIABETES = "diabetes", "Diabetes"
    HYPERTENSION = "hypertension", "Hypertension"
    JOINT_PROBLEMS = "joint_problems", "Joint problems"
    OTHER = "other", "Other"
    NONE = "none", "None"


class Supplement(models.TextChoices):
    PROTEIN = "protein", "Protein"
    MULTIVITAMIN = "multivitamin", "Multivitamin"
    OMEGA3 = "omega3", "Omega-3"
    OTHER = "other", "Other"
    NONE = "none", "None"


HEIGHT_RANGE_CM = (100, 250)
WEIGHT_RANGE_KG = (30, 300)
TRAINING_DAYS_RANGE = (1, 6)
MEALS_PER_DAY_RANGE = (1, 10)
MAX_TARGET_WEIGHT_CHANGE_KG = 100


class UserDetails(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="details")
    height_cm = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(HEIGHT_RANGE_CM[0]), MaxValueValidator(HEIGHT_RANGE_CM[1])]
    )
    initial_weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(WEIGHT_RANGE_KG[0]), MaxValueValidator(WEIGHT_RANGE_KG[1])],
    )
    goal = models.CharField(max_length=20, choices=Goal.choices)
    target_weight_change_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(MAX_TARGET_WEIGHT_CHANGE_KG)],
    )
    weekly_training_days = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(TRAINING_DAYS_RANGE[0]),
            MaxValueValidator(TRAINING_DAYS_RANGE[1]),
        ]
    )
    daily_training_time = models.CharField(max_length=10, choices=DailyTrainingTime.choices)
    physical_activity_level = models.CharField(max_length=20, choices=ActivityLevel.choices)
    usual_exercise_types = models.JSONField(
        default=list, blank=True, validators=[ChoiceListValidator(ExerciseType)]
    )
    available_equipment = models.JSONField(
        default=list, blank=True, validators=[ChoiceListValidator(Equipment)]
    )
    training_preference = models.CharField(
        max_length=20, choices=TrainingPreference.choices, blank=True
    )
    preferences_text = models.TextField(blank=True)
    # Weekdays picked by the client (Monday = 0); empty means the default calendar.
    training_days = models.JSONField(default=list, blank=True)
    # Reminders (phase 12): time of day the client trains (null = DEFAULT_TRAINING_TIME), opt-in
    # email on training days and the day of the last one sent (one per day at most).
    training_time = models.TimeField(null=True, blank=True)
    reminders_enabled = models.BooleanField(default=False)
    last_reminder_on = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "user details"

    def __str__(self) -> str:
        return f"Details of user {self.user_id}"

    def save(self, *args, **kwargs):
        # Chosen days only make sense for the number of weekly days they were picked for.
        if self.training_days and len(self.training_days) != self.weekly_training_days:
            self.training_days = []
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = {*kwargs["update_fields"], "training_days"}
        super().save(*args, **kwargs)

    @property
    def target_weight_kg(self):
        if self.goal == Goal.LOSE_WEIGHT:
            return self.initial_weight_kg - self.target_weight_change_kg
        if self.goal == Goal.GAIN_MUSCLE:
            return self.initial_weight_kg + self.target_weight_change_kg
        return self.initial_weight_kg


class DietPreferences(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="diet_preferences")
    diet_type = models.CharField(max_length=20, choices=DietType.choices)
    food_restrictions = models.JSONField(
        default=list, blank=True, validators=[ChoiceListValidator(FoodRestriction)]
    )
    custom_food_restrictions = models.TextField(blank=True)
    meals_per_day = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MEALS_PER_DAY_RANGE[0]),
            MaxValueValidator(MEALS_PER_DAY_RANGE[1]),
        ]
    )
    macronutrient_intake_self_assessment = models.CharField(
        max_length=20, choices=MacroSelfAssessment.choices
    )

    class Meta:
        verbose_name_plural = "diet preferences"

    def __str__(self) -> str:
        return f"Diet preferences of user {self.user_id}"


class HealthInfo(TimeStampedModel):
    """Called «MedicalConditions» in the original ER diagram."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="health_info")
    medical_conditions = models.JSONField(
        default=list, blank=True, validators=[ChoiceListValidator(MedicalCondition)]
    )
    custom_medical_condition = models.TextField(blank=True)
    supplements = models.JSONField(
        default=list, blank=True, validators=[ChoiceListValidator(Supplement)]
    )

    class Meta:
        verbose_name_plural = "health info"

    def __str__(self) -> str:
        return f"Health info of user {self.user_id}"


class HealthDataAccess(TimeStampedModel):
    """A professional was shown a client's health answers (GDPR art. 9 accountability, phase 15).

    Who, whom and when; never the values. It goes with the client's account when it is deleted, and
    the client finds it in the data download.
    """

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="health_data_accesses")
    staff = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    # Snapshot: the record still says who it was if the professional's account is deleted.
    staff_role = models.CharField(max_length=20, choices=Role.choices)
    staff_name = models.CharField(max_length=150)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["client", "-created_at"])]
        verbose_name_plural = "health data accesses"

    def __str__(self) -> str:
        return f"{self.staff_name} saw the health data of user {self.client_id}"
