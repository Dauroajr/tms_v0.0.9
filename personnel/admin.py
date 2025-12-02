from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from core.admin import TenantAwareAdmin
from .models import Employee, DriverProfile, SecurityProfile, EmployeeDocument


class DriverProfileInline(admin.StackedInline):
    model = DriverProfile
    extra = 0
    can_delete = False
    fields = [
        "license_number",
        "license_category",
        "license_issue_date",
        "license_expiry_date",
        "has_mopp",
        "mopp_expiry_date",
        "has_defensive_driving",
        "defensive_driving_date",
        "last_medical_exam_date",
        "next_medical_exam_date",
        "blood_type",
        "total_trips",
        "total_km_driven",
        "accidents_count",
        "violations_count",
    ]


class SecurityProfileInline(admin.StackedInline):
    model = SecurityProfile
    extra = 0
    can_delete = False
    fields = [
        "security_license_number",
        "security_license_issue_date",
        "security_license_expiry_date",
        "has_firearms_license",
        "firearms_license_number",
        "firearms_license_expiry",
        "has_vigilant_course",
        "vigilant_course_date",
        "has_recycling_course",
        "recycling_course_date",
        "next_recycling_date",
        "last_medical_exam_date",
        "next_medical_exam_date",
    ]


class EmployeeDocumentInline(admin.TabularInline):
    model = EmployeeDocument
    extra = 0
    fields = ["document_type", "document_number", "issue_date", "expiry_date", "file"]
    readonly_fields = []


@admin.register(Employee)
class EmployeeAdmin(TenantAwareAdmin):
    list_display = [
        "employee_number",
        "full_name",
        "employee_type_badge",
        "cpf",
        "status_badge",
        "hire_date",
        "age",
        "tenure",
        "tenant",
    ]

    list_filter = [
        "employee_type",
        "status",
        "payment_type",
        "gender",
        "hire_date",
    ] + TenantAwareAdmin.list_filter

    search_fields = [
        "full_name__icontains",
        "cpf__icontains",
        "employee_number__icontains",
        "phone__icontains",
        "email__icontains"
    ]

    readonly_fields = TenantAwareAdmin.readonly_fields + [
        "age_display",
        "tenure_display",
        "profiles_display",
    ]

    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("employee_number", "employee_type", "full_name", "photo")},
        ),
        (
            _("Personal Information"),
            {"fields": ("cpf", "rg", "birth_date", "age_display", "gender")},
        ),
        (
            _("Contact Information"),
            {"fields": ("phone", "email", "address", "city", "state", "zip_code")},
        ),
        (
            _("Employment Information"),
            {"fields": ("hire_date", "termination_date", "tenure_display", "status")},
        ),
        (
            _("Financial Information"),
            {
                "fields": (
                    "salary",
                    "payment_type",
                    "bank_name",
                    "bank_branch",
                    "bank_account",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Emergency Contact"),
            {
                "fields": (
                    "emergency_contact_name",
                    "emergency_contact_relationship",
                    "emergency_contact_phone",
                ),
                "classes": ("collapse",),
            },
        ),
        (_("Profiles"), {"fields": ("profiles_display",)}),
        (_("Additional Information"), {"fields": ("notes",), "classes": ("collapse",)}),
        (
            _("Tenant & Metadata"),
            {"fields": TenantAwareAdmin.readonly_fields, "classes": ("collapse",)},
        ),
    )

    inlines = []

    def get_inlines(self, request, obj=None):
        """Dynamically add inlines based on employee type."""
        inlines = [EmployeeDocumentInline]

        if obj:
            if obj.employee_type == "driver":
                inlines.insert(0, DriverProfileInline)
            elif obj.employee_type == "security":
                inlines.insert(0, SecurityProfileInline)

        return inlines

    def employee_type_badge(self, obj):
        colors = {
            "driver": "primary",
            "security": "danger",
            "mechanic": "warning",
            "admin": "info",
            "helper": "secondary",
            "other": "secondary",
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.employee_type, "secondary"),
            obj.get_employee_type_display(),
        )

    employee_type_badge.short_description = _("Type")

    def status_badge(self, obj):
        colors = {
            "active": "success",
            "on_leave": "warning",
            "vacation": "info",
            "suspended": "danger",
            "terminated": "secondary",
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, "secondary"),
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")

    def age(self, obj):
        return obj.get_age()

    age.short_description = _("Age")

    def tenure(self, obj):
        years = obj.get_tenure_years()
        return f"{years} year{'s' if years != 1 else ''}"

    tenure.short_description = _("Tenure")

    def age_display(self, obj):
        return format_html("<strong>{}</strong> years old", obj.get_age())

    age_display.short_description = _("Age")

    def tenure_display(self, obj):
        years = obj.get_tenure_years()
        return format_html(
            "<strong>{}</strong> year{} of service", years, "s" if years != 1 else ""
        )

    tenure_display.short_description = _("Tenure")

    def profiles_display(self, obj):
        profiles = []
        if obj.has_driver_profile():
            profiles.append('<span class="badge bg-primary">Driver Profile</span>')
        if obj.has_security_profile():
            profiles.append('<span class="badge bg-danger">Security Profile</span>')

        if profiles:
            return format_html(" ".join(profiles))
        return format_html("<em>No additional profiles</em>")

    profiles_display.short_description = _("Additional Profiles")


@admin.register(DriverProfile)
class DriverProfileAdmin(TenantAwareAdmin):
    list_display = [
        "employee",
        "license_number",
        "license_category",
        "license_status",
        "medical_exam_status",
        "total_trips",
        "total_km_driven",
        "tenant",
    ]

    list_filter = [
        "license_category",
        "has_mopp",
        "has_defensive_driving",
        "license_expiry_date",
    ] + TenantAwareAdmin.list_filter

    search_fields = ["employee__full_name__icontains", "license_number__icontains"]

    readonly_fields = TenantAwareAdmin.readonly_fields + [
        "license_validity_display",
        "medical_exam_validity_display",
        "performance_display",
    ]

    fieldsets = (
        (_("Employee"), {"fields": ("employee",)}),
        (
            _("License Information"),
            {
                "fields": (
                    "license_number",
                    "license_category",
                    "license_issue_date",
                    "license_expiry_date",
                    "license_first_issue_date",
                    "license_validity_display",
                )
            },
        ),
        (
            _("Qualifications"),
            {
                "fields": (
                    "has_mopp",
                    "mopp_expiry_date",
                    "has_defensive_driving",
                    "defensive_driving_date",
                )
            },
        ),
        (
            _("Medical Information"),
            {
                "fields": (
                    "last_medical_exam_date",
                    "next_medical_exam_date",
                    "medical_exam_validity_display",
                    "blood_type",
                )
            },
        ),
        (
            _("Performance"),
            {
                "fields": (
                    "total_trips",
                    "total_km_driven",
                    "accidents_count",
                    "violations_count",
                    "performance_display",
                )
            },
        ),
        (_("Additional Information"), {"fields": ("notes",), "classes": ("collapse",)}),
        (
            _("Tenant & Metadata"),
            {"fields": TenantAwareAdmin.readonly_fields, "classes": ("collapse",)},
        ),
    )

    def license_status(self, obj):
        if obj.license_is_valid():
            if obj.license_expires_soon():
                return format_html('<span class="badge bg-warning">Expires Soon</span>')
            return format_html('<span class="badge bg-success">Valid</span>')
        return format_html('<span class="badge bg-danger">Expired</span>')

    license_status.short_description = _("License")

    def medical_exam_status(self, obj):
        if obj.medical_exam_is_valid():
            if obj.medical_exam_expires_soon():
                return format_html('<span class="badge bg-warning">Expires Soon</span>')
            return format_html('<span class="badge bg-success">Valid</span>')
        return format_html('<span class="badge bg-danger">Expired</span>')

    medical_exam_status.short_description = _("Medical")

    def license_validity_display(self, obj):
        if obj.license_is_valid():
            days = (obj.license_expiry_date - timezone.now().date()).days
            return format_html(
                '<span class="badge bg-success">Valid (expires in {} days)</span>', days
            )
        return format_html('<span class="badge bg-danger">Expired</span>')

    license_validity_display.short_description = _("License Validity")

    def medical_exam_validity_display(self, obj):
        if obj.medical_exam_is_valid():
            days = (obj.next_medical_exam_date - timezone.now().date()).days
            return format_html(
                '<span class="badge bg-success">Valid (next exam in {} days)</span>',
                days,
            )
        return format_html('<span class="badge bg-danger">Exam Required</span>')

    medical_exam_validity_display.short_description = _("Medical Exam Validity")

    def performance_display(self, obj):
        return format_html(
            "<strong>Trips:</strong> {} | <strong>KM:</strong> {} | "
            "<strong>Accidents:</strong> {} | <strong>Violations:</strong> {}",
            obj.total_trips,
            obj.total_km_driven,
            obj.accidents_count,
            obj.violations_count,
        )

    performance_display.short_description = _("Performance Summary")


@admin.register(SecurityProfile)
class SecurityProfileAdmin(TenantAwareAdmin):
    list_display = [
        "employee",
        "security_license_number",
        "license_status",
        "has_firearms_license",
        "needs_recycling",
        "tenant",
    ]

    list_filter = [
        "has_firearms_license",
        "has_vigilant_course",
        "has_recycling_course",
        "security_license_expiry_date",
    ] + TenantAwareAdmin.list_filter

    search_fields = [
        "employee__full_name__icontains",
        "security_license_number__icontains",
        "firearms_license_number__icontains",
    ]

    readonly_fields = TenantAwareAdmin.readonly_fields + [
        "license_validity_display",
        "recycling_status_display",
    ]

    fieldsets = (
        (_("Employee"), {"fields": ("employee",)}),
        (
            _("Security License"),
            {
                "fields": (
                    "security_license_number",
                    "security_license_issue_date",
                    "security_license_expiry_date",
                    "license_validity_display",
                )
            },
        ),
        (
            _("Certifications"),
            {
                "fields": (
                    "has_firearms_license",
                    "firearms_license_number",
                    "firearms_license_expiry",
                    "has_vigilant_course",
                    "vigilant_course_date",
                    "has_recycling_course",
                    "recycling_course_date",
                    "next_recycling_date",
                    "recycling_status_display",
                )
            },
        ),
        (
            _("Medical Information"),
            {"fields": ("last_medical_exam_date", "next_medical_exam_date")},
        ),
        (_("Performance"), {"fields": ("shifts_worked", "incidents_reported")}),
        (
            _("Additional Information"),
            {"fields": ("specializations", "notes"), "classes": ("collapse",)},
        ),
        (
            _("Tenant & Metadata"),
            {"fields": TenantAwareAdmin.readonly_fields, "classes": ("collapse",)},
        ),
    )

    def license_status(self, obj):
        if obj.license_is_valid():
            if obj.license_expires_soon():
                return format_html('<span class="badge bg-warning">Expires Soon</span>')
            return format_html('<span class="badge bg-success">Valid</span>')
        return format_html('<span class="badge bg-danger">Expired</span>')

    license_status.short_description = _("License")

    def needs_recycling(self, obj):
        if obj.needs_recycling_course():
            return format_html('<span class="badge bg-danger">Required</span>')
        return format_html('<span class="badge bg-success">OK</span>')

    needs_recycling.short_description = _("Recycling Course")

    def license_validity_display(self, obj):
        if obj.license_is_valid():
            days = (obj.security_license_expiry_date - timezone.now().date()).days
            return format_html(
                '<span class="badge bg-success">Valid (expires in {} days)</span>', days
            )
        return format_html('<span class="badge bg-danger">Expired</span>')

    license_validity_display.short_description = _("License Validity")

    def recycling_status_display(self, obj):
        if obj.needs_recycling_course():
            return format_html(
                '<span class="badge bg-danger">Recycling Course Required</span>'
            )
        if obj.next_recycling_date:
            days = (obj.next_recycling_date - timezone.now().date()).days
            return format_html(
                '<span class="badge bg-success">Next course in {} days</span>', days
            )
        return format_html('<span class="badge bg-warning">Not scheduled</span>')

    recycling_status_display.short_description = _("Recycling Status")


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(TenantAwareAdmin):
    list_display = [
        "employee",
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

    search_fields = ["employee__full_name__icontains", "document_number__icontains"]

    def validity_status(self, obj):
        if obj.is_valid():
            if obj.expires_soon():
                return format_html('<span class="badge bg-warning">Expires Soon</span>')
            return format_html('<span class="badge bg-success">Valid</span>')
        return format_html('<span class="badge bg-danger">Expired</span>')

    validity_status.short_description = _("Status")


""" from django.contrib import admin
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
 """
