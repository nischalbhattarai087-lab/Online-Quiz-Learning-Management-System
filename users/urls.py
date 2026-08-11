"""
users/urls.py — App-level URL configuration for the `users` application.

All URLs are prefixed with /accounts/ by lms/urls.py:
  /accounts/register/                  → RegisterView
  /accounts/login/                     → UserLoginView
  /accounts/logout/                    → UserLogoutView
  /accounts/profile/                   → UserProfileView
  /accounts/password-reset/            → PasswordResetView
  /accounts/password-reset/done/       → PasswordResetDoneView
  /accounts/reset/<uidb64>/<token>/    → PasswordResetConfirmView
  /accounts/reset/done/                → PasswordResetCompleteView
  /accounts/dashboard/student/         → StudentDashboardView
  /accounts/dashboard/teacher/         → TeacherDashboardView

app_name creates a namespace so templates reference URLs as:
  {% url 'users:login' %}
  {% url 'users:profile' %}
  {% url 'users:password_reset' %}
"""

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

app_name = 'users'

urlpatterns = [
    # ------------------------------------------------------------------
    # Authentication (Register, Login, Logout)
    # ------------------------------------------------------------------
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),

    # ------------------------------------------------------------------
    # User Profile & Settings
    # ------------------------------------------------------------------
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/edit/', views.UserProfileEditView.as_view(), name='profile_edit'),
    path('password-change/', views.UserPasswordChangeView.as_view(), name='password_change'),

    # ------------------------------------------------------------------
    # Django Built-in Password Reset System
    # ------------------------------------------------------------------
    # Step 1: Submit email address form
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset_form.html',
            email_template_name='users/password_reset_email.html',
            subject_template_name='users/password_reset_subject.txt',
            success_url=reverse_lazy('users:password_reset_done'),
        ),
        name='password_reset',
    ),
    # Step 2: "Check your email" confirmation page
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    # Step 3: Set new password form (clicked link from email with UID and Token)
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            success_url=reverse_lazy('users:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    # Step 4: Password reset completed success page
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),

    # ------------------------------------------------------------------
    # Dashboards (Role Protected)
    # ------------------------------------------------------------------
    path(
        'dashboard/student/',
        views.StudentDashboardView.as_view(),
        name='student_dashboard',
    ),
    path(
        'dashboard/teacher/',
        views.TeacherDashboardView.as_view(),
        name='teacher_dashboard',
    ),
]
