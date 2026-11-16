from django.urls import path

from apps.progress import views

urlpatterns = [
    path("me/progress/dashboard", views.DashboardView.as_view(), name="my-progress-dashboard"),
    path("me/progress/history", views.SessionHistoryView.as_view(), name="my-progress-history"),
    path("me/progress/stats", views.TrainingStatsView.as_view(), name="my-progress-stats"),
    path("me/weight-records", views.WeightRecordsView.as_view(), name="my-weight-records"),
    path("me/badges", views.BadgesView.as_view(), name="my-badges"),
    path("adherence", views.AdherenceListView.as_view(), name="adherence"),
    path("users/<int:pk>/adherence", views.ClientAdherenceView.as_view(), name="client-adherence"),
]
