import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TenantManager(models.Manager):
    """Custom Manager for Tenant model to handle active tenants."""

    def active(self):
        """Returns only active tenants."""
        return self.filter(is_active=True)

    def for_user(self, user):
        """Returns tenants accessible by a specific user."""
        return self.filter(
            members__user=user,
            members__is_active=True,
            is_active=True,
        ).distinct()


class Tenant(models.Model):
    """Main tenant model: represents a company or organization."""

    PLAN_CHOICES = [
        ("free", _("Free")),
        ("basic", _("Basic")),
        ("premium", _("Premium")),
        ("entreprise", _("Enterprise")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text=_("Unique identifier for the tenant, used ni URLs and subdomains"),
    )
    name = models.CharField(max_length=200, help_text=_("Display name"))
    legal_name = models.CharField(max_length=200, help_text=_("Legal company name"))
    document = models.CharField(
        max_length=30,
        unique=True,
        help_text=_("Unique identifier like SSN or Tax ID, CPF or CNPJ"),
    )
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=250, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    settings = models.JSONField(default=dict, blank=True, null=True)
    subscription_expires_at = models.DateTimeField(blank=True, null=True)

    objects = TenantManager()

    class Meta:
        db_table = "tenants"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "plan"]),
        ]

    def __str__(self):
        return self.name

    def add_member(self, user, role="user", is_owner=False, invited_by=None):
        """Adds a new member to the tenant."""
        membership, created = TenantUser.objects.get_or_create(
            tenant=self,
            user=user,
            defaults={"role": role, "is_owner": is_owner, "invited_by": invited_by},
        )
        return membership


class TenantUser(models.Model):
    """Many-To-Many relationship between User and Tenant."""

    ROLE_CHOICES = [
        ("owner", _("Owner")),
        ("admin", _("Administrator")),
        ("manager", _("Manager")),
        ("user", _("User")),
        ("viewer", _("Viewer")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_memberships",
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="members")
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="user")
    is_owner = models.BooleanField(default=False)
    permissions = models.JSONField(default=list, blank=True)

    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="invitations_sent",
    )
    is_active = models.BooleanField(default=True)
    last_access = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "tenant_users"
        unique_together = ["user", "tenant"]
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.tenant.name} ({self.role})"

    def get_permissions(self):
        """Get all permissions for this membership."""
        role_permissions = {
            "owner": ["all"],
            "admin": ["read", "write", "delete", "invite"],
            "manager": ["read", "write", "invite"],
            "user": ["read", "write"],
            "viewer": ["read"],
        }
        base_permissions = role_permissions.get(self.role, [])
        return list(set(base_permissions + self.permissions))


class TenantInvitation(models.Model):
    """Manages invitations to join tenants."""

    ROLE_CHOICES = TenantUser.ROLE_CHOICES[:1]  # Exclude 'owner' role from invitations
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("accepted", _("Accepted")),
        ("declined", _("Declined")),
        ("expired", _("Expired")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="invitations"
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invitations_created",
    )
    email = models.EmailField()
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="user")
    token = models.CharField(max_length=128, unique=True, default=secrets.token_urlsafe)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(blank=True, null=True)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="invitations_accepted",
    )

    class Meta:
        db_table = "tenant_invitations"
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["tenant", "email", "expires_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def clean(self):
        """Validate invitation before saving."""
        from accounts.models import CustomUser

        try:
            user = CustomUser.objects.get(email=self.email)
            if self.tenant.members.filter(user=user, is_active=True).exists():
                raise ValidationError(
                    _("This user is already a member of this tenant.")
                )
        except CustomUser.DoesNotExist:
            pass

        # Check if there's already a pending invitation for this e-mail.

        if not self.pk:  # Only check on creation
            existing = TenantInvitation.objects.filter(
                tenant=self.tenant,
                email=self.email,
                accepted_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).first()
            if existing:
                raise ValidationError(
                    _("There is already a pending invitation for this e-mail.")
                )

    def is_valid(self):
        """Check if the invitation is still valid (not expired and pending)."""
        return self.accepted_at is None and self.expires_at > timezone.now()

    def accept(self, user):
        """Accept invitation."""
        if not self.is_valid():
            raise ValueError("Invitation is no longer valid.")

        if user.email != self.email:
            raise ValueError('Invitation e-mail does not match user e-mail')

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
