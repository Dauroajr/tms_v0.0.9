from datetime import timezone
import logging


from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import Tenant, TenantUser
from audit.models import TenantAuditLog
from .middleware import get_current_tenant, get_current_user


logger = logging.getLogger('tenant.audit')


@receiver(post_save, sender=Tenant)
def create_owner_membership(sender, instance, created, **kwargs):
    """ When a tenant is created, add the creator as owner. """

    if created:
        user = get_current_user()
        if user and user.is_authenticated:
            TenantUser.objects.create(
                user=user,
                tenant=instance,
                role='owner',
                is_owner=True
            )

            # Log the Tenant creation
            TenantAuditLog.obkects.create(
                tenant=instance,
                user=user,
                action='create',
                model_name='Tenant',
                object_id=str(instance.id)
            )


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """ Log user login event, and update last_login_tenant. """

    if hasattr(request, 'tenant') and request.tenant:
        user.last_login_tenant = request.tenant
        user.save(update_fields=['last_login_tenant'])

        # Update membership last access.
        try:
            membership = TenantUser.objects.get(
                user=user,
                tenant=request.tenant
            )
            membership.last_access = timezone.now()
            membership.save(update_fields=['last_access'])
        except TenantUser.DoesNotExists:
            pass

        # Create audit log:
        TenantAuditLog.objects.create(
            tenant=request.tenant,
            user=user,
            action='login',
            model_name='User',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """ Log user logout event. """

    if hasattr(request, 'tenant') and request.tenant:
        TenantAuditLog.objects.create(
            tenant=request.tenant,
            user=user,
            action='logout',
            model_name='User',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )


# Generic audit signal for any model
def audit_model_change(sender, instance, action, **kwargs):
    """ Generic audit log for model changes within a tenant context. """

    tenant = get_current_tenant()
    user = get_current_user()

    if tenant and user:
        changes = None
        if action == 'update' and hasattr(instance, '_original_values'):
            changes = {
                field: {
                    'old': instance._original_values.get(field),
                    'new': getattr(instance, field)
                }
                for field in instance._original_values
                if instance._original_values.get(field) != getattr(instance, field)
            }

        TenantAuditLog.objects.create(
            tenant=tenant,
            user=user,
            action=action,
            model_name=instance.__class__.__name__,
            object_id=str(instance.pk) if instance.pk else None,
            changes=changes
        )
