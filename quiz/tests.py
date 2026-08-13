from django.test import TestCase
from django.urls import reverse
from users.models import User
from .models import Quiz, Question, Choice, Attempt, AttemptAnswer


class QuizManagementTest(TestCase):
    """
    Tests for Teacher & Admin Quiz Management.
    """

    def setUp(self):
        self.teacher1 = User.objects.create_user(
            username='teacher_one',
            email='teacher1@example.com',
            password='Password123!',
            role=User.Role.TEACHER,
        )

        self.teacher2 = User.objects.create_user(
            username='teacher_two',
            email='teacher2@example.com',
            password='Password123!',
            role=User.Role.TEACHER,
        )

        self.student = User.objects.create_user(
            username='student_user',
            email='student@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
        )

        self.admin = User.objects.create_superuser(
            username='admin_user',
            email='admin@example.com',
            password='Password123!',
            role=User.Role.ADMIN,
        )

        self.quiz = Quiz.objects.create(
            title='Python Basics',
            description='Test python fundamentals',
            teacher=self.teacher1,
            time_limit_minutes=15,
            is_published=False,
        )

        self.question = Question.objects.create(
            quiz=self.quiz,
            text='What is the keyword for defining a function in Python?',
            order=1,
        )

        self.choice_correct = Choice.objects.create(
            question=self.question,
            text='def',
            is_correct=True,
        )

        self.choice_wrong = Choice.objects.create(
            question=self.question,
            text='func',
            is_correct=False,
        )

    def test_teacher_can_create_quiz(self):
        """Teacher can create a new quiz."""
        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.post(reverse('quiz:quiz_create'), {
            'title': 'Django Framework Quiz',
            'description': 'Test Django knowledge',
            'time_limit_minutes': 20,
            'is_published': False,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Quiz.objects.filter(title='Django Framework Quiz', teacher=self.teacher1).exists())

    def test_teacher_can_toggle_publish(self):
        """Teacher can publish quiz if questions exist."""
        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.post(reverse('quiz:quiz_toggle_publish', kwargs={'pk': self.quiz.id}))
        self.assertEqual(response.status_code, 302)
        self.quiz.refresh_from_db()
        self.assertTrue(self.quiz.is_published)

    def test_teacher_cannot_manage_other_teacher_quiz(self):
        """Teacher 2 cannot edit or delete Teacher 1's quiz."""
        self.client.login(username='teacher_two', password='Password123!')
        
        # Try editing
        response = self.client.get(reverse('quiz:quiz_edit', kwargs={'pk': self.quiz.id}))
        self.assertEqual(response.status_code, 404)

        # Try deleting
        response = self.client.post(reverse('quiz:quiz_delete', kwargs={'pk': self.quiz.id}))
        self.assertEqual(response.status_code, 404)

    def test_admin_can_view_all_quizzes(self):
        """Admin can access quiz overview page."""
        self.client.login(username='admin_user', password='Password123!')
        response = self.client.get(reverse('quiz:admin_quiz_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Basics')


class StudentQuizExecutionTest(TestCase):
    """
    Tests for Student taking quizzes and score calculation.
    """

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher_quiz',
            email='teacher_q@example.com',
            password='Password123!',
            role=User.Role.TEACHER,
        )

        self.student = User.objects.create_user(
            username='student_taker',
            email='student_t@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
        )

        # Create published quiz with 2 questions
        self.quiz = Quiz.objects.create(
            title='General Knowledge Quiz',
            teacher=self.teacher,
            time_limit_minutes=10,
            is_published=True,
        )

        # Question 1
        self.q1 = Question.objects.create(quiz=self.quiz, text='Capital of France?', order=1)
        self.q1_correct = Choice.objects.create(question=self.q1, text='Paris', is_correct=True)
        self.q1_wrong = Choice.objects.create(question=self.q1, text='London', is_correct=False)

        # Question 2
        self.q2 = Question.objects.create(quiz=self.quiz, text='2 + 2 = ?', order=2)
        self.q2_correct = Choice.objects.create(question=self.q2, text='4', is_correct=True)
        self.q2_wrong = Choice.objects.create(question=self.q2, text='5', is_correct=False)

    def test_student_can_view_published_quizzes(self):
        """Student sees published quizzes in available list."""
        self.client.login(username='student_taker', password='Password123!')
        response = self.client.get(reverse('quiz:available_quizzes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'General Knowledge Quiz')

    def test_student_takes_quiz_and_scores_100_percent(self):
        """Student submits all correct choices and gets 100% score."""
        self.client.login(username='student_taker', password='Password123!')
        response = self.client.post(
            reverse('quiz:quiz_attempt', kwargs={'quiz_id': self.quiz.id}),
            {
                f'question_{self.q1.id}': self.q1_correct.id,
                f'question_{self.q2.id}': self.q2_correct.id,
            }
        )
        self.assertEqual(response.status_code, 302)

        attempt = Attempt.objects.get(quiz=self.quiz, student=self.student)
        self.assertEqual(attempt.score, 100.0)
        self.assertEqual(attempt.correct_answers_count, 2)
        self.assertEqual(attempt.total_questions_count, 2)

    def test_student_takes_quiz_and_scores_50_percent(self):
        """Student submits one correct choice and one incorrect choice."""
        self.client.login(username='student_taker', password='Password123!')
        response = self.client.post(
            reverse('quiz:quiz_attempt', kwargs={'quiz_id': self.quiz.id}),
            {
                f'question_{self.q1.id}': self.q1_correct.id,
                f'question_{self.q2.id}': self.q2_wrong.id,
            }
        )
        self.assertEqual(response.status_code, 302)

        attempt = Attempt.objects.get(quiz=self.quiz, student=self.student)
        self.assertEqual(attempt.score, 50.0)
        self.assertEqual(attempt.correct_answers_count, 1)

    def test_student_cannot_attempt_twice(self):
        """Student cannot take the same quiz a second time."""
        Attempt.objects.create(
            quiz=self.quiz,
            student=self.student,
            score=100.0,
            correct_answers_count=2,
            total_questions_count=2,
        )

        self.client.login(username='student_taker', password='Password123!')
        response = self.client.get(reverse('quiz:quiz_attempt', kwargs={'quiz_id': self.quiz.id}))
        self.assertEqual(response.status_code, 302)  # Redirects to results
