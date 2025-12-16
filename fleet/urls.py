from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.urls import path
from django.views.i18n import set_language

from . import views

app_name = 'fleet'

urlpatterns = [
    path('vehicles/', views.VehicleListView.as_view(), name='vehicle_list'),
    path('vehicles/create/', views.VehicleCreateView.as_view(), name='vehicle_create'),
    path('vehicles/<uuid:pk>/', views.VehicleDetailView.as_view(), name='vehicle_detail'),
    path('vehicles/<uuid:pk>/edit', views.VehicleUpdateView.as_view(), name='vehicle_update'),
    path('vehicles/<uuid:pk>/delete', views.VehicleDeleteView.as_view(), name='vehicle_delete'),

    path('brands/', views.VehicleBrandListView.as_view(), name='brand_list'),
    path('brands/create', views.VehicleBrandCreateView.as_view(), name='brand_create'),
    path('brands/<uuid:pk>/edit', views.VehicleBrandUpdateView.as_view(), name='brand_update'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
