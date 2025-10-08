from django.contrib import admin
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
        return False  # Audit logs should never be deleted
