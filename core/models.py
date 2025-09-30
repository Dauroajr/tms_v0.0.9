import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TenantAwareManager(models.Manager):
    """Custom manager that automatically filters ny tenant. """

    def get_queryset(self):
        """ Override get_queryset to filter by tenant. """

        queryset = super().get_queryset()

        # Get current tenant from thread local storage (set by middleware)
        from .middleware import get_current_tenant

        tenant = get_current_tenant()

        if tenant:
            return queryset.filter(tenant=tenant)
        return queryset

    def for_tenant(self, tenant):
        """ Explicit tenant filtering. """
        return super().get_queryset().filter(tenant=tenant)


class TenantAwareModel(models.Model):
    """ Abstract bas class for all models that need tenant isloation. """

    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='%(class)s_set'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )

    objects = TenantAwareManager()
    all_objects = models.Manager()  # Bypass tenant filter when needed.

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant', 'created_at'])
        ]

    def save(self, *args, **kwargs):
        """ Override save to auto-inject tenant and user info."""
        from .middleware import get_current_tenant, get_current_user

        if not self.tenant_id:
            tenant = get_current_tenant()
            if tenant:
                self.tenant = tenant
            else:
                raise ValueError("Cannot save without tenant context.")

        user = get_current_user()
        if user and user.is_authenticated:
            if not self.pk:
                self.created_by = user
            self.updated_by = user

        super().save(*args, **kwargs)
