from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from users.decorators import student_required, teacher_required
from users.models import User
from .forms import CourseForm
from .models import Category, Course, Enrollment


# =============================================================================
# Public / Student Course Browsing & Detail
# =============================================================================

class CourseListView(View):
    """
    Public catalogue of published courses with category filtering,
    difficulty filtering, and keyword search.
    """
    template_name = 'courses/course_list.html'

    def get(self, request):
        courses_qs = Course.objects.filter(is_published=True).select_related('category', 'teacher')

        # Filter by Search Query
        query = request.GET.get('q', '').strip()
        if query:
            courses_qs = courses_qs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(teacher__first_name__icontains=query) |
                Q(teacher__last_name__icontains=query) |
                Q(teacher__username__icontains=query)
            )

        # Filter by Category
        category_slug = request.GET.get('category', '').strip()
        selected_category = None
        if category_slug:
            selected_category = get_object_or_404(Category, slug=category_slug)
            courses_qs = courses_qs.filter(category=selected_category)

        # Filter by Difficulty
        difficulty = request.GET.get('difficulty', '').strip()
        if difficulty in Course.Difficulty.values:
            courses_qs = courses_qs.filter(difficulty=difficulty)

        courses_qs = courses_qs.order_by('-created_at')

        paginator = Paginator(courses_qs, 9)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        categories = Category.objects.all()

        return render(request, self.template_name, {
            'courses': page_obj,
            'page_obj': page_obj,
            'categories': categories,
            'selected_category': selected_category,
            'selected_difficulty': difficulty,
            'query': query,
            'page_title': 'Explore Courses',
        })


class CourseDetailView(View):
    """
    Public detail page for a published course.
    Determines whether the currently authenticated student is already enrolled.
    """
    template_name = 'courses/course_detail.html'

    def get(self, request, slug):
        course = get_object_or_404(
            Course.objects.select_related('teacher', 'category'),
            slug=slug,
            is_published=True,
        )

        is_enrolled = False
        if request.user.is_authenticated and getattr(request.user, 'role', None) == User.Role.STUDENT:
            is_enrolled = Enrollment.objects.filter(
                student=request.user,
                course=course,
                is_active=True,
            ).exists()

        return render(request, self.template_name, {
            'course': course,
            'is_enrolled': is_enrolled,
            'page_title': course.title,
        })


# =============================================================================
# Student Course Enrollment & My Courses
# =============================================================================

@method_decorator(student_required, name='dispatch')
class CourseEnrollView(View):
    """
    POST endpoint allowing authenticated Students to enroll in published courses.
    Rejects duplicate enrollments and non-student roles.
    """
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, is_published=True)

        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'is_active': True},
        )

        if not created:
            if enrollment.is_active:
                messages.info(request, f'You are already enrolled in "{course.title}".')
            else:
                enrollment.is_active = True
                enrollment.save()
                messages.success(request, f'You have successfully re-enrolled in "{course.title}".')
        else:
            messages.success(request, f'You have successfully enrolled in "{course.title}".')

        return redirect('courses:student_courses')

    def get(self, request, slug):
        """Disallow GET for enrollment action and redirect back to course detail."""
        return redirect('courses:course_detail', slug=slug)


@method_decorator(student_required, name='dispatch')
class StudentCourseListView(View):
    """
    Lists all active course enrollments belonging to the logged-in Student.
    """
    template_name = 'courses/student/my_courses.html'

    def get(self, request):
        enrollments = (
            Enrollment.objects.filter(student=request.user, is_active=True)
            .select_related('course', 'course__category', 'course__teacher')
            .order_by('-enrolled_at')
        )

        paginator = Paginator(enrollments, 9)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, self.template_name, {
            'enrollments': page_obj,
            'page_obj': page_obj,
            'page_title': 'My Courses',
        })


# =============================================================================
# Teacher Course CRUD & Management
# =============================================================================

@method_decorator(teacher_required, name='dispatch')
class TeacherCourseListView(View):
    """
    Lists only courses created by the logged-in Teacher.
    Includes pagination (10 courses per page).
    """
    template_name = 'courses/teacher/course_list.html'

    def get(self, request):
        courses_qs = Course.objects.filter(teacher=request.user).order_by('-created_at')
        paginator = Paginator(courses_qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, self.template_name, {
            'courses': page_obj,
            'page_obj': page_obj,
            'page_title': 'My Courses',
        })


@method_decorator(teacher_required, name='dispatch')
class TeacherCourseCreateView(View):
    """
    Allows a Teacher to create a new Course.
    Automatically assigns request.user as the course teacher.
    """
    template_name = 'courses/teacher/course_form.html'

    def get(self, request):
        form = CourseForm()
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Create New Course',
            'action': 'Create',
        })

    def post(self, request):
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, f'Course "{course.title}" created successfully!')
            return redirect('courses:teacher_course_list')

        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Create New Course',
            'action': 'Create',
        })


@method_decorator(teacher_required, name='dispatch')
class TeacherCourseDetailView(View):
    """
    Displays full details of a course owned by the logged-in Teacher.
    Returns 404 if the course does not belong to request.user.
    """
    template_name = 'courses/teacher/course_detail.html'

    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, teacher=request.user)
        return render(request, self.template_name, {
            'course': course,
            'page_title': f'Course: {course.title}',
        })


@method_decorator(teacher_required, name='dispatch')
class TeacherCourseUpdateView(View):
    """
    Allows a Teacher to edit their own Course.
    Returns 404 if the course does not belong to request.user.
    """
    template_name = 'courses/teacher/course_form.html'

    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, teacher=request.user)
        form = CourseForm(instance=course)
        return render(request, self.template_name, {
            'form': form,
            'course': course,
            'page_title': f'Edit Course: {course.title}',
            'action': 'Update',
        })

    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, teacher=request.user)
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            updated_course = form.save(commit=False)
            updated_course.teacher = request.user
            updated_course.save()
            messages.success(request, f'Course "{updated_course.title}" updated successfully!')
            return redirect('courses:teacher_course_detail', slug=updated_course.slug)

        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {
            'form': form,
            'course': course,
            'page_title': f'Edit Course: {course.title}',
            'action': 'Update',
        })


@method_decorator(teacher_required, name='dispatch')
class TeacherCourseDeleteView(View):
    """
    Allows a Teacher to delete their own Course.
    GET: Display confirmation page.
    POST: Delete the course.
    """
    template_name = 'courses/teacher/course_confirm_delete.html'

    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, teacher=request.user)
        return render(request, self.template_name, {
            'course': course,
            'page_title': f'Delete Course: {course.title}',
        })

    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, teacher=request.user)
        title = course.title
        course.delete()
        messages.success(request, f'Course "{title}" has been deleted successfully.')
        return redirect('courses:teacher_course_list')


@method_decorator(teacher_required, name='dispatch')
class TeacherCoursePublishView(View):
    """
    Publish a course owned by the logged-in Teacher.
    Requires POST method.
    """
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, teacher=request.user)
        course.is_published = True
        course.save()
        messages.success(request, f'Course "{course.title}" is now published!')
        return redirect('courses:teacher_course_list')

    def get(self, request, slug):
        return redirect('courses:teacher_course_list')


@method_decorator(teacher_required, name='dispatch')
class TeacherCourseUnpublishView(View):
    """
    Unpublish a course owned by the logged-in Teacher.
    Requires POST method.
    """
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, teacher=request.user)
        course.is_published = False
        course.save()
        messages.success(request, f'Course "{course.title}" has been unpublished.')
        return redirect('courses:teacher_course_list')

    def get(self, request, slug):
        return redirect('courses:teacher_course_list')

