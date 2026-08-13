from django import forms
from django.core.exceptions import ValidationError
from .models import Category, Course


class CourseForm(forms.ModelForm):
    """
    Form for Teachers to create and update Courses.
    Excludes teacher ownership field to prevent teacher manipulation.
    """

    # Override the title field to use a custom required error message so that
    # both truly-empty and whitespace-only titles produce the same error.
    title = forms.CharField(
        max_length=200,
        error_messages={'required': 'Course title is required.'},
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Master Python & Django Web Development',
        }),
    )

    class Meta:
        model = Course
        fields = [
            'title',
            'description',
            'category',
            'difficulty',
            'price',
            'thumbnail',
            'is_published',
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed course overview, learning objectives, and prerequisites...',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-select',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '0.00 for free courses',
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise ValidationError('Course title is required.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if not description:
            raise ValidationError('Course description is required.')
        return description

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if not category:
            raise ValidationError('Course category is required.')
        return category

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError('Course price cannot be negative.')
        return price
