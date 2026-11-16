from django.urls import path

from apps.statistics import views

urlpatterns = [
    path(
        "statistics/exercise-popularity",
        views.ExercisePopularityView.as_view(),
        name="statistics-exercise-popularity",
    ),
    path(
        "statistics/platform-growth",
        views.PlatformGrowthView.as_view(),
        name="statistics-platform-growth",
    ),
    path("statistics/sessions", views.SessionsPerMonthView.as_view(), name="statistics-sessions"),
    path(
        "statistics/plan-popularity",
        views.PlanPopularityView.as_view(),
        name="statistics-plan-popularity",
    ),
    path("statistics/summary", views.SummaryView.as_view(), name="statistics-summary"),
    path("statistics/years", views.YearsView.as_view(), name="statistics-years"),
]
