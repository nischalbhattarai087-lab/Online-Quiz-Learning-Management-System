from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from users.decorators import admin_required
from users.models import User
from .forms import AdminTeacherCreationForm


@method_decorator(admin_required, name='dispatch')
class AdminDashboardView(View):
    """
    Main Admin Dashboard page.
    Displays overall platform statistics calculated dynamically from the DB.
    """

    template_name = 'admin_dashboard/dashboard.html'

    def get(self, request):
        total_users = User.objects.count()
        total_students = User.objects.filter(role=User.Role.STUDENT).count()
        total_teachers = User.objects.filter(role=User.Role.TEACHER).count()
        total_admins = User.objects.filter(role=User.Role.ADMIN).count()

        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
        pending_teachers = User.objects.filter(role=User.Role.TEACHER, is_active=False).count()

        recent_users = User.objects.order_by('-date_joined')[:5]

        context = {
            'page_title': 'Admin Dashboard',
            'user': request.user,
            'total_users': total_users,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_admins': total_admins,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'pending_teachers': pending_teachers,
            'recent_users': recent_users,
        }
        return render(request, self.template_name, context)


@method_decorator(admin_required, name='dispatch')
class AdminUserListView(View):
    """
    User Management Page for Administrators.
    Provides search by username/email/name, role filtering, and active/inactive status filtering.
    """

    template_name = 'admin_dashboard/users.html'

    def get(self, request):
        queryset = User.objects.all().order_by('-date_joined')

        # 1. Search Query
        query = request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )

        # 2. Role Filter
        role_filter = request.GET.get('role', '').strip()
        if role_filter in [User.Role.STUDENT, User.Role.TEACHER, User.Role.ADMIN]:
            queryset = queryset.filter(role=role_filter)

        # 3. Status Filter
        status_filter = request.GET.get('status', '').strip()
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        context = {
            'page_title': 'User Management',
            'user': request.user,
            'users_list': queryset,
            'query': query,
            'selected_role': role_filter,
            'selected_status': status_filter,
        }
        return render(request, self.template_name, context)


@method_decorator(admin_required, name='dispatch')
class AdminTeacherListView(View):
    """
    Teacher Management Page for Administrators.
    Lists all Teacher accounts, their activation/approval status, and provides
    form for creating new Teacher accounts directly.
    """

    template_name = 'admin_dashboard/teachers.html'

    def get(self, request):
        teachers = User.objects.filter(role=User.Role.TEACHER).order_by('-date_joined')
        form = AdminTeacherCreationForm()
        context = {
            'page_title': 'Teacher Management',
            'user': request.user,
            'teachers': teachers,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        teachers = User.objects.filter(role=User.Role.TEACHER).order_by('-date_joined')
        form = AdminTeacherCreationForm(request.POST)

        if form.is_valid():
            teacher = form.save()
            messages.success(
                request,
                f'Teacher account created successfully for {teacher.full_name} ({teacher.username}).'
            )
            return redirect('admin_dashboard:teachers')

        messages.error(request, 'Please correct the errors in the form below.')
        context = {
            'page_title': 'Teacher Management',
            'user': request.user,
            'teachers': teachers,
            'form': form,
        }
        return render(request, self.template_name, context)


@method_decorator(admin_required, name='dispatch')
class AdminTeacherToggleStatusView(View):
    """
    Toggle active/approval status of a Teacher account.
    """

    def post(self, request, pk):
        teacher = get_object_or_404(User, pk=pk, role=User.Role.TEACHER)

        # Toggle active status
        teacher.is_active = not teacher.is_active
        teacher.save()

        status_str = 'activated' if teacher.is_active else 'deactivated'
        messages.success(
            request,
            f'Teacher {teacher.username} has been {status_str}.'
        )
        return redirect('admin_dashboard:teachers')
