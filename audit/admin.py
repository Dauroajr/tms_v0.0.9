
import json

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import TenantAuditLog


@admin.register(TenantAuditLog)
class TenantAuditLogAdmin(admin.ModelAdmin):

    list_display = [
        "timestamp",
        "tenant_name",
        "user_display",
        "action_badge",
        "modelP_name",
        "object_id",
        "ip_address",
    ]

    list_filter = [
        "action",
        "model_name",
        "timestamp",
        ("tenant", admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        "user__username",
        "user__email",
        "model_name",
        "object_id",
        "ip_address",
    ]

    readonly_fields = [
        "id",
        "tenant",
        "user",
        "action",
        "model_name",
        "object_id",
        "changes_display",
        "ip_address",
        "user_agent",
        "timestamp",
    ]

    fieldsets = (
        (_("Basic Information"), {"fields": ("id", "tenant", "user", "timestamp")}),
        (_("Action Details"), {"fields": ("action", "model_name", "object_id")}),
        (_("Changes"), {"fields": ("changes_display",)}),
        (
            _("Request Information"),
            {"fields": ("ip_address", "user_agent"), "classes": ("collapse",)},
        ),
    )

    ordering = ["-timestamp"]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return False

    def tenant_name(self, obj):
        return obj.tenant.name

    tenant_name.short_descruption = _("Tenant")
    tenant_name.admin_order_field = "tenant__name"

    def user_display(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return _("System")

    user_display.short_description = _("User")
    user_display.admin_order_field = "user__username"

    def action_badge(self, obj):
        colors = {
            "create": "success",
            "update": "info",
            "delete": "danger",
            "view": "secondary",
            "login": "primary",
            "logout": "warning",
            "permission_change": "dark",
        }
        color = colors.get(obj.action, 'secondary')
        return format_html(
            f"<span class='badge bg={color}'>{obj.get_action_display()}"
        )

    action_badge.short_description = _("Action")
    action_badge.admin_order_field = "action"

    def changes_display(self, obj):
        if not obj.changes:
            return _("No changes recorded.")

        try:
            formatted = json.dumps(obj.changes, indent=2, ensure_ascii=False)
            return format_html(
                f"<pre style='background:#F5F5F5;padding:10px;'>{formatted}</pre>"
            )
        except Exception:
            return str(obj.changes)

    changes_display.short_description = _('Changes')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tenant', 'user')
