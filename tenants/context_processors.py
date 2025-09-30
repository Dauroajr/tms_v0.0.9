from tenants.models import TenantUser


# tenant/context_processors.py
def tenant_context(request):
    """
    Add tenant information to template context
    """
    context = {
        "current_tenant": None,
        "user_tenants": [],
        "is_tenant_owner": False,
        "tenant_role": None,
    }

    if hasattr(request, "tenant") and request.tenant:
        context["current_tenant"] = request.tenant

        if request.user.is_authenticated:
            # Get all user's tenants
            context["user_tenants"] = request.user.get_tenants()

            # Check if user is owner of current tenant
            try:
                membership = TenantUser.objects.get(
                    user=request.user, tenant=request.tenant, is_active=True
                )
                context["is_tenant_owner"] = membership.is_owner
                context["tenant_role"] = membership.role
            except TenantUser.DoesNotExist:
                pass

    return context
