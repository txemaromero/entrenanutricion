from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.nutrition import views

router = DefaultRouter(trailing_slash=False)
router.register("meal-plans", views.MealPlanViewSet, basename="meal-plan")
router.register("foods", views.FoodViewSet, basename="food")

urlpatterns = [
    path("me/nutrition-plan", views.MyNutritionPlanView.as_view(), name="my-nutrition-plan"),
    path("me/nutrition-plan/menu", views.MyMenuView.as_view(), name="my-menu"),
    path("me/shopping-list", views.MyShoppingListView.as_view(), name="my-shopping-list"),
    path("me/food-log", views.MyFoodLogView.as_view(), name="my-food-log"),
    path("me/food-log/summary", views.MyFoodLogSummaryView.as_view(), name="my-food-log-summary"),
    path(
        "me/food-log/copy-menu",
        views.MyFoodLogCopyMenuView.as_view(),
        name="my-food-log-copy-menu",
    ),
    path("me/food-log/<int:pk>", views.MyFoodLogEntryView.as_view(), name="my-food-log-entry"),
    path(
        "users/<int:pk>/food-log/summary",
        views.ClientFoodLogSummaryView.as_view(),
        name="client-food-log-summary",
    ),
    *router.urls,
]
