from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def get_tenant_from_request(request):
    """
    Get the current tenant from request.
    Returns None if no tenant is set.
    """

    return getattr(request, "tenant", None)


def require_tenant(request):
    """
    Ensure request has a tenant set.
    Raises ValidationError if no tenant is found.
    """

    tenant = get_tenant_from_request(request)
    if not tenant:
        raise ValidationError(_("Tenant context is required for this operation."))
    return tenant


def switch_tenant(request, tenant):
    """Switch the current user to a different tenant.

    Args:
        request: HttpRequest object
        tenant: Tenant object to switch to

    Returns:
        bool: True if switch was successful
    """

    user = request.user

    if not user.is_authenticated:
        return False

    # Check if user has access to this tenant
    if not user.has_tenant_permission(tenant):
        return False

    # Update session
    request.session["tenant_id"] = str(tenant.id)

    # Update user's current tenant
    user.current_tenant = tenant
    user.save(update_fields=["current_tenant"])

    return True


def get_user_tenants(user):
    """
    Get all tenants accessible by a user.

    Args:
        user: User object

    Returns:
        QuerySet: Tenant queryset
    """

    if not user.is_authenticated:
        return []

    return user.get_tenants()


def create_with_tenant(model_class, tenant, **kwargs):
    """
    Helper to create an object with explicit tenant.

    Args:
        model_class: Model class to create
        tenant: Tenant object
        **kwargs: Field values for the model

    Returns:
        Created object instance
    """

    obj = model_class(tenant=tenant, **kwargs)
    obj.save(skip_tenant_check=True)
    return obj


def bulk_create_with_tenant(model_class, tenant, objects_data):
    """
    Bulk create objects with tenant.

    Args:
        model_class: Model class
        tenant: Tenant object
        objects_data: List of dicts with object data

    Returns:
        List of created objects
    """

    objects = []
    for data in objects_data:
        obj = model_class(tenant=tenant, **data)
        objects.append(obj)

    # Use all_objects to bypass tenant filtering
    return model_class.all_objects.bulk_create(objects)


def clone_for_tenant(obj, target_tenant, exclude_fields=None):
    """
    Clone an object to a different tenant.

    Args:
        obj: Object to clone
        target_tenant: Target tenant
        exclude_fields: Fields to exclude from cloning

    Returns:
        Cloned object
    """

    if exclude_fields is None:
        exclude_fields = ["id", "pk", "created_at", "updated_at"]

    # Get all field values
    data = {}
    for field in obj._meta.fields:
        if field.name not in exclude_fields:
            data[field.name] = getattr(obj, field.name)

    # Override tenant
    data["tenant"] = target_tenant

    # Create new object
    new_obj = obj.__class__(**data)
    new_obj.save(skip_tenant_check=True)

    return new_obj


def validate_tenant_access(user, tenant, permission=None):
    """
    Validate if user has access to a tenant.

    Args:
        user: User object
        tenant: Tenant object
        permission: Optional specific permission to check

    Returns:
        bool: True if user has access

    Raises:
        PermissionDenied: If user doesn't have access
    """

    from django.core.exceptions import PermissionDenied

    if not user.is_authenticated:
        raise PermissionDenied(_("Authentication required."))

    if not user.has_tenant_permission(tenant, permission):
        raise PermissionDenied(
            _("You do not have permission to access this organization.")
        )
