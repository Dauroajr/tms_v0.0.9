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
        return super().form_invaled(form)


class LoginView(DjangoLoginView):
    """ Custom login view. """
