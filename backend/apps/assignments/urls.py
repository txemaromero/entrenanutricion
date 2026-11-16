from django.urls import path

from apps.assignments import views

urlpatterns = [
    path("assignments/pending", views.PendingAssignmentsView.as_view(), name="assignments-pending"),
    path(
        "users/<int:pk>/assign-training-plan",
        views.AssignTrainingPlanView.as_view(),
        name="assign-training-plan",
    ),
    path(
        "users/<int:pk>/assign-nutrition-plan",
        views.AssignNutritionPlanView.as_view(),
        name="assign-nutrition-plan",
    ),
]
