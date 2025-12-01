import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from audit.models import TenantAuditLog
from tenants.middleware import get_current_user
from personnel.models import Driver
from .models import Vehicle, VehicleAssignment, MaintenanceRecord


logger = logging.getLogger('fleet')


@receiver(post_save, sender=Vehicle)
def log_vehicle_change(sender, instance, created, **kwargs):
    """ Log vehicle creation/update. """
    user = get_current_user()

    if not user or not user.is_authenticated:
        return
    try:
        ...
