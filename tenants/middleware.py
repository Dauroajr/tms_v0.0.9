# tenant/middleware.py
import threading
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from .models import Tenant, TenantUser

# Thread-local storage for tenant and user context
_thread_locals = threading.local()


def set_current_tenant(tenant):
    """Set the current tenant in thread-local storage"""
    _thread_locals.tenant = tenant


def get_current_tenant():
    """Get the current tenant from thread-local storage"""
    return getattr(_thread_locals, "tenant", None)


def set_current_user(user):
    """Set the current user in thread-local storage"""
    _thread_locals.user = user


def get_current_user():
    """Get the current user from thread-local storage"""
    return getattr(_thread_locals, "user", None)


class TenantMiddleware:
    """
    Middleware to handle tenant detection and context injection
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Clear thread locals at the start of each request
        self.clear_thread_locals()

        # Detect and set tenant
        tenant = self.get_tenant(request)

        if tenant:
            request.tenant = tenant
            set_current_tenant(tenant)

            # Validate user access to tenant
            if request.user.is_authenticated and not request.user.is_superuser:
                self.validate_tenant_access(request, tenant)
        else:
            request.tenant = None

        # Set current user in thread local
        if request.user and not isinstance(request.user, AnonymousUser):
            set_current_user(request.user)

        response = self.get_response(request)

        # Clear thread locals after response
        self.clear_thread_locals()

        return response

    def get_tenant(self, request):
        """
        Detect tenant from request using multiple strategies
        """
        tenant = None

        # Strategy 1: Subdomain
        tenant = self.get_tenant_from_subdomain(request)

        # Strategy 2: Header (for API requests)
        if not tenant:
            tenant = self.get_tenant_from_header(request)

        # Strategy 3: Session (for authenticated users)
        if not tenant and request.user.is_authenticated:
            tenant = self.get_tenant_from_session(request)

        # Strategy 4: User's current tenant
        if not tenant and request.user.is_authenticated:
            tenant = self.get_tenant_from_user(request)

        return tenant

    def get_tenant_from_subdomain(self, request):
        """Extract tenant from subdomain"""
        hostname = request.get_host().split(":")[0].lower()
        parts = hostname.split(".")

        # Assuming format: tenant-slug.domain.com
        if len(parts) > 2:
            subdomain = parts[0]
            # Skip www and other reserved subdomains
            if subdomain not in ["www", "api", "admin", "static"]:
                try:
                    return Tenant.objects.get(slug=subdomain, is_active=True)
                except Tenant.DoesNotExist:
                    pass

        return None

    def get_tenant_from_header(self, request):
        """Extract tenant from X-Tenant-ID header"""
        tenant_id = request.META.get("HTTP_X_TENANT_ID")
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                pass

        return None

    def get_tenant_from_session(self, request):
        """Extract tenant from session"""
        tenant_id = request.session.get("tenant_id")
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                # Clear invalid tenant from session
                del request.session["tenant_id"]

        return None

    def get_tenant_from_user(self, request):
        """Get user's current tenant"""
        if hasattr(request.user, "current_tenant"):
            return request.user.current_tenant
        return None

    def validate_tenant_access(self, request, tenant):
        """Validate that the user has access to the tenant"""
        # Check if user is a member of the tenant
        if not request.user.has_tenant_permission(tenant):
            # Check if this is a public route (e.g., invitation acceptance)
            if not self.is_public_route(request):
                raise PermissionDenied("You don't have access to this tenant")

    def is_public_route(self, request):
        """Check if the current route is public"""
        public_paths = [
            "/auth/login/",
            "/auth/register/",
            "/auth/logout/",
            "/invitations/accept/",
            "/api/health/",
        ]
        return any(request.path.startswith(path) for path in public_paths)

    def clear_thread_locals(self):
        """Clear thread-local storage"""
        if hasattr(_thread_locals, "tenant"):
            del _thread_locals.tenant
        if hasattr(_thread_locals, "user"):
            del _thread_locals.user
