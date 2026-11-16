from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role, User
from apps.assignments import selectors, services
from apps.assignments.serializers import (
    AssignPlanInputSerializer,
    NutritionAssignmentSerializer,
    PendingUserSerializer,
    TrainingAssignmentSerializer,
    get_meal_plan,
    get_training_plan,
)
from apps.core.permissions import IsNutritionistOrAdmin, IsStaff, IsTrainerOrAdmin


def get_client(pk: int) -> User:
    return get_object_or_404(User, pk=pk, role=Role.CLIENT, is_active=True)


class PendingAssignmentsView(generics.ListAPIView):
    """Clients waiting for plans: trainers see those without a training plan, nutritionists
    those without a nutrition plan and admins both (each row says what is `missing`)."""

    permission_classes = [IsStaff]
    serializer_class = PendingUserSerializer
    search_fields = ["first_name", "last_name", "email"]
    ordering_fields = ["date_joined", "last_name"]
    ordering = ["date_joined", "id"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # schema generation
            return User.objects.none()
        return selectors.pending_clients(self.request.user.role)


class AssignTrainingPlanView(APIView):
    permission_classes = [IsTrainerOrAdmin]

    @extend_schema(request=AssignPlanInputSerializer, responses={201: TrainingAssignmentSerializer})
    def post(self, request, pk: int):
        user = get_client(pk)
        data = AssignPlanInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        plan = get_training_plan(data.validated_data["plan_id"])
        assignment = services.assign_training_plan(
            user, plan, request.user, replace=data.validated_data["replace"]
        )
        return Response(
            TrainingAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED
        )


class AssignNutritionPlanView(APIView):
    permission_classes = [IsNutritionistOrAdmin]

    @extend_schema(
        request=AssignPlanInputSerializer, responses={201: NutritionAssignmentSerializer}
    )
    def post(self, request, pk: int):
        user = get_client(pk)
        data = AssignPlanInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        plan = get_meal_plan(data.validated_data["plan_id"])
        assignment = services.assign_nutrition_plan(
            user, plan, request.user, replace=data.validated_data["replace"]
        )
        return Response(
            NutritionAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED
        )
