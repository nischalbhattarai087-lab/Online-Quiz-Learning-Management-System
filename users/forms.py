"""
users/forms.py

Why use Django Forms?
- They centralise validation logic in ONE place (not scattered across views).
- They handle CSRF protection, field rendering, and error message generation.
- They integrate with Django's password validators defined in settings.py.
- Using UserCreationForm as the base means we inherit the two-password
  comparison ("password1 must equal password2") check for free.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User


class UserRegistrationForm(UserCreationForm):
    """
    Registration form for new students.

    Inherits from UserCreationForm which provides:
      - password1  (Enter password)
      - password2  (Confirm password)
      - The cross-field validator that checks both passwords match.
      - Integration with AUTH_PASSWORD_VALIDATORS in settings.py.

    We then ADD our LMS-specific fields (first_name, last_name, email).
    Role is NOT shown — it defaults to 'student' silently (set in save()).
    """

    # ------------------------------------------------------------------
    # Extra fields not in UserCreationForm by default
    # ------------------------------------------------------------------

    first_name = forms.CharField(
        max_length=150,
        required=True,
        # widget=forms.TextInput controls the raw <input> HTML element.
        # attrs dict maps directly to HTML attributes on that element.
        widget=forms.TextInput(attrs={
            'id': 'id_first_name',
            'placeholder': 'First name',
            'autocomplete': 'given-name',
        }),
        label='First Name',
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'id_last_name',
            'placeholder': 'Last name',
            'autocomplete': 'family-name',
        }),
        label='Last Name',
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'id': 'id_email',
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        }),
        label='Email Address',
        # help_text shown below the input in templates via {{ field.help_text }}
        help_text='Must be unique. You will use this to log in.',
    )

    # password1 and password2 come from UserCreationForm.
    # We override only their widgets to add placeholder text and IDs.
    password1 = forms.CharField(
        label='Password',
        strip=False,   # preserve leading/trailing spaces — user's choice
        widget=forms.PasswordInput(attrs={
            'id': 'id_password1',
            'placeholder': 'Create a strong password',
            'autocomplete': 'new-password',
        }),
        # validate_password runs all AUTH_PASSWORD_VALIDATORS from settings.
        # It checks: minimum length (8), common passwords list, numeric-only.
        validators=[validate_password],
    )

    password2 = forms.CharField(
        label='Confirm Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'id': 'id_password2',
            'placeholder': 'Repeat your password',
            'autocomplete': 'new-password',
        }),
    )

    # ------------------------------------------------------------------
    # Meta inner class
    # ------------------------------------------------------------------
    class Meta(UserCreationForm.Meta):
        """
        Meta controls which model this form saves to and which fields
        are included in the form (in this exact order in the HTML).
        """
        model = User
        # Explicitly list the fields so the form renders them in order.
        # username, password1, password2 come from UserCreationForm.
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2',
        ]

    # ------------------------------------------------------------------
    # Field-level validation: clean_<fieldname>()
    # ------------------------------------------------------------------
    # Django calls clean_<fieldname>() automatically for each field
    # after the field's own built-in validation passes.
    # If you raise ValidationError here, it attaches the error to
    # THAT specific field — the template can then display it inline.

    def clean_email(self):
        """
        Enforce email uniqueness at the form level (not just DB level).

        Why do this here and not rely solely on the DB unique constraint?
        - The DB constraint gives a raw IntegrityError, not a friendly form error.
        - Here we catch duplicates BEFORE the INSERT and return a clean,
          user-friendly message attached to the email field.
        """
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            # __iexact = case-insensitive match.
            # Prevents "user@example.com" and "User@EXAMPLE.COM" both registering.
            raise ValidationError(
                'An account with this email address already exists. '
                'Please use a different email or log in.'
            )
        return email

    def clean_username(self):
        """
        Enforce case-insensitive username uniqueness.
        Django's default username check IS case-sensitive at the DB level
        on some backends. We make it explicit and user-friendly.
        """
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username__iexact=username).exists():
            raise ValidationError(
                'This username is already taken. Please choose another.'
            )
        return username

    # ------------------------------------------------------------------
    # save() — set role before committing to DB
    # ------------------------------------------------------------------
    def save(self, commit=True):
        """
        Override save() to:
          1. Force role = 'student'  (public registration always creates students)
          2. Call set_password() via super() to hash the password correctly.

        commit=False → returns an unsaved User instance (useful in views
        that need to attach extra data before saving).
        commit=True  → saves to the database immediately (our use case).

        NEVER store the raw password — super().save() calls set_password()
        internally, which runs Django's password hashing pipeline (PBKDF2
        by default).
        """
        # super().save(commit=False) builds the User object with hashed password
        # but does NOT yet write it to the DB.
        user = super().save(commit=False)

        # Force role — even if a malicious actor tampers with POST data,
        # the role is always set here, not from form input.
        user.role = User.Role.STUDENT

        if commit:
            user.save()  # now writes to DB

        return user
