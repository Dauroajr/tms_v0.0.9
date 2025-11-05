from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser
from tenants.models import TenantUser


class TenantUserInline(admin.TabularInline):
    """ Inline for displaying user's tenant memberships. """

    model = TenantUser
    fk_name = 'user'
    extra = 0
    fields = ['tenant', 'role', 'is_owner', 'is_active', 'joined_at']
    readonly_fields = ['joined_at']
    can_delete = False


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    """ Admin interface for CustomUser model. """

    list_display = [
        'username',
        'email',
        'first_name',
        'last_name',
        'current_tenant',
        'is_active',
        'is_staff',
        'date_joined'
    ]

    list_filter = [
        'is_active',
        'is_staff',
        'is_superuser',
        'document_type',
        'date_joined',
        'last_login'
    ]

    search_fields = [
        'icontains__username',
        'icontains__email',
        'icontains__first_name',
        'icontains__last_name',
        'icontains__document_number',
        'icontains__phone'
    ]

    ordering = ['-date_joined',]

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal Info'), {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'phone'
            )
        }),
        (_('Document Information'), {
            'fields': (
                'document_type',
                'document_number'
            )
        }),
        (_('Tenant Information'), {
            'fields': (
                'current_tenant',
                'last_login_tenant'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        (_('Important Dates'), {
            'fields': (
                'last_login',
                'date_joined',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'created_at',
        'updated_at',
        'date_joined',
        'last_login',
    ]

    inlines = [TenantUserInline]

    def get_queryset(self, request):
        """ Optimize query with select_related. """
        qs = super().get_queryset(request)
        return qs.select_related('current_tenant', 'last_login_tenant')
