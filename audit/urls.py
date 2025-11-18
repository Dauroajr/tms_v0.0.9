from django.urls import path, include
from . import views


app_name = 'audit'

urlpatterns = [
    path('', views.AuditLogListView.as_view(), name='log_list'),
    path('<uuid:pk>/', views.AuditLogDetailView.as_view(), name='log_detail'),
    path('export/', views.ExportAuditLogsView.as_view(), name='export'),
]


