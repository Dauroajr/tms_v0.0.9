from django.contrib import messages
from django.db.models import Q, F
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from core.mixins import TenantRequiredMixin, TenantAdminRequiredMixin
from core.views import (
    TenantAwareCreateView,
    TenantAwareListView,
    TenantAwareDeleteView,
    TenantAwareDetailView,
    TenantAwareUpdateView,
)

from .models import Employee, DriverProfile, SecurityProfile, EmployeeDocument
from .forms import (
    EmployeeForm,
    EmployeeDocumentForm,
    DriverProfileForm,
    SecurityProfileForm,
)


# ============ EMPLOYEE VIEWS ==============


class EmployeeListView(TenantAwareListView):

    model = Employee
    template_name = "personnel/employee_list.html"
    context_object_name = "employees"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by employee type
        employee_type = self.request.GET.get("type")
        if employee_type:
            queryset = queryset.filter(employee_type=employee_type)

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Search by name or employee number
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains__iexact=search)  # should remove iexact?
                | Q(employee_number__icontains__iexact=search)  # should remove iexact?
                | Q(cof__icontains__iexact=search)  # should remove iexact?
            )
        return queryset.order_by("full_name")

    def get_context_data(self, **kwargs):
        """Add statistics and filters."""
        context = super().get_context_data(**kwargs)

        # Current filters
        context["current_type"] = self.request.GET.get("type", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["current_search"] = self.request.GET.get("search", "")

        # Statistics
        all_employees = Employee.objects.filter(tenant=self.request.tenant)
        context["total_employees"] = all_employees.count()
        context["total_drivers"] = all_employees.filter(employee_type="driver").count()
        context["total_security"] = all_employees.filter(
            employee_type="security"
        ).count()
        context["active_employees"] = all_employees.filter(status="active").count()

        return context


class EmployeeDetailView(TenantAwareDetailView):

    model = Employee
    template_name = "personnel/employee_detail.html"
    context_object_name = "employee"

    def get_context_data(self, **kwargs):
        """Add related data."""
        context = super().get_context_data(**kwargs)
        employee = self.object

        # Get documents
        context["documents"] = employee.documents.all()

        # Get profile based on type
        if employee.employee_type == "driver":
            context["driver_profile"] = getattr(employee, "driver_profile", None)
        elif employee.employee_type == "security":
            context["security_profile"] = getattr(employee, "security_profile", None)

        # Get vehicle assignments if driver
        if employee.employee_type == "driver":
            context["vehicle_assignments"] = (
                employee.vehicle_assignments.select_related(
                    "vehicle", "vehicle__brand"
                ).order_by("-start_date")[:5]
            )

        return context


class EmployeeCreateView(TenantAwareCreateView):

    model = Employee
    form_class = EmployeeForm
    template_name = "personnel/employee_form.html"
    success_url = reverse_lazy("personnel:employee_list")

    def form_valid(self, form):
        employee = form.instance
        messages.success(
            self.request,
            _("Employee {name} created successfully").format(name=employee.full_name),
        )

        response = super().form_valid(form)

        # Redirect to profile creation if driver or security
        if employee.employee_type == "driver":
            messages.info(
                self.request,
                _("Now create the driver profile with license information."),
            )
            return redirect("personnel:driver_profile_create", employee_pk=employee.pk)
        elif employee.employee_type == "security":
            messages.info(self.request, _("Now create the security profile."))
            return redirect(
                "personnel:security_profile_create", employee_pk=employee.pk
            )

        return response

    def form_invalid(self, form):
        """Handle invalid form."""
        messages.error(self.request, _("Please correct the errors below."))
        return super().form_invalid(form)


class EmployeeUpdateView(TenantAdminRequiredMixin, TenantAwareUpdateView):
    """Update an employee."""

    model = Employee
    form_class = EmployeeForm
    template_name = "personnel/employee_form.html"
    success_url = reverse_lazy("personnel:employee_list")

    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, _("Employee updated successfully."))
        return super().form_valid(form)


class EmployeeDeleteView(TenantAdminRequiredMixin, TenantAwareDeleteView):
    """Delete an employee."""

    model = Employee
    template_name = "personnel/employee_confirm_delete.html"
    success_url = reverse_lazy("personnel:employee_list")

    def delete(self, request, *args, **kwargs):
        """Handle delete."""
        employee = self.get_object()
        messages.success(
            request,
            _("Employee {name} deleted successfully.").format(name=employee.full_name),
        )
        return super().delete(request, *args, **kwargs)


# ==================== DRIVER PROFILE VIEWS ====================


class DriverProfileCreateView(TenantAdminRequiredMixin, TenantAwareCreateView):
    """Create driver profile."""

    model = DriverProfile
    form_class = DriverProfileForm
    template_name = "personnel/driver_profile_form.html"

    def get_success_url(self):
        """Redirect to employee detail."""
        return reverse_lazy(
            "personnel:employee_detail", kwargs={"pk": self.object.employee.pk}
        )

    def get_initial(self):
        """Pre-fill employee."""
        initial = super().get_initial()
        employee_pk = self.kwargs.get("employee_pk")
        if employee_pk:
            initial["employee"] = employee_pk
        return initial

    def get_form(self, form_class=None):
        """Lock employee field if provided in URL."""
        form = super().get_form(form_class)
        employee_pk = self.kwargs.get("employee_pk")
        if employee_pk:
            form.fields["employee"].widget.attrs["readonly"] = True
            form.fields["employee"].disabled = True
        return form

    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, _("Driver profile created successfully."))
        return super().form_valid(form)


class DriverProfileUpdateView(TenantAdminRequiredMixin, TenantAwareUpdateView):
    """Update driver profile."""

    model = DriverProfile
    form_class = DriverProfileForm
    template_name = "personnel/driver_profile_form.html"

    def get_success_url(self):
        """Redirect to employee detail."""
        return reverse_lazy(
            "personnel:employee_detail", kwargs={"pk": self.object.employee.pk}
        )

    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, _("Driver profile updated successfully."))
        return super().form_valid(form)


# ==================== SECURITY PROFILE VIEWS ====================


class SecurityProfileCreateView(TenantAdminRequiredMixin, TenantAwareCreateView):
    """Create security profile."""

    model = SecurityProfile
    form_class = SecurityProfileForm
    template_name = "personnel/security_profile_form.html"

    def get_success_url(self):
        """Redirect to employee detail."""
        return reverse_lazy(
            "personnel:employee_detail", kwargs={"pk": self.object.employee.pk}
        )

    def get_initial(self):
        """Pre-fill employee."""
        initial = super().get_initial()
        employee_pk = self.kwargs.get("employee_pk")
        if employee_pk:
            initial["employee"] = employee_pk
        return initial

    def get_form(self, form_class=None):
        """Lock employee field if provided in URL."""
        form = super().get_form(form_class)
        employee_pk = self.kwargs.get("employee_pk")
        if employee_pk:
            form.fields["employee"].widget.attrs["readonly"] = True
            form.fields["employee"].disabled = True
        return form

    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, _("Security profile created successfully."))
        return super().form_valid(form)


class SecurityProfileUpdateView(TenantAdminRequiredMixin, TenantAwareUpdateView):
    """Update security profile."""

    model = SecurityProfile
    form_class = SecurityProfileForm
    template_name = "personnel/security_profile_form.html"

    def get_success_url(self):
        """Redirect to employee detail."""
        return reverse_lazy(
            "personnel:employee_detail", kwargs={"pk": self.object.employee.pk}
        )

    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, _("Security profile updated successfully."))
        return super().form_valid(form)


# ==================== QUICK ACCESS VIEWS ====================


class DriverListView(EmployeeListView):
    """Quick access to drivers only."""

    template_name = "personnel/driver_list.html"

    def get_queryset(self):
        """Filter to drivers only."""
        return super().get_queryset().filter(employee_type="driver")


class SecurityListView(EmployeeListView):
    """Quick access to security only."""

    template_name = "personnel/security_list.html"

    def get_queryset(self):
        """Filter to security only."""
        return super().get_queryset().filter(employee_type="security")
