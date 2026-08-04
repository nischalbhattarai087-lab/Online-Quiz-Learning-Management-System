from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model that extends Django's built-in AbstractUser.

    Why AbstractUser instead of AbstractBaseUser?
    - AbstractUser already provides: username, email, first_name, last_name,
      password (hashed), is_active, is_staff, is_superuser, date_joined,
      last_login, and all authentication machinery (login, permissions, etc.).
    - AbstractBaseUser is a bare-bones base — you wire up everything yourself.
    - For most LMS projects, AbstractUser is the right choice: you inherit
      everything Django gives you and just ADD the fields you need.
    """

    # ------------------------------------------------------------------
    # Role choices
    # ------------------------------------------------------------------
    # Using TextChoices (Django 3.0+) keeps choices and their database
    # values in one place, gives you clean constants (User.Role.STUDENT),
    # and auto-generates the human-readable labels.
    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        TEACHER = 'teacher', 'Teacher'
        ADMIN   = 'admin',   'Admin'

    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------

    # 'username' and 'first_name' / 'last_name' are inherited from
    # AbstractUser — no need to redefine them.

    # email — override to enforce uniqueness across the whole table.
    # AbstractUser defines email as a plain CharField with no unique
    # constraint, so we must redefine it here.
    email = models.EmailField(
        unique=True,
        verbose_name='Email address',
        help_text='Required. A valid email address (must be unique).',
    )

    # profile_picture — stored under media/profile_pictures/<filename>.
    # blank=True  → the field is optional in forms.
    # null=True   → the database column may be NULL (no image uploaded yet).
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        verbose_name='Profile picture',
        help_text='Optional. Upload a profile photo (JPEG, PNG …).',
    )

    # role — every user belongs to exactly one role; default is Student.
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name='Role',
        help_text='Select the user\'s role within the platform.',
    )

    # ------------------------------------------------------------------
    # Meta
    # ------------------------------------------------------------------
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['date_joined']  # newest registrations last in admin list

    # ------------------------------------------------------------------
    # String representation
    # ------------------------------------------------------------------
    def __str__(self):
        # e.g. "john_doe (Teacher)"
        return f'{self.username} ({self.get_role_display()})'

    # ------------------------------------------------------------------
    # Helper properties — useful in templates and views
    # ------------------------------------------------------------------
    @property
    def full_name(self):
        """Return first + last name, falling back to username."""
        return self.get_full_name() or self.username

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_admin_role(self):
        # NOTE: Django already has `is_superuser`; this is the *application*
        # level 'Admin' role — they are intentionally separate concepts.
        return self.role == self.Role.ADMIN
