import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from audit.models import TenantAuditLog
from tenants.middleware import get_current_user
from .models import Employee, DriverProfile, SecurityProfile

logger = logging.getLogger("personnel")


@receiver(post_save, sender=Employee)
def log_employee_change(sender, instance, created, **kwargs):
    """Log employee creation/update."""
    user = get_current_user()

    if not user or not user.is_authenticated:
        return

    try:
        TenantAuditLog.objects.create(
            tenant=instance.tenant,
            user=user,
            action="create" if created else "update",
            model_name="Employee",
            object_id=str(instance.id),
            changes={
                "employee_number": instance.employee_number,
                "full_name": instance.full_name,
                "employee_type": instance.employee_type,
                "status": instance.status,
            },
        )
        logger.info(
            f"Employee {instance.full_name} ({instance.employee_number}) "
            f"{'created' if created else 'updated'}"
        )
    except Exception as e:
        logger.error(f"Error logging employee change: {str(e)}")


@receiver(pre_save, sender=Employee)
def auto_generate_employee_number(sender, instance, **kwargs):
    """Auto-generate employee number if not provided."""
    if not instance.employee_number:
        # Get the last employee number for this tenant
        last_employee = (
            Employee.objects.filter(tenant=instance.tenant)
            .order_by("-employee_number")
            .first()
        )

        if last_employee and last_employee.employee_number.isdigit():
            next_number = int(last_employee.employee_number) + 1
        else:
            next_number = 1

        instance.employee_number = str(next_number).zfill(6)  # e.g., 000001


@receiver(post_save, sender=DriverProfile)
def log_driver_profile_change(sender, instance, created, **kwargs):
    """Log driver profile creation/update."""
    user = get_current_user()

    if not user or not user.is_authenticated:
        return

    try:
        TenantAuditLog.objects.create(
            tenant=instance.tenant,
            user=user,
            action="create" if created else "update",
            model_name="DriverProfile",
            object_id=str(instance.id),
            changes={
                "employee": instance.employee.full_name,
                "license_number": instance.license_number,
                "license_category": instance.license_category,
            },
        )
        logger.info(
            f"Driver profile for {instance.employee.full_name} "
            f"{'created' if created else 'updated'}"
        )
    except Exception as e:
        logger.error(f"Error logging driver profile change: {str(e)}")


@receiver(post_save, sender=SecurityProfile)
def log_security_profile_change(sender, instance, created, **kwargs):
    """Log security profile creation/update."""
    user = get_current_user()

    if not user or not user.is_authenticated:
        return

    try:
        TenantAuditLog.objects.create(
            tenant=instance.tenant,
            user=user,
            action="create" if created else "update",
            model_name="SecurityProfile",
            object_id=str(instance.id),
            changes={
                "employee": instance.employee.full_name,
                "security_license_number": instance.security_license_number,
            },
        )
        logger.info(
            f"Security profile for {instance.employee.full_name} "
            f"{'created' if created else 'updated'}"
        )
    except Exception as e:
        logger.error(f"Error logging security profile change: {str(e)}")


""" import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from audit.models import TenantAuditLog
from tenants.middleware import get_current_user
from personnel.models import Driver, DriverDocument

logger = logging.getLogger("personnel")


@receiver(post_save, sender=Driver)
def log_driver_change(sender, instance, created, **kwargs):
    '''Log driver creation/update.'''
    user = get_current_user()

    if not user or not user.is_authenticated:
        return

    try:
        TenantAuditLog.objects.create(
            tenant=instance.tenant,
            user=user,
            action="create" if created else "update",
            model_name="Driver",
            object_id=str(instance.id),
            changes={
                "driver_full_name": instance.driver_full_name,
                "license_number": instance.license_number,
                "status": instance.status,
            },
        )
        logger.info(
            f"Driver {instance.driver_full_name} {'created' if created else 'updated'}"
        )
    except Exception as e:
        logger.error(f"Error logging driver change: {str(e)}")
 """
