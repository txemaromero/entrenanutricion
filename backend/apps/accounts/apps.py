from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

    def ready(self):
        from apps.accounts import schema  # noqa: F401  (registers the OpenAPI auth extension)
        from apps.accounts.models import User
        from apps.core.signals import register_file_cleanup

        register_file_cleanup(User, ["profile_photo"])
