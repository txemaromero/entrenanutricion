from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import get_error_detail

from apps.accounts.models import (
    MAX_TARGET_WEIGHT_CHANGE_KG,
    TRAINING_DAYS_RANGE,
    WEIGHT_RANGE_KG,
    ActivityLevel,
    DietPreferences,
    Equipment,
    ExerciseType,
    FoodRestriction,
    Gender,
    Goal,
    HealthDataAccess,
    HealthInfo,
    Language,
    MedicalCondition,
    Role,
    Supplement,
    TrainingPreference,
    User,
    UserDetails,
)
from apps.accounts.selectors import current_weight_kg, plan_flags
from apps.core.files import validate_image_file
from apps.core.images import PHOTO_MAX_PX, optimize_image
from apps.core.serializers import ChoiceListField
from apps.core.translation import localized
from apps.core.utils import FileUrlField
from apps.core.validators import age_on, validate_adult_age, validate_person_name


def person_name_field(**kwargs):
    return serializers.CharField(max_length=150, validators=[validate_person_name], **kwargs)


def weight_field(**kwargs):
    return serializers.DecimalField(
        max_digits=5,
        decimal_places=1,
        min_value=WEIGHT_RANGE_KG[0],
        max_value=WEIGHT_RANGE_KG[1],
        **kwargs,
    )


def check_password_strength(password: str, user=None) -> str:
    try:
        password_validation.validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(get_error_detail(exc)) from exc
    return password


# Far beyond any real password, and short enough that hashing it costs nothing extra.
MAX_PASSWORD_LENGTH = 128


def email_is_taken(email: str, exclude_pk=None) -> bool:
    queryset = User.objects.filter(email__iexact=email.strip())
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    return queryset.exists()


# --- Auth ----------------------------------------------------------------------------------------


class RegisterSerializer(serializers.Serializer):
    first_name = person_name_field()
    last_name = person_name_field()
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=MAX_PASSWORD_LENGTH
    )
    birth_date = serializers.DateField()
    gender = serializers.ChoiceField(choices=Gender.choices)
    terms_accepted = serializers.BooleanField()
    health_data_consent = serializers.BooleanField(
        help_text="Explicit consent to process health data (GDPR art. 9.2.a)."
    )

    def validate_email(self, value):
        value = value.strip().lower()
        if email_is_taken(value):
            raise serializers.ValidationError(
                "This email is already registered.", code="email_taken"
            )
        return value

    def validate_password(self, value):
        return check_password_strength(value)

    def validate(self, attrs):
        # The account does not exist yet: the password is compared with the name and email it will
        # have (password_too_similar), on a provisional, unsaved user.
        candidate = User(
            email=attrs["email"], first_name=attrs["first_name"], last_name=attrs["last_name"]
        )
        try:
            check_password_strength(attrs["password"], candidate)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({"password": exc.detail}) from exc
        return attrs

    def validate_birth_date(self, value):
        validate_adult_age(value, timezone.localdate())
        return value

    def validate_terms_accepted(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must accept the terms and conditions.", code="terms_required"
            )
        return value

    def validate_health_data_consent(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must consent to the use of your health data.", code="health_consent_required"
            )
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, max_length=MAX_PASSWORD_LENGTH)
    remember_me = serializers.BooleanField(default=False)


class AccessTokenSerializer(serializers.Serializer):
    """The refresh token is never in a body: it travels in the httpOnly cookie."""

    access = serializers.CharField()


class EmailExistsQuerySerializer(serializers.Serializer):
    email = serializers.EmailField()


# --- Current user --------------------------------------------------------------------------------


class MeDetailsSerializer(serializers.ModelSerializer):
    target_weight_kg = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    current_weight_kg = serializers.SerializerMethodField()

    class Meta:
        model = UserDetails
        fields = [
            "height_cm",
            "initial_weight_kg",
            "current_weight_kg",
            "target_weight_kg",
            "target_weight_change_kg",
            "goal",
            "physical_activity_level",
            "weekly_training_days",
            "daily_training_time",
        ]

    def get_current_weight_kg(self, details) -> float | None:
        weight = current_weight_kg(details.user)
        return float(weight) if weight is not None else None


class MeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    consent_required = serializers.BooleanField(read_only=True)
    age = serializers.SerializerMethodField()
    profile_photo_url = FileUrlField(source="profile_photo")
    onboarding_completed = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()
    has_training_plan = serializers.SerializerMethodField()
    has_nutrition_plan = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "birth_date",
            "age",
            "gender",
            "role",
            "status",
            "profile_photo_url",
            "onboarding_completed",
            "has_training_plan",
            "has_nutrition_plan",
            "consent_required",
            "email_verified",
            "language",
            "details",
            "date_joined",
        ]

    def _flags(self, user) -> tuple[bool, bool]:
        if not hasattr(self, "_plan_flags_cache"):
            self._plan_flags_cache = plan_flags(user)
        return self._plan_flags_cache

    def get_age(self, user) -> int | None:
        return age_on(user.birth_date, timezone.localdate()) if user.birth_date else None

    def get_email_verified(self, user) -> bool:
        return user.email_verified_at is not None

    def get_onboarding_completed(self, user) -> bool:
        return hasattr(user, "details")

    def get_has_training_plan(self, user) -> bool:
        return self._flags(user)[0]

    def get_has_nutrition_plan(self, user) -> bool:
        return self._flags(user)[1]

    def get_details(self, user) -> dict | None:
        details = getattr(user, "details", None)
        return MeDetailsSerializer(details).data if details else None


class ProfileUpdateSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=Language.choices, required=False)
    first_name = person_name_field(required=False)
    last_name = person_name_field(required=False)
    current_weight_kg = weight_field(required=False)
    goal = serializers.ChoiceField(choices=Goal.choices, required=False)
    physical_activity_level = serializers.ChoiceField(choices=ActivityLevel.choices, required=False)
    weekly_training_days = serializers.IntegerField(
        min_value=TRAINING_DAYS_RANGE[0], max_value=TRAINING_DAYS_RANGE[1], required=False
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


def passwords_match(attrs, field: str = "new_password") -> None:
    if attrs[field] != attrs["confirm_password"]:
        raise serializers.ValidationError(
            {
                "confirm_password": serializers.ErrorDetail(
                    "The passwords do not match.", code="passwords_do_not_match"
                )
            }
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Checks the emailed link (uid + token) and the new password."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(trim_whitespace=False, max_length=MAX_PASSWORD_LENGTH)
    confirm_password = serializers.CharField(trim_whitespace=False, max_length=MAX_PASSWORD_LENGTH)

    def validate(self, attrs):
        user = self._user_from_uid(attrs["uid"])
        if user is None or not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError(
                "The link is not valid or has expired. Request a new one.",
                code="reset_link_invalid",
            )
        try:
            check_password_strength(attrs["new_password"], user)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({"new_password": exc.detail}) from exc
        passwords_match(attrs)
        attrs["user"] = user
        return attrs

    @staticmethod
    def _user_from_uid(uid: str):
        try:
            pk = force_str(urlsafe_base64_decode(uid))
            return User.objects.filter(pk=int(pk), is_active=True).first()
        except (TypeError, ValueError, OverflowError):
            return None


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(trim_whitespace=False, max_length=MAX_PASSWORD_LENGTH)
    new_password = serializers.CharField(trim_whitespace=False, max_length=MAX_PASSWORD_LENGTH)
    confirm_password = serializers.CharField(trim_whitespace=False, max_length=MAX_PASSWORD_LENGTH)

    def validate_current_password(self, value):
        if not self.context["user"].check_password(value):
            raise serializers.ValidationError(
                "The current password is incorrect.", code="current_password_incorrect"
            )
        return value

    def validate_new_password(self, value):
        return check_password_strength(value, self.context["user"])

    def validate(self, attrs):
        passwords_match(attrs)
        return attrs


class PhotoUploadSerializer(serializers.Serializer):
    photo = serializers.FileField(validators=[validate_image_file])

    def validate_photo(self, value):
        return optimize_image(value, PHOTO_MAX_PX)


# --- Onboarding ----------------------------------------------------------------------------------


class DietPreferencesSerializer(serializers.ModelSerializer):
    food_restrictions = ChoiceListField(FoodRestriction)

    class Meta:
        model = DietPreferences
        fields = [
            "diet_type",
            "food_restrictions",
            "custom_food_restrictions",
            "meals_per_day",
            "macronutrient_intake_self_assessment",
        ]
        extra_kwargs = {"custom_food_restrictions": {"required": False, "allow_blank": True}}

    def validate(self, attrs):
        restrictions = attrs.get("food_restrictions", [])
        if restrictions and FoodRestriction.NONE not in restrictions:
            if not attrs.get("custom_food_restrictions", "").strip():
                raise serializers.ValidationError(
                    {
                        "custom_food_restrictions": serializers.ErrorDetail(
                            "Describe your food restrictions.", code="required"
                        )
                    }
                )
        else:
            attrs["custom_food_restrictions"] = ""
        return attrs


class HealthInfoSerializer(serializers.ModelSerializer):
    medical_conditions = ChoiceListField(MedicalCondition)
    supplements = ChoiceListField(Supplement)

    class Meta:
        model = HealthInfo
        fields = ["medical_conditions", "custom_medical_condition", "supplements"]
        extra_kwargs = {"custom_medical_condition": {"required": False, "allow_blank": True}}

    def validate(self, attrs):
        if MedicalCondition.OTHER in attrs.get("medical_conditions", []):
            if not attrs.get("custom_medical_condition", "").strip():
                raise serializers.ValidationError(
                    {
                        "custom_medical_condition": serializers.ErrorDetail(
                            "Describe your medical condition.", code="required"
                        )
                    }
                )
        else:
            attrs["custom_medical_condition"] = ""
        return attrs


class OnboardingSerializer(serializers.ModelSerializer):
    initial_weight_kg = weight_field()
    target_weight_change_kg = serializers.DecimalField(
        max_digits=5,
        decimal_places=1,
        min_value=0,
        max_value=MAX_TARGET_WEIGHT_CHANGE_KG,
        required=False,
        default=0,
    )
    usual_exercise_types = ChoiceListField(ExerciseType, exclusive=())
    available_equipment = ChoiceListField(Equipment, exclusive=(Equipment.NO_EQUIPMENT,))
    training_preference = serializers.ChoiceField(choices=TrainingPreference.choices)
    diet = DietPreferencesSerializer(source="user.diet_preferences")
    health = HealthInfoSerializer(source="user.health_info")
    target_weight_kg = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)

    class Meta:
        model = UserDetails
        fields = [
            "height_cm",
            "initial_weight_kg",
            "goal",
            "target_weight_change_kg",
            "target_weight_kg",
            "weekly_training_days",
            "daily_training_time",
            "physical_activity_level",
            "usual_exercise_types",
            "available_equipment",
            "training_preference",
            "preferences_text",
            "training_days",
            "diet",
            "health",
        ]
        extra_kwargs = {
            "preferences_text": {"required": False, "allow_blank": True},
            # Picked from the training plan (PUT /me/training-days), not in the onboarding form.
            "training_days": {"read_only": True},
        }

    def validate(self, attrs):
        goal = attrs.get("goal")
        change = attrs.get("target_weight_change_kg") or 0
        initial = attrs.get("initial_weight_kg")
        if goal == Goal.MAINTAIN:
            attrs["target_weight_change_kg"] = 0
        elif change <= 0:
            raise serializers.ValidationError(
                {
                    "target_weight_change_kg": serializers.ErrorDetail(
                        "Indicate how many kilograms you want to lose or gain.", code="required"
                    )
                }
            )
        elif initial is not None:
            target = initial - change if goal == Goal.LOSE_WEIGHT else initial + change
            low, high = WEIGHT_RANGE_KG
            if not low <= target <= high:
                raise serializers.ValidationError(
                    {
                        "target_weight_change_kg": serializers.ErrorDetail(
                            "The resulting target weight is out of range.", code="out_of_range"
                        )
                    }
                )
        # Nested sources ("user.diet_preferences") come back nested under "user".
        nested = attrs.pop("user", {})
        attrs["diet"] = nested.get("diet_preferences", {})
        attrs["health"] = nested.get("health_info", {})
        return attrs


# --- User management -----------------------------------------------------------------------------


class PlanRefSerializer(serializers.Serializer):
    """A training or nutrition plan (a model instance or a dict) with its name in the language."""

    id = serializers.IntegerField()
    name = serializers.CharField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not isinstance(instance, dict):
            data["name"] = localized(instance, "name")
        return data


def _current(user, attr: str):
    """Current assignment from the `current_*` prefetch (a list of 0 or 1 items)."""
    items = getattr(user, attr, None)
    return items[0] if items else None


def _plan_ref(assignment) -> dict | None:
    if assignment is None:
        return None
    return {"id": assignment.plan_id, "name": localized(assignment.plan, "name")}


class UserListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    profile_photo_url = FileUrlField(source="profile_photo")
    training_plan = serializers.SerializerMethodField()
    nutrition_plan = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "status",
            "profile_photo_url",
            "training_plan",
            "nutrition_plan",
            "date_joined",
        ]

    @extend_schema_field(PlanRefSerializer(allow_null=True))
    def get_training_plan(self, user):
        return _plan_ref(_current(user, "current_training"))

    @extend_schema_field(PlanRefSerializer(allow_null=True))
    def get_nutrition_plan(self, user):
        return _plan_ref(_current(user, "current_nutrition"))


class WeightPointSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    date = serializers.DateField()
    weight_kg = serializers.FloatField()


class TrainingAssignmentInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    plan = PlanRefSerializer()
    cycle = serializers.IntegerField()
    progress = serializers.IntegerField()
    date_started = serializers.DateField()


class NutritionAssignmentInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    plan = PlanRefSerializer()
    date_assigned = serializers.DateField()


class UserDetailSerializer(UserListSerializer):
    """Full profile for staff: onboarding answers, weight history and current plans."""

    age = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()
    onboarding = serializers.SerializerMethodField()
    weight_records = serializers.SerializerMethodField()
    training_assignment = serializers.SerializerMethodField()
    nutrition_assignment = serializers.SerializerMethodField()

    class Meta(UserListSerializer.Meta):
        fields = [
            *UserListSerializer.Meta.fields,
            "birth_date",
            "age",
            "gender",
            "details",
            "onboarding",
            "weight_records",
            "training_assignment",
            "nutrition_assignment",
        ]

    def get_age(self, user) -> int | None:
        return age_on(user.birth_date, timezone.localdate()) if user.birth_date else None

    @extend_schema_field(MeDetailsSerializer(allow_null=True))
    def get_details(self, user):
        details = getattr(user, "details", None)
        return MeDetailsSerializer(details).data if details else None

    @extend_schema_field(OnboardingSerializer(allow_null=True))
    def get_onboarding(self, user):
        details = getattr(user, "details", None)
        return OnboardingSerializer(details).data if details else None

    @extend_schema_field(WeightPointSerializer(many=True))
    def get_weight_records(self, user):
        return [
            {"id": record.id, "date": record.date, "weight_kg": float(record.weight_kg)}
            for record in user.weight_records.all()
        ]

    @extend_schema_field(TrainingAssignmentInfoSerializer(allow_null=True))
    def get_training_assignment(self, user):
        assignment = _current(user, "current_training")
        if assignment is None:
            return None
        return {
            "id": assignment.id,
            "plan": _plan_ref(assignment),
            "cycle": assignment.cycle,
            "progress": assignment.progress,
            "date_started": assignment.date_started,
        }

    @extend_schema_field(NutritionAssignmentInfoSerializer(allow_null=True))
    def get_nutrition_assignment(self, user):
        assignment = _current(user, "current_nutrition")
        if assignment is None:
            return None
        return {
            "id": assignment.id,
            "plan": _plan_ref(assignment),
            "date_assigned": assignment.date_assigned,
        }


class HealthDataAccessSerializer(serializers.ModelSerializer):
    """Who of the team was shown a client's health answers, and when (never the values)."""

    accessed_at = serializers.DateTimeField(source="created_at")

    class Meta:
        model = HealthDataAccess
        fields = ["id", "staff", "staff_name", "staff_role", "accessed_at"]


class UserCreateSerializer(RegisterSerializer):
    """Admin creates any role; every field is required. The user accepts the terms, the privacy
    policy and (clients) the health data consent on first use (consent_required)."""

    role = serializers.ChoiceField(choices=Role.choices)
    terms_accepted = None
    health_data_consent = None


class UserUpdateSerializer(ProfileUpdateSerializer):
    role = serializers.ChoiceField(choices=Role.choices, required=False)
    photo = serializers.FileField(required=False, validators=[validate_image_file])

    def validate_photo(self, value):
        return optimize_image(value, PHOTO_MAX_PX)


class ConsentSerializer(serializers.Serializer):
    privacy_policy = serializers.BooleanField()
    health_data = serializers.BooleanField(required=False, default=False)

    def validate_privacy_policy(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must accept the privacy policy.", code="privacy_required"
            )
        return value


class AccountDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(trim_whitespace=False, max_length=MAX_PASSWORD_LENGTH)

    def validate_password(self, value):
        if not self.context["user"].check_password(value):
            raise serializers.ValidationError(
                "The password is incorrect.", code="current_password_incorrect"
            )
        return value


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=500)


class EmailVerifiedSerializer(serializers.Serializer):
    email_verified = serializers.BooleanField()
