"""
users/views.py

Contains four views:
  1. RegisterView         — student self-registration (built in previous step)
  2. UserLoginView        — authenticates + logs in; role-based redirect
  3. StudentDashboardView — protected: only students
  4. TeacherDashboardView — protected: only teachers

Login flow in detail:
  GET  /accounts/login/  → render empty LoginForm
  POST /accounts/login/  → form.is_valid() calls authenticate() internally
                           → on success: login(request, user) creates session
                           → redirect based on user.role
                           → on failure: re-render form with error messages
"""

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.edit import FormView

from .decorators import (
    admin_required,
    login_required_custom,
    role_required,
    student_required,
    teacher_required,
)
from .forms import (
    CustomPasswordChangeForm,
    LoginForm,
    UserProfileForm,
    UserRegistrationForm,
)
from django.db.models import Avg
from .models import User
from quiz.models import Attempt, Quiz
from courses.models import Course


# =============================================================================
# 1. RegisterView
# =============================================================================

class RegisterView(FormView):
    """
    Handles student self-registration.

    Attributes:
        template_name  — which HTML template to render
        form_class     — the form Django will instantiate automatically
        success_url    — where to redirect after a valid form submission
    """

    template_name = 'users/register.html'
    form_class = UserRegistrationForm

    # Now points to login since login is implemented in this step.
    success_url = reverse_lazy('users:login')

    # ------------------------------------------------------------------
    # GET request
    # ------------------------------------------------------------------
    def get(self, request, *args, **kwargs):
        """Redirect already-authenticated users away from register page."""
        if request.user.is_authenticated:
            return _role_redirect(request.user)
        return super().get(request, *args, **kwargs)

    # ------------------------------------------------------------------
    # POST request — valid form
    # ------------------------------------------------------------------
    def form_valid(self, form):
        """Save the new user, flash success message, redirect to login."""
        user = form.save()
        messages.success(
            request=self.request,
            message=(
                f'Account created successfully for {user.username}! '
                'You can now log in.'
            ),
        )
        return super().form_valid(form)

    # ------------------------------------------------------------------
    # POST request — invalid form
    # ------------------------------------------------------------------
    def form_invalid(self, form):
        """Re-render the form with validation errors."""
        messages.error(
            request=self.request,
            message='Please correct the errors below and try again.',
        )
        return super().form_invalid(form)


# =============================================================================
# 2. UserLoginView
# =============================================================================

class UserLoginView(View):
    """
    Processes the login form.

    Why use View (not FormView) here?
    - FormView's form_valid() always redirects to a static success_url.
    - Here the redirect destination depends on the user's ROLE, which we
      only know after authentication — so we need custom form_valid logic.
    - Using the base View class and handling GET/POST explicitly is cleaner.
    """

    template_name = 'users/login.html'

    # ------------------------------------------------------------------
    # GET — render empty login form
    # ------------------------------------------------------------------
    def get(self, request):
        # If the user is already logged in, skip the login page.
        if request.user.is_authenticated:
            return _role_redirect(request.user)

        # ?next= is set by Django's @login_required when it redirects to login.
        # We pass it into the template so the form action can include it.
        next_url = request.GET.get('next', '')
        form = LoginForm()
        return render(request, self.template_name, {
            'form': form,
            'next': next_url,
        })

    # ------------------------------------------------------------------
    # POST — validate credentials and log in
    # ------------------------------------------------------------------
    def post(self, request):
        """
        Steps:
          1. Instantiate LoginForm with POST data.
          2. form.is_valid() triggers field validation then clean(), which
             calls authenticate() — returning a User or None.
          3. On success: call login() to create the session, then redirect.
          4. On failure: re-render with errors.
        """
        form = LoginForm(data=request.POST)

        # Pass the request to the form so authenticate() can use it
        # (some custom backends and rate-limiters need the request object).
        form.request = request

        next_url = request.POST.get('next', '')

        if form.is_valid():
            # authenticate() already ran inside form.clean() — retrieve result.
            user = form.get_user()

            # ----------------------------------------------------------
            # Remember Me logic
            # ----------------------------------------------------------
            # Django sessions expire when the browser closes by default.
            # SESSION_COOKIE_AGE in settings controls the max age.
            # Setting expiry to 0 makes it a session cookie (closes with browser).
            # Setting expiry to None uses the global SESSION_COOKIE_AGE value.
            remember = form.cleaned_data.get('remember_me')
            if not remember:
                # Session expires when the browser is closed.
                request.session.set_expiry(0)
            else:
                # Session persists for SESSION_COOKIE_AGE seconds (set in settings).
                # We explicitly call set_expiry(None) to use the global default.
                request.session.set_expiry(None)

            # ----------------------------------------------------------
            # login() — creates the session and attaches the user
            # ----------------------------------------------------------
            # login() does three things:
            #   a. Generates a new session key (prevents session fixation attacks).
            #   b. Stores the user's ID and backend in the session.
            #   c. Sets request.user = user for the rest of this request.
            login(request, user)

            messages.success(
                request,
                f'Welcome back, {user.first_name or user.username}! '
                f'Signed in as {user.get_role_display()}.',
            )

            # ----------------------------------------------------------
            # Role-based redirect
            # ----------------------------------------------------------
            # If the user was redirected here by @login_required (via ?next=),
            # honour that redirect. Otherwise send them to their dashboard.
            if next_url:
                return redirect(next_url)
            return _role_redirect(user)

        # Form is invalid — re-render with error messages.
        messages.error(request, 'Login failed. Please check your credentials.')
        return render(request, self.template_name, {
            'form': form,
            'next': next_url,
        })


# =============================================================================
# 3. UserLogoutView
# =============================================================================

class UserLogoutView(View):
    """
    Handles user logout and session teardown.

    Security & Implementation details:
    1. Django's logout(request) function:
       - Flushes the session data completely from the database/storage backend.
       - Deletes the session cookie from the user's browser.
       - Clears request.user, replacing it with an AnonymousUser instance.
       - Cycles the session key to protect against session fixation attacks.

    2. HTTP Method Strategy:
       - POST: The primary and secure HTTP method for logging out (prevents CSRF
         attacks from external <img> tags or links trying to force logouts).
       - GET: Handled gracefully for direct URL navigation, ensuring users are
         logged out and redirected to home with feedback without crashing.
    """

    def post(self, request):
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, 'You have been logged out successfully.')
        return redirect('home')

    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, 'You have been logged out successfully.')
        return redirect('home')


# =============================================================================
# 4. StudentDashboardView
# =============================================================================

@method_decorator(student_required, name='dispatch')
class StudentDashboardView(View):
    """
    Student dashboard — accessible only to authenticated users with role='student'.
    """

    template_name = 'users/student_dashboard.html'

    def get(self, request):
        attempts = Attempt.objects.filter(student=request.user)
        attempts_count = attempts.count()
        avg_score_data = attempts.aggregate(Avg('score'))['score__avg'] or 0.0

        context = {
            'user': request.user,
            'page_title': 'Student Dashboard',
            'enrolled_courses_count': 0,
            'quiz_attempts_count': attempts_count,
            'avg_quiz_score': round(avg_score_data, 1),
            'recent_attempts': attempts.select_related('quiz')[:5],
        }
        return render(request, self.template_name, context)


# =============================================================================
# 5. TeacherDashboardView
# =============================================================================

@method_decorator(teacher_required, name='dispatch')
class TeacherDashboardView(View):
    """
    Teacher dashboard — accessible only to authenticated users with role='teacher'.
    """

    template_name = 'users/teacher_dashboard.html'

    def get(self, request):
        teacher_courses = Course.objects.filter(teacher=request.user)
        total_courses = teacher_courses.count()

        teacher_quizzes = Quiz.objects.filter(teacher=request.user)
        total_quizzes = teacher_quizzes.count()

        attempts_on_teacher_quizzes = Attempt.objects.filter(quiz__teacher=request.user)
        avg_score_data = attempts_on_teacher_quizzes.aggregate(Avg('score'))['score__avg'] or 0.0

        context = {
            'user': request.user,
            'page_title': 'Teacher Dashboard',
            'total_courses': total_courses,
            'total_students': User.objects.filter(role=User.Role.STUDENT).count(),
            'total_quizzes': total_quizzes,
            'avg_score': round(avg_score_data, 1),
            'recent_courses': teacher_courses.order_by('-created_at')[:5],
            'recent_quizzes': teacher_quizzes.order_by('-created_at')[:5],
        }
        return render(request, self.template_name, context)


# =============================================================================
# Role-Based Test Views (RBAC Verification)
# =============================================================================

@method_decorator(student_required, name='dispatch')
class StudentOnlyView(View):
    """Test view accessible exclusively to Student role users."""
    template_name = 'users/student_only.html'

    def get(self, request):
        return render(request, self.template_name, {
            'page_title': 'Student Only Area',
            'user': request.user,
        })


@method_decorator(teacher_required, name='dispatch')
class TeacherOnlyView(View):
    """Test view accessible exclusively to Teacher role users."""
    template_name = 'users/teacher_only.html'

    def get(self, request):
        return render(request, self.template_name, {
            'page_title': 'Teacher Only Area',
            'user': request.user,
        })


@method_decorator(admin_required, name='dispatch')
class AdminOnlyView(View):
    """Test view accessible exclusively to Admin role users."""
    template_name = 'users/admin_only.html'

    def get(self, request):
        return render(request, self.template_name, {
            'page_title': 'Admin Only Area',
            'user': request.user,
        })


# =============================================================================
# 5. UserProfileView
# =============================================================================

@method_decorator(login_required_custom, name='dispatch')
class UserProfileView(View):
    """
    User Profile View — displays user account details.

    Access Control:
    - Protected by @method_decorator(login_required_custom, name='dispatch').
    - Unauthenticated requests are intercepted and redirected to /accounts/login/
      with a warning flash message ("You must be logged in to access that page.").

    Displayed Data:
    - Profile picture (or avatar initials fallback)
    - Username
    - Email address
    - First name & Last name
    - System Role (Student / Teacher / Admin)
    - Date joined timestamp
    """

    template_name = 'users/profile.html'

    def get(self, request):
        context = {
            'user': request.user,
            'page_title': 'My Profile',
        }
        return render(request, self.template_name, context)


# =============================================================================
# 6. UserProfileEditView
# =============================================================================

@method_decorator(login_required_custom, name='dispatch')
class UserProfileEditView(View):
    """
    Allows authenticated users to update first_name, last_name, and profile_picture.
    Role is intentionally excluded from the form and model updates.
    """

    template_name = 'users/profile_edit.html'

    def get(self, request):
        form = UserProfileForm(instance=request.user)
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Edit Profile',
        })

    def post(self, request):
        form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('users:profile')

        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Edit Profile',
        })


# =============================================================================
# 7. UserPasswordChangeView
# =============================================================================

@method_decorator(login_required_custom, name='dispatch')
class UserPasswordChangeView(View):
    """
    Handles password changing for logged-in users.
    Uses CustomPasswordChangeForm (old_password, new_password1, new_password2).
    Calls update_session_auth_hash(request, user) to prevent session invalidation/logout.
    """

    template_name = 'users/password_change.html'

    def get(self, request):
        form = CustomPasswordChangeForm(user=request.user)
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Change Password',
        })

    def post(self, request):
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # CRITICAL: update_session_auth_hash keeps the user logged in
            # by updating the session hash with the user's new password hash.
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:profile')

        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Change Password',
        })


# =============================================================================
# Private helper
# =============================================================================

def _role_redirect(user):
    """
    Return an HttpResponseRedirect to the correct dashboard for the given user.

    Centralising this logic means RegisterView, UserLoginView, and any
    future "already logged in" guards all redirect consistently.

    Role mapping:
      student → /accounts/dashboard/student/
      teacher → /accounts/dashboard/teacher/
      admin   → /admin/  (Django's built-in admin panel)
      unknown → home
    """
    if user.role == User.Role.STUDENT:
        return redirect('users:student_dashboard')
    elif user.role == User.Role.TEACHER:
        return redirect('users:teacher_dashboard')
    elif user.role == User.Role.ADMIN:
        return redirect('admin_dashboard:dashboard')
    return redirect('home')
