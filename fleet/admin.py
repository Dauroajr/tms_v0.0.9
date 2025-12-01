from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from core.admin import TenantAwareAdmin
from .models import (
    Vehicle,
    VehicleBrand,
    VehicleDocument,
    VehicleAssignment,
    MaintenanceRecord,
)


@admin.register(VehicleBrand)
class VehicleBrandAdmin(TenantAwareAdmin):

    list_display = ["name", "country", "vehicles_count", "is_active", "tenant"]

    list_filter = [
        "is_active",
        "country",
    ] + TenantAwareAdmin.list_filter

    search_fields = ["name__icontains", "country__icontains"]
    readonly_fields = TenantAwareAdmin.readonly_fields + ["vehicles_count"]

    fieldsets = (
        (_("Brand Information"), {"fields": ("name", "country", "logo", "is_active")}),
        (_("Statistics"), {"fields": ("vehicles_count",)}),
        (_("Additional Information"), {"fields": ("notes",), "classes": ("collapse",)}),
        (
            _("Tenant & Metadata"),
            {"fields": TenantAwareAdmin.readonly_fields, "classes": ("collapse",)},
        ),
    )

    def vehicles_count(self, obj):
        count = obj.get_vehicles_count()
        return format_html(
            "<strong>{}</strong> vehicle{}", count, "s" if count != 1 else ""
        )

    vehicles_count.short_description = _("Vehicles Count")


class VehicleDocumentInline(admin.TabularInline):

    model = VehicleDocument
    extra = 0
    fields = ["document_type", "document_number", "issue_date", "expiry_date", "file"]
    readonly_fields = []


class MaintenanceRecordInline(admin.TabularInline):

    model = MaintenanceRecord
    extra = 0
    fields = ["maintenance_type", "status", "scheduled_date", "cost"]
    readonly_fields = []
    can_delete = False


@admin.register(Vehicle)
class VehicleAdmin(TenantAwareAdmin):

    list_display = [
        "type",
        "brand",
        "model",
        "plate",
        "color",
        "year",
        "status_badge",
        "current_driver",
        "tenant",
    ]

    list_filter = [
        "status",
        "type",
        "color",
        "fuel_type",
        "year",
        "brand",
    ] + TenantAwareAdmin.list_filter

    search_fields = [
        "plate__icontains",
        "brand__icontains",
        "model__icontains",
        "chassis_number__icontains",
        "renavam__icontains",
    ]

    readonly_fields = TenantAwareAdmin.readonly_fields + [
        "current_driver_display",
        "maintenance_status",
    ]

    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("plate", "type", "brand", "model", "year", "color", "status")},
        ),
        (_("Specifications"), {"fields": ("capacity_kg", "capacity_m3", "fuel_type")}),
        (_("Identification"), {"fields": ("chassis_number", "renavam")}),
        (
            _("Purchase Information"),
            {"fields": ("purchase_date", "purchase_value"), "classes": ("collapse",)},
        ),
        (
            _("Tracking"),
            {
                "fields": (
                    "current_km",
                    "last_maintenance_km",
                    "next_maintenance_km",
                    "maintenance_status",
                )
            },
        ),
        (_("Current Assignment"), {"fields": ("current_driver_display",)}),
        (_("Additional Information"), {"fields": ("notes",), "classes": ("collapse",)}),
        (
            _("Tenant & Metadata"),
            {"fields": TenantAwareAdmin.readonly_fields, "classes": ("collapse",)},
        ),
    )

    inlines = [VehicleDocumentInline, MaintenanceRecordInline]

    def status_badge(self, obj):
        colors = {
            "active": "success",
            "maintenance": "warning",
            "inactive": "secondary",
            "sold": "danger",
        }
        return format_html(
            "<span class='badge bg={}'>{}</span>",
            colors.get(obj.status, "secondary"),
            obj.get_status_dysplay(),
        )

    status_badge.short_description = _("Status")

    def current_driver(self, obj):
        assignment = obj.current_assignment
        if assignment:
            return assignment.driver.get_full_name
        return "-"

    current_driver.short_description = _("Current Driver")

    def current_driver_display(self, obj):
        assignment = obj.current_assignment
        if assignment:
            return format_html(
                '<strong>{}</strong><br><small>{% translate "Since" %}: {}</small>',
                assignment.driver.get_full_name,
                assignment.start_date,
            )
        return format_html("<em>{% translate 'Not assigned %}</em>")

    current_driver_display.short_description = _("Current Driver")

    def maintenance_status(self, obj):
        if obj.needs_maintenance():
            return format_html(
                "<span class='badge bg-danger'>{% translate 'Maintenance required' %}</span>"
            )
        return format_html(
            "<span class='badge bg-success'>{% translate 'Up to date' %}</span>"
        )

    maintenance_status.short_description = _("Maintenance Status")


@admin.register(VehicleDocument)
class VehicleDocumentAdmin(TenantAwareAdmin):
    list_display = [
        "vehicle",
        "document_type",
        "document_number",
        "issue_date",
        "expiry_date",
        "validity_status",
        "tenant",
    ]

    list_filter = [
        "document_type",
        "issue_date",
        "expiry_date",
    ] + TenantAwareAdmin.list_filter

    search_fields = ["vehicle__plate", "document_number"]

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

    validity_status.short_description = _("Status")


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(TenantAwareAdmin):

    list_display = [
        "vehicle",
        "maintenance_type",
        "status_badge",
        "scheduled_date",
        "completed_date",
        "cost",
        "tenant",
    ]

    list_filter = [
        "status",
        "maintenance_type",
        "scheduled_date",
    ] + TenantAwareAdmin.list_filter

    search_fields = [
        "vehicle__plate__icontains",
        "description__icontains",
        "service_provider__icontains",
    ]

    def status_badge(self, obj):
        colors = {
            "scheduled": "info",
            "in_progress": "warning",
            "completed": "success",
            "cancelled": "secondary",
        }
        return format_html(
            "<span class='badge bg-{}'>{}</span>",
            colors.get(obj.status, "secondary"),
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")


@admin.register(VehicleAssignment)
class VehicleAssignmentAdmin(TenantAwareAdmin):
    list_display = [
        "driver",
        "vehicle",
        "start_date",
        "end_date",
        "is_active_badge",
        "tenant",
    ]

    list_filter = [
        "is_active",
        "start_date",
    ] + TenantAwareAdmin.list_filter

    search_fields = [
        "driver__driver_full_name__icontains",
        "vehicle__plate__icontains"
    ]

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                "<span class='badge bg-success'>{% translate 'Active' %}</span>"
            )
        return format_html(
            "<span class='badge bg-secondary'>{% translate 'Inactive' %}</span>"
        )

    is_active_badge.short_description = _("Status")
