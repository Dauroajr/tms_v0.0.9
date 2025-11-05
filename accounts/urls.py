from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Profile URLs
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/delete/', views.delete_account, name='delete_account'),

    # Password Management URLs
    path(
        'password/change/',
        PasswordChangeView.as_view(
            template_name='accounts/password_change.html',
            success_url='/accounts/password/change/done/'
        ),
        name='password_change'
    ),
    path(
        'password/change/done/',
        PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html'
        ),
        name='password_change_done'
    ),

    # Password Reset URLs
    path(
        'password/reset/',
        PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url='/accounts/password/reset/done/'
        ),
        name='password_reset'
    ),
    path(
        'password/reset/done/',
        PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'password/reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url='/accounts/password/reset/complete/'
        ),
        name='password_reset_confirm'
    ),
    path(
        'password/reset/complete/',
        PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]
