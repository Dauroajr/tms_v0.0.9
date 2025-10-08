import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class TenantAuditLog(models.Model):
    """ Audit log for tracking all tenant-related operations. """

    ACTION_CHOICES = [
        ("create", _("Create")),
        ("update", _("Update")),
        ("delete", _("Delete")),
        ("view", _("View")),
        ("login", _("Login")),
        ("logout", _("Logout")),
        ("permission_change", _("Permission Change")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=255, blank=True, null=True)
    changes = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenant_audit_log'
        indexes = [
            models.Index(fields=['tenant', '-timestamp']),
            models.Index(fields=['tenant', 'user', 'action'])
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} - {self.timestamp}"
