from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """
    Represents a course category (e.g., Programming, Cybersecurity, Web Development).
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Category Name',
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        help_text='Unique URL-friendly slug.',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Course(models.Model):
    """
    Represents an educational course in the LMS.
    Must belong to a Teacher (User with role='teacher') and a Category.
    """
    class Difficulty(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    title = models.CharField(
        max_length=255,
        verbose_name='Course Title',
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text='Unique URL slug for the course.',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Course Description',
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name='Course Instructor',
        help_text='Must be a user with the Teacher role.',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Course Category',
    )
    thumbnail = models.ImageField(
        upload_to='courses/thumbnails/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
        verbose_name='Course Thumbnail Image',
        help_text='Upload an image (JPG, PNG, WEBP).',
    )
    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.BEGINNER,
        verbose_name='Difficulty Level',
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name='Price ($)',
        help_text='Set 0.00 for free courses.',
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name='Is Published',
        help_text='Only published courses will be visible to students.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"

    def clean(self):
        super().clean()
        # Enforce that course teacher must have role='teacher'
        if self.teacher_id and hasattr(self.teacher, 'role'):
            from users.models import User
            if self.teacher.role != User.Role.TEACHER:
                raise ValidationError({
                    'teacher': 'Assigned course instructor must have the Teacher role.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Enrollment(models.Model):
    """
    Represents a student's enrollment in a course.
    Enforces that only Students can enroll and each student can enroll at most once per course.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Student',
        help_text='Student enrolled in the course.',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Course',
    )
    enrolled_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Enrolled At',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
        help_text='Indicates whether the student enrollment is currently active.',
    )

    class Meta:
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        ordering = ['-enrolled_at']
        unique_together = ('student', 'course')
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course'],
                name='unique_student_course_enrollment',
            )
        ]

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"

    def clean(self):
        super().clean()
        if self.student_id and hasattr(self.student, 'role'):
            from users.models import User
            if self.student.role != User.Role.STUDENT:
                raise ValidationError({
                    'student': 'Only users with the Student role can enroll in courses.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

