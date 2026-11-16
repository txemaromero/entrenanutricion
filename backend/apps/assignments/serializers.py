from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.serializers import PlanRefSerializer
from apps.core.utils import FileUrlField
from apps.nutrition.models import MealPlan, UserNutritionPlan
from apps.training.models import TrainingPlan, UserTrainingPlan


class AssignPlanInputSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    replace = serializers.BooleanField(default=False)


class TrainingAssignmentSerializer(serializers.ModelSerializer):
    plan = PlanRefSerializer(read_only=True)
    user_status = serializers.CharField(source="user.status", read_only=True)

    class Meta:
        model = UserTrainingPlan
        fields = [
            "id",
            "user_id",
            "plan",
            "assigned_by_id",
            "date_started",
            "cycle",
            "progress",
            "is_current",
            "user_status",
        ]


class NutritionAssignmentSerializer(serializers.ModelSerializer):
    plan = PlanRefSerializer(read_only=True)
    user_status = serializers.CharField(source="user.status", read_only=True)

    class Meta:
        model = UserNutritionPlan
        fields = [
            "id",
            "user_id",
            "plan",
            "assigned_by_id",
            "date_assigned",
            "is_current",
            "user_status",
        ]


def get_plan(model, plan_id: int):
    plan = model.objects.filter(pk=plan_id).first()
    if plan is None:
        raise serializers.ValidationError(
            {"plan_id": [serializers.ErrorDetail("Unknown plan.", code="does_not_exist")]}
        )
    return plan


def get_training_plan(plan_id: int) -> TrainingPlan:
    return get_plan(TrainingPlan, plan_id)


def get_meal_plan(plan_id: int) -> MealPlan:
    return get_plan(MealPlan, plan_id)


class PendingUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    profile_photo_url = FileUrlField(source="profile_photo")
    goal = serializers.CharField(source="details.goal", read_only=True)
    weekly_training_days = serializers.IntegerField(
        source="details.weekly_training_days", read_only=True
    )
    missing = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "profile_photo_url",
            "goal",
            "weekly_training_days",
            "date_joined",
            "missing",
        ]

    @extend_schema_field(
        serializers.ListField(child=serializers.ChoiceField(["training", "nutrition"]))
    )
    def get_missing(self, user):
        missing = []
        if not user.has_training:
            missing.append("training")
        if not user.has_nutrition:
            missing.append("nutrition")
        return missing
