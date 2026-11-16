from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdmin
from apps.statistics import services


class YearQuerySerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=2000, max_value=2100, required=False)
    limit = serializers.IntegerField(min_value=1, max_value=50, required=False, default=10)


class PopularityRowSerializer(serializers.Serializer):
    exercise_id = serializers.IntegerField()
    name = serializers.CharField()
    count = serializers.IntegerField()


class PopularitySerializer(serializers.Serializer):
    year = serializers.IntegerField()
    results = PopularityRowSerializer(many=True)


class GrowthRowSerializer(serializers.Serializer):
    month = serializers.IntegerField()
    count = serializers.IntegerField()


class GrowthSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    months = GrowthRowSerializer(many=True)


class UsersByRoleSerializer(serializers.Serializer):
    client = serializers.IntegerField()
    admin = serializers.IntegerField()
    trainer = serializers.IntegerField()
    nutritionist = serializers.IntegerField()


class ClientsByGoalSerializer(serializers.Serializer):
    lose_weight = serializers.IntegerField()
    gain_muscle = serializers.IntegerField()
    maintain = serializers.IntegerField()


class SummarySerializer(serializers.Serializer):
    users_by_role = UsersByRoleSerializer()
    active_clients = serializers.IntegerField()
    pending_assignment = serializers.IntegerField()
    pending_onboarding = serializers.IntegerField()
    sessions_this_month = serializers.IntegerField()
    sessions_previous_period = serializers.IntegerField(
        help_text="Sessions of the same days of the previous month (1st to today's day)."
    )
    new_clients_this_month = serializers.IntegerField()
    new_clients_previous_period = serializers.IntegerField(
        help_text="Clients who signed up on the same days of the previous month."
    )
    clients_by_goal = ClientsByGoalSerializer(help_text="Active clients per goal.")


class PlanPopularityRowSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    name = serializers.CharField()
    count = serializers.IntegerField(help_text="Clients with this plan assigned right now.")


class PlanPopularitySerializer(serializers.Serializer):
    training = PlanPopularityRowSerializer(many=True)
    nutrition = PlanPopularityRowSerializer(many=True)


class YearsSerializer(serializers.Serializer):
    years = serializers.ListField(child=serializers.IntegerField())


YEAR = OpenApiParameter("year", int, description="Defaults to the current year.")


def read_query(request) -> dict:
    query = YearQuerySerializer(data=request.query_params)
    query.is_valid(raise_exception=True)
    return {
        "year": query.validated_data.get("year") or timezone.localdate().year,
        "limit": query.validated_data["limit"],
    }


class ExercisePopularityView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        parameters=[YEAR, OpenApiParameter("limit", int, description="1–50, default 10.")],
        responses=PopularitySerializer,
    )
    def get(self, request):
        query = read_query(request)
        results = services.exercise_popularity(query["year"], query["limit"])
        return Response({"year": query["year"], "results": results})


class PlatformGrowthView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(parameters=[YEAR], responses=GrowthSerializer)
    def get(self, request):
        year = read_query(request)["year"]
        return Response({"year": year, "months": services.platform_growth(year)})


class SessionsPerMonthView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(parameters=[YEAR], responses=GrowthSerializer)
    def get(self, request):
        year = read_query(request)["year"]
        return Response({"year": year, "months": services.sessions_per_month(year)})


class PlanPopularityView(APIView):
    """Training and nutrition plans with the most clients right now."""

    permission_classes = [IsAdmin]

    @extend_schema(
        parameters=[OpenApiParameter("limit", int, description="1–50, default 10.")],
        responses=PlanPopularitySerializer,
    )
    def get(self, request):
        return Response(services.plan_popularity(read_query(request)["limit"]))


class SummaryView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(responses=SummarySerializer)
    def get(self, request):
        return Response(services.summary())


class YearsView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(responses=YearsSerializer)
    def get(self, request):
        return Response({"years": services.years_with_data()})
