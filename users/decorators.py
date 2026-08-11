"""
users/decorators.py

Role-Based Access Control (RBAC) Decorators.

Provides reusable permission decorators for controlling access by user role:
  - login_required_custom
  - role_required(*allowed_roles, raise_exception=True)
  - student_required
  - teacher_required
  - admin_required
"""

from functools import wraps
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .models import User


def login_required_custom(view_func):
    """
    Redirect unauthenticated users to the login page with a warning flash message.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(
                request,
                'You must be logged in to access that page.',
            )
            return redirect('users:login')
        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(*allowed_roles, raise_exception=True):
    """
    Decorator factory to restrict a view to users whose role is in allowed_roles.

    Behavior:
      - Unauthenticated: Redirects to login page with a warning message (302).
      - Authenticated & Wrong Role: Raises PermissionDenied (HTTP 403 Forbidden)
        if raise_exception=True, or redirects to home/dashboard if raise_exception=False.
      - Authenticated & Correct Role: Allows request to proceed to the view.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please log in to continue.')
                return redirect('users:login')

            if request.user.role not in allowed_roles:
                if raise_exception:
                    raise PermissionDenied("You do not have permission to access this page.")

                messages.error(
                    request,
                    f'Access denied. Required role: {", ".join(allowed_roles)}.'
                )
                if request.user.role == User.Role.STUDENT:
                    return redirect('users:student_dashboard')
                elif request.user.role == User.Role.TEACHER:
                    return redirect('users:teacher_dashboard')
                elif request.user.role == User.Role.ADMIN:
                    return redirect('/admin/')
                return redirect('home')

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def student_required(view_func=None, raise_exception=True):
    """
    Permission decorator restricting access to users with the 'student' role.
    Can be used as @student_required or @method_decorator(student_required, name='dispatch').
    """
    actual_decorator = role_required(User.Role.STUDENT, raise_exception=raise_exception)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def teacher_required(view_func=None, raise_exception=True):
    """
    Permission decorator restricting access to users with the 'teacher' role.
    Can be used as @teacher_required or @method_decorator(teacher_required, name='dispatch').
    """
    actual_decorator = role_required(User.Role.TEACHER, raise_exception=raise_exception)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def admin_required(view_func=None, raise_exception=True):
    """
    Permission decorator restricting access to users with the 'admin' role.
    Can be used as @admin_required or @method_decorator(admin_required, name='dispatch').
    """
    actual_decorator = role_required(User.Role.ADMIN, raise_exception=raise_exception)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator
