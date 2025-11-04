from django.conf import settings
from django.views.i18n import set_language
from django.urls import path

from . import views


app_name = 'tenants'


urlpatterns = [
    path("", views.TenantSelectView.as_view(), name="select"),
    path("create/", views.TenantCreateView.as_view(), name="create"),
    path("<uuid:tenant_id>/details/", views.TenantDetailView.as_view(), name="detail"),
    path("<uuid:tenant_id>/edit/", views.TenantUpdateView.as_view(), name="update"),
    path(
        "<uuid:tenant_id>/members/",
        views.TenantMemberListView.as_view(),
        name="members",
    ),
    path("<uuid:tenant_id>/invite/", views.invite_user, name="invite"),
    path("invitations/<str:token>/accept/", views.accept_invitation, name="accept"),
    path(
        "<uuid:tenant_id>/members/<uuid:user_id>/remove/",
        views.remove_member,
        name="remove",
    ),
]

""" urlpatterns = [
    # Tenant selection
    path("", views.TenantSelectView.as_view(), name="select"),
    # Tenant management
    path("create/", views.TenantCreateView.as_view(), name="create"),
    path("<uuid:tenant_id>/", views.TenantDetailView.as_view(), name="detail"),
    path("<uuid:tenant_id>/edit/", views.TenantUpdateView.as_view(), name="update"),
    # Member management
    path(
        "<uuid:tenant_id>/members/",
        views.TenantMembersListView.as_view(),
        name="members",
    ),
    path("<uuid:tenant_id>/invite/", views.invite_user, name="invite"),
    path(
        "<uuid:tenant_id>/members/<uuid:user_id>/remove/",
        views.remove_member,
        name="remove_member",
    ),
    # Invitations
    path(
        "invitations/<str:token>/accept/", views.accept_invitation, name="accept_invite"
    ),
] """
