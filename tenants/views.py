from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
                    _(f"{request.user.username} does not have access to {tenant.name}.")
                )
                return redirect('tenants:select')

            # Set tenant in session and user model
            request.session['tenant_id'] = str(tenant.id)
            request.user.current_tenant = tenant
            request.user.save(update_fields=['current_tenant'])

            messages.success(request, _(f"Switched to {tenant.name}"))
            return redirect('dashboard')
        except Tenant.DoesNotExist:
            messages.error(request, _("Invalid tenant selection."))
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
            user=self.request.user,
            role='owner',
            is_owner=True
        )

        messages.success(
            self.request,
            _(f"Company {tenant.name} created successfully!")
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
            raise PermissionDenied(_("You do not have access to this tenant."))

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
                raise PermissionDenied(_("Only tenant owners can edit this tenant."))
        except TenantUser.DoesNotExist:
            raise PermissionDenied(_("You are not a member of this tenant."))

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, _("Tenant information updated successfully!"))
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
            raise PermissionDenied(_("You don't have access to this tenant."))

        return tenant.members.filter(is_active=True).selected_related(
            'user'
        ).order_by('-is_owner', '-joined_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = self.kwargs.get('tenant_id')
        tenant = get_object_or_404(Tenant, id=tenant_id)

        context['tenant'] = tenant
        context['pending_invitations'] = tenant.invitations.filter(
            accepted_at__isnull=True,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')

        # Check if current user is owner
        try:
            membership = TenantUser.objects.get(
                user=self.request.user,
                tenant=tenant,
                is_active=True
            )
            context['is_owner'] = membership.is_owner
        except TenantUser.DoesNotExist:
            context['is_owner'] = False

        return context


@login_required
@tenant_required
@tenant_owner_required
def invite_user(request):
    """ View for inviting users to join a tenant."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'user')

        if not email:
            messages.error(request, _('Email is required.'))
            return redirect('tenants:members', tenant_id=request.tenant.id)

        try:
            # Attempt to create invitation with validation
            invitation = TenantInvitation(
                tenant=request.tenant,
                email=email,
                invited_by=request.user,
                role=role
            )
            invitation.full_clean()
            invitation.save()

            messages.success(request, _(f"Invitation sent to {email}"))
            return redirect('tenants:members', tenant_id=request.tenant_id)

        except ValidationError as e:
            messages.error(request, str(e.message))
            return redirect('tenants:members', tenant_id=request.tenant_id)
        except Exception as e:
            messages.error(request, _(f"An error has occurred: {str(e)}"))
            return redirect('tenants>members', tenant_id=request.tenant_id)

    context = {
        'roles': TenantUser.ROLE_CHOICES[1:],
        'tenant': request.tenant
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
        messages.error(request, _('This invitation was sent to a different email address.'))
        return redirect('dashboard')

    try:
        # Accepting the invitation
        with transaction.atomic():
            membership = invitation.accept(request.user)  # noqa

            # Set as the current tenant
            request.session['tenant_id'] = str(invitation.tenant.id)
            request.user.current_tenant = invitation.tenant
            request.user.save(update_fields=['current_tenant'])

            messages.success(request, _(f"You've joined {invitation.tenant.name}!"))
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('dashboard')

    return redirect('dashboard')


@login_required
@tenant_required
@tenant_owner_required
def remove_member(request, tenant_id, user_id):
    """ View for removing a member from a tenant. """

    tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)

    # Verify user is owner
    try:
        membership = TenantUser.objects.get(
            user=request.user,
            tenant=tenant,
            is_active=True
        )
        if not membership.is_owner:
            raise PermissionDenied(_("Only tenant owners can remove members."))
    except TenantUser.DoesNotExist:
        raise PermissionDenied(_("You are not a member of this tenant."))

    # Get the member to remove
    member = get_object_or_404(
        TenantUser,
        id=user_id,
        tenant=tenant
    )

    # Prevent removing the last owner
    if member.is_owner:
        other_owners = tenant.members.filter(
            is_owner=True,
            is_active=True
        ).exclude(id=member.id).exists()

        if not other_owners:
            messages.error(request, _("Cannot remove the last owner of the tenant."))
            return redirect('tenants:members', tenant_id=tenant_id)

    # Remove member
    if request.method == 'POST':
        member.is_active = False
        member.save(update_fields=['is_active'])
        messages.success(request, _(f"{member.user.email} has been removed from {tenant.name}"))
        return redirect('tenants:members', tenant_id=tenant_id)

    context = {
        'member': member,
        'tenant': tenant
    }
    return render(request, 'tenants/remove_member.html', context)
