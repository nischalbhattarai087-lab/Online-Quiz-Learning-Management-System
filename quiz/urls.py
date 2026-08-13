from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # ------------------------------------------------------------------
    # Teacher Quiz Management
    # ------------------------------------------------------------------
    path('teacher/quizzes/', views.TeacherQuizListView.as_view(), name='teacher_quiz_list'),
    path('teacher/quizzes/create/', views.QuizCreateView.as_view(), name='quiz_create'),
    path('teacher/quizzes/<int:pk>/edit/', views.QuizEditView.as_view(), name='quiz_edit'),
    path('teacher/quizzes/<int:quiz_id>/questions/', views.QuizQuestionManageView.as_view(), name='question_manage'),
    path('teacher/questions/<int:question_id>/delete/', views.QuestionDeleteView.as_view(), name='question_delete'),
    path('teacher/quizzes/<int:pk>/delete/', views.QuizDeleteView.as_view(), name='quiz_delete'),
    path('teacher/quizzes/<int:pk>/toggle-publish/', views.QuizPublishToggleView.as_view(), name='quiz_toggle_publish'),

    # ------------------------------------------------------------------
    # Student Quiz Execution & History
    # ------------------------------------------------------------------
    path('available/', views.AvailableQuizzesView.as_view(), name='available_quizzes'),
    path('<int:quiz_id>/attempt/', views.QuizAttemptView.as_view(), name='quiz_attempt'),
    path('attempts/<int:attempt_id>/result/', views.AttemptResultView.as_view(), name='attempt_result'),
    path('history/', views.StudentAttemptHistoryView.as_view(), name='student_history'),

    # ------------------------------------------------------------------
    # Admin Overview
    # ------------------------------------------------------------------
    path('admin/overview/', views.AdminQuizListView.as_view(), name='admin_quiz_list'),
]
