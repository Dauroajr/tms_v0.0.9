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
    return getattr(_thread_locals, 'tenant', None)


def set_current_user(user):
    """Set the current user in thread-local storage"""
    _thread_locals.user = user


def get_current_user():
    """Get the current user from thread-local storage"""
    return getattr(_thread_locals, 'user', None)


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
        hostname = request.get_host().split(':')[0].lower()
        parts = hostname.split('.')
        
        # Assuming format: tenant-slug.domain.com
        if len(parts) > 2:
            subdomain = parts[0]
            # Skip www and other reserved subdomains
            if subdomain not in ['www', 'api', 'admin', 'static']:
                try:
                    return Tenant.objects.get(slug=subdomain, is_active=True)
                except Tenant.DoesNotExist:
                    pass
        
        return None
    
    def get_tenant_from_header(self, request):
        """Extract tenant from X-Tenant-ID header"""
        tenant_id = request.META.get('HTTP_X_TENANT_ID')
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                pass
        
        return None
    
    def get_tenant_from_session(self, request):
        """Extract tenant from session"""
        tenant_id = request.session.get('tenant_id')
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                # Clear invalid tenant from session
                del request.session['tenant_id']
        
        return None
    
    def get_tenant_from_user(self, request):
        """Get user's current tenant"""
        if hasattr(request.user, 'current_tenant'):
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
            '/auth/login/',
            '/auth/register/',
            '/auth/logout/',
            '/invitations/accept/',
            '/api/health/',
        ]
        return any(request.path.startswith(path) for path in public_paths)
    
    def clear_thread_locals(self):
        """Clear thread-local storage"""
        if hasattr(_thread_locals, 'tenant'):
            del _thread_locals.tenant
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user


# tenant/decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def tenant_required(function=None, redirect_url='/select-tenant/'):
    """
    Decorator to ensure a tenant is selected
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request, 'tenant') or request.tenant is None:
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
        if not hasattr(request, 'tenant') or request.tenant is None:
            raise PermissionDenied("Tenant required")
        
        try:
            membership = TenantUser.objects.get(
                user=request.user,
                tenant=request.tenant,
                is_active=True
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
            if not hasattr(request, 'tenant') or request.tenant is None:
                raise PermissionDenied("Tenant required")
            
            if not request.user.has_tenant_permission(request.tenant, permission):
                raise PermissionDenied(f"Permission '{permission}' required")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


# tenant/context_processors.py
def tenant_context(request):
    """
    Add tenant information to template context
    """
    context = {
        'current_tenant': None,
        'user_tenants': [],
        'is_tenant_owner': False,
        'tenant_role': None,
    }
    
    if hasattr(request, 'tenant') and request.tenant:
        context['current_tenant'] = request.tenant
        
        if request.user.is_authenticated:
            # Get all user's tenants
            context['user_tenants'] = request.user.get_tenants()
            
            # Check if user is owner of current tenant
            try:
                membership = TenantUser.objects.get(
                    user=request.user,
                    tenant=request.tenant,
                    is_active=True
                )
                context['is_tenant_owner'] = membership.is_owner
                context['tenant_role'] = membership.role
            except TenantUser.DoesNotExist:
                pass
    
    return context


# settings.py - Key configurations
"""
Add these configurations to your Django settings.py file:
"""

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Middleware configuration (order matters!)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tenant.middleware.TenantMiddleware',  # Must come after AuthenticationMiddleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Context processors
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'tenant.context_processors.tenant_context',  # Add tenant context
            ],
        },
    },
]

# Tenant-specific settings
TENANT_MODEL = 'tenant.Tenant'
TENANT_SUBDOMAIN_PREFIX = 'app'  # e.g., tenant1.app.yourdomain.com
TENANT_DEFAULT_SLUG = 'demo'  # For development/testing

# Session configuration for tenant isolation
SESSION_COOKIE_NAME = 'tenant_sessionid'
SESSION_
