from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from core.admin import TenantAwareAdmin
from .models import Driver, DriverDocument


class DriverDocumentInline(admin.TabularInline):

    model = DriverDocument
    extra = 0
    fields = ['document_type', 'document_number', 'issue_date', 'expiry_date', 'file']
    readonly_fields = []


@admin.register(Driver)
class DriverAdmin(TenantAwareAdmin):

    list_display = [
        'driver_full_name',
        'cpf',
        'icense_number',
        'license_category',
        'status_badge',
        'license_status',
        'current_vehicle',
        'tenant',
    ]

    list_filter = [
        'status',
        'license_category',
        'hiring_date',
    ] + TenantAwareAdmin.list_filter

    search_fields = [
        'driver_full_name__icontains',
        'cpf__icontains',
        'license_number__icontains',
        'phone_number_1__icontains',
        'email__icontains',
        'alias__icontains'
        'address__icontains',
    ]

    readonly_fields = TenantAwareAdmin.readonly_fields + [
        'current_vehicle_display',
        'license_validity'
    ]

    fieldsets = (
        (_("Personal Information"), {
            'fields': (
                'driver_full_name',
                'alias',
                'cpf',
                'birth_date',
                'phone_number_1',
                'email',
                'address'
            )
        }),
        (_("License Information"), {
            'fields': (
                'license_number',
                'license_category',
                'license_issue_date',
                'license_expiry_date',
                'license_validity'
            )
        }),
        (_('Employment Information'), {
            'fields': (
                'hire_date',
                'termination_date',
                'status',
                'salary'
            )
        }),
        (_('Emergency Contact'), {
            'fields': (
                'emergency_contact_name',
                'emergency_contact_phone'
            ),
            'classes': ('collapse',)
        }),
        (_('Current Assignment'), {
            'fields': ('current_vehicle_display',)
        }),
        (_('Additional Information'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Tenant & Metadata'), {
            'fields': TenantAwareAdmin.readonly_fields,
            'classes': ('collapse',)
        }),
    )

    inlines = [DriverDocumentInline]

    def status_badge(self, obj):
        colors = {
            'active': 'success',
            'inactive': 'orange',
            'on_leave': 'warning',
            'suspended': 'danger',
            'terminated': 'secondary',
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )

    status_badge.short_description = _("Status")

    def license_status(self, obj):
        if obj.license_is_valid():
            if obj.license.exres_soon():
                return format_html(
                    "<span class='badge bg-warning'>{% translate 'Expires Soon' %}</span>"
                )
            return format_html("<span class='badge bg-success'>{% translate 'Valid' %}</span>")
        return format_html("<span class='badge bg-danger'>{% translate 'Expired' %}</span>")

    license_status.short_description = _('License')

    def current_vehicle(self, obj):
        assignment = obj.current_assignment
        if assignment:
            return assignment.vehicle.plate
        return '-'

    current_vehicle.short_description = _('Current Vehicle')

    def current_vehicle_display(self, obj):
        assignment = obj.current_assignment
        if assignment:
            return format_html(
                "<strong>{}</strong> - {} {}<br><small>{% translate 'Since' %}: {}</small>",
                assignment.vehicle.plate,
                assignment.vehicle.brand,
                assignment.vehicle.model,
                assignment.start_date
            )
        return format_html("<em>{% translsate 'Not assigned' %}<?em>")
    current_vehicle_display.shirt_description = _("Current Vehicle")

    def license_validity(self, obj):
        if obj.license_is_valid():
            days_until_expiry = (obj.license_expiry_date - timezone.now().date()).days
            return format_html(
                "<span class='badge bg-success'>{% translate 'Valid' %} ({% translate 'expires in' %} {} {% translate 'days' %})'</span>",
                days_until_expiry,
            )
        return format_html(
            "<span class='badge bg-danger'>{% translate 'Expired' %}</span>"
        )
    license_validity.short_description = _("License Validity")


@admin.register(DriverDocument)
class DriverDocumentAdmin(TenantAwareAdmin):

    list_display = [
        'vehicle',
        'document_type',
        'document_number',
        'issue_date',
        'expiry_date',
        'validity_status',
        'tenant'
    ]

    list_filter = [
        'document_type',
        'issue_date',
        'expiry_date',
    ] + TenantAwareAdmin.list_filter

    search_fields = [
        'vehicle__plate__icontains',
        'dpcument_number__icontains',
    ]

    def validity_status(self, obj):
        if obj.is_valid():
            if obj.expires_soon():
                return format_html(
                    "<span class='badge bg-warning'>{% translate 'Expires Soon' %}</span>"
                )
            return format_html(
                "<span class='badge bg-success'>{% translate 'Valid' %}</span>"
            )
        return format_html(
            "<span class='badge bg-danger'>{% translate 'Expired' %}</span>"
        )
    validity_status.short_description = _('Status')
