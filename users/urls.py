"""
users/urls.py — App-level URL configuration for the `users` application.

All URLs are prefixed with /accounts/ by lms/urls.py:
  /accounts/register/            → RegisterView
  /accounts/login/               → UserLoginView
  /accounts/dashboard/student/   → StudentDashboardView
  /accounts/dashboard/teacher/   → TeacherDashboardView

app_name creates a namespace so templates reference URLs as:
  {% url 'users:login' %}
  {% url 'users:student_dashboard' %}
"""

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Registration
    path('register/', views.RegisterView.as_view(), name='register'),

    # Login
    # Django's @login_required redirects unauthenticated users to the URL
    # defined in settings.LOGIN_URL — we set that to 'users:login' in base.py.
    path('login/', views.UserLoginView.as_view(), name='login'),

    # Dashboards
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
