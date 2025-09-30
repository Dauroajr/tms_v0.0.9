# tenant/decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

from .models import TenantUser


def tenant_required(function=None, redirect_url="/select-tenant/"):
    """
    Decorator to ensure a tenant is selected
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request, "tenant") or request.tenant is None:
                if request.user.is_authenticated:
                    messages.warning(request, "Please select a tenant first.")
                    return redirect(redirect_url)
                else:
                    raise PermissionDenied("Tenant required")
            return view_func(request, *args, **kwargs)

        return wrapped_view

    if function:
        return decorator(function)
    return decorator


def tenant_owner_required(view_func):
    """
    Decorator to ensure the user is a tenant owner
    """

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request, "tenant") or request.tenant is None:
            raise PermissionDenied("Tenant required")

        try:
            membership = TenantUser.objects.get(
                user=request.user, tenant=request.tenant, is_active=True
            )
            if not membership.is_owner:
                raise PermissionDenied("Only tenant owners can perform this action")
        except TenantUser.DoesNotExist:
            raise PermissionDenied("You are not a member of this tenant")

        return view_func(request, *args, **kwargs)

    return wrapped_view


def tenant_permission_required(permission):
    """
    Decorator to check specific tenant permissions
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request, "tenant") or request.tenant is None:
                raise PermissionDenied("Tenant required")

            if not request.user.has_tenant_permission(request.tenant, permission):
                raise PermissionDenied(f"Permission '{permission}' required")

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator
