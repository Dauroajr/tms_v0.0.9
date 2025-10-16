from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _


def home_view(request):
    context = {
        # "welcome_message": messages.success(request, _('Welcome to TMS')),
    }
    return render(request, 'home.html', context)
