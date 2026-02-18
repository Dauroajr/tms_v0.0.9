from django.contrib import messages
from django.db import models, transaction
from django.db.models import Count, Q, Avg, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# from django.views import View
from django.views.generic import ListView, DetailView, View, TemplateView
from django.http import HttpResponse, JsonResponse

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
    VehicleAssignmentWorkday,
    VehicleBrand,
    VehicleDocument,
    MaintenanceRecord,
    WorkdayApproval,
    WorkReport,
    PaymentOrder,
    ExpenseReport,
)
from .forms import (
    VehicleForm,
    VehicleBrandForm,
    VehicleDocumentForm,
    VehicleAssignmentForm,
    VehicleAssignmentWorkdayForm,
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


# Adicione/substitua esta view em fleet/views.py


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

        # Filter drivers (only active drivers without active assignments)
        from personnel.models import Employee

        form.fields["driver"].queryset = Employee.objects.filter(
            tenant=self.request.tenant,
            employee_type="driver",
            status="active",
        ).exclude(vehicle_assignments__is_active=True)

        return form

    def form_valid(self, form):
        """Handle successful form submission."""
        assignment = form.instance

        # A validação e salvamento do tenant é feito pelo TenantAwareCreateView
        # Mas vamos garantir que está setado
        if not assignment.tenant_id:
            assignment.tenant = self.request.tenant

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

        # Log dos erros para debug
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Assignment form errors: {form.errors}")

        return super().form_invalid(form)


# Substitua esta view em fleet/views.py


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

        # Workday statistics - ADICIONADO
        context["pending_workdays"] = assignment.workdays.filter(
            status="pending"
        ).count()
        context["approved_workdays"] = assignment.workdays.filter(
            status="approved"
        ).count()
        context["paid_workdays"] = assignment.workdays.filter(status="paid").count()
        context["rejected_workdays"] = assignment.workdays.filter(
            status="rejected"
        ).count()

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


# Substitua/verifique esta view em fleet/views.py


class VehicleAssignmentDeleteView(TenantAdminRequiredMixin, TenantAwareDeleteView):
    """Delete a vehicle assignment."""

    model = VehicleAssignment
    template_name = "fleet/assignment_confirm_delete.html"
    success_url = reverse_lazy("fleet:assignment_list")

    def dispatch(self, request, *args, **kwargs):
        """Check if assignment can be deleted."""
        assignment = self.get_object()

        # Check if there are paid workdays
        paid_workdays = assignment.workdays.filter(status="paid").count()
        if paid_workdays > 0:
            messages.error(
                request,
                _(
                    "Cannot delete assignment with {count} paid workday(s). "
                    "Please contact your administrator."
                ).format(count=paid_workdays),
            )
            return redirect("fleet:assignment_detail", pk=assignment.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add additional context."""
        context = super().get_context_data(**kwargs)
        assignment = self.object

        # Add workday counts
        context["total_workdays"] = assignment.workdays.count()
        context["paid_workdays"] = assignment.workdays.filter(status="paid").count()
        context["approved_workdays"] = assignment.workdays.filter(
            status="approved"
        ).count()
        context["pending_workdays"] = assignment.workdays.filter(
            status="pending"
        ).count()

        return context

    def delete(self, request, *args, **kwargs):
        """Handle delete with message."""
        assignment = self.get_object()
        driver_name = assignment.driver.full_name
        vehicle_plate = assignment.vehicle.plate
        workdays_count = assignment.workdays.count()

        messages.success(
            request,
            _(
                "Assignment of {driver} to vehicle {vehicle} deleted successfully. "
                "{count} workday(s) were also removed."
            ).format(driver=driver_name, vehicle=vehicle_plate, count=workdays_count),
        )
        return super().delete(request, *args, **kwargs)


# ==================== WORKDAY VIEWS ====================


class WorkdayListView(TenantAwareListView):
    """List all workdays."""

    model = VehicleAssignmentWorkday
    template_name = "fleet/workday_list.html"
    context_object_name = "workdays"
    paginate_by = 30

    def get_queryset(self):
        """Get filtered queryset."""
        queryset = super().get_queryset()

        # Filter by assignment
        assignment_id = self.request.GET.get("assignment")
        if assignment_id:
            queryset = queryset.filter(assignment_id=assignment_id)

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by date range
        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset.select_related(
            "assignment", "assignment__vehicle", "assignment__driver", "approved_by"
        ).order_by("-date")

    def get_context_data(self, **kwargs):
        """Add filter options and statistics."""
        context = super().get_context_data(**kwargs)

        # Get all assignments for filter
        context["assignments"] = VehicleAssignment.objects.filter(
            tenant=self.request.tenant
        ).select_related("vehicle", "driver")

        # Current filters
        context["current_assignment"] = self.request.GET.get("assignment", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["current_date_from"] = self.request.GET.get("date_from", "")
        context["current_date_to"] = self.request.GET.get("date_to", "")

        # Statistics
        queryset = self.get_queryset()
        context["total_workdays"] = queryset.count()
        context["pending_workdays"] = queryset.filter(status="pending").count()
        context["approved_workdays"] = queryset.filter(status="approved").count()
        context["paid_workdays"] = queryset.filter(status="paid").count()

        # Calculate totals
        from django.db.models import Sum

        totals = queryset.aggregate(
            total_hours=Sum("total_hours"),
            total_overtime=Sum("overtime_hours"),
            total_amount=Sum("total_amount"),
        )
        context.update(totals)

        return context


class WorkdayCreateView(TenantAdminRequiredMixin, TenantAwareCreateView):
    """Create a new workday."""

    model = VehicleAssignmentWorkday
    form_class = VehicleAssignmentWorkdayForm
    template_name = "fleet/workday_form.html"

    def get_success_url(self):
        """Redirect to assignment detail or workday list."""
        if self.object.assignment:
            return reverse_lazy(
                "fleet:assignment_detail", kwargs={"pk": self.object.assignment.pk}
            )
        return reverse_lazy("fleet:workday_list")

    def get_form_kwargs(self):
        """Pass assignment to form if provided."""
        kwargs = super().get_form_kwargs()

        # Get assignment from URL parameter
        assignment_id = self.request.GET.get("assignment")
        if assignment_id:
            try:
                assignment = VehicleAssignment.objects.get(
                    pk=assignment_id, tenant=self.request.tenant
                )
                kwargs["assignment"] = assignment
            except VehicleAssignment.DoesNotExist:
                pass

        return kwargs

    def form_valid(self, form):
        """Handle successful form submission."""
        workday = form.instance
        messages.success(
            self.request,
            _("Workday for {driver} on {date} registered successfully.").format(
                driver=workday.assignment.driver.full_name, date=workday.date
            ),
        )
        return super().form_valid(form)


class WorkdayDetailView(TenantAwareDetailView):
    """View workday details."""

    model = VehicleAssignmentWorkday
    template_name = "fleet/workday_detail.html"
    context_object_name = "workday"


class WorkdayUpdateView(TenantAdminRequiredMixin, TenantAwareUpdateView):
    """Update a workday."""

    model = VehicleAssignmentWorkday
    form_class = VehicleAssignmentWorkdayForm
    template_name = "fleet/workday_form.html"

    def get_success_url(self):
        """Redirect back to assignment detail."""
        return reverse_lazy(
            "fleet:assignment_detail", kwargs={"pk": self.object.assignment.pk}
        )

    def dispatch(self, request, *args, **kwargs):
        """Check if workday can be edited."""
        workday = self.get_object()
        if not workday.can_edit():
            messages.error(
                request,
                _("This workday cannot be edited (status: {status}).").format(
                    status=workday.get_status_display()
                ),
            )
            return redirect("fleet:workday_detail", pk=workday.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, _("Workday updated successfully."))
        return super().form_valid(form)


class WorkdayDeleteView(TenantAdminRequiredMixin, TenantAwareDeleteView):
    """Delete a workday."""

    model = VehicleAssignmentWorkday
    template_name = "fleet/workday_confirm_delete.html"

    def get_success_url(self):
        """Redirect to workday list."""
        return reverse_lazy("fleet:workday_list")

    def dispatch(self, request, *args, **kwargs):
        """Check if workday can be deleted."""
        workday = self.get_object()
        if workday.status == "paid":
            messages.error(request, _("Cannot delete a paid workday."))
            return redirect("fleet:workday_detail", pk=workday.pk)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Handle delete with message."""
        workday = self.get_object()
        assignment = workday.assignment

        response = super().delete(request, *args, **kwargs)

        # Recalculate assignment totals
        assignment.calculate_totals()

        messages.success(request, _("Workday deleted successfully."))
        return response


class WorkdayApproveView(TenantAdminRequiredMixin, View):
    """Approve a workday."""

    def post(self, request, pk):
        """Approve the workday."""
        workday = get_object_or_404(
            VehicleAssignmentWorkday, pk=pk, tenant=request.tenant
        )

        if not workday.can_approve():
            messages.error(
                request,
                _("This workday cannot be approved (status: {status}).").format(
                    status=workday.get_status_display()
                ),
            )
        else:
            workday.approve(request.user)
            workday.assignment.calculate_totals()
            messages.success(request, _("Workday approved successfully."))

        return redirect("fleet:workday_detail", pk=pk)


class WorkdayRejectView(TenantAdminRequiredMixin, View):
    """Reject a workday."""

    def post(self, request, pk):
        """Reject the workday."""
        workday = get_object_or_404(
            VehicleAssignmentWorkday, pk=pk, tenant=request.tenant
        )

        if workday.status != "pending":
            messages.error(request, _("Only pending workdays can be rejected."))
        else:
            workday.reject(request.user)
            messages.warning(request, _("Workday rejected."))

        return redirect("fleet:workday_detail", pk=pk)


class WQorkdayApprovalListView(TenantAwareListView):

    model = WorkdayApproval
    template_name = "fleet/approval_list.html"
    context_object_name = "approvals"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filters
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        driver_id = self.request.GET.get("driver")
        if driver_id:
            queryset = queryset.filter(assignment__driver_id=driver_id)

        return queryset.select_related(
            "assignment",
            "assignment__driver",
            "assignment__vehicle",
            "workday",
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Statistics
        queryset = self.get_queryset()
        context["total_approvals"] = queryset.count()
        context["pending_approvals"] = queryset.filter(status="pending").count()
        context["approved_count"] = queryset.filter(status="approved").count()

        # Filters
        context["current_status"] = self.request.GET.get("status", "")
        context["current_driver"] = self.request.GET.get("driver", "")

        # Drivers for filters
        from personnel.models import Employee

        context["drivers"] = Employee.objects.filter(
            tenant=self.request.tenant, employee_type="driver"
        )

        return context


class WorkdayApprovalCreateView(TenantAdminRequiredMixin, View):
    # Criar aprovação em lote de workdays

    tempalte_name = "fleet/payment/approval_create.html"

    def get(self, request, assignment_pk):
        """Mostrar Workdays pendentes para aprovação."""
        assignment = get_object_or_404(
            VehicleAssignment, pk=assignment_pk, tenant=request.tenant
        )

        # Workdays pendentes
        pending_workdays = assignment.workdays.filter(
            status="pending",
            approval__isnull=True,
        ).order_by("date")

        if not pending_workdays.exists():
            messages.warning(request, _("No pending workdays to approve"))
            return redirect("fleet:assignment_detail", pk=assignment_pk)

        context = {
            "assignment": assignment,
            "workdays": pending_workdays,
            "total_workdays": pending_workdays.count(),
            "total_amount": sum(w.total_amount for w in pending_workdays),
        }

        return render(request, self.tempalte_name, context)

    @transaction.atomic
    def post(self, request, assignment_pk):
        """Aprovar workdays selecionados."""
        assignment = get_object_or_404(
            VehicleAssignment, pk=assignment_pk, tenant=request.tenant
        )

        # IDs dos workdays selecionados
        workday_ids = request.POST.getlist("workday_ids")

        if not workday_ids:
            messages.error(request, _("Select at least one workday."))
            return redirect("fleet:approval_create", assignment_pk=assignment_pk)

        # Buscar Workdays
        workdays = assignment.workdays.filter(
            id__in=workday_ids,
            status="pending",
            approval__isnull=True,
        ).order_by("date")

        if not workdays.exists():
            messages.error(request, _("Invalid workdays selected."))
            return redirect("fleet:approval_create", assignment_pk=assignment_pk)

        # Criar aprovações
        approval = WorkdayApproval.objects.create(
            tenant=request.tenant,
            assignment=assignment,
            period_start=workdays.first().date,
            period_end=workdays.last().date,
            created_by=request.user,
        )

        # Vincular workdays à aprovação
        workdays.update(approval=approval)

        # Calcular totais
        approval.calculate_totals()

        messages.success(
            request,
            _("Approval batch created with {count} workdays.").format(
                count=workdays.count()
            ),
        )

        return redirect("fleet:approval_detail", pk=approval.pk)


class WorkdayApprovalDetailView(TenantAwareDetailView):

    model = WorkdayApproval
    template_name = "fleet/payment/approval_detail.html"
    context_object_name = "approval"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        approval = self.object
        context["workdays"] = approval.workdays.all().order_by("date")

        return context


class WorkdayApprovalApproveView(TenantAdminRequiredMixin, View):

    @transaction.atomic
    def post(self, request, pk):
        approval = get_object_or_404(
            WorkdayApproval, pk=pk, tenant=request.tenant, status="pending"
        )

        # Aprovar
        approval.approve(request.user)

        # Gerar relatório automaticamente
        report = self._generate_work_report(approval, request.user)

        messages.success(
            request,
            _("Workdays approved! Work report #{number} generated.").format(
                number=report.report_number
            ),
        )

        return redirect("fleet:work_report_detail", pk=report.pk)

    def _generate_work_report(self, approval, user):
        """Gerar relatório de trabalho após aprovação."""
        report = WorkReport.objects.create(
            tenant=approval.tenant,
            approval=approval,
            assignment=approval.assignment,
            created_by=user,
        )
        report.generate_report_number()
        report.save()

        # TODO: Gerar PDF
        # TODO: Enviar e-mails

        return report


class WorkdayApprovalListView(TenantAwareListView):
    """Lista de aprovações de workdays."""

    model = WorkdayApproval
    template_name = "fleet/payment/approval_list.html"
    context_object_name = "approvals"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        driver_id = self.request.GET.get("driver")
        if driver_id:
            queryset = queryset.filter(assignment__driver_id=driver_id)

        return queryset.select_related(
            "assignment",
            "assignment__driver",
            "assignment__vehicle",
            "assignment__vehicle__brand",
            "approved_by"
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Estatísticas
        queryset = self.get_queryset()
        context["total_approvals"] = queryset.count()
        context["pending_approvals"] = queryset.filter(status="pending").count()
        context["approved_count"] = queryset.filter(status="approved").count()

        # Filtros
        context["current_status"] = self.request.GET.get("status", "")
        context["current_driver"] = self.request.GET.get("driver", "")

        # Drivers para filtro
        from personnel.models import Employee

        context["drivers"] = Employee.objects.filter(
            tenant=self.request.tenant, employee_type="driver"
        )

        return context


class WorkdayApprovalRejectView(TenantAdminRequiredMixin, View):
    """Rejeitar lote de workdays com motivo."""

    @transaction.atomic
    def post(self, request, pk):
        approval = get_object_or_404(
            WorkdayApproval, pk=pk, tenant=request.tenant, status="pending"
        )

        rejection_reason = request.POST.get("rejection_reason", "").strip()

        if not rejection_reason:
            messages.error(request, _("Rejection reason is required."))
            return redirect("fleet:approval_detail", pk=pk)

        # Rejeitar
        approval.reject(request.user, rejection_reason)

        messages.warning(
            request,
            _("Approval batch rejected. All workdays have been marked as rejected."),
        )

        return redirect("fleet:approval_detail", pk=pk)


class WorkReportListView(TenantAwareListView):
    """Lista de relatórios de trabalho."""

    model = WorkReport
    template_name = "fleet/payment/work_report_list.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.select_related(
            "assignment",
            "assignment__driver",
            "assignment__vehicle",
            "assignment__vehicle__brand",
            "approval",
        ).order_by("-created_at")


class WorkReportDetailView(TenantAwareDetailView):

    model = WorkReport
    template_name = "fleet/payment/work_report_detail.html"
    context_object_name = "report"


class WorkReportApproveView(TenantAdminRequiredMixin, View):

    @transaction.atomic
    def post(self, request, pk):
        report = get_object_or_404(
            WorkReport,
            pk=pk,
            tenant=request.tenant,
            status__in=["generated", "sent", "reviewed"],
        )

        # Aprovar Relatório
        report.status = "approved"
        report.save()

        # Gerar Ordem de Pagamento
        payment_order = self._genetare_payment_order(report, request.user)

        messages.success(
            request,
            _("Report approved! Payment order #{number} generated.").format(
                number=payment_order.payment_number
            ),
        )
        return redirect("fleet:payment_orde_detail", pk=payment_order.pk)

    def _generate_payment_order(self, report, user):
        payment_order = PaymentOrder.objects.create(
            tenant=report.tenant,
            work_report=report,
            assignment=report.assignment,
            driver=report.assignment.driver,
            gross_amount=report.approval.total_amount,
            deductions=0,
            created_by=user,
        )
        payment_order.generate_payment_number()
        payment_order.calculate_net_amount()
        payment_order.save()

        return payment_order


# ============= PAYMENT ORDER ================


class PaymentOrderListView(TenantAwareListView):

    model = PaymentOrder
    template_name = "fleet/payment/payment_order_list.html"
    context_object_name = "payment_orders"
    paginate_by = 20

    def get_queyset(self):
        queryset = super().get_queryset()

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        driver_id = self.request.GET.get("driver")
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)

        return queryset.select_related(
            'driver',
            'assignment',
            'assignment__vehicle',
            'assignment__vehicle__brand',
            'work_report',
            'work_report__approval',
            'approved_by',
            'paid_by'
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = self.get_queryset()
        context["pending_count"] = queryset.filter(status="pending").count()
        context["approved_count"] = queryset.filter(status="approved").count()
        context["paid_count"] = queryset.filter(status="paid").count()

        # Total a Pagar
        from django.db.models import Sum

        context["total_pending+_amount"] = (
            queryset.filter(status__in=["pending", "approved"]).aggregate(
                total=Sum("net_amount")
            )["total"]
            or 0
        )

        return context


class PaymentOrderDetailView(TenantAwareDetailView):

    model = PaymentOrder
    template_name = "fleet/payment_order_detail.html"
    context_object_name = "payment_order"


class PaymentOrderApproveView(TenantAdminRequiredMixin, View):
    """Aprovar ordem para pagamento -> Gerar nota de despesas"""

    @transaction.atomic
    def post(self, request, pk):
        payment_order = get_object_or_404(
            PaymentOrder,
            pk=pk,
            tenant=request.tenant,
            status="pending",
        )

        # Aprovar pagamento
        payment_order.approve_for_payment(request.user)

        # Gerar nota de despesas para o cliente
        expense_report = self._generate_expense_report(payment_order, request.user)

        messages.success(
            request,
            _("Payment approved! Expense report #{number} generated.").format(
                number=expense_report.report_number
            ),
        )

        return redirect("fleet:expense_report_detail", pk=expense_report.pk)

    def _generate_expense_report(self, payment_order, user):
        """Gerar relatório de despesas para o cliente."""
        # TODO: ('Buscar dados do cliente do Assignment')
        client_name = "Cliente XYZ"  # Placeholder
        client_email = "cliente@example.com"  # Placeholder

        expense_report = ExpenseReport.objects.create(
            tenant=payment_order.tenant,
            payment_order=payment_order,
            assignment=payment_order.assignment,
            client_name=client_name,
            client_email=client_email,
            total_amount=payment_order.net_amount,
            created_by=user,
        )
        expense_report.generate_report_number()
        expense_report.save()

        # TODO: ('Gerar PDF')
        # TODO: ('Enviar para cliente')
        expense_report.send_to_client()

        return expense_report


class PaymentOrderPayView(TenantAdminRequiredMixin, View):
    """Efetivar pagamento ao motorista."""

    template_name = "fleet/payment/payment_order_pay.html"

    def get(self, request, pk):
        payment_order = get_object_or_404(
            PaymentOrder, pk=pk, tenant=request.tenant, status="approved"
        )

        # Verificar se nota de despesas foi aprovada pelo cliente
        if hasattr(payment_order, "expense_report"):
            if payment_order.expense_report.status != "approved":
                messages.warning(
                    request,
                    _("Expense report must be approved by client before payment."),
                )
                return redirect("fleet:payment_order_detail", pk=pk)

        context = {"payment_order": payment_order}
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, pk):
        payment_order = get_object_or_404(
            PaymentOrder, pk=pk, tenant=request.tenant, status="approved"
        )

        payment_method = request.POST.get("payment_method")
        payment_reference = request.POST.get("payment_reference", "")

        if not payment_method:
            messages.error(request, _("Payment method is required."))
            return redirect("fleet:payment_order_pay", pk=pk)

        # Marcar como pago
        payment_order.mark_as_paid(request.user, payment_method, payment_reference)

        # TODO: Gerar comprovante PDF

        # Finalizar assignment se todos pagamentos foram feitos
        self._check_and_finalize_assignment(payment_order.assignment)

        messages.success(
            request,
            _("Payment of R$ {amount} completed!").format(
                amount=payment_order.net_amount
            ),
        )

        return redirect("fleet:payment_order_detail", pk=pk)

    def _check_and_finalize_assignment(self, assignment):
        """Verificar se todos pagamentos foram feitos e finalizar assignment."""
        pending_payments = assignment.payment_orders.exclude(status="paid")

        if not pending_payments.exists():
            # Todos pagamentos foram feitos
            assignment.is_active = False
            if not assignment.end_date:
                assignment.end_date = timezone.now().date()
            assignment.save()


# =========== EXPENSE REPORT =================


class ExpenseReportListView(TenantAwareListView):
    """Lista de relatórios de despesas enviados ao cliente."""

    model = ExpenseReport
    template_name = "fleet/payment/expense_report_list.html"
    context_object_name = "expense_reports"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtro por status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filtro por cliente
        client = self.request.GET.get("client")
        if client:
            queryset = queryset.filter(client_name__icontains=client)

        return queryset.select_related(
            'assignment',
            'assignment__driver',
            'assignment__vehicle',
            'assignment__vehicle__brand',  # ← ADICIONAR
            'payment_order',
            'payment_order__work_report',  # ← ADICIONAR
            'payment_order__work_report__approval'
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = self.get_queryset()

        # Estatísticas
        context["total_reports"] = queryset.count()
        context["generated_count"] = queryset.filter(status="generated").count()
        context["sent_count"] = queryset.filter(status="sent").count()
        context["approved_count"] = queryset.filter(status="approved").count()
        context["rejected_count"] = queryset.filter(status="rejected").count()

        # Total de valores
        from django.db.models import Sum

        context["total_amount"] = (
            queryset.aggregate(total=Sum("total_amount"))["total"] or 0
        )

        context["pending_approval_amount"] = (
            queryset.filter(status__in=["generated", "sent"]).aggregate(
                total=Sum("total_amount")
            )["total"]
            or 0
        )

        return context


class ExpenseReportDetailView(TenantAwareDetailView):

    model = ExpenseReport
    template_name = "fleet/payment/expense_report_detail.html"
    context_object_name = "expense_report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Incluir workdays do approval relacionado
        expense_report = self.object
        context["workdays"] = (
            expense_report.payment_order.work_report.approval.workdays.all()
        )

        return context


# Simulação de aprovação do cliente (em produção, seria por link no e-mail)
class ExpenseReportClientApproveView(View):
    """
    Cliente aprova relatório de despesas.
    Esta é uma view PÚBLICA (não requer autenticação).
    Acesso via token de segurança enviado por e-mail.
    """

    template_name = "fleet/payment/expense_report_client_approve.html"

    def get(self, request, pk, token):
        """Mostrar formulário de aprovação para o cliente."""

        # TODO: Validar token de segurança
        # Por ora, vamos aceitar qualquer acesso para desenvolvimento

        expense_report = get_object_or_404(
            ExpenseReport, pk=pk, status__in=["generated", "sent"]
        )

        context = {
            "expense_report": expense_report,
            "token": token,
        }

        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, pk, token):
        """Cliente confirma aprovação."""

        # TODO: Validar token de segurança

        expense_report = get_object_or_404(
            ExpenseReport, pk=pk, status__in=["generated", "sent"]
        )

        action = request.POST.get("action")
        client_notes = request.POST.get("client_notes", "")

        if action == "approve":
            # Cliente aprova
            expense_report.approve_by_client(client_notes)

            messages.success(
                request, _("Expense report approved! Payment will be processed soon.")
            )

            # TODO: Notificar empresa que cliente aprovou

        elif action == "reject":
            # Cliente rejeita
            expense_report.status = "rejected"
            expense_report.client_notes = client_notes
            expense_report.save()

            messages.warning(
                request, _("Expense report rejected. The company will be notified.")
            )

            # TODO: Notificar empresa que cliente rejeitou

        # Redirecionar para página de agradecimento
        return render(
            request,
            "fleet/payment/expense_report_client_thanks.html",
            {
                "expense_report": expense_report,
                "action": action,
            },
        )
