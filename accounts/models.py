# accounts/models.py

import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from tenants.models import Tenant, TenantUser


class CustomUser(AbstractUser):
    """
    Extends Django's AbstractUser for multi-tenant support.
    This model should be set as AUTH_USER_MODEL in settings.py
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    current_tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_users',
        help_text=_('Currently active tenant for this user')
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    document_number = models.CharField(
        max_length=30,
        # unique=True,
        blank=True,
        null=True,
        help_text=_('Unique identifier like SSN or Tax ID, CPF or CNPJ')
    )
    document_type = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        choices=[
            ('SSN', 'SSN'),
            ('TAXID', 'Tax ID'),
            ('CPF', 'CPF'),
            ('CNPJ', 'CNPJ')
        ],
        default='CPF'
    )
    last_login_tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='last_login_users',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['document_number'])
        ]

    def __str__(self):
        """String representation of user."""
        full_name = self.get_full_name()
        return f"{full_name or self.username} ({self.email})"

    def get_tenants(self):
        """Returns all tenants the user belongs to."""
        return Tenant.objects.filter(
            members__user=self,
            members__is_active=True,
            is_active=True
        ).distinct()

    def has_tenant_permission(self, tenant, permission=None):
        """
        Check if the user has a specific permission in the given tenant.

        Args:
            tenant: Tenant object to check permission for;
            permission: Optional specificpermission string

        Returns:
            bool: True if user has permission, False otherwise
        """
        if self.is_superuser:
            return True

        try:
            membership = self.tenant_memberships.get(tenant=tenant, is_active=True)
            if permission:
                return permission in membership.get_permissions()
            return True
        except TenantUser.DoesNotExist:
            return False

    def is_tenant_owner(self, tenant):
        """ Check if user is owner of the kgiven tenant."""

        try:
            membership = self.tenant_memberships.get(
                tenant=tenant,
                is_active=True,
            )
            return membership.is_owner
        except TenantUser.DoesNotExtist:
            return False

    def clean(self):
        """ Validate user data. """

        super().clean()

        # Validate document number, if provided.
        if self.document_number and self.document_type:
            if self.document_type == 'CPF':
                self.validate_cpf()
            elif self.document_type == 'CNPJ':
                self.validate_cnpj()

    def validate_cpf(self):
        """ Validate Brazilian CPF format. """
        cpf = ''.join(filter(str.isdigit, self.document_number))

        if len(cpf) != 11:
            raise ValidationError(_('CPF must have 11 digits.'))

        # Check for invalid sequences (all same digits)
        if cpf == cpf[0] * 11:
            raise ValidationError(_('Invalid CPF number.'))

        # Validate check digits
        for i in range(9, 11):
            value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
            digit = ((value * 10) % 11) % 10
            if digit != int(cpf[i]):
                raise ValidationError(_('Invalid CPF number.'))

    def validate_cnpj(self):
        """ Validate Brazilian CNPJ format."""

        cnpj = ''.join(filter(str.isdigit, self.document_number))

        if len(cnpj) != 14:
            raise ValidationError(_('CNPJ must have 14 digits.'))

        # Check for invalid sequences
        if cnpj == cnpj[0] * 14:
            raise ValidationError(_('Invalid CNPJ.'))

        # Validate check digits
        weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        for i in range(12, 14):
            value = sum(int(cnpj[num]) * weights[num + 12 - i] for num in range(i))
            digit = 11 - (value % 11)
            digit = 0 if digit > 9 else digit
            if digit != int(cnpj[i]):
                raise ValidationError(_('Invalid CNPJ.'))
