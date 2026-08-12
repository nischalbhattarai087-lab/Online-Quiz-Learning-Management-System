from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from users.models import User


class AdminTeacherCreationForm(forms.Form):
    """
    Form used by Administrators to create new Teacher accounts.
    Forces role to Teacher upon creation.
    """

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'id_admin_teacher_username',
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Username',
        }),
        label='Username',
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'id': 'id_admin_teacher_email',
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'email@example.com',
        }),
        label='Email Address',
    )

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'id_admin_teacher_first_name',
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'First Name',
        }),
        label='First Name',
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'id_admin_teacher_last_name',
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Last Name',
        }),
        label='Last Name',
    )

    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'id': 'id_admin_teacher_password1',
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Initial Password',
        }),
        validators=[validate_password],
    )

    password2 = forms.CharField(
        label='Confirm Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'id': 'id_admin_teacher_password2',
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Confirm Initial Password',
        }),
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email address already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned_data

    def save(self):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        password = self.cleaned_data['password1']

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.TEACHER,
            is_active=True,
        )
        return user
