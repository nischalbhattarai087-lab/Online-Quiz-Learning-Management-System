"""
URL configuration for lms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from users.views import StudentDashboardView, TeacherDashboardView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Users app — registration, login, logout, profile, etc.
    path('accounts/', include('users.urls', namespace='users')),

    # Admin Dashboard app
    path('admin-dashboard/', include('admin_dashboard.urls', namespace='admin_dashboard')),

    # Role-specific dashboard URL aliases
    path('student/dashboard/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher_dashboard'),

    # Simple home route using base.html template
    path('', TemplateView.as_view(template_name='base.html'), name='home'),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

