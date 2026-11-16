from django.contrib import admin

from apps.training import models


class WorkoutExerciseInline(admin.TabularInline):
    model = models.WorkoutExercise
    extra = 0


class TrainingPlanWorkoutInline(admin.TabularInline):
    model = models.TrainingPlanWorkout
    extra = 0


@admin.register(models.Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active", "muscle_groups"]
    search_fields = ["name"]


@admin.register(models.Workout)
class WorkoutAdmin(admin.ModelAdmin):
    inlines = [WorkoutExerciseInline]
    search_fields = ["name"]


@admin.register(models.TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    inlines = [TrainingPlanWorkoutInline]
    list_display = ["name", "goal", "difficulty", "is_active"]


@admin.register(models.UserTrainingPlan)
class UserTrainingPlanAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "cycle", "progress", "is_current"]
    list_filter = ["is_current"]


admin.site.register(models.MuscleGroup)
admin.site.register(models.WorkoutSession)
