import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from tenants.models import Tenant, TenantUser


class CustomUser(AbstractUser):
    """
    Extends Django's AbstractUser for multi-tenant support.
    This model should be set as AUTH_USER_MODEL in settings.py
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    current_tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_users',
        help_text=_('Currentlky active tenant for this user')
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    document_number = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        help_text=_('Unique identifier like SSN or Tax ID, CPF or CNPJ')
    )
    document_type = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        choices=[('SSN', 'SSN'), ('TAXID', 'Tax ID'), ('CPF', 'CPF'), ('CNPJ', 'CNPJ')],
        default='CPF'
    )
    last_login_tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='last_login_users',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['document_number'])
        ]

    def get_tenants(self):
        """Returns all tenants the user belongs to."""
        return self.tenant_memberships.filter(is_active=True).select_related('tenant')

    def has_tenant_permission(self, tenant, permission=None):
        """Check if the user has a specific permission in the given tenant."""
        try:
            membership = self.tenant_memberships.get(tenant=tenant, is_active=True)
            if permission:
                return permission in membership.get_permissions()
            return True
        except TenantUser.DoesNotExist:
            return False
