import csv
import json
from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, DetailView, View

from tenants.decorators import tenant_required
from tenants.models import TenantUser
from .models import TenantAuditLog


class AuditLogListView(LoginRequiredMixin, ListView):
    """View for listing logs of the current Tenant.
    """

    model = TenantAuditLog
    template_name = 'audit/log_list.html'
    context_object_name = 'logs'
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, 'tenant') or not request.tenant:
            raise PermissionDenied(_('Tenant required'))

        # Only owners and admins can view audit logs.
        try:
            membership = TenantUser.objects.get(
                user=request.user,
                tenant=request.tenant,
                is_active=True
            )
            if not (membership.is_owner or membership.role in ['admin', 'owner']):
                raise PermissionDenied(_('Only owners and admins can view audit logs.'))
        except TenantUser.DoesNotExist:
            raise PermissionDenied(_('You are not a member of this tenant.'))

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = TenantAuditLog.objects.filter(
            tenant=self.request.tenant,
        ).select_related('user')

        # Apply filters from GET parameters
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)

        model_name = self.request.GET.get('model')
        if model_name:
            queryset = queryset.filter(model_name=model_name)

        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Date range filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__gte=date_from)
            except ValueError:
                pass

        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d')
                # Include the entire day for date_to
                date_to += timedelta(days=1)
                queryset = queryset.filter(timestamp__lt=date_to)
            except ValueError:
                pass

        # Search Query
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) | Q(user__email__icontains=search) | Q(model_name__icontains=search) | Q(object_id__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        """ Add filter context. """
        context = super().get_context_data(**kwargs)

        # Get unique values for filters
        context['actions'] = TenantAuditLog.ACTION_CHOICES
        context['models'] = TenantAuditLog.objects.filter(
            tenant=self.request.tenant
        ).values_list('model_name', flat=True).distinct()

        context['users'] = TenantUser.objects.filter(
            tenant=self.request.tenant,
            is_active=True
        ).select_related('user')

        # Preserve filter values
        context['current_action'] = self.request.GET.get('action', '')
        context['current_model'] = self.request.GET.get('model', '')
        context['current_user'] = self.request.GET.get('user', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['search'] = self.request.GET.get('search', '')

        return context


class AuditLogDetailView(LoginRequiredMixin, DetailView):
    """View for displaying details of a specific audit log. """

    model = TenantAuditLog
    template_name = 'audit/log_detail.html'
    context_object_name = 'log'

    def dispatch(self, request, *args, **kwargs):
        """ Check if user has permission to view audit logs. """

        if not hasattr(request, 'tenant') or not request.tenant:
            raise PermissionDenied(_('Tenant required'))

        # Only owners and admins can view logs
        try:
            membership = TenantUser.objects.get(
                user=request.user,
                tenant=request.tenant,
                is_active=True
            )
            if not (membership.is_owner or membership.role in ['admin', 'owner']):
                raise PermissionDenied(_('Only owners and admins can view logs'))
        except TenantUser.DoesNotExist:
            raise PermissionDenied(_('You are not a memebr of this tenant.'))

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """ Filter by current tenant."""
        return TenantAuditLog.objects.filter(
            tenant=self.request.tenant,
        ).select_related('user')


class ExportAuditLogsView(LoginRequiredMixin, View):
    """ View for exporting audit logs to CSV or JSON. """

    def dispatch(self, request, *args, **kwargs):
        """ Check if user has permission to export audit logs. """
        if not hasattr(request, 'tenant') or not request.tenant:
            raise PermissionDenied(_('Tenant required'))

        try:
            membership = TenantUser.objects.get(
                user=request.user,
                tenant=request.tenant,
                is_active=True
            )
            if not (membership.is_owner or membership.role in ['admin', 'owner']):
                raise PermissionDenied(_('Only owners and admins can export audit logs.'))
        except TenantUser.DoesNotExist:
            raise PermissionDenied(_('You are not a member of this tenant.'))

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """ Export audit logs based of format parameter. """
        export_format = request.GET.get('format', 'csv')

        # Get filtered queryset (reuse filters from List view)
        queryset = TenantAuditLog.objects.filter(
            tenant=request.tenant
        ).select_related('user')

        # Apply same filters as List view
        action = request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)

        model_name = request.GET.get('model')
        if model_name:
            queryset = queryset.filter(model_name=model_name)

        user_id = request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        date_from = request.GET.get('date_from')
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%d-%M-%Y')
                queryset = queryset.filter(timestamp__gte=date_from)
            except ValueError:
                pass

        date_to = request.GET.get('date_to')
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%d-%M-%Y')
                date_to += timedelta(days=1)
                queryset = queryset.filter(timestamp__lt=date_to)
            except ValueError:
                pass

        if export_format == 'json':
            return self.export_json(queryset)
        else:
            return self.export_csv(queryset)

    def export_csv(self, queryset):
        """ Exportlogs to CSV format."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f"attachment; filename='audit_logs_{timezone.now().strftime('''%d%m%Y_%H%M%S''')}.csv'"

        writer = csv.writer(response)
        writer.writerow([
            'Timestamp',
            'User',
            'Action',
            'Model',
            'Object ID',
            'IP Address',
            'Changes',
        ])

        for log in queryset:
            writer.writerow([
                log.strftime('%d-%m-%Y %H:%M:%S'),
                log.user.get_full_name() if log.user else 'System',
                log.get_action_display(),
                log.model_name,
                log.object_id or '',
                log.ip_address or '',
                json.dumps(log.changes) if log.changes else ''
            ])

        return response

    def export_json(self, queryset):
        """ Export logs to JSON format. """
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f"attachment; filename='audit_logs_{timezone.now().strftime('''%d%m%Y_%H%M%S''')}.json'"

        data = []
        for log in queryset:
            data.append({
                'id': str(log.id),
                'timestamp': log.timestamp.isoformat(),
                'user': log.user.get_full_name() if log.user else 'System',
                'user_email': log.user.email if log.user else None,
                'action': log.action,
                'model_name': log.model_name,
                'object_id': log.object_id,
                'changes': log.changes,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent
            })

        response.write(json.dumps(data, indent=2, ensure_ascii=False))
        return response
