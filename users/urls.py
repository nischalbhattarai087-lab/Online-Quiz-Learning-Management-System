"""
users/urls.py  —  App-level URL configuration for the `users` application.

Why a separate urls.py per app?
- Each Django app owns its own URL namespace.
- The root lms/urls.py just *includes* this file under a prefix.
- This keeps the project modular: moving/renaming the app only requires
  changing one include() line in lms/urls.py.

app_name creates a URL namespace so templates can use:
  {% url 'users:register' %}   instead of just   {% url 'register' %}
This prevents name collisions when multiple apps define a 'register' view.
"""

from django.urls import path
from . import views

# Namespace — must match the `namespace` kwarg in lms/urls.py include().
app_name = 'users'

urlpatterns = [
    # /accounts/register/
    # name='register' → referenced as 'users:register' in templates and views.
    path('register/', views.RegisterView.as_view(), name='register'),

    # Placeholder for login — will be implemented in the next step.
    # We define the URL now so reverse_lazy('users:login') in the view
    # doesn't raise a NoReverseMatch error.
    # path('login/', views.LoginView.as_view(), name='login'),
]
