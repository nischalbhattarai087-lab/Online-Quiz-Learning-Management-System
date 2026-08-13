from django import forms
from django.forms import inlineformset_factory
from .models import Quiz, Question, Choice


class QuizForm(forms.ModelForm):
    """
    Form for teachers to create and edit quizzes.
    """
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit_minutes', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Intro to Python & Data Structures',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Provide brief context or instructions for students...',
            }),
            'time_limit_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 300,
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


class QuestionForm(forms.ModelForm):
    """
    Form for adding/editing a single question in a quiz.
    """
    class Meta:
        model = Question
        fields = ['text', 'order']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter question text here...',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
            }),
        }


class ChoiceForm(forms.ModelForm):
    """
    Form for adding/editing a choice option for a question.
    """
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option text',
            }),
            'is_correct': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


# Formset for inline Choice management within Question creation/editing
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    extra=4,
    min_num=2,
    validate_min=True,
    max_num=6,
    can_delete=True
)
