from django.contrib import admin
from .models import Quiz, Question, Choice, Attempt, AttemptAnswer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ('text', 'quiz', 'order', 'created_at')
    list_filter = ('quiz',)


class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'is_published', 'time_limit_minutes', 'created_at')
    list_filter = ('is_published', 'teacher')
    search_fields = ('title', 'description', 'teacher__username')


class AttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'correct_answers_count', 'total_questions_count', 'submitted_at')
    list_filter = ('quiz', 'submitted_at')
    search_fields = ('student__username', 'quiz__title')


admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(AttemptAnswer)
