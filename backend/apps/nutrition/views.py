import django_filters
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role, User
from apps.accounts.services import record_health_data_access
from apps.core.exceptions import NotFoundError
from apps.core.permissions import (
    AuthenticatedReadNutritionistWrite,
    IsClient,
    IsStaff,
    StaffReadNutritionistWrite,
)
from apps.core.translation import localized, order_by_localized_name
from apps.nutrition import diary, menus, services
from apps.nutrition.models import Food, FoodCategory, FoodLogEntry, MealPlan, MealPlanCategory
from apps.nutrition.serializers import (
    CopyMenuInputSerializer,
    DiaryDaySerializer,
    DiaryQuerySerializer,
    DiarySummaryQuerySerializer,
    DiarySummarySerializer,
    FoodLogEntryInputSerializer,
    FoodLogEntryUpdateSerializer,
    FoodSerializer,
    MealPlanListSerializer,
    MealPlanSerializer,
    MenuInputSerializer,
    MenuSerializer,
    MyNutritionPlanSerializer,
    ShoppingListQuerySerializer,
    ShoppingListSerializer,
)


class FoodFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(choices=FoodCategory.choices)

    class Meta:
        model = Food
        fields = ["category"]


class FoodViewSet(viewsets.ModelViewSet):
    """Food library (per 100 g). Foods are not referenced by plans, so deleting is permanent."""

    permission_classes = [AuthenticatedReadNutritionistWrite]
    serializer_class = FoodSerializer
    filterset_class = FoodFilter
    search_fields = ["name", "translations"]
    ordering_fields = ["name", "calories", "proteins_g", "carbs_g", "fats_g"]

    def get_queryset(self):
        return order_by_localized_name(Food.objects.all())

    def perform_destroy(self, instance):
        services.delete_food(instance)


class MealPlanFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(choices=MealPlanCategory.choices)

    class Meta:
        model = MealPlan
        fields = ["category", "diet_label"]


@extend_schema(
    parameters=[OpenApiParameter("include_inactive", bool, description="Also list deleted plans.")]
)
class MealPlanViewSet(viewsets.ModelViewSet):
    permission_classes = [StaffReadNutritionistWrite]
    filterset_class = MealPlanFilter
    search_fields = ["name", "description", "translations"]
    ordering_fields = ["name", "calories", "created_at"]

    def get_queryset(self):
        queryset = order_by_localized_name(MealPlan.objects.all())
        include_inactive = self.request.query_params.get("include_inactive", "").lower()
        if self.action == "list" and include_inactive not in {"1", "true", "yes"}:
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_serializer_class(self):
        return MealPlanListSerializer if self.action == "list" else MealPlanSerializer

    def perform_destroy(self, instance):
        services.delete_meal_plan(instance)

    @extend_schema(methods=["GET"], responses=MenuSerializer)
    @extend_schema(methods=["PUT"], request=MenuInputSerializer, responses=MenuSerializer)
    @action(detail=True, methods=["get", "put"], url_path="menu")
    def menu(self, request, pk=None):
        """Sample day menu of the plan (nutritionists and admins edit it)."""
        plan = self.get_object()
        if request.method == "GET":
            return Response(MenuSerializer(menus.menu_of(plan)).data)
        data = MenuInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(MenuSerializer(menus.set_menu(plan, data.validated_data["items"])).data)


class MyNutritionPlanView(APIView):
    permission_classes = [IsClient]

    @extend_schema(responses=MyNutritionPlanSerializer)
    def get(self, request):
        assignment = services.get_current_assignment(request.user)
        plan = assignment.plan
        payload = {
            "id": plan.id,
            "name": localized(plan, "name"),
            "category": plan.category,
            "diet_label": plan.diet_label,
            "description": localized(plan, "description"),
            "calories": plan.calories,
            "date_assigned": assignment.date_assigned,
            "macros": services.macro_breakdown(plan),
            "meals": services.meal_breakdown(plan),
        }
        return Response(MyNutritionPlanSerializer(payload).data)


class MyMenuView(APIView):
    """The sample day menu of the client's current plan."""

    permission_classes = [IsClient]

    @extend_schema(responses=MenuSerializer)
    def get(self, request):
        plan = services.get_current_assignment(request.user).plan
        return Response(MenuSerializer(menus.menu_of(plan)).data)


class MyShoppingListView(APIView):
    """Foods of the menu for some days, with the total grams of each."""

    permission_classes = [IsClient]

    @extend_schema(parameters=[ShoppingListQuerySerializer], responses=ShoppingListSerializer)
    def get(self, request):
        query = ShoppingListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        plan = services.get_current_assignment(request.user).plan
        result = menus.shopping_list(plan, query.validated_data["days"])
        return Response(ShoppingListSerializer(result).data)


def _day_response(user, on_date, status_code=status.HTTP_200_OK):
    return Response(DiaryDaySerializer(diary.day_log(user, on_date)).data, status=status_code)


class MyFoodLogView(APIView):
    """The diary of one day (today by default) and new entries."""

    permission_classes = [IsClient]

    @extend_schema(parameters=[DiaryQuerySerializer], responses=DiaryDaySerializer)
    def get(self, request):
        query = DiaryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return _day_response(request.user, query.validated_data.get("date", timezone.localdate()))

    @extend_schema(request=FoodLogEntryInputSerializer, responses={201: DiaryDaySerializer})
    def post(self, request):
        data = FoodLogEntryInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        entry = diary.add_entry(
            request.user, values["date"], values["meal"], values["food"], values["grams"]
        )
        return _day_response(request.user, entry.date, status.HTTP_201_CREATED)


class MyFoodLogEntryView(APIView):
    """Change the grams or the meal of an entry, or delete it (returns the day)."""

    permission_classes = [IsClient]

    def _entry(self, request, pk: int) -> FoodLogEntry:
        entry = FoodLogEntry.objects.filter(pk=pk, user=request.user).first()
        if entry is None:
            raise NotFoundError("Entry not found.")
        return entry

    @extend_schema(request=FoodLogEntryUpdateSerializer, responses=DiaryDaySerializer)
    def patch(self, request, pk: int):
        entry = self._entry(request, pk)
        data = FoodLogEntryUpdateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        diary.update_entry(entry, **data.validated_data)
        return _day_response(request.user, entry.date)

    @extend_schema(request=None, responses=DiaryDaySerializer)
    def delete(self, request, pk: int):
        entry = self._entry(request, pk)
        entry.delete()
        return _day_response(request.user, entry.date)


class MyFoodLogCopyMenuView(APIView):
    """Log the foods of the plan's menu: one meal or the whole day."""

    permission_classes = [IsClient]

    @extend_schema(request=CopyMenuInputSerializer, responses={201: DiaryDaySerializer})
    def post(self, request):
        data = CopyMenuInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        diary.copy_menu(request.user, data.validated_data["date"], data.validated_data.get("meal"))
        return _day_response(request.user, data.validated_data["date"], status.HTTP_201_CREATED)


class MyFoodLogSummaryView(APIView):
    permission_classes = [IsClient]

    @extend_schema(parameters=[DiarySummaryQuerySerializer], responses=DiarySummarySerializer)
    def get(self, request):
        query = DiarySummaryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        result = diary.summary(request.user, query.validated_data["days"])
        return Response(DiarySummarySerializer(result).data)


class ClientFoodLogSummaryView(APIView):
    """Staff: the last days of a client's diary against the target of their plan."""

    permission_classes = [IsStaff]

    @extend_schema(parameters=[DiarySummaryQuerySerializer], responses=DiarySummarySerializer)
    def get(self, request, pk: int):
        client = User.objects.filter(pk=pk, role=Role.CLIENT, is_active=True).first()
        if client is None:
            raise NotFoundError("Client not found.")
        query = DiarySummaryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        record_health_data_access(request.user, client)
        result = diary.summary(client, query.validated_data["days"])
        return Response(DiarySummarySerializer(result).data)
