from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import DietPreferences, HealthInfo, User, UserDetails


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["last_name", "first_name"]
    list_display = ["email", "first_name", "last_name", "role", "status", "is_active"]
    list_filter = ["role", "status", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        (
            "Profile",
            {"fields": ["first_name", "last_name", "birth_date", "gender", "profile_photo"]},
        ),
        ("Role", {"fields": ["role", "status", "is_active", "is_staff", "is_superuser"]}),
        ("Dates", {"fields": ["date_joined", "terms_accepted_at", "last_login"]}),
    ]
    add_fieldsets = [
        (None, {"fields": ["email", "first_name", "last_name", "role", "password1", "password2"]}),
    ]


admin.site.register(UserDetails)
admin.site.register(DietPreferences)
admin.site.register(HealthInfo)
