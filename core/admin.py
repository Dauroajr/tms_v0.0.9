from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class TenantAwareAdmin(admin.ModelAdmin):
    """
    Base admin class for TenantAware models.
    Automatically filters by tenant and sets tenant on save.
    """

    list_display = ["id", "tenant", "created_at", "created_by"]
    list_filter = [
        "created_at",
        "updated_at",
        ("tenant", admin.RelatedOnlyFieldListFilter),
    ]
    readonly_fields = [
        "id",
        "tenant",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    ]

    def get_queryset(self, request):
        """Filter queryset by user's tenants if not superuser."""
        qs = super().get_queryset(request)

        # Superusers see everything
        if request.user.is_superuser:
            return qs

        # Regular users only see their tenants' data
        user_tenants = request.user.get_tenants()
        return qs.filter(tenant__in=user_tenants)

    def save_model(self, request, obj, form, change):
        """Auto-inject tenant and user on save."""
        if not obj.tenant_id and hasattr(request, "tenant"):
            obj.tenant = request.tenant

        if not change:  # New object
            if not obj.created_by:
                obj.created_by = request.user

        if not obj.updated_by:
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)

    def has_view_permission(self, request, obj=None):
        """Check if user has permission to view this object."""
        if not super().has_view_permission(request, obj):
            return False

        if obj and not request.user.is_superuser:
            # Check if user has access to this tenant
            if not request.user.has_tenant_permission(obj.tenant):
                return False

        return True

    def has_change_permission(self, request, obj=None):
        """Check if user has permission to change this object."""
        if not super().has_change_permission(request, obj):
            return False

        if obj and not request.user.is_superuser:
            if not request.user.has_tenant_permission(obj.tenant):
                return False

        return True

    def has_delete_permission(self, request, obj=None):
        """Check if user has permission to delete this object."""
        if not super().has_delete_permission(request, obj):
            return False

        if obj and not request.user.is_superuser:
            if not request.user.has_tenant_permission(obj.tenant):
                return False

        return True


class ReadOnlyTenantAwareAdmin(TenantAwareAdmin):
    """
    Read-only version of TenantAwareAdmin.
    Useful for audit logs and other immutable data.
    """

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
