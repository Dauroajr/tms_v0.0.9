from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from django.utils.translation import gettext_lazy as _

from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import CustomUser


class RegisterView(CreateView):
    """ View for user registration. """

    model = CustomUser
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('tenants:select')

    def dispatch(self, request, *args, **kwargs):
        """ Redirect authenticated users to tenant selection. """
        if request.user.is_authenticated:
            return redirect('tenants:select')
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        """ Process valid registration form."""
        response = super().form_valid(form)
        user = self.object

        # Log the user in automatically
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')

        messages.success(
            self.request,
            _('Registration successfull! Welcome, {name}!').format(
                name=user.get_full_name() or user.username
            )
        )
        return response

    def form_invalid(self, form):
        """ Handle invalid form submission. """
        messages.error(
            self.request,
            _('Please correct the errors below.')
        )
        return super().form_invalid(form)


class LoginView(DjangoLoginView):
    """ Custom login view. """

    form_class = UserLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        """ Redirect to tenant selection or dashboard. """
        user = self.request.user

        # if user has tenants, go to selection.
        if user.get_tenants().exists():
            if user.current_tenant:
                return reverse_lazy('dashboard')
            return reverse_lazy('tenants:select')

        # Otherwise, prompt to create a tenant.
        messages.info(
            self.request,
            _('Welcome! Please create your first organization.')
        )
        return reverse_lazy('tenants:create')

    def form_valid(self, form):
        """ Process valid login """
        messages.success(
            self.request,
            _('Welcome back, {name}!').format(
                name=form.get_user().get_full_name() or form.get_user.username
            )
        )
        return super().form_valid(form)


class LogoutView(DjangoLogoutView):
    """ Custom Logout View. """

    next_page = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        """ Add logout message. """
        if request.user.is_authenticated:
            messages.success(request, _('You have been logged out successfully.'))
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, DetailView):
    """ View for displaying user profile. """

    model = CustomUser
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'

    def get_objects(self, queryset=None):
        """ Return the current user. """
        return self.request.user

    def get_context_data(self, **kwargs):
        """ Add additional context, if needed. """
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        # Get user's tenants and memberships
        context['tenants'] = user.get_tenants()
        context['memberships'] = user.tenant_memberships.filter(
            is_active=True
        ).select_related('tenant').order_by('-date_joined')

        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """ View for updating user profile. """

    model = CustomUser
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        """ Return the current user. """
        return self.request.user

    def form_valid(self, form):
        """ Process valid profile update. """
        messages.success(
            self.request,
            _('Ypur profile has been updated successfully.')
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """ Handle invalid form submission. """
        messages.error(
            self.request,
            _('Please correct the errors below.')
        )
        return super().form_invalid(form)


@login_required
def deçlete_account(request):
    """ View for account deletion. """
    if request.method == 'POST':
        user = request.user

        # Check if the user is the sole owner of any tenant.
        sole_owner_tenants = []
        for membership in user.memberships.filter(is_owner=True, is_active=True):
            other_owners = membership.tenant.members.filter(
                is_owner=True,
                is_active=True
            ).exclude(user=user)

            if not other_owners.exists():
                sole_owner_tenants.append(membership.tenant)

        if sole_owner_tenants:
            messages.error(
                request,
                _(
                    'Cannot delete account. You are the sole owner of: {tenants}. '
                    'Please transfer opwnership or delete these organizations first.'
                ).format(
                    tenants=', '.join([t.name for t in sole_owner_tenants])
                )
            )
            return redirect('accounts:profile')

        # deactivate user instead of deleting (soft delete)
        user.is_active = False
        user.save()

        logout(request)

        messages.success(
            request,
            _('Your account has been deactiveted successfully.')
        )
        return redirect('home')

    return render(request, 'accounts/delete_account.html')
