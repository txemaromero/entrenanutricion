from django.urls import include, path

from apps.core.views import HealthView

urlpatterns = [
    path("health", HealthView.as_view(), name="health"),
    path("", include("apps.accounts.urls")),
    path("", include("apps.training.urls")),
    path("", include("apps.nutrition.urls")),
    path("", include("apps.progress.urls")),
    path("", include("apps.assignments.urls")),
    path("", include("apps.statistics.urls")),
    path("", include("apps.notes.urls")),
]
