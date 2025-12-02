from django.apps import AppConfig


class FleetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fleet"
    verbose_name = "Fleet Management"

    def ready(self):
        """Import signals when app is ready."""
        import fleet.signals  # noqa: F401
