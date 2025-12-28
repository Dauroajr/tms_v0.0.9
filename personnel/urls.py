from django.urls import path

from . import views

app_name = "personnel"

urlpatterns = [
    # Employee URLs
    path("employees/", views.EmployeeListView.as_view(), name="employee_list"),
    path(
        "employees/create/", views.EmployeeCreateView.as_view(), name="employee_create"
    ),
    path(
        "employees/<uuid:pk>/",
        views.EmployeeDetailView.as_view(),
        name="employee_detail",
    ),
    path(
        "employees/<uuid:pk>/edit/",
        views.EmployeeUpdateView.as_view(),
        name="employee_update",
    ),
    path(
        "employees/<uuid:pk>/delete/",
        views.EmployeeDeleteView.as_view(),
        name="employee_delete",
    ),
    # Quick Access - Drivers
    path("drivers/", views.DriverListView.as_view(), name="driver_list"),
    # Quick Access - Security
    path("security/", views.SecurityListView.as_view(), name="security_list"),
    # Driver Profile URLs
    path(
        "driver-profile/create/<uuid:employee_pk>/",
        views.DriverProfileCreateView.as_view(),
        name="driver_profile_create",
    ),
    path(
        "driver-profile/<uuid:pk>/edit/",
        views.DriverProfileUpdateView.as_view(),
        name="driver_profile_update",
    ),
    # Security Profile URLs
    path(
        "security-profile/create/<uuid:employee_pk>/",
        views.SecurityProfileCreateView.as_view(),
        name="security_profile_create",
    ),
    path(
        "security-profile/<uuid:pk>/edit/",
        views.SecurityProfileUpdateView.as_view(),
        name="security_profile_update",
    ),
]
