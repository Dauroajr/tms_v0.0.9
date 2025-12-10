from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


default_app_config = 'personnel.apps.PersonnelConfig'


class PersonnelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "personnel"
    verbose_name = _("Personnel Management")

    def ready(self):
        """Import signals when app is ready."""
        import personnel.signals  # noqa: F401
