from django.apps import AppConfig


class AgentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.agents"

    def ready(self):
        # Register built-in tools and event handlers on startup.
        from apps.agents import tools  # noqa: F401
        from apps.agents import handlers  # noqa: F401
