from django.conf import settings
from django.db import models


class Quiz(models.Model):
    """
    Represents a quiz created by a Teacher.
    """
    title = models.CharField(
        max_length=255,
        verbose_name='Quiz Title',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description',
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_quizzes',
        verbose_name='Created By (Teacher)',
    )
    time_limit_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name='Time Limit (Minutes)',
        help_text='Time allowed for students to complete the quiz.',
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name='Is Published',
        help_text='Only published quizzes are visible to students.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (Teacher: {self.teacher.username})"

    @property
    def total_questions(self):
        return self.questions.count()


class Question(models.Model):
    """
    Represents a question within a Quiz.
    """
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    text = models.TextField(
        verbose_name='Question Text',
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name='Display Order',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"


class Choice(models.Model):
    """
    Represents an answer option for a Question.
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices',
    )
    text = models.CharField(
        max_length=255,
        verbose_name='Choice Text',
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name='Is Correct Answer',
    )

    class Meta:
        verbose_name = 'Choice'
        verbose_name_plural = 'Choices'

    def __str__(self):
        return f"{self.text} {'(Correct)' if self.is_correct else ''}"


class Attempt(models.Model):
    """
    Represents a student's attempt at taking a Quiz.
    Enforces one attempt per student per quiz.
    """
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
    )
    score = models.FloatField(
        default=0.0,
        verbose_name='Score (%)',
    )
    correct_answers_count = models.PositiveIntegerField(default=0)
    total_questions_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'
        unique_together = ('quiz', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} ({self.score:.1f}%)"


class AttemptAnswer(models.Model):
    """
    Records the specific choice selected by a student for a question in an attempt.
    """
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )
    chosen_choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Attempt Answer'
        verbose_name_plural = 'Attempt Answers'

    def __str__(self):
        return f"{self.attempt.student.username} Q: {self.question.id} -> Choice: {self.chosen_choice.id}"
