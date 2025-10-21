from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView

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
                messages.error(
                    request,
                    f"{request.user.username} does not have access to {tenant.name}."
                )
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

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)

        # Creator automatically becomes the owner of the tenant.
        tenant = self.object
        tenant.add_member(
            user=self.requiest.user,
            role='owner',
            is_owner=True
        )

        messages.success(
            self.request,
            f"Company {tenant.name} created successfully!"
        )

        # Set as current tenant
        self.request.session['tenant_id'] = str(tenant.id)
        self.request.user.current_tenant = tenant
        self.request.user.save(update_fields=['current_tenant'])

        return response


class TenantDetailView(LoginRequiredMixin, DetailView):
    """ View for displaying tenant details. """

    model = Tenant
    template_name = 'tenants/detail.html'
    context_object_name = 'tenant'
    pk_url_kwarg = 'tenant_id'

    def get_queryset(self):
        return Tenant.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.get_object()

        # Check user permission
        if not self.request.user.has_tenant_permission(tenant):
            raise PermissionDenied(f"You do not have access to this tenant.")

        # Get member count and recent members
        context['member_count'] = tenant.members.filter(is_active=True).count()
        context['recent_members'] = tenant.members.filter(
            is_active=True
        ).select_related('user').order_by('-joined_at')[:5]

        return context


class TenantUpdateView(LoginRequiredMixin, UpdateView):
    """ View for updating tenant information. """

    model = Tenant
    template_name = 'tenants/update.html'
    fields = [
        'name',
        'legal_name',
        'email',
        'phone',
        'address',
        'plan'
    ]
    pk_url_kwarg = 'tenant_id'

    def get_queryset(self):
        return Tenant.objects.filter(is_active=True)

    def get_success_url(self):
        return reverse_lazy('tenants:detail', kwargs={'tenant_id': self.object.id})

    def dispatch(self, request, *args, **kwargs):
        tenant = self.get_object()
        # Only owner can update tenant information
        try:
            membership = TenantUser.objects.get(
                user=request.user,
                tenant=tenant,
                is_active=True
            )
            if not membership.is_owner:
                raise PermissionDenied("Only tenant owners can edit this tenant.")
        except TenantUser.DoesNotExist:
            raise PermissionDenied("You are not a member of this tenant.")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Tenant information updated successfully!")
        return super().form_valid(form)


class TenantMemberListView(LoginRequiredMixin, ListView):
    """ View for listing all members of a tenant. """
    template_name = 'tenants/memebrs_list.html'
    context_object_name = 'members'
    paginate_by = 20

    def get_queryset(self):
        tenant_id = self.kwargs.get('tenant_id')
        tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)

        # Check user permission
        if not self.request.user.has_tenant_permission(tenant):
            raise PermissionDenied("You don't have access to this tenant.")

        return tenant.members.filter(is_active=True).selected_related(
            'user'
        ).order_by('-is_owner', '-joined_at')

    


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
