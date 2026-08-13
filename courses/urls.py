from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # ------------------------------------------------------------------
    # Teacher Course CRUD
    # ------------------------------------------------------------------
    path('teacher/courses/', views.TeacherCourseListView.as_view(), name='teacher_course_list'),
    path('teacher/courses/create/', views.TeacherCourseCreateView.as_view(), name='teacher_course_create'),
    path('teacher/courses/<slug:slug>/', views.TeacherCourseDetailView.as_view(), name='teacher_course_detail'),
    path('teacher/courses/<slug:slug>/edit/', views.TeacherCourseUpdateView.as_view(), name='teacher_course_edit'),
    path('teacher/courses/<slug:slug>/delete/', views.TeacherCourseDeleteView.as_view(), name='teacher_course_delete'),
    path('teacher/courses/<slug:slug>/publish/', views.TeacherCoursePublishView.as_view(), name='teacher_course_publish'),
    path('teacher/courses/<slug:slug>/unpublish/', views.TeacherCourseUnpublishView.as_view(), name='teacher_course_unpublish'),
]
