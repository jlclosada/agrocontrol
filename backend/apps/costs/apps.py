from django.apps import AppConfig


class CostsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.costs"
    verbose_name = "Costes y rentabilidad"

    def ready(self):
        from apps.costs import signals  # noqa: F401
