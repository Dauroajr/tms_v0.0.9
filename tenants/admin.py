import json

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Tenant, TenantUser, TenantInvitation


class TenantUserInline(admin.TabularInline):
    """Inline for displaying tenant members."""

    model = TenantUser
    extra = 0
    fields = ["user", "role", "is_owner", "is_active", "joined_at"]
    readonly_fields = ["joined_at"]
    can_delete = False
    fk_name = "tenant"


class TenantInvitationInline(admin.TabularInline):
    """Inline for displaying tenant invitations."""

    model = TenantInvitation
    extra = 0
    fields = ["email", "role", "invited_by", "created_at", "expires_at", "accepted_at"]
    readonly_fields = ["created_at", "expires_at", "accepted_at"]
    can_delete = False


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin interface for Tenant model."""

    list_display = [
        "name",
        "slug",
        "plan_badge",
        "is_active",
        "member_count",
        "created_at",
    ]

    list_filter = ["is_active", "plan", "created_at"]

    search_fields = ["name", "legal_name", "slug", "document", "email"]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "settings_display",
        "member_count",
    ]

    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("id", "name", "legal_name", "slug", "document")},
        ),
        (_("Contact Information"), {"fields": ("email", "phone", "address")}),
        (
            _("Status & Plan"),
            {"fields": ("is_active", "plan", "subscription_expires_at")},
        ),
        (
            _("Settings"),
            {"fields": ("settings", "settings_display"), "classes": ("collapse",)},
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "member_count"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [TenantUserInline, TenantInvitationInline]

    def plan_badge(self, obj):
        """Display plan with color badge."""
        colors = {
            "free": "secondary",
            "basic": "info",
            "premium": "warning",
            "enterprise": "success",
        }
        color = colors.get(obj.plan, "secondary")
        return format_html(
            '<span class="badge bg-{}">{}</span>', color, obj.get_plan_display()
        )

    plan_badge.short_description = _("Plan")
    plan_badge.admin_order_field = "plan"

    def member_count(self, obj):
        """Display number of active members."""
        count = obj.members.filter(is_active=True).count()
        return format_html(
            "<strong>{}</strong> member{}", count, "s" if count != 1 else ""
        )

    member_count.short_description = _("Members")

    def settings_display(self, obj):
        """Display settings in a formatted way."""
        if not obj.settings:
            return _("No settings configured")

        try:
            formatted = json.dumps(obj.settings, indent=2, ensure_ascii=False)
            return format_html(
                '<pre style="background:#f5f5f5;padding:10px;border-radius:4px;max-height:400px;overflow-y:auto;">{}</pre>',
                formatted,
            )
        except (TypeError, ValueError):
            return str(obj.settings)

    settings_display.short_description = _("Settings (Formatted)")

    def get_queryset(self, request):
        """Optimize queryset."""
        qs = super().get_queryset(request)
        return qs.prefetch_related("members")


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    """Admin interface for TenantUser model."""

    list_display = [
        "user_display",
        "tenant",
        "role_badge",
        "is_owner",
        "is_active",
        "joined_at",
    ]

    list_filter = [
        "role",
        "is_owner",
        "is_active",
        "joined_at",
        ("tenant", admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "tenant__name",
    ]

    readonly_fields = ["id", "joined_at", "last_access"]

    fieldsets = (
        (
            _("Membership"),
            {"fields": ("id", "user", "tenant", "role", "is_owner", "is_active")},
        ),
        (_("Permissions"), {"fields": ("permissions",)}),
        (_("Invitation"), {"fields": ("invited_by",)}),
        (
            _("Activity"),
            {"fields": ("joined_at", "last_access"), "classes": ("collapse",)},
        ),
    )

    def user_display(self, obj):
        """Display user with full name."""
        return obj.user.get_full_name() or obj.user.username

    user_display.short_description = _("User")
    user_display.admin_order_field = "user__username"

    def role_badge(self, obj):
        """Display role with color badge."""
        colors = {
            "owner": "primary",
            "admin": "success",
            "manager": "info",
            "user": "secondary",
            "viewer": "light",
        }
        color = colors.get(obj.role, "secondary")
        return format_html(
            '<span class="badge bg-{}">{}</span>', color, obj.get_role_display()
        )

    role_badge.short_description = _("Role")
    role_badge.admin_order_field = "role"

    def get_queryset(self, request):
        """Optimize queryset."""
        qs = super().get_queryset(request)
        return qs.select_related("user", "tenant", "invited_by")


@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    """Admin interface for TenantInvitation model."""

    list_display = [
        "email",
        "tenant",
        "role",
        "status_badge",
        "invited_by",
        "created_at",
        "expires_at",
    ]

    list_filter = [
        "role",
        "created_at",
        "expires_at",
        ("tenant", admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        "email",
        "tenant__name",
        "invited_by__username",
        "invited_by__email",
    ]

    readonly_fields = [
        "id",
        "token",
        "created_at",
        "accepted_at",
        "accepted_by",
        "status_badge",
    ]

    fieldsets = (
        (_("Invitation"), {"fields": ("id", "tenant", "email", "role", "invited_by")}),
        (
            _("Status"),
            {"fields": ("status_badge", "token", "created_at", "expires_at")},
        ),
        (_("Acceptance"), {"fields": ("accepted_at", "accepted_by")}),
    )

    def status_badge(self, obj):
        """Display invitation status."""
        if obj.accepted_at:
            return format_html('<span class="badge bg-success">Accepted</span>')
        elif obj.expires_at < timezone.now():
            return format_html('<span class="badge bg-danger">Expired</span>')
        else:
            return format_html('<span class="badge bg-warning">Pending</span>')

    status_badge.short_description = _("Status")

    def get_queryset(self, request):
        """Optimize queryset."""
        qs = super().get_queryset(request)
        return qs.select_related("tenant", "invited_by", "accepted_by")


# Import timezone for status_badge
# from django.utils import timezone


""" from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _

from audit.models import TenantAuditLog
from .models import Tenant, TenantUser, TenantInvitation


@admin.register(Tenant)
class TenantAdmin(ModelAdmin):

    list_display = ['name', 'slug', 'document', 'plan', 'is_active', 'created_at']
    list_filter = ['is_active', 'plan', 'created_at']
    search_fields = ['name__icontains', 'legal_name__icontains', 'document__icontains', 'slug__icontains']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'name', 'legal_name', 'slug', 'document')
        }),

        (_('Contact'), {
            'fields': ('email', 'phone', 'address')
        }),

        (_('Subscription'), {
            'fields': ('plan', 'subscription_expires_at', 'is_active')
        }),

        (_('Settings'), {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),

        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TenantUser)
class TenantUserAdmin(ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'is_owner', 'is_active', 'joined_at']
    list_filter = ['role', 'is_owner', 'is_active', 'joined_at']
    search_fields = ['user__email__icontains', 'user__username__icontains', 'tenant__name__icontains']
    readonly_fields = ['id', 'joined_at', 'last_access']
    # autocomplete_fields = ['user', 'tenant', 'invited_by']


@admin.register(TenantInvitation)
class TenantInvitationAdmin(ModelAdmin):
    list_display = ['email', 'tenant', 'role', 'invited_by', 'created_at', 'expires_at', 'accepted_at']
    list_filter = ['role', 'created_at', 'expires_at']
    search_fields = ['email__icontains', 'tenant__name__icontains', 'invited_by__username__icontains']
    readonly_fields = ['id', 'token', 'created_at', 'accepted_at', 'accepted_by']
    # autocomplete_fields = ['tenant', 'invited_by']


@admin.register(TenantAuditLog)
class TenantAuditLogAdmin(ModelAdmin):
    list_display = ['tenant', 'user', 'action', 'model_name', 'timestamp']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = [
        'tenant__name__icontains',
        'user__username__icontains',
        'user__email__icontains',
        'model_name__icontains',
        'action__icontains'
    ]
    readonly_fields = ['id', 'tenant', 'user', 'action', 'timestamp', ]
    # autocomplete_fields = ['tenant', 'user']

    def has_add_permission(self, request):
        return False  # Audit logs should be added automatically, not manually

    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs should never be deleted """
