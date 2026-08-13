from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from users.decorators import admin_required, student_required, teacher_required
from users.models import User
from .forms import ChoiceFormSet, QuestionForm, QuizForm
from .models import Attempt, AttemptAnswer, Choice, Question, Quiz


# =============================================================================
# TEACHER VIEWS
# =============================================================================

@method_decorator(teacher_required, name='dispatch')
class TeacherQuizListView(View):
    """
    Lists quizzes created by the logged-in teacher.
    """
    template_name = 'quiz/teacher_quiz_list.html'

    def get(self, request):
        quizzes = Quiz.objects.filter(teacher=request.user).order_by('-created_at')
        return render(request, self.template_name, {
            'quizzes': quizzes,
            'page_title': 'My Quizzes',
        })


@method_decorator(teacher_required, name='dispatch')
class QuizCreateView(View):
    """
    Create a new Quiz header (title, description, time_limit).
    """
    template_name = 'quiz/quiz_form.html'

    def get(self, request):
        form = QuizForm()
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Create New Quiz',
            'action': 'Create',
        })

    def post(self, request):
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.teacher = request.user
            quiz.save()
            messages.success(request, f'Quiz "{quiz.title}" created! Now add questions to it.')
            return redirect('quiz:question_manage', quiz_id=quiz.id)

        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Create New Quiz',
            'action': 'Create',
        })


@method_decorator(teacher_required, name='dispatch')
class QuizEditView(View):
    """
    Edit an existing Quiz metadata.
    """
    template_name = 'quiz/quiz_form.html'

    def get(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk, teacher=request.user)
        form = QuizForm(instance=quiz)
        return render(request, self.template_name, {
            'form': form,
            'quiz': quiz,
            'page_title': f'Edit Quiz: {quiz.title}',
            'action': 'Update',
        })

    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk, teacher=request.user)
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, f'Quiz "{quiz.title}" updated successfully.')
            return redirect('quiz:teacher_quiz_list')

        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {
            'form': form,
            'quiz': quiz,
            'page_title': f'Edit Quiz: {quiz.title}',
            'action': 'Update',
        })


@method_decorator(teacher_required, name='dispatch')
class QuizQuestionManageView(View):
    """
    Manage questions and choices for a quiz. Allows adding a question with choices.
    """
    template_name = 'quiz/question_manage.html'

    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
        questions = quiz.questions.all().prefetch_related('choices')
        question_form = QuestionForm()
        choice_formset = ChoiceFormSet()
        return render(request, self.template_name, {
            'quiz': quiz,
            'questions': questions,
            'question_form': question_form,
            'choice_formset': choice_formset,
            'page_title': f'Manage Questions — {quiz.title}',
        })

    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
        questions = quiz.questions.all().prefetch_related('choices')
        question_form = QuestionForm(request.POST)
        choice_formset = ChoiceFormSet(request.POST)

        if question_form.is_valid() and choice_formset.is_valid():
            # Ensure at least one choice is marked correct
            choices_data = choice_formset.cleaned_data
            correct_count = sum(1 for c in choices_data if c and not c.get('DELETE', False) and c.get('is_correct'))
            
            if correct_count == 0:
                messages.error(request, 'You must mark at least one choice as correct!')
            else:
                with transaction.atomic():
                    question = question_form.save(commit=False)
                    question.quiz = quiz
                    question.save()

                    choice_formset.instance = question
                    choice_formset.save()

                messages.success(request, 'Question added successfully!')
                return redirect('quiz:question_manage', quiz_id=quiz.id)

        messages.error(request, 'Please correct the errors in the question or choices.')
        return render(request, self.template_name, {
            'quiz': quiz,
            'questions': questions,
            'question_form': question_form,
            'choice_formset': choice_formset,
            'page_title': f'Manage Questions — {quiz.title}',
        })


@method_decorator(teacher_required, name='dispatch')
class QuestionDeleteView(View):
    """
    Delete a question from a quiz.
    """
    def post(self, request, question_id):
        question = get_object_or_404(Question, id=question_id, quiz__teacher=request.user)
        quiz_id = question.quiz.id
        question.delete()
        messages.success(request, 'Question deleted.')
        return redirect('quiz:question_manage', quiz_id=quiz_id)


@method_decorator(teacher_required, name='dispatch')
class QuizDeleteView(View):
    """
    Delete an entire Quiz.
    """
    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk, teacher=request.user)
        title = quiz.title
        quiz.delete()
        messages.success(request, f'Quiz "{title}" deleted successfully.')
        return redirect('quiz:teacher_quiz_list')


@method_decorator(teacher_required, name='dispatch')
class QuizPublishToggleView(View):
    """
    Toggle is_published state of a quiz.
    """
    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk, teacher=request.user)
        if quiz.total_questions == 0:
            messages.error(request, 'Cannot publish a quiz with 0 questions! Please add questions first.')
            return redirect('quiz:question_manage', quiz_id=quiz.id)

        quiz.is_published = not quiz.is_published
        quiz.save()
        status_text = 'published and is now visible to students' if quiz.is_published else 'unpublished (hidden from students)'
        messages.success(request, f'Quiz "{quiz.title}" has been {status_text}.')
        return redirect('quiz:teacher_quiz_list')


# =============================================================================
# STUDENT VIEWS
# =============================================================================

@method_decorator(student_required, name='dispatch')
class AvailableQuizzesView(View):
    """
    Lists all published quizzes available for students, along with their attempt status.
    """
    template_name = 'quiz/available_quizzes.html'

    def get(self, request):
        quizzes = Quiz.objects.filter(is_published=True).order_by('-created_at')
        
        # Map existing attempt by student
        user_attempts = {
            attempt.quiz_id: attempt 
            for attempt in Attempt.objects.filter(student=request.user)
        }

        quizzes_with_status = []
        for quiz in quizzes:
            quizzes_with_status.append({
                'quiz': quiz,
                'attempt': user_attempts.get(quiz.id),
            })

        return render(request, self.template_name, {
            'quizzes_with_status': quizzes_with_status,
            'page_title': 'Available Quizzes',
        })


@method_decorator(student_required, name='dispatch')
class QuizAttemptView(View):
    """
    Handles taking a quiz (GET: display questions, POST: grade & save submission).
    """
    template_name = 'quiz/quiz_attempt.html'

    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)
        
        # Check if already attempted
        existing_attempt = Attempt.objects.filter(quiz=quiz, student=request.user).first()
        if existing_attempt:
            messages.info(request, 'You have already completed this quiz!')
            return redirect('quiz:attempt_result', attempt_id=existing_attempt.id)

        questions = quiz.questions.all().prefetch_related('choices')
        if not questions.exists():
            messages.error(request, 'This quiz has no questions available.')
            return redirect('quiz:available_quizzes')

        return render(request, self.template_name, {
            'quiz': quiz,
            'questions': questions,
            'page_title': f'Attempting: {quiz.title}',
        })

    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)

        # Enforce single attempt
        if Attempt.objects.filter(quiz=quiz, student=request.user).exists():
            messages.error(request, 'You have already submitted an attempt for this quiz.')
            return redirect('quiz:available_quizzes')

        questions = quiz.questions.all().prefetch_related('choices')
        total_questions = questions.count()

        if total_questions == 0:
            messages.error(request, 'Quiz has no questions.')
            return redirect('quiz:available_quizzes')

        correct_answers_count = 0
        attempt_answers = []

        with transaction.atomic():
            # Create attempt record
            attempt = Attempt.objects.create(
                quiz=quiz,
                student=request.user,
                total_questions_count=total_questions,
            )

            for question in questions:
                # Expect form input name="question_<id>"
                choice_id = request.POST.get(f'question_{question.id}')
                if choice_id:
                    chosen_choice = Choice.objects.filter(id=choice_id, question=question).first()
                    if chosen_choice:
                        attempt_answers.append(
                            AttemptAnswer(
                                attempt=attempt,
                                question=question,
                                chosen_choice=chosen_choice
                            )
                        )
                        if chosen_choice.is_correct:
                            correct_answers_count += 1

            # Bulk save attempt answers
            AttemptAnswer.objects.bulk_create(attempt_answers)

            # Calculate score percentage
            score_percentage = (correct_answers_count / total_questions) * 100.0 if total_questions > 0 else 0.0
            attempt.score = score_percentage
            attempt.correct_answers_count = correct_answers_count
            attempt.save()

        messages.success(request, f'Quiz submitted! Score: {score_percentage:.1f}%')
        return redirect('quiz:attempt_result', attempt_id=attempt.id)


@method_decorator(student_required, name='dispatch')
class AttemptResultView(View):
    """
    Displays the score breakdown and answer review for a student's attempt.
    """
    template_name = 'quiz/attempt_result.html'

    def get(self, request, attempt_id):
        attempt = get_object_or_404(Attempt, id=attempt_id, student=request.user)
        
        # Fetch question responses
        submitted_answers = {
            ans.question_id: ans.chosen_choice_id
            for ans in attempt.answers.all()
        }

        questions_review = []
        for question in attempt.quiz.questions.all().prefetch_related('choices'):
            chosen_choice_id = submitted_answers.get(question.id)
            choices_data = []
            for choice in question.choices.all():
                is_selected = (choice.id == chosen_choice_id)
                choices_data.append({
                    'choice': choice,
                    'is_selected': is_selected,
                    'is_correct': choice.is_correct,
                })
            
            questions_review.append({
                'question': question,
                'choices': choices_data,
                'user_choice_id': chosen_choice_id,
            })

        return render(request, self.template_name, {
            'attempt': attempt,
            'questions_review': questions_review,
            'page_title': f'Results: {attempt.quiz.title}',
        })


@method_decorator(student_required, name='dispatch')
class StudentAttemptHistoryView(View):
    """
    Displays history of all quiz attempts taken by the logged-in student.
    """
    template_name = 'quiz/attempt_history.html'

    def get(self, request):
        attempts = Attempt.objects.filter(student=request.user).select_related('quiz', 'quiz__teacher').order_by('-submitted_at')
        return render(request, self.template_name, {
            'attempts': attempts,
            'page_title': 'My Quiz History',
        })


# =============================================================================
# ADMIN VIEWS
# =============================================================================

@method_decorator(admin_required, name='dispatch')
class AdminQuizListView(View):
    """
    Admin overview of all quizzes across teachers in the LMS platform.
    """
    template_name = 'quiz/admin_quiz_list.html'

    def get(self, request):
        quizzes = Quiz.objects.all().select_related('teacher').order_by('-created_at')
        total_quizzes = quizzes.count()
        published_quizzes = quizzes.filter(is_published=True).count()
        total_attempts = Attempt.objects.count()

        return render(request, self.template_name, {
            'quizzes': quizzes,
            'total_quizzes': total_quizzes,
            'published_quizzes': published_quizzes,
            'total_attempts': total_attempts,
            'page_title': 'Quiz Platform Management',
        })
