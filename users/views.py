"""
users/views.py

Why a class-based view (FormView) instead of a function-based view?
- FormView handles the GET/POST branching automatically.
- GET  → renders the empty form.
- POST → validates the form; re-renders on failure, redirects on success.
- It is DRY: no manual `if request.method == 'POST'` boilerplate.
- It is easy to extend (override get_form_kwargs, form_valid, etc.).
"""

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .forms import UserRegistrationForm


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

    # reverse_lazy() is used instead of reverse() because class attributes
    # are evaluated at import time, before the URL configuration is loaded.
    # reverse_lazy() defers the URL resolution until it is actually needed.
    #
    # ⚠️  Pointing to 'home' until login view is implemented in the next step.
    # Change to reverse_lazy('users:login') once login is built.
    success_url = reverse_lazy('home')

    # ------------------------------------------------------------------
    # GET request
    # ------------------------------------------------------------------
    def get(self, request, *args, **kwargs):
        """
        If a logged-in user visits /register/, redirect them away.
        Prevents re-registration while already authenticated.
        """
        if request.user.is_authenticated:
            return self._redirect_authenticated()
        return super().get(request, *args, **kwargs)

    # ------------------------------------------------------------------
    # POST request — valid form
    # ------------------------------------------------------------------
    def form_valid(self, form):
        """
        Called by FormView ONLY when form.is_valid() returns True.

        Steps:
          1. form.save() creates the User with hashed password and role=student.
          2. A success flash message is queued (rendered in the template).
          3. super().form_valid() issues an HTTP 302 redirect to success_url.

        We do NOT log the user in here — that is the login step.
        """
        user = form.save()

        # Django's messages framework queues a one-time notification.
        # It is rendered in the template via {% for message in messages %}.
        # messages.SUCCESS maps to CSS class "success" in the template.
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
        """
        Called by FormView when form.is_valid() returns False.

        The default behaviour (which we keep) is to re-render the template
        with the same form instance, which now carries field-level errors.
        The template iterates {{ field.errors }} to display them inline.

        We add a generic top-level error message as a courtesy.
        """
        messages.error(
            request=self.request,
            message='Please correct the errors below and try again.',
        )
        return super().form_invalid(form)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _redirect_authenticated(self):
        """Redirect already-logged-in users to the home page."""
        from django.shortcuts import redirect
        return redirect('home')
