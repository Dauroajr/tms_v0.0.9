from django.utils import timezone
import logging

from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db import transaction

from .models import Tenant, TenantUser
from audit.models import TenantAuditLog
from .middleware import get_current_tenant, get_current_user


logger = logging.getLogger('tenant.audit')


@receiver(post_save, sender=Tenant)
def create_owner_membership(sender, instance, created, **kwargs):
    """ When a tenant is created, add the creator as owner.
    This signal handler is called after Tenant.save(). """

    if created:
        user = get_current_user()

        #  Validate user exists and is authenticated
        if not user and not user.is_authenticated:
            logger.warning(
                f"Tenant {instance.id} created but no authenticated user found in context"
            )
            return

        try:
            with transaction.atomic():
                #  Create the owner membership
                TenantUser.objects.create(
                    user=user,
                    tenant=instance,
                    role='owner',
                    is_owner=True
                )

                #  Create audit log for tenant creation
                if hasattr(instance, 'audit'):
                    TenantAuditLog.objects.create(
                        tenant=instance,
                        user=user,
                        action='create',
                        model_name='Tenant',
                        object_id=str(instance.id),
                        changes={
                            'name': instance.name,
                            'slug': instance.slug,
                            'document': instance.document,
                        }
                    )

                logger.info(
                    f"Owner membership created for tenant {instance.id} ",
                    f"{instance.name} by user {user.id}"
                )
        except Exception as e:
            logger.error(
                f"Error creating owner membership for tenant {instance.id}: {str(e)}",
                exc_info=True
            )
            raise


@receiver(post_save, sender=TenantUser)
def log_member_change(sender, instance, created, **kwargs):
    """ Log when a new member joins a tenant. """
    if created:
        user = get_current_user()

        try:
            action = 'add_member'
            message = f"User {instance.user.email} koined as {instance.role}"

            TenantAuditLog.objects.create(
                tenant=instance.tenant,
                user=user or instance.invited_by,
                action=action,
                model_name='TenantUser',
                object_id=str(instance.id),
                changes={
                    'role': instance.role,
                    'is_owner': instance.is_owner
                }
            )

            logger.info(
                f"Tenant {instance.tenant.id}: {message}"
            )
        except Exception as e:
            logger.error(
                f"Error logging member change for tenant {instance.tenant.id}: {str(e)}",
                exc_info=True
            )


@receiver(post_delete, sender=TenantUser)
def log_member_removal(sender, instance, **kwargs):
    """ Log when a member is removed from a tenant. """
    user = get_current_user()

    try:
        TenantAuditLog.objects.create(
            tenant=instance.tenant,
            user=user,
            action='remove_member',
            model_name='TenantUser',
            object_id=str(instance.id),
            changes={
                'user_email': instance.user.email,
                'role': instance.role
            }
        )

        logger.info(
            f"Tenant {instance.tenant.id}: User {instance.user.email} removed"
        )
    except Exception as e:
        logger.error(
            f"Error logging member removal for tenant {instance.tenant.id}: {str(e)}",
            exc_info=True
        )


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """ Log user login event, and update last_login_tenant.
    Called when a user logs in successfully. """

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
        except TenantUser.DoesNotExist:
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
