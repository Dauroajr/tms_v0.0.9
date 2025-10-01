from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy

from .decorators import tenant_required, tenant_owner_required
from .models import Tenant, TenantUser, TenantInvitation


class TenantSelectView(LoginRequiredMixin, ListView):
    """ View for selecting a tenant when the user belongs to multiple tenants. """

    template_name = 'tenants/select.html'
    context_object_name = 'memberships'

    def get_queryset(self):
        return self.request.user.tenant_memberships.filter(
            is_active=True
        ).select_related('tenant')

    def post(self, request, *args, **kwargs):
        tenant_id = request.POST.get('tenant_id')
        try:
            tenant = Tenant.objects.get(id=tenant_id, is_active=True)

            if not request.user.has_tenant_permission(tenant):
                messages.error(request, f"{request.user.username} does not have access to {tenant.name}.")
                return redirect('tenants:select')

            # Set tenant in session and user model
            request.session['tenant_id'] = str(tenant.id)
            request.user.current_tenant = tenant
            request.user.save(update_fields=['current_tenant'])

            messages.success(request, f"Switched to {tenant.name}")
            return redirect('dashboard')
        except Tenant.DoesNotExist:
            messages.error(request, "Invalid tenant selection.")
            return redirect('tenants:select')


class TenantCreateView(LoginRequiredMixin, CreateView):
    ...
