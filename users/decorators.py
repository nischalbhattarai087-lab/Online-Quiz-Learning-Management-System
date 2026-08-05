"""
users/decorators.py

Custom access-control decorators.

Why write our own instead of using only @login_required?
- Django's @login_required only checks is_authenticated — it knows nothing
  about our custom Role system (student / teacher / admin).
- We need a @role_required decorator that checks BOTH authentication AND role.
- Keeping decorators in one file makes them reusable across all apps.

Django decorators work by wrapping the view function:
  decorated_view = decorator(original_view)
When the URL is hit, Django calls decorated_view(request, …), which runs the
decorator's logic first, then optionally calls original_view(request, …).
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import User


def login_required_custom(view_func):
    """
    Redirect unauthenticated users to the login page.

    Why not just use Django's @login_required?
    - We CAN and often do, but this custom version lets us attach a flash
      message (messages.warning) before the redirect so the user knows WHY
      they were sent to login.
    - Django's built-in @login_required does NOT add a flash message.

    Usage:
        @login_required_custom
        def my_view(request):
            ...

    How it works:
    1. @wraps(view_func) copies the original function's name and docstring
       onto the wrapper. This is required so Django's URL resolver and
       admin introspection can identify the view correctly.
    2. If the user is not authenticated, we flash a warning and redirect.
    3. If authenticated, we call the real view.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(
                request,
                'You must be logged in to access that page.',
            )
            # redirect() to a named URL — uses Django's URL reversal.
            return redirect('users:login')
        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    """
    Restrict a view to users whose role is in allowed_roles.

    This is a decorator FACTORY — it takes arguments and returns a decorator.
    The extra layer of nesting is required because:
      @role_required('student', 'teacher')  ← called with arguments
    evaluates as:
      decorator = role_required('student', 'teacher')
      view      = decorator(original_view)

    Usage:
        @role_required('student')
        def student_dashboard(request):
            ...

        @role_required('teacher', 'admin')
        def manage_courses(request):
            ...

    Security model:
    - Unauthenticated → redirect to login (same as login_required_custom).
    - Wrong role      → 403 flash message + redirect to home.
    - Correct role    → let the view run normally.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # Gate 1: must be logged in
            if not request.user.is_authenticated:
                messages.warning(request, 'Please log in to continue.')
                return redirect('users:login')

            # Gate 2: must have the correct role
            if request.user.role not in allowed_roles:
                messages.error(
                    request,
                    f'You do not have permission to access that page. '
                    f'(Required: {", ".join(allowed_roles)})'
                )
                return redirect('home')

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator
