"""
users/forms.py

Contains two forms:
  1. UserRegistrationForm — student self-registration.
  2. LoginForm           — username + password + Remember Me.

Why use Django Forms for login (instead of writing raw POST handling)?
- Centralised validation with automatic error binding to fields.
- Clean separation: the form validates credentials; the view acts on them.
- authenticate() is called INSIDE the form's clean() so the view stays thin.
"""

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
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


# =============================================================================
# LoginForm
# =============================================================================

class LoginForm(forms.Form):
    """
    Login form — validates credentials and stores the authenticated User
    object on self.user_cache so the view can call login() without
    repeating the authenticate() call.

    Why NOT inherit AuthenticationForm (Django's built-in)?
    - AuthenticationForm is tightly coupled to request objects and has
      subtleties around inactive-account handling that differ per project.
    - Writing our own gives full control over field labels, error messages,
      and the Remember Me checkbox while keeping the logic transparent.

    Flow:
      1. User submits username + password.
      2. clean() calls authenticate(request, username=…, password=…).
         authenticate() iterates AUTHENTICATION_BACKENDS (default: ModelBackend)
         which looks up the user by username and verifies the hashed password.
      3. If authenticate() returns None → wrong credentials → ValidationError.
      4. If authenticate() returns a User but is_active is False → locked account.
      5. On success, self.user_cache holds the authenticated User instance.
      6. The view calls form.get_user() and then login(request, user).
    """

    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'id_login_username',
            'placeholder': 'Your username',
            'autocomplete': 'username',
        }),
        label='Username',
    )

    password = forms.CharField(
        required=True,
        # strip=False — preserve spaces the user intentionally typed
        strip=False,
        widget=forms.PasswordInput(attrs={
            'id': 'id_login_password',
            'placeholder': 'Your password',
            'autocomplete': 'current-password',
        }),
        label='Password',
    )

    remember_me = forms.BooleanField(
        required=False,      # BooleanField is required=False by default; unchecked = False
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'id': 'id_remember_me',
        }),
        label='Keep me signed in',
    )

    # ------------------------------------------------------------------
    # Cross-field validation: clean()
    # ------------------------------------------------------------------
    # clean() runs AFTER all individual clean_<field>() methods succeed.
    # This is the right place for checks that involve multiple fields
    # (here: username + password together).

    def clean(self):
        """
        Authenticate the user. Attach the user object to self.user_cache
        if successful; raise ValidationError otherwise.

        Non-field errors raised here are accessible in the template via
        {{ form.non_field_errors }} — they appear at the top of the form,
        not attached to a specific input.
        """
        # super().clean() collects all cleaned individual fields first.
        cleaned = super().clean()

        username = cleaned.get('username')
        password = cleaned.get('password')

        # Only attempt authentication if both fields passed individual validation.
        if username and password:
            # authenticate() returns a User object on success, None on failure.
            # It also handles the AUTHENTICATION_BACKENDS pipeline.
            # We pass `request` so backends that need it (e.g. rate limiters) work.
            self.user_cache = authenticate(
                request=self.request if hasattr(self, 'request') else None,
                username=username,
                password=password,
            )

            if self.user_cache is None:
                # authenticate() returned None: either wrong username or wrong password.
                # We give a GENERIC message intentionally — a specific message like
                # "username not found" would let attackers enumerate valid usernames.
                raise ValidationError(
                    'Invalid username or password. Please try again.',
                    code='invalid_credentials',
                )

            if not self.user_cache.is_active:
                # The account exists but is deactivated (e.g. banned by admin).
                raise ValidationError(
                    'Your account has been deactivated. '
                    'Please contact support.',
                    code='inactive',
                )

        return cleaned

    # ------------------------------------------------------------------
    # Helper: expose the authenticated user to the view
    # ------------------------------------------------------------------
    def get_user(self):
        """
        Return the authenticated user object after is_valid() succeeds.
        Raises AttributeError if called before is_valid() — intentional.
        """
        return self.user_cache


# =============================================================================
# UserProfileForm
# =============================================================================

class UserProfileForm(forms.ModelForm):
    """
    Form for updating profile details (first_name, last_name, profile_picture).
    Role is strictly excluded to prevent unauthorized role modifications.
    Includes custom image validation for size (<= 5MB) and file format.
    """

    first_name = forms.CharField(
        max_length=150,
        required=True,
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

    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'id': 'id_profile_picture',
            'accept': 'image/*',
        }),
        label='Profile Picture',
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'profile_picture']

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture and hasattr(picture, 'size'):
            max_size = 5 * 1024 * 1024  # 5 MB
            if picture.size > max_size:
                raise ValidationError('Profile picture size cannot exceed 5 MB.')

            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            ext = str(picture.name).lower()
            if not any(ext.endswith(e) for e in valid_extensions):
                raise ValidationError(
                    'Unsupported image format. Allowed formats: JPG, JPEG, PNG, GIF, WEBP.'
                )
        return picture


# =============================================================================
# CustomPasswordChangeForm
# =============================================================================

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Password change form extending Django's built-in PasswordChangeForm.
    Provides old_password, new_password1, and new_password2 with custom widget styling.
    """

    old_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'id': 'id_old_password',
            'placeholder': 'Enter your current password',
            'autocomplete': 'current-password',
        }),
    )

    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'id': 'id_new_password1',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password',
        }),
        validators=[validate_password],
    )

    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'id': 'id_new_password2',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
        }),
    )


