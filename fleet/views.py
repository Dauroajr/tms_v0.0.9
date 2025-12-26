from django.contrib import messages
from django.db import models
from django.db.models import Count, Q, Avg, Sum
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from core.mixins import TenantAdminRequiredMixin
from core.views import (
    TenantAwareListView,
    TenantAwareCreateView,
    TenantAwareUpdateView,
    TenantAwareDetailView,
    TenantAwareDeleteView,
)

from .models import (
    Vehicle,
    VehicleAssignment,
    VehicleBrand,
    VehicleDocument,
    MaintenanceRecord,
)
from .forms import (
    VehicleForm,
    VehicleBrandForm,
    VehicleDocumentForm,
    VehicleAssignmentForm,
    MaintenanceRecordForm,
)


class FleetDashboardView(TenantAwareListView):

    model = Vehicle
    template_name = "fleet/dashboard.html"
    context_object_name = "vehicles"

    def get_context_data(self, **kwargs):
        # Add dashborad statistics to context
        context = super().get_context_data(**kwargs)

        # Get all vehicles for current tenant
        vehicles = Vehicle.objects.filter(tenant=self.request.tenant)

        # Basic statistics
        context["total_vehicles"] = vehicles.count()
        context["active_vehicles"] = vehicles.filter(status="is_active").count()
        context["maintenance_vehicles"] = vehicles.filter(status="maintenance").count()
        context["inactive_vehicles"] = vehicles.filter(status="inactive").count()
        context["available_vehicles"] = vehicles.filter(status="available").count()

        # Vehicles by type
        context["vehicles_by_type"] = (
            vehicles.values("type").annotate(count=Count("id")).order_by("-count")
        )

        # Vehicles by brand
        context["vehicles_by_brand"] = (
            vehicles.values("brand__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )  # Top 5 brands

        # Assignments statistics
        total_assignments = VehicleAssignment.objects.filter(tenant=self.request.tenant)
        context["total_assignments"] = total_assignments.count()
        context["active_assignments"] = total_assignments.filter(is_active=True).count()
        context["available_for_assignment"] = (
            vehicles.filter(status="active")
            .exclude(assignments__is_active=True)
            .count()
        )

        # Maintenance Statistics
        maintenance_records = MaintenanceRecord.objects.filter(
            tenant=self.request.tenant
        )
        context["total_maintenance"] = maintenance_records.count()
        context["scheduled_maintenance"] = maintenance_records.filter(
            status="scheduled"
        ).count()
        context["in_progress_maintenance"] = maintenance_records.filter(
            status="in_progress"
        ).count()

        # Vehicles needing maintenance
        context["vehicles_need_maintenance"] = [
            v for v in vehicles if v.needs_maintenance()
        ]

        # Recent vehicles
        context["recent_vehicles"] = vehicles.order_by("-created_at")[:5]

        # Documents epiration alerts
        today = timezone.now().date()
        thirty_days = today + timezone.timedelta(days=30)

        expiring_docs = VehicleDocument.objects.filter(
            tenant=self.request.tenant,
            expiry_date__isnull=False,
            expiry_date__lte=thirty_days,
            expiry_date__gte=today,
        ).select_related("vehicle")
        context["expiring_documents"] = expiring_docs

        expired_docs = VehicleDocument.objects.filter(
            tenant=self.request.tenant,
            expiry_date__isnull=False,
            expiry_date__lt=today,
        ).select_related("vehicle")
        context["expired_documents"] = expired_docs

        # Recent Maintenance Records
        context["recent_maintenance"] = maintenance_records.select_related(
            "vehicle"
        ).order_by("-scheduled_date")[:5]

        # Upcoming Maintenance
        context["upcoming_maintenance"] = (
            maintenance_records.filter(
                status="scheduled",
                scheduled_date__gte=timezone.now(),
            )
            .select_related("vehicle")
            .order_by("scheduled_date")[:5]
        )

        # Average Fleet Age
        current_year = timezone.now().year
        avg_age = vehicles.aggregate(avg_age=Avg(current_year - models.F("year")))
        context["average_fleet_age"] = avg_age["avg_age"] or 0

        # Total Fleet Value
        total_value = vehicles.aggregate(total_value=Sum("purchase_value"))
        context["total_fleet_value"] = total_value["total_value"] or 0

        # Fuel Type Distribution
        context["vehicle_by_fuel"] = (
            vehicles.values("fuel_type").annotate(count=Count("id")).order_by("-count")
        )

        return context


class VehicleListView(TenantAwareListView):

    model = Vehicle
    template_name = "fleet/vehicle.html"
    context_object_name = "vehicles"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        vehicle_type = self.request.GET.get("vehicle_type")
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                models.Q(plate__icontains=search)
                | models.Q(brand__name__icontains=search)
                | models.Q(model__icontains=search)
            )

        return queryset.select_related("brand").prefetch_related("assignments")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["status_choices"] = Vehicle.STATUS_CHOICES
        context["type_choices"] = Vehicle.TYPE_CHOICES

        context["current_status"] = self.request.GET.get("status", "")
        context["current_type"] = self.request.GET.get("type", "")
        context["current_search"] = self.request.GET.get("search", "")

        context["total_vehicles"] = self.get_queryset().count()
        context["active_vehicles"] = self.get_queryset().filter(status="active").count()
        context["maintenance_vehicles"] = (
            self.get_queryset().filter(status="maintenance").count()
        )

        return context


class VehicleDetailView(TenantAwareDetailView):

    model = Vehicle
    template_name = "fleet/vehicle_detail.html"
    context_object_name = "vehicle"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle = self.object

        context["documents"] = vehicle.documents.all()
        context["maintenance_records"] = vehicle.maintenance_records.all()[:10]
        context["current_assignment"] = vehicle.current_assignment
        context["assignment_history"] = vehicle.assignments.all()[:5]

        return context


class VehicleCreateView(TenantAdminRequiredMixin, TenantAwareCreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "fleet/vehicle_form.html"
    success_url = reverse_lazy("fleet:vehicle_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            _(f"Vehicle {form.instance.plate} has been created successfully."),
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Please correct the errors below."))
        return super().form_invalid(form)


class VehicleUpdateView(TenantAdminRequiredMixin, TenantAwareUpdateView):

    model = Vehicle
    form_class = VehicleForm
    template_name = "fleet/vehicle_form.html"
    success_url = reverse_lazy("fleet:vehicle_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            _(f"Vehicle {form.instance.plate} has been updated successfully."),
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.errors(self.request, _("Please correct the errors below."))
        return super().form_invalid(form)


class VehicleDeleteView(TenantAdminRequiredMixin, TenantAwareDeleteView):

    model = Vehicle
    template_name = "fleet/vehicle_confirm_delete.html"
    success_url = reverse_lazy("fleet:vehicle_list")

    def delete(self, request, *args, **kwargs):
        vehicle = self.get_object()
        messages.success(
            request, _(f"Vehicle {vehicle.plate} has been deleted successfully.")
        )
        return super().delete(request, *args, **kwargs)


class VehicleBrandListView(TenantAwareListView):

    model = VehicleBrand
    template_name = "fleet/brand_list.html"
    context_object_name = "brands"
    paginate_by = 20


class VehicleBrandCreateView(TenantAdminRequiredMixin, TenantAwareCreateView):

    model = VehicleBrand
    form_class = VehicleBrandForm
    template_name = "fleet/brand_form.html"
    success_url = reverse_lazy("fleet:brand_list")

    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(
            self.request,
            _("Brand {name} has been created successfully.").format(
                name=form.instance.name
            ),
        )
        return super().form_valid(form)


class VehicleBrandUpdateView(TenantAdminRequiredMixin, TenantAwareUpdateView):

    model = VehicleBrand
    form_class = VehicleBrandForm
    template_name = "fleet/brand_form.html"
    success_url = reverse_lazy("fleet:brand_list")

    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(
            self.request,
            _("Brand {name} has been updated successfully.").format(
                name=form.instance.name
            ),
        )
        return super().form_valid(form)


class VehicleAssignmentListView(TenantAwareListView):

    model = VehicleAssignment
    template_name = "fleet/assignment_list.html"
    context_object_name = "assignments"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by 'Active' status
        is_active = self.request.GET.get("active")
        if is_active == "true":
            queryset = queryset.filter(is_active=True)
        elif is_active == "false":
            queryset = queryset.filter(is_active=False)

        # Filter by vehicle
        vehicle_id = self.request.GET.get("vehicle")
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)

        # Filter by driver
        driver_id = self.request.GET.get("driver")
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)

        return queryset.select_related("vehicle", "driver", "vehicle__brand").order_by(
            "-start_date"
        )

    def get_context_data(self, **kwargs):
        """Add filter options to context."""
        context = super().get_context_data(**kwargs)

        # Get all vehicles and drivers for filters
        context["vehicles"] = Vehicle.objects.filter(
            tenant=self.request.tenant
        ).select_related("brand")

        from personnel.models import Employee

        context["drivers"] = Employee.objects.filter(
            tenant=self.request.tenant,
            employee_type="driver",
            status="active",  # ← CORRETO: Employee usa 'status', não 'is_active'
        )

        # Current filters
        context["current_active"] = self.request.GET.get("active", "")
        context["current_vehicle"] = self.request.GET.get("vehicle", "")
        context["current_driver"] = self.request.GET.get("driver", "")

        # Statistics
        context["total_assignments"] = self.get_queryset().count()
        context["active_assignments"] = (
            self.get_queryset().filter(is_active=True).count()
        )
        context["ended_assignments"] = (
            self.get_queryset().filter(is_active=False).count()
        )

        return context


class VehicleAssignmentCreateView(TenantAdminRequiredMixin, TenantAwareCreateView):
    """Create a new vehicle assignment."""

    model = VehicleAssignment
    form_class = VehicleAssignmentForm
    template_name = "fleet/assignment_form.html"
    success_url = reverse_lazy("fleet:assignment_list")

    def get_form(self, form_class=None):
        """Filter form choices to current tenant."""
        form = super().get_form(form_class)

        # Filter vehicles (only active and available)
        form.fields["vehicle"].queryset = (
            Vehicle.objects.filter(tenant=self.request.tenant, status="active")
            .exclude(assignments__is_active=True)
            .select_related("brand")
        )

        # Filter drivers (only active drivers)
        from personnel.models import Employee

        form.fields["driver"].queryset = Employee.objects.filter(
            tenant=self.request.tenant,
            employee_type="driver",
            status="active",  # ← Mude aqui também
        ).exclude(vehicle_assignments__is_active=True)

        return form

    def form_valid(self, form):
        """Handle successful form submission."""
        assignment = form.instance
        messages.success(
            self.request,
            _("Vehicle {vehicle} assigned to {driver} successfully.").format(
                vehicle=assignment.vehicle.plate, driver=assignment.driver.full_name
            ),
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle invalid form submission."""
        messages.error(self.request, _("Please correct the errors below."))
        return super().form_invalid(form)


class VehicleAssignmentDetailView(TenantAwareDetailView):
    """View details of a vehicle assignment."""

    model = VehicleAssignment
    template_name = "fleet/assignment_detail.html"
    context_object_name = "assignment"

    def get_context_data(self, **kwargs):
        """Add additional context."""
        context = super().get_context_data(**kwargs)
        assignment = self.object

        # Get driver's license info
        if hasattr(assignment.driver, "driver_profile"):
            context["driver_profile"] = assignment.driver.driver_profile

        # Calculate assignment duration
        if assignment.end_date:
            duration = (assignment.end_date - assignment.start_date).days
            context["assignment_duration"] = duration
        else:
            duration = (timezone.now().date() - assignment.start_date).days
            context["assignment_duration"] = duration

        return context


class VehicleAssignmentUpdateView(TenantAdminRequiredMixin, TenantAwareUpdateView):
    """Update a vehicle assignment."""

    model = VehicleAssignment
    form_class = VehicleAssignmentForm
    template_name = "fleet/assignment_form.html"
    success_url = reverse_lazy("fleet:assignment_list")

    def get_form(self, form_class=None):
        """Filter form choices to current tenant."""
        form = super().get_form(form_class)

        # Filter vehicles
        form.fields["vehicle"].queryset = Vehicle.objects.filter(
            tenant=self.request.tenant
        ).select_related("brand")

        # Filter drivers
        from personnel.models import Employee

        form.fields["driver"].queryset = Employee.objects.filter(
            tenant=self.request.tenant,
            employee_type="driver",
            status="active",  # ← E aqui
        )

        return form

    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, _("Assignment updated successfully."))
        return super().form_valid(form)


class VehicleAssignmentEndView(TenantAdminRequiredMixin, TenantAwareUpdateView):
    """End a vehicle assignment."""

    model = VehicleAssignment
    template_name = "fleet/assignment_end.html"
    fields = ["end_date", "notes"]
    success_url = reverse_lazy("fleet:assignment_list")

    def get_initial(self):
        """Set initial end_date to today."""
        return {"end_date": timezone.now().date()}

    def form_valid(self, form):
        """End the assignment."""
        assignment = form.instance
        assignment.is_active = False

        messages.success(
            self.request,
            _("Assignment ended. Vehicle {vehicle} is now available.").format(
                vehicle=assignment.vehicle.plate
            ),
        )
        return super().form_valid(form)


class VehicleAssignmentDeleteView(TenantAdminRequiredMixin, TenantAwareDeleteView):
    """Delete a vehicle assignment."""

    model = VehicleAssignment
    template_name = "fleet/assignment_confirm_delete.html"
    success_url = reverse_lazy("fleet:assignment_list")

    def delete(self, request, *args, **kwargs):
        """Handle delete with message."""
        assignment = self.get_object()
        messages.success(
            request,
            _(
                "Assignment of {driver} to vehicle {vehicle} deleted successfully."
            ).format(
                driver=assignment.driver.full_name, vehicle=assignment.vehicle.plate
            ),
        )
        return super().delete(request, *args, **kwargs)
