
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include
from django.views.i18n import set_language

from .views import home_view, dashboard_view


urlpatterns = [
    path("admin/", admin.site.urls),

    path("", home_view, name="home"),
    path("dashboard/", dashboard_view, name='dashboard'),

    path("accounts/", include("accounts.urls")),
    path("audit/", include("audit.urls")),
    path("core/", include("core.urls")),
    path("fleet/", include("fleet.urls")),
    path("tenants/", include("tenants.urls")),

    path("i18n/", set_language, name="set_language"),
]

""" urlpatterns += i18n_patterns(
    path('set_language/', set_language, name='set_language'),
    path('', include('tms_app.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('accounts.urls')),
    path('tenants/', include('tenants.urls')),
    path('audit/', include('audit.urls')),
    path('core/', include('core.urls')),
) """

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
