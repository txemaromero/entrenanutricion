from django.apps import AppConfig


class TrainingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.training"

    def ready(self):
        from apps.core.signals import register_file_cleanup
        from apps.training.models import ExerciseMedia, TrainingPlan, Workout

        register_file_cleanup(ExerciseMedia, ["file"])
        register_file_cleanup(Workout, ["media"])
        register_file_cleanup(TrainingPlan, ["media"])
