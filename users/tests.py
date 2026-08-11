"""
users/tests.py

Comprehensive Role-Based Access Control (RBAC) tests.

Tests:
  1. Student accessing student page → 200 OK (Allowed)
  2. Student accessing teacher page → 403 Forbidden (Denied)
  3. Teacher accessing teacher page → 200 OK (Allowed)
  4. Teacher accessing student page → 403 Forbidden (Denied)
  5. Admin accessing admin page → 200 OK (Allowed)
  6. Logged-out user accessing protected page → 302 Redirect to login (Denied)
  7. Role manipulation prevention on profile-edit form
"""

from django.test import TestCase, Client
from django.urls import reverse
from users.models import User


class RoleBasedAccessControlTest(TestCase):
    """
    Test suite for verifying role-based access control and security permissions.
    """

    def setUp(self):
        """Set up test users for each role."""
        # Create Student
        self.student = User.objects.create_user(
            username='student_test',
            email='student@example.com',
            password='Password123!',
            first_name='Student',
            last_name='User',
            role=User.Role.STUDENT
        )

        # Create Teacher
        self.teacher = User.objects.create_user(
            username='teacher_test',
            email='teacher@example.com',
            password='Password123!',
            first_name='Teacher',
            last_name='User',
            role=User.Role.TEACHER
        )

        # Create Admin
        self.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@example.com',
            password='Password123!',
            first_name='Admin',
            last_name='User',
            role=User.Role.ADMIN
        )

        # Test URLs
        self.student_url = reverse('users:student_only')
        self.teacher_url = reverse('users:teacher_only')
        self.admin_url = reverse('users:admin_only')
        self.login_url = reverse('users:login')
        self.profile_edit_url = reverse('users:profile_edit')

    # ------------------------------------------------------------------
    # 1. Student access tests
    # ------------------------------------------------------------------
    def test_student_access_student_page_allowed(self):
        """Student accessing student-only page must return 200 OK."""
        self.client.login(username='student_test', password='Password123!')
        response = self.client.get(self.student_url)
        self.assertEqual(response.status_code, 200)

    def test_student_access_teacher_page_denied(self):
        """Student accessing teacher-only page must be denied with 403 Forbidden."""
        self.client.login(username='student_test', password='Password123!')
        response = self.client.get(self.teacher_url)
        self.assertEqual(response.status_code, 403)

    def test_student_access_admin_page_denied(self):
        """Student accessing admin-only page must be denied with 403 Forbidden."""
        self.client.login(username='student_test', password='Password123!')
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------------
    # 2. Teacher access tests
    # ------------------------------------------------------------------
    def test_teacher_access_teacher_page_allowed(self):
        """Teacher accessing teacher-only page must return 200 OK."""
        self.client.login(username='teacher_test', password='Password123!')
        response = self.client.get(self.teacher_url)
        self.assertEqual(response.status_code, 200)

    def test_teacher_access_student_page_denied(self):
        """Teacher accessing student-only page must be denied with 403 Forbidden."""
        self.client.login(username='teacher_test', password='Password123!')
        response = self.client.get(self.student_url)
        self.assertEqual(response.status_code, 403)

    def test_teacher_access_admin_page_denied(self):
        """Teacher accessing admin-only page must be denied with 403 Forbidden."""
        self.client.login(username='teacher_test', password='Password123!')
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------------
    # 3. Admin access tests
    # ------------------------------------------------------------------
    def test_admin_access_admin_page_allowed(self):
        """Admin accessing admin-only page must return 200 OK."""
        self.client.login(username='admin_test', password='Password123!')
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # 4. Unauthenticated access tests
    # ------------------------------------------------------------------
    def test_logged_out_user_access_student_page_denied(self):
        """Logged-out user accessing protected student page must redirect to login (302)."""
        response = self.client.get(self.student_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)

    def test_logged_out_user_access_teacher_page_denied(self):
        """Logged-out user accessing protected teacher page must redirect to login (302)."""
        response = self.client.get(self.teacher_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)

    def test_logged_out_user_access_admin_page_denied(self):
        """Logged-out user accessing protected admin page must redirect to login (302)."""
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)

    # ------------------------------------------------------------------
    # 5. Prevent role manipulation
    # ------------------------------------------------------------------
    def test_prevent_role_manipulation(self):
        """A student submitting role='admin' in POST payload must not be able to elevate role."""
        self.client.login(username='student_test', password='Password123!')
        response = self.client.post(self.profile_edit_url, {
            'first_name': 'Hacker',
            'last_name': 'Student',
            'role': 'admin'   # Malicious attempt to self-elevate role
        })
        self.assertEqual(response.status_code, 302)

        # Refresh user instance from DB
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, User.Role.STUDENT)
        self.assertEqual(self.student.first_name, 'Hacker')
