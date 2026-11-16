from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.training import views

router = DefaultRouter(trailing_slash=False)
router.register("muscle-groups", views.MuscleGroupViewSet, basename="muscle-group")
router.register("exercises", views.ExerciseViewSet, basename="exercise")
router.register("workouts", views.WorkoutViewSet, basename="workout")
router.register("training-plans", views.TrainingPlanViewSet, basename="training-plan")

urlpatterns = [
    path("me/training-plan", views.MyTrainingPlanView.as_view(), name="my-training-plan"),
    path("me/training-days", views.MyTrainingDaysView.as_view(), name="my-training-days"),
    path(
        "me/training-plan/workouts/<int:pk>",
        views.MyWorkoutDayView.as_view(),
        name="my-training-workout",
    ),
    path(
        "me/training-plan/workouts/<int:pk>/exercises/<int:item_id>",
        views.MyExerciseCompletionView.as_view(),
        name="my-training-exercise-completion",
    ),
    path(
        "me/training-plan/workouts/<int:pk>/complete",
        views.MyCompleteWorkoutView.as_view(),
        name="my-training-workout-complete",
    ),
    path("me/exercises/<int:pk>", views.MyExerciseDetailView.as_view(), name="my-exercise"),
    path(
        "me/exercises/<int:pk>/history",
        views.MyExerciseHistoryView.as_view(),
        name="my-exercise-history",
    ),
    path("me/records", views.MyRecordsView.as_view(), name="my-records"),
    path("me/reminders", views.MyRemindersView.as_view(), name="my-reminders"),
    *router.urls,
]
