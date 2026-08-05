"""
Django development settings for lms project.
"""

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-!065c+u=2&qzbzyc!vxucxsm^i&x=1*sdn0$87i%ph!9k3r*x&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ------------------------------------------------------------------
# Email Configuration (Development Environment)
# ------------------------------------------------------------------
# In development, we use console.EmailBackend so sent password-reset
# emails are printed directly into standard output (terminal stdout).
# This allows testing the entire password reset flow without setting up
# a real SMTP mail server.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'LMS Portal <noreply@lmsportal.com>'

