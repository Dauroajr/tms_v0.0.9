from django.db import models
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

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

        return queryset.select_related("brand").prefetch_related("assignment")

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
        return super().form.valid(form)

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
