from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from users.decorators import teacher_required
from .forms import CourseForm
from .models import Course


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
            # Backend enforces that request.user is set as owner
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
            # Re-enforce course owner cannot be changed
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
