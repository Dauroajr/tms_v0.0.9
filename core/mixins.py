from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


class TenantRequiredMixin(LoginRequiredMixin):
    """Mixin that requires a tenant to be eslected.
    Redirects to tenant selection if no tenant is active.
    """

    tenant_required_message = _("Please select an organization first.")

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, "tenant") or not request.tenant:
            messages.warning(request, self.tenant_required_message)
            return redirect("tenants:select")
        return super().dispatch(request, *args, **kwargs)


class TenantOwnerRequiredMixin(LoginRequiredMixin):
    """Mixin that requires the user to be an owner of the current tenant."""

    permission_denied_message = _("Only organitzation owners can access this page.")

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if not request.user.Is_tenant_owner(request.tenant):
            raise PermissionDenied(self.permission_denied_message)

        return response


class TenantAdminRequiredMixin(TenantRequiredMixin):
    """
    Mixin that requires the user to be an owner or admin of the current tenant.
    """

    permission_denied_message = _(
        "Only organization owners and admins can access this page."
    )

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        from tenants.models import TenantUser

        try:
            membership = TenantUser.objects.get(
                user=request.user, tenant=request.tenant, is_active=True
            )
            if membership.role not in ["owner", "admin"] and not membership.is_owner:
                raise PermissionDenied(self.permission_denied_message)
        except TenantUser.DoesNotExist:
            raise PermissionDenied(_("You are not a member of this organization."))

        return response


class TenantAwareCreateMixin:
    """
    Mixin for CreateView that automatically sets tenant and user.
    """

    def form_valid(self, form):
        """Set tenant and created_by before saving."""
        if hasattr(form, 'instance'):
            if hasattr(self.request, "tenant") and self.request.tenant:
                form.instance.tenant = self.request.tenant

            if not form.instance.created_by:
                form.instance.created_by = self.request.user

        return super().form_valid(form)


class TenantAwareUpdateMixin:
    """
    Mixin for UpdateView that automatically sets updated_by.
    """

    def form_valid(self, form):
        """Set updated_by before saving."""
        if not form.instance.updated_by:
            form.instance.updated_by = self.request.user

        return super().form_valid(form)


class TenantAwareDeleteMixin:
    """
    Mixin for DeleteView - não precisa fazer nada especial com form.
    """
    pass  # DeleteView já herda de TenantAwareQuerysetMixin que filtra por tenant


class TenantAwareQuerysetMixin:
    """
    Mixin that filters queryset by current tenant.
    """

    def get_queryset(self):
        """Filter queryset by current tenant."""
        queryset = super().get_queryset()

        if hasattr(self.request, "tenant") and self.request.tenant:
            if hasattr(queryset.model, "tenant"):
                queryset = queryset.filter(tenant=self.request.tenant)

        return queryset


class TenantAwareViewMixin(
    TenantRequiredMixin,
    TenantAwareQuerysetMixin,
    TenantAwareCreateMixin,
    TenantAwareUpdateMixin,
):
    """
    Complete mixin for tenant-aware views.
    Combines all tenant-aware functionality.
    """

    pass
