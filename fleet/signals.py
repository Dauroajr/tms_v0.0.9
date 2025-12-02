import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from audit.models import TenantAuditLog
from tenants.middleware import get_current_user
from personnel.models import Driver
from .models import Vehicle, VehicleAssignment, MaintenanceRecord


logger = logging.getLogger("fleet")


@receiver(post_save, sender=Vehicle)
def log_vehicle_change(sender, instance, created, **kwargs):
    """Log vehicle creation/update."""
    user = get_current_user()

    if not user or not user.is_authenticated:
        return

    try:
        TenantAuditLog.objects.create(
            tenant=instance.tenant,
            user=user,
            action="create" if created else "update",
            model_name="Vehicle",
            object_id=str(instance.id),
            changes={
                "plate": instance.plate,
                "brand": instance.brand,  # .name if instance.brand else None,
                "model": instance.model,
                "status": instance.status,
            },
        )
        logger.info(f"Vehicle {instance.plate} {'created' if created else 'updated'}")
    except Exception as e:
        logger.error(_(f"Error logging vehicle change: {str(e)}"))


@receiver(post_save, sender=VehicleAssignment)
def log_assignment_change(sender, instance, created, **kwargs):
    """Log vehicle assignment."""
    user = get_current_user()

    if not user or not user.is_authenticated:
        return

    try:
        TenantAuditLog.objects.create(
            tenant=instance.tenant,
            user=user,
            action="create" if created else "update",
            model_name="VehicleAssignment",
            object_id=str(instance.id),
            changes={
                "driver": instance.driver.driver_full_name,
                "vehicle": instance.vehicle.plate,
                "is_active": instance.is_active,
                "start_date": str(instance.start_date),
            },
        )
        logger.info(
            f"Assignment: {instance.driver.driver_full_name} → {instance.vehicle.plate} "
            f"({'active' if instance.is_active else 'ended'})"
        )
    except Exception as e:
        logger.error(f"Error logging assignment change: {str(e)}")


@receiver(post_save, sender=MaintenanceRecord)
def log_maintenance_change(sender, instance, created, **kwargs):
    """Log maintenance record."""
    user = get_current_user()

    if not user or not user.is_authenticated:
        return

    try:
        TenantAuditLog.objects.create(
            tenant=instance.tenant,
            user=user,
            action="create" if created else "update",
            model_name="MaintenanceRecord",
            object_id=str(instance.id),
            changes={
                "vehicle": instance.vehicle.plate,
                "maintenance_type": instance.maintenance_type,
                "status": instance.status,
                "scheduled_date": str(instance.scheduled_date),
            },
        )
        logger.info(
            f"Maintenance for {instance.vehicle.plate}: "
            f"{instance.get_maintenance_type_display()} - {instance.status}"
        )
    except Exception as e:
        logger.error(f"Error logging maintenance change: {str(e)}")
