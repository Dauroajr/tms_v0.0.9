from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.urls import path
from django.views.i18n import set_language

from . import views

app_name = "fleet"

urlpatterns = [
    # Dashboard
    path("", views.FleetDashboardView.as_view(), name="dashboard"),

    # Vehicle URLs
    path("vehicles/", views.VehicleListView.as_view(), name="vehicle_list"),
    path("vehicles/create/", views.VehicleCreateView.as_view(), name="vehicle_create"),
    path("vehicles/<uuid:pk>/", views.VehicleDetailView.as_view(), name="vehicle_detail"),
    path("vehicles/<uuid:pk>/edit", views.VehicleUpdateView.as_view(), name="vehicle_update",),
    path("vehicles/<uuid:pk>/delete", views.VehicleDeleteView.as_view(), name="vehicle_delete",),

    # Vehicle Brand URLs
    path("brands/", views.VehicleBrandListView.as_view(), name="brand_list"),
    path("brands/create", views.VehicleBrandCreateView.as_view(), name="brand_create"),
    path("brands/<uuid:pk>/edit", views.VehicleBrandUpdateView.as_view(), name="brand_update"),

    # Vehicle Assignment URLs
    path('assignments/', views.VehicleAssignmentListView.as_view(), name='assignment_list'),
    path('assignments/create/', views.VehicleAssignmentCreateView.as_view(), name='assignment_create'),
    path('assignments/<uuid:pk>/', views.VehicleAssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignments/<uuid:pk>/edit/', views.VehicleAssignmentUpdateView.as_view(), name='assignment_update'),
    path('assignments/<uuid:pk>/end/', views.VehicleAssignmentEndView.as_view(), name='assignment_end'),
    path('assignments/<uuid:pk>/delete/', views.VehicleAssignmentDeleteView.as_view(), name='assignment_delete'),

    # Workday URLs
    path('workdays/', views.WorkdayListView.as_view(), name='workday_list'),
    path('workdays/create', views.WorkdayCreateView.as_view(), name='workday_create'),
    path('workdays/<uuid:pk>/', views.WorkdayDetailView.as_view(), name='workday_detail'),
    path('workdays/<uuid:pk>/edit/', views.WorkdayUpdateView.as_view(), name='workday_update'),
    path('workdays/<uuid:pk>/delete/', views.WorkdayDeleteView.as_view(), name='workday_delete'),
    path('workdays/<uuid:pk>/approve/', views.WorkdayApproveView.as_view(), name='workday_approve'),
    path('workdays/<uuid:pk>/reject/', views.WorkdayRejectView.as_view(), name='workday_reject'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
