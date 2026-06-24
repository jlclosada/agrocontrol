from django.apps import AppConfig


class FieldbookConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.fieldbook"

    def ready(self):
        from apps.fieldbook import signals  # noqa: F401
