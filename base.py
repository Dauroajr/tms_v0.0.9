# accounts/models.py

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class CustomUser(AbstractUser):
    """
    Extends Django's AbstractUser for multi-tenant support.
    This model should be set as AUTH_USER_MODEL in settings.py
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    current_tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_users',
        help_text="Currently active tenant for this user"
    )
    phone = models.CharField(max_length=20, blank=True)
    document_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="CPF or CNPJ"
    )
    document_type = models.CharField(
        max_length=4,
        choices=[('CPF', 'CPF'), ('CNPJ', 'CNPJ')],
        default='CPF'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_login_users'
    )

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['document_number']),
        ]

    def get_tenants(self):
        """Returns all tenants this user belongs to"""
        return self.tenant_memberships.filter(is_active=True).select_related('tenant')

    def has_tenant_permission(self, tenant, permission=None):
        """Check if user has specific permission in a tenant"""
        try:
            membership = self.tenant_memberships.get(tenant=tenant, is_active=True)
            if permission:
                return permission in membership.get_permissions()
            return True
        except TenantUser.DoesNotExist:
            return False


# tenant/models.py
import uuid
import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class TenantManager(models.Manager):
    """Custom manager for Tenant model"""
    
    def active(self):
        """Returns only active tenants"""
        return self.filter(is_active=True)
    
    def for_user(self, user):
        """Returns tenants accessible by a specific user"""
        return self.filter(
            members__user=user,
            members__is_active=True,
            is_active=True
        ).distinct()


class Tenant(models.Model):
    """
    Main Tenant model - represents a company/organization
    """
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Subdomain identifier"
    )
    name = models.CharField(max_length=100, help_text="Display name")
    legal_name = models.CharField(max_length=200, help_text="Legal company name")
    document = models.CharField(
        max_length=20,
        unique=True,
        help_text="CNPJ"
    )
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    settings = models.JSONField(default=dict)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'tenants'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'plan']),
        ]
    
    def __str__(self):
        return self.name
    
    def add_member(self, user, role='user', is_owner=False, invited_by=None):
        """Add a new member to the tenant"""
        membership, created = TenantUser.objects.get_or_create(
            tenant=self,
            user=user,
            defaults={
                'role': role,
                'is_owner': is_owner,
                'invited_by': invited_by
            }
        )
        return membership


class TenantUser(models.Model):
    """
    Many-to-many relationship between User and Tenant
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('user', 'User'),
        ('viewer', 'Viewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant_memberships'
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='members'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_owner = models.BooleanField(default=False)
    permissions = models.JSONField(default=list, blank=True)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invitations_sent'
    )
    is_active = models.BooleanField(default=True)
    last_access = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tenant_users'
        unique_together = ['user', 'tenant']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.tenant.name} ({self.role})"
    
    def get_permissions(self):
        """Get all permissions for this membership"""
        role_permissions = {
            'owner': ['all'],
            'admin': ['read', 'write', 'delete', 'invite'],
            'manager': ['read', 'write', 'invite'],
            'user': ['read', 'write'],
            'viewer': ['read'],
        }
        base_permissions = role_permissions.get(self.role, [])
        return list(set(base_permissions + self.permissions))


class TenantInvitation(models.Model):
    """
    Manages invitations to join tenants
    """
    ROLE_CHOICES = TenantUser.ROLE_CHOICES[1:]  # Exclude 'owner'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invitations_created'
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invitations_accepted'
    )
    
    class Meta:
        db_table = 'tenant_invitations'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['tenant', 'email', 'expires_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if invitation is still valid"""
        return (
            self.accepted_at is None and
            self.expires_at > timezone.now()
        )
    
    def accept(self, user):
        """Accept the invitation"""
        if not self.is_valid():
            raise ValueError("Invitation is no longer valid")
        
        self.accepted_at = timezone.now()
        self.accepted_by = user
        self.save()
        
        # Create tenant membership
        return TenantUser.objects.create(
            user=user,
            tenant=self.tenant,
            role=self.role,
            invited_by=self.invited_by
        )


# core/models.py - Base classes for tenant-aware models
class TenantAwareManager(models.Manager):
    """
    Custom manager that automatically filters by tenant
    """
    def get_queryset(self):
        """
        Override to filter by current tenant from thread local storage
        """
        queryset = super().get_queryset()
        
        # Get current tenant from thread local storage (set by middleware)
        from .middleware import get_current_tenant
        tenant = get_current_tenant()
        
        if tenant:
            return queryset.filter(tenant=tenant)
        return queryset
    
    def for_tenant(self, tenant):
        """Explicit tenant filtering"""
        return super().get_queryset().filter(tenant=tenant)


class TenantAwareModel(models.Model):
    """
    Abstract base class for all models that need tenant isolation
    """
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    
    objects = TenantAwareManager()
    all_objects = models.Manager()  # Bypass tenant filter when needed
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
        ]
    
    def save(self, *args, **kwargs):
        """
        Override save to auto-inject tenant and user info
        """
        from .middleware import get_current_tenant, get_current_user
        
        if not self.tenant_id:
            tenant = get_current_tenant()
            if tenant:
                self.tenant = tenant
            else:
                raise ValueError("Cannot save without tenant context")
        
        user = get_current_user()
        if user and user.is_authenticated:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
        
        super().save(*args, **kwargs)


# audit/models.py
class TenantAuditLog(models.Model):
    """
    Audit log for tracking all tenant-related operations
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('permission_change', 'Permission Change'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    changes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tenant_audit_logs'
        indexes = [
            models.Index(fields=['tenant', '-timestamp']),
            models.Index(fields=['tenant', 'user', 'action']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} - {self.timestamp}"


# Example business model using TenantAwareModel
class Product(TenantAwareModel):
    """
    Example of a tenant-isolated business model
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(default=0)
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'products'
        unique_together = ['tenant', 'sku']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['tenant', 'sku']),
        ]
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
