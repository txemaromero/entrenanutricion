import django_filters
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.emails import language_from_header
from apps.accounts.models import Equipment, Goal
from apps.accounts.services import remember_language
from apps.core.files import media_kind
from apps.core.permissions import IsClient, IsStaff, StaffReadTrainerWrite
from apps.core.translation import localized, order_by_localized_name
from apps.core.utils import file_url
from apps.training import reminders, services
from apps.training.models import (
    Difficulty,
    Exercise,
    ExerciseCompletion,
    ExerciseMedia,
    MuscleGroup,
    TrainingPlan,
    TrainingPlanWorkout,
    Workout,
    WorkoutExercise,
)
from apps.training.serializers import (
    ClientExerciseDetailSerializer,
    CompleteWorkoutResultSerializer,
    ExerciseCompletionInputSerializer,
    ExerciseCompletionResultSerializer,
    ExerciseHistorySerializer,
    ExerciseListSerializer,
    ExerciseMediaSerializer,
    ExerciseMediaUploadSerializer,
    ExerciseSerializer,
    MediaUploadSerializer,
    MuscleGroupSerializer,
    MyTrainingPlanSerializer,
    MyWorkoutDaySerializer,
    PersonalRecordSerializer,
    RemindersInputSerializer,
    RemindersSerializer,
    TrainingDaysInputSerializer,
    TrainingDaysSerializer,
    TrainingPlanListSerializer,
    TrainingPlanSerializer,
    WorkoutListSerializer,
    WorkoutSerializer,
)

INCLUDE_INACTIVE = OpenApiParameter(
    "include_inactive", bool, description="Also list deactivated (soft-deleted) items."
)


def wants_inactive(request) -> bool:
    return request.query_params.get("include_inactive", "").lower() in {"1", "true", "yes"}


EXERCISE_PREFETCH = ("muscle_groups", "media", "steps")
ITEMS_PREFETCH = Prefetch(
    "items",
    queryset=WorkoutExercise.objects.select_related("exercise").prefetch_related(
        "exercise__muscle_groups", "exercise__media"
    ),
)


class MediaActionsMixin:
    """`PUT/DELETE <resource>/{id}/media` for resources with a single `media` file."""

    @extend_schema(request={"multipart/form-data": MediaUploadSerializer})
    @action(detail=True, methods=["put", "delete"], parser_classes=[MultiPartParser, FormParser])
    def media(self, request, pk=None):
        instance = self.get_object()
        if request.method == "DELETE":
            services.set_media(instance, None)
        else:
            upload = MediaUploadSerializer(data=request.data)
            upload.is_valid(raise_exception=True)
            services.set_media(instance, upload.validated_data["media"])
        return Response(self.get_serializer(self.get_queryset().get(pk=instance.pk)).data)


# --- Staff catalog -------------------------------------------------------------------------------


class MuscleGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MuscleGroup.objects.all()
    serializer_class = MuscleGroupSerializer
    permission_classes = [IsStaff]
    pagination_class = None


class ExerciseFilter(django_filters.FilterSet):
    muscle_group = django_filters.CharFilter(field_name="muscle_groups__slug")

    class Meta:
        model = Exercise
        fields = ["muscle_group"]


@extend_schema(parameters=[INCLUDE_INACTIVE])
class ExerciseViewSet(viewsets.ModelViewSet):
    permission_classes = [StaffReadTrainerWrite]
    filterset_class = ExerciseFilter
    search_fields = ["name", "description", "translations"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        queryset = Exercise.objects.prefetch_related(*EXERCISE_PREFETCH).distinct()
        if self.action == "list" and not wants_inactive(self.request):
            queryset = queryset.filter(is_active=True)
        return order_by_localized_name(queryset)

    def get_serializer_class(self):
        return ExerciseListSerializer if self.action == "list" else ExerciseSerializer

    def perform_destroy(self, instance):
        services.delete_exercise(instance)

    @extend_schema(
        request={"multipart/form-data": ExerciseMediaUploadSerializer},
        responses={201: ExerciseMediaSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="media",
        parser_classes=[MultiPartParser, FormParser],
    )
    def add_media(self, request, pk=None):
        exercise = self.get_object()
        upload = ExerciseMediaUploadSerializer(data=request.data)
        upload.is_valid(raise_exception=True)
        media = services.add_exercise_media(exercise, **upload.validated_data)
        return Response(
            ExerciseMediaSerializer(media, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(responses={204: None})
    @action(detail=True, methods=["delete"], url_path=r"media/(?P<media_id>\d+)")
    def delete_media(self, request, pk=None, media_id=None):
        exercise = self.get_object()
        get_object_or_404(ExerciseMedia, pk=media_id, exercise=exercise).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkoutViewSet(MediaActionsMixin, viewsets.ModelViewSet):
    permission_classes = [StaffReadTrainerWrite]
    search_fields = ["name", "description", "translations"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return order_by_localized_name(Workout.objects.prefetch_related(ITEMS_PREFETCH))

    def get_serializer_class(self):
        return WorkoutListSerializer if self.action == "list" else WorkoutSerializer

    def perform_destroy(self, instance):
        services.delete_workout(instance)


class TrainingPlanFilter(django_filters.FilterSet):
    goal = django_filters.ChoiceFilter(choices=Goal.choices)
    difficulty = django_filters.ChoiceFilter(choices=Difficulty.choices)
    equipment = django_filters.ChoiceFilter(choices=Equipment.choices)

    class Meta:
        model = TrainingPlan
        fields = ["goal", "difficulty", "equipment"]


@extend_schema(parameters=[INCLUDE_INACTIVE])
class TrainingPlanViewSet(MediaActionsMixin, viewsets.ModelViewSet):
    permission_classes = [StaffReadTrainerWrite]
    filterset_class = TrainingPlanFilter
    search_fields = ["name", "description", "translations"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        if self.action == "list":
            queryset = TrainingPlan.objects.annotate(workout_count=Count("plan_workouts"))
            if not wants_inactive(self.request):
                queryset = queryset.filter(is_active=True)
            return order_by_localized_name(queryset)
        workouts = TrainingPlanWorkout.objects.select_related("workout").prefetch_related(
            "workout__items"
        )
        return TrainingPlan.objects.prefetch_related(Prefetch("plan_workouts", queryset=workouts))

    def get_serializer_class(self):
        return TrainingPlanListSerializer if self.action == "list" else TrainingPlanSerializer

    def perform_destroy(self, instance):
        services.delete_training_plan(instance)


# --- Client: my training plan --------------------------------------------------------------------


def _workout_ref(workout: Workout, request) -> dict:
    return {
        "id": workout.id,
        "name": localized(workout, "name"),
        "description": localized(workout, "description"),
        "media_url": file_url(workout.media, request),
        "media_kind": media_kind(workout.media.name) if workout.media else None,
    }


def _row_payload(row, scheduled: dict, request) -> dict:
    workout = row.plan_workout.workout
    return {
        "id": row.id,
        "order": row.plan_workout.order,
        "status": row.status,
        "completed_at": row.completed_at,
        "scheduled_date": scheduled.get(row.id),
        "workout": _workout_ref(workout, request),
        "summary": services.workout_summary(workout, workout.items.all()),
    }


class MyTrainingPlanView(APIView):
    permission_classes = [IsClient]

    @extend_schema(responses=MyTrainingPlanSerializer)
    def get(self, request):
        assignment = services.get_current_assignment(request.user)
        rows = services.plan_rows_for_display(assignment)
        scheduled = services.schedule_rows(request.user, rows)
        plan = assignment.plan
        days = services.get_training_days(request.user)
        next_row = next((row for row in rows if row.status == "available"), None)
        payload = {
            "id": assignment.id,
            "cycle": assignment.cycle,
            "progress": assignment.progress,
            "date_started": assignment.date_started,
            "weekly_training_days": days["weekly_training_days"],
            "training_days": days["days"],
            "custom_training_days": days["custom"],
            "plan": {
                **_workout_ref(plan, request),
                "goal": plan.goal,
                "difficulty": plan.difficulty,
                "equipment": plan.equipment,
                "duration_weeks": plan.duration_weeks,
            },
            "workouts": [_row_payload(row, scheduled, request) for row in rows],
            "next_workout_id": next_row.id if next_row else None,
        }
        return Response(MyTrainingPlanSerializer(payload).data)


class MyTrainingDaysView(APIView):
    """Weekdays the client trains on (replaces the default calendar)."""

    permission_classes = [IsClient]

    @extend_schema(responses=TrainingDaysSerializer)
    def get(self, request):
        return Response(TrainingDaysSerializer(services.get_training_days(request.user)).data)

    @extend_schema(request=TrainingDaysInputSerializer, responses=TrainingDaysSerializer)
    def put(self, request):
        serializer = TrainingDaysInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.set_training_days(request.user, serializer.validated_data["days"])
        return Response(TrainingDaysSerializer(result).data)


class MyWorkoutDayView(APIView):
    permission_classes = [IsClient]

    @extend_schema(responses=MyWorkoutDaySerializer)
    def get(self, request, pk: int):
        row = services.get_user_workout(request.user, pk)
        rows = services.plan_rows_for_display(row.user_plan)
        scheduled = services.schedule_rows(request.user, rows)
        items = list(
            WorkoutExercise.objects.filter(workout_id=row.plan_workout.workout_id)
            .select_related("exercise")
            .prefetch_related("exercise__muscle_groups", "exercise__media")
        )
        done = services.completed_item_ids(row)
        logged = dict(
            ExerciseCompletion.objects.filter(user_plan_workout=row).values_list(
                "workout_exercise_id", "sets"
            )
        )
        previous = services.last_sets(request.user, [item.exercise_id for item in items])
        payload = {
            **_row_payload(row, scheduled, request),
            "summary": services.workout_summary(row.plan_workout.workout, items),
            "progress": services.day_progress(items, done),
            "exercises": [
                {
                    "id": item.id,
                    "order": item.order,
                    "sets": item.sets,
                    "reps": item.reps,
                    "rest_seconds": item.rest_seconds,
                    "completed": item.id in done,
                    "logged_sets": logged.get(item.id) or [],
                    "last_sets": previous.get(item.exercise_id),
                    "exercise": item.exercise,
                }
                for item in items
            ],
        }
        return Response(MyWorkoutDaySerializer(payload, context={"request": request}).data)


class MyExerciseCompletionView(APIView):
    permission_classes = [IsClient]

    @extend_schema(
        request=ExerciseCompletionInputSerializer, responses=ExerciseCompletionResultSerializer
    )
    def put(self, request, pk: int, item_id: int):
        data = ExerciseCompletionInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        result = services.set_exercise_completion(
            request.user,
            pk,
            item_id,
            data.validated_data["completed"],
            data.validated_data.get("sets"),
        )
        return Response(ExerciseCompletionResultSerializer(result).data)


class MyRecordsView(APIView):
    """Personal records of the client: heaviest set and estimated 1RM per exercise."""

    permission_classes = [IsClient]

    @extend_schema(responses=PersonalRecordSerializer(many=True))
    def get(self, request):
        return Response(
            PersonalRecordSerializer(services.personal_records(request.user), many=True).data
        )


class MyExerciseHistoryView(APIView):
    """Latest sessions of one exercise with their sets (progression of loads)."""

    permission_classes = [IsClient]

    @extend_schema(responses=ExerciseHistorySerializer)
    def get(self, request, pk: int):
        records = [
            record
            for record in services.personal_records(request.user)
            if record["exercise"]["id"] == pk
        ]
        payload = {
            "record": records[0] if records else None,
            "entries": services.exercise_history(request.user, pk),
        }
        return Response(ExerciseHistorySerializer(payload).data)


class MyCompleteWorkoutView(APIView):
    permission_classes = [IsClient]

    @extend_schema(request=None, responses=CompleteWorkoutResultSerializer)
    def post(self, request, pk: int):
        result = services.complete_workout(request.user, pk)
        return Response(CompleteWorkoutResultSerializer(result).data)


class MyExerciseDetailView(APIView):
    permission_classes = [IsClient]

    @extend_schema(responses=ClientExerciseDetailSerializer)
    def get(self, request, pk: int):
        exercise = services.get_accessible_exercise(request.user, pk)
        return Response(ClientExerciseDetailSerializer(exercise, context={"request": request}).data)


class MyRemindersView(APIView):
    """Training time and email reminders of the client (phase 12)."""

    permission_classes = [IsClient]

    @extend_schema(responses=RemindersSerializer)
    def get(self, request):
        return Response(RemindersSerializer(reminders.reminder_settings(request.user)).data)

    @extend_schema(request=RemindersInputSerializer, responses=RemindersSerializer)
    def put(self, request):
        data = RemindersInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        # The reminder is written in the language the client is using now.
        remember_language(
            request.user, language_from_header(request.headers.get("Accept-Language"))
        )
        result = reminders.update_reminders(
            request.user, data.validated_data["enabled"], data.validated_data.get("training_time")
        )
        return Response(RemindersSerializer(result).data)
