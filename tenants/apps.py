from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


default_app_config = 'tenants.apps.TenantsConfig'


class TenantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenants'
    verbose_name = _('Tenant Management')

    def ready(self):
        import tenants.signals  # noqa
