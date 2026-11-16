from django.contrib import admin

from apps.nutrition.models import Food, MealPlan, UserNutritionPlan


@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "diet_label", "calories", "is_active"]
    list_filter = ["category", "is_active"]


@admin.register(UserNutritionPlan)
class UserNutritionPlanAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "date_assigned", "is_current"]


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "calories", "proteins_g", "carbs_g", "fats_g"]
    list_filter = ["category"]
    search_fields = ["name"]
