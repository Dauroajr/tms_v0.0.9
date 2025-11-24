import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TenantAwareManager(models.Manager):
    """Custom manager that automatically filters by tenant."""

    def get_queryset(self):
        """Override get_queryset to filter by tenant."""

        queryset = super().get_queryset()

        # Get current tenant from thread local storage (set by middleware)
        from .middleware import get_current_tenant

        tenant = get_current_tenant()

        if tenant:
            return queryset.filter(tenant=tenant)
        return queryset

    def for_tenant(self, tenant):
        """Explicit tenant filtering."""
        return super().get_queryset().filter(tenant=tenant)

    def all_tenants(self):
        return super().get_queryset()


class TenantAwareModel(models.Model):
    """Abstract base class for all models that need tenant isolation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant",  # Corrigido: tenants, não tenant
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="%(class)s_set",
        help_text=_("Tenant that owns this record"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="%(class)s_created",
        help_text=_("User who created this record"),
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
        help_text=_("User who last updated this record"),
    )

    objects = TenantAwareManager()
    all_objects = models.Manager()  # Bypass tenant filter when needed

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["tenant", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """Override save to auto-inject tenant and user info."""
        from tenants.middleware import get_current_tenant, get_current_user

        # Auto-inject tenant if not set
        if not self.tenant_id:
            tenant = get_current_tenant()
            if tenant:
                self.tenant = tenant
            else:
                # Allow saving without tenant for special cases (migrations, fixtures)
                if not kwargs.get("force_insert") and not kwargs.get(
                    "skip_tenant_check"
                ):
                    raise ValueError(
                        f"Cannot save {self.__class__.__name__} without tenant context. "
                        f"Use save(skip_tenant_check=True) to bypass."
                    )

        # Auto-inject user info
        user = get_current_user()
        if user and user.is_authenticated:
            if not self.pk:  # New record
                if not self.created_by:
                    self.created_by = user
            if not self.updated_by:
                self.updated_by = user

        # Remove custom kwarg before calling parent save
        kwargs.pop("skip_tenant_check", None)

        super().save(*args, **kwargs)

    def __str__(self):
        """Default string representation."""
        return f"{self.__class__.__name__} ({self.id})"
