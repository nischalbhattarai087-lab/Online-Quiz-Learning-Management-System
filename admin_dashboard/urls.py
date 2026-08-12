from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('users/', views.AdminUserListView.as_view(), name='users'),
    path('teachers/', views.AdminTeacherListView.as_view(), name='teachers'),
    path('teachers/<int:pk>/toggle/', views.AdminTeacherToggleStatusView.as_view(), name='teacher_toggle'),
]
