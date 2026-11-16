from collections import Counter

import django_filters
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services import record_health_data_accesses
from apps.core.pagination import DefaultLimitOffsetPagination
from apps.core.permissions import IsClient, IsStaff
from apps.progress import adherence, services
from apps.progress.badges import badges_overview, sync_badges
from apps.progress.serializers import (
    AdherenceListSerializer,
    AdherenceQuerySerializer,
    AdherenceRowSerializer,
    BadgesSerializer,
    ClientAdherenceSerializer,
    DashboardQuerySerializer,
    DashboardSerializer,
    SessionHistorySerializer,
    TrainingStatsSerializer,
    WeightRecordInputSerializer,
    WeightRecordResultSerializer,
    WeightSummarySerializer,
)
from apps.progress.stats import training_stats
from apps.training.models import WorkoutSession


class DashboardView(APIView):
    permission_classes = [IsClient]

    @extend_schema(
        parameters=[OpenApiParameter("month", str, description="Month to show, YYYY-MM.")],
        responses=DashboardSerializer,
    )
    def get(self, request):
        query = DashboardQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        year, month = query.validated_data.get("month") or (None, None)
        return Response(DashboardSerializer(services.dashboard(request.user, year, month)).data)


class SessionHistoryFilter(django_filters.FilterSet):
    # `from`/`to` are inclusive local dates.
    date_from = django_filters.DateFilter(
        field_name="completed_at", lookup_expr="date__gte", label="from"
    )
    date_to = django_filters.DateFilter(
        field_name="completed_at", lookup_expr="date__lte", label="to"
    )
    workout = django_filters.NumberFilter(field_name="workout_id")

    class Meta:
        model = WorkoutSession
        fields = ["workout"]

    def __init__(self, data=None, *args, **kwargs):
        if data is not None:
            data = data.copy()
            for public, internal in (("from", "date_from"), ("to", "date_to")):
                if public in data:
                    data[internal] = data[public]
        super().__init__(data, *args, **kwargs)


@extend_schema(
    parameters=[
        OpenApiParameter("from", str, description="First day (YYYY-MM-DD), inclusive."),
        OpenApiParameter("to", str, description="Last day (YYYY-MM-DD), inclusive."),
    ]
)
class SessionHistoryView(generics.ListAPIView):
    permission_classes = [IsClient]
    serializer_class = SessionHistorySerializer
    filterset_class = SessionHistoryFilter
    ordering_fields = ["completed_at"]
    search_fields: list[str] = []

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # schema generation
            return WorkoutSession.objects.none()
        return services.session_history(self.request.user)


class TrainingStatsView(APIView):
    """Sessions, minutes and volume per week, and the muscle groups worked lately."""

    permission_classes = [IsClient]

    @extend_schema(responses=TrainingStatsSerializer)
    def get(self, request):
        return Response(TrainingStatsSerializer(training_stats(request.user)).data)


class WeightRecordsView(APIView):
    permission_classes = [IsClient]

    @extend_schema(responses=WeightSummarySerializer)
    def get(self, request):
        return Response(WeightSummarySerializer(services.weight_summary(request.user)).data)

    @extend_schema(
        request=WeightRecordInputSerializer, responses={201: WeightRecordResultSerializer}
    )
    def post(self, request):
        services.require_details(request.user)
        data = WeightRecordInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        services.record_weight(
            request.user, data.validated_data["weight_kg"], data.validated_data.get("date")
        )
        # The whole series is returned so the chart can redraw at once (regression #7).
        summary = services.weight_summary(request.user)
        result = {**summary, "new_badges": sync_badges(request.user)}
        return Response(WeightRecordResultSerializer(result).data, status=status.HTTP_201_CREATED)


class BadgesView(APIView):
    """Badges of the client with their progress (gamification, phase 9)."""

    permission_classes = [IsClient]

    @extend_schema(responses=BadgesSerializer)
    def get(self, request):
        return Response(BadgesSerializer(badges_overview(request.user)).data)


def shown_weights(rows) -> list:
    """Clients whose rows show a weight (or its change)."""
    return [
        row["user"]
        for row in rows
        if row["current_weight_kg"] is not None or row["weight_change_kg"] is not None
    ]


class AdherenceListView(APIView):
    """Staff: clients with a plan, worst adherence first, with the count per status."""

    permission_classes = [IsStaff]

    @extend_schema(parameters=[AdherenceQuerySerializer], responses=AdherenceListSerializer)
    def get(self, request):
        query = AdherenceQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        rows = adherence.adherence_rows(
            adherence.clients_with_plan(query.validated_data.get("search", ""))
        )
        counts = Counter(row["status"] for row in rows)
        bands, average = adherence.distribution(rows), adherence.average_percent(rows)
        if status_filter := query.validated_data.get("status"):
            rows = [row for row in rows if row["status"] == status_filter]
        paginator = DefaultLimitOffsetPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        # Their weight is health data (D-83): logged for the clients of the page that show one.
        record_health_data_accesses(request.user, shown_weights(page))
        return Response(
            {
                "count": paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "counts": [
                    {"status": name, "count": counts.get(name, 0)} for name in adherence.STATUSES
                ],
                "distribution": bands,
                "average_percent": average,
                "results": AdherenceRowSerializer(
                    page, many=True, context={"request": request}
                ).data,
            }
        )


class ClientAdherenceView(APIView):
    """Staff: adherence of one client with the last four weeks."""

    permission_classes = [IsStaff]

    @extend_schema(responses=ClientAdherenceSerializer)
    def get(self, request, pk: int):
        row = adherence.client_adherence(pk)
        record_health_data_accesses(request.user, shown_weights([row]))
        return Response(ClientAdherenceSerializer(row, context={"request": request}).data)
