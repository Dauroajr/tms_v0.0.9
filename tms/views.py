from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _


def home_view(request):
    context = {
        # "welcome_message": messages.success(request, _('Welcome to TMS')),
    }
    return render(request, 'home.html', context)


@login_required
def dashboard_view(request):
    """ Dashboard view. Requires logged in user and tenant selection. """
    context = {}

    if not hasattr(request.user, 'tenant') or not request.tenant:
        messages.warning(
            request,
            _('Please select an organization to access the dashboard.')
        )
        return redirect('tenants:select')

    return render(request, 'dashboard.html', context)
