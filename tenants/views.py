from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy

from .decorators import tenant_required, tenant_owner_required
from .models import Tenant, TenantUser, TenantInvitation
from accounts.models import CustomUser


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
    """ View for creating a new tenant (company registration). """

    model = Tenant
    template_name = 'tenants/create.html'
    fields = [
        'name',
        'legal_name',
        'document',
        'slug',
        'email',
        'phone',
    ]
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)

        # Creator automatically becomes the owner of the tenant.
        messages.success(
            self.request,
            f"Company {self.object.name} created successfully!"
        )

        # Set as current tenant
        self.request.session['tenant_id'] = str(self.object.id)
        self.request.user.current_tenant = self.object
        self.request.user.save(update_fields=['current_tenant'])

        return response


@login_required
@tenant_required
@tenant_owner_required
def invite_user(request):
    """ View for inviting users to join a tenant."""
    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role', 'user')

        # Check if the user already exists in the tenant
        existing_user = CustomUser.objects.filter(email=email).first()
        if existing_user:
            if request.tenant.members.filter(user=existing_user).exists():
                messages.error(request, 'User is already a member of this tenant')
                return redirect('tenants:members')

        # Create invitation
        invitation = TenantInvitation.objects.create(
            tenant=request.tenant,
            email=email,
            invited_by=request.user,
            role=role
        )

        # Send invitation email logic
        # send_invitation_email(invitation)

        messages.success(request, f"Invitation sent to {email}")
        return redirect('tenants:members')

    context = {
        'roles': TenantUser.ROLE_CHOICES[1:]
    }
    return render(request, 'tenants/invite.html', context)


@login_required
def accept_invitation(request, token):
    """ View for accepting a tena t invitation. """
    invitation = get_object_or_404(TenantInvitation, token=token)

    if not invitation.is_valid():
        messages.error(request, 'This invitation has expired or already been used.')
        return redirect('login')

    # Check if e-mail matches
    if request.user.email != invitation.email:
        messages.error(request, 'This invitation was sent to a different email address.')
        return redirect('dashboard')

    # Accepting the invitation
    membership = invitation.accept(request.user)

    # Set as the current tenant
    request.session['tenant_id'] = str(invitation.tenant.id)
    request.user.current_tenant = invitation.tenant
    request.user.save(update_fields=['current_tenant'])

    messages.success(request, f"You've joined {invitation.tenant.name}!")
    return redirect('dashboard')
