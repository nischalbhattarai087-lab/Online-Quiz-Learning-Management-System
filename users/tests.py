"""
users/tests.py

Comprehensive Role-Based Access Control (RBAC) & Student Dashboard tests.

Tests:
  1. Student accessing student page → 200 OK (Allowed)
  2. Student accessing teacher page → 403 Forbidden (Denied)
  3. Teacher accessing teacher page → 200 OK (Allowed)
  4. Teacher accessing student page → 403 Forbidden (Denied)
  5. Admin accessing admin page → 200 OK (Allowed)
  6. Logged-out user accessing protected page → 302 Redirect to login (Denied)
  7. Role manipulation prevention on profile-edit form
  8. Student Dashboard access & security tests
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


class StudentDashboardTest(TestCase):
    """
    Test suite for Student Dashboard functionality & security.
    """

    def setUp(self):
        # Create Student 1
        self.student1 = User.objects.create_user(
            username='alice_student',
            email='alice@example.com',
            password='Password123!',
            first_name='Alice',
            last_name='Smith',
            role=User.Role.STUDENT
        )

        # Create Student 2
        self.student2 = User.objects.create_user(
            username='bob_student',
            email='bob@example.com',
            password='Password123!',
            first_name='Bob',
            last_name='Jones',
            role=User.Role.STUDENT
        )

        # Create Teacher
        self.teacher = User.objects.create_user(
            username='teacher_dave',
            email='dave@example.com',
            password='Password123!',
            first_name='Dave',
            last_name='Teacher',
            role=User.Role.TEACHER
        )

        # Create Admin
        self.admin = User.objects.create_superuser(
            username='admin_boss',
            email='boss@example.com',
            password='Password123!',
            first_name='Boss',
            last_name='Admin',
            role=User.Role.ADMIN
        )

        self.dashboard_url = reverse('student_dashboard')

    def test_student_can_access_dashboard(self):
        """1. Authenticated student can access dashboard (200 OK)."""
        self.client.login(username='alice_student', password='Password123!')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/student_dashboard.html')

    def test_unauthenticated_user_cannot_access_dashboard(self):
        """2. Unauthenticated user cannot access dashboard (302 redirect to login)."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_teacher_cannot_access_student_dashboard(self):
        """3. Teacher cannot access student dashboard (403 Forbidden)."""
        self.client.login(username='teacher_dave', password='Password123!')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_access_student_dashboard(self):
        """4. Admin cannot access student dashboard (403 Forbidden)."""
        self.client.login(username='admin_boss', password='Password123!')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 403)

    def test_dashboard_displays_logged_in_student_information(self):
        """5. Dashboard displays logged-in student's actual DB information."""
        self.client.login(username='alice_student', password='Password123!')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice')
        self.assertContains(response, 'alice@example.com')
        self.assertContains(response, 'alice_student')

    def test_another_user_information_is_never_displayed(self):
        """6. When Alice is logged in, Bob's information is never displayed."""
        self.client.login(username='alice_student', password='Password123!')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'bob_student')
        self.assertNotContains(response, 'bob@example.com')


class TeacherDashboardTest(TestCase):
    """
    Test suite for Teacher Dashboard access control, security, and content.
    """

    def setUp(self):
        # Teacher user
        self.teacher = User.objects.create_user(
            username='teacher_alice',
            email='teacher_alice@example.com',
            password='Password123!',
            first_name='Alice',
            last_name='Teacher',
            role=User.Role.TEACHER,
        )

        # Student user — must be blocked
        self.student = User.objects.create_user(
            username='student_bob',
            email='student_bob@example.com',
            password='Password123!',
            first_name='Bob',
            last_name='Student',
            role=User.Role.STUDENT,
        )

        # Admin user — must be blocked
        self.admin = User.objects.create_superuser(
            username='admin_carol',
            email='admin_carol@example.com',
            password='Password123!',
            first_name='Carol',
            last_name='Admin',
            role=User.Role.ADMIN,
        )

        self.dashboard_url = reverse('teacher_dashboard')
        self.student_dashboard_url = reverse('student_dashboard')

    def test_teacher_can_access_dashboard(self):
        """1. Authenticated teacher can access the Teacher Dashboard (200 OK)."""
        self.client.login(username='teacher_alice', password='Password123!')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/teacher_dashboard.html')

    def test_student_cannot_access_teacher_dashboard(self):
        """2. Student cannot access Teacher Dashboard (403 Forbidden)."""
        self.client.login(username='student_bob', password='Password123!')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_access_teacher_dashboard(self):
        """3. Admin cannot access Teacher Dashboard (403 Forbidden)."""
        self.client.login(username='admin_carol', password='Password123!')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 403)

    def test_logged_out_user_cannot_access_teacher_dashboard(self):
        """4. Unauthenticated user is redirected to login (302)."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_dashboard_displays_authenticated_teacher_information(self):
        """5. Teacher Dashboard displays the logged-in teacher's own DB information."""
        self.client.login(username='teacher_alice', password='Password123!')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice')
        self.assertContains(response, 'teacher_alice@example.com')
        self.assertContains(response, 'teacher_alice')

    def test_student_dashboard_still_works_after_teacher_dashboard_added(self):
        """6. Student Dashboard continues to work after Teacher Dashboard was implemented."""
        self.client.login(username='student_bob', password='Password123!')
        response = self.client.get(self.student_dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/student_dashboard.html')


class AdminManagementAndSecurityTest(TestCase):
    """
    Test suite for Admin User Management, Teacher Creation & Approval, and Security.
    """

    def setUp(self):
        # Admin user
        self.admin = User.objects.create_superuser(
            username='super_admin',
            email='admin@example.com',
            password='AdminPassword123!',
            first_name='Super',
            last_name='Admin',
            role=User.Role.ADMIN,
        )

        # Teacher user (active)
        self.active_teacher = User.objects.create_user(
            username='active_teacher',
            email='teacher1@example.com',
            password='TeacherPassword123!',
            first_name='Active',
            last_name='Teacher',
            role=User.Role.TEACHER,
            is_active=True,
        )

        # Teacher user (deactivated)
        self.inactive_teacher = User.objects.create_user(
            username='inactive_teacher',
            email='teacher2@example.com',
            password='TeacherPassword123!',
            first_name='Inactive',
            last_name='Teacher',
            role=User.Role.TEACHER,
            is_active=False,
        )

        # Student user
        self.student = User.objects.create_user(
            username='student_user',
            email='student1@example.com',
            password='StudentPassword123!',
            first_name='Student',
            last_name='User',
            role=User.Role.STUDENT,
        )

        self.register_url = reverse('users:register')
        self.login_url = reverse('users:login')
        self.admin_dashboard_url = reverse('admin_dashboard:dashboard')
        self.admin_users_url = reverse('admin_dashboard:users')
        self.admin_teachers_url = reverse('admin_dashboard:teachers')

    def test_1_public_registration_creates_student(self):
        """1. Public registration creates a Student account."""
        response = self.client.post(self.register_url, {
            'first_name': 'New',
            'last_name': 'Student',
            'username': 'new_student',
            'email': 'newstudent@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='new_student')
        self.assertEqual(user.role, User.Role.STUDENT)

    def test_2_public_registration_cannot_create_teacher(self):
        """2. Public registration cannot create Teacher even if role=Teacher is posted."""
        response = self.client.post(self.register_url, {
            'first_name': 'Hacker',
            'last_name': 'Teacher',
            'username': 'hacker_teacher',
            'email': 'hackerteacher@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'teacher',  # Attempted payload injection
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='hacker_teacher')
        self.assertEqual(user.role, User.Role.STUDENT)

    def test_3_public_registration_cannot_create_admin(self):
        """3. Public registration cannot create Admin even if role=Admin is posted."""
        response = self.client.post(self.register_url, {
            'first_name': 'Hacker',
            'last_name': 'Admin',
            'username': 'hacker_admin',
            'email': 'hackeradmin@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'admin',  # Attempted payload injection
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='hacker_admin')
        self.assertEqual(user.role, User.Role.STUDENT)

    def test_4_student_cannot_change_their_role(self):
        """4. Student cannot change their role via profile edit."""
        self.client.login(username='student_user', password='StudentPassword123!')
        self.client.post(reverse('users:profile_edit'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'role': 'admin',  # Malicious POST
        })
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, User.Role.STUDENT)

    def test_5_teacher_cannot_change_their_role_to_admin(self):
        """5. Teacher cannot change their role to Admin via profile edit."""
        self.client.login(username='active_teacher', password='TeacherPassword123!')
        self.client.post(reverse('users:profile_edit'), {
            'first_name': 'Teacher',
            'last_name': 'Name',
            'role': 'admin',
        })
        self.active_teacher.refresh_from_db()
        self.assertEqual(self.active_teacher.role, User.Role.TEACHER)

    def test_6_student_cannot_access_admin_dashboard(self):
        """6. Student cannot access Admin Dashboard (403 Forbidden)."""
        self.client.login(username='student_user', password='StudentPassword123!')
        response = self.client.get(self.admin_dashboard_url)
        self.assertEqual(response.status_code, 403)

    def test_7_teacher_cannot_access_admin_dashboard(self):
        """7. Teacher cannot access Admin Dashboard (403 Forbidden)."""
        self.client.login(username='active_teacher', password='TeacherPassword123!')
        response = self.client.get(self.admin_dashboard_url)
        self.assertEqual(response.status_code, 403)

    def test_8_student_cannot_access_teacher_management(self):
        """8. Student cannot access Teacher Management (403 Forbidden)."""
        self.client.login(username='student_user', password='StudentPassword123!')
        response = self.client.get(self.admin_teachers_url)
        self.assertEqual(response.status_code, 403)

    def test_9_teacher_cannot_access_teacher_management(self):
        """9. Teacher cannot access Teacher Management (403 Forbidden)."""
        self.client.login(username='active_teacher', password='TeacherPassword123!')
        response = self.client.get(self.admin_teachers_url)
        self.assertEqual(response.status_code, 403)

    def test_10_admin_can_access_admin_dashboard(self):
        """10. Admin can access Admin Dashboard (200 OK)."""
        self.client.login(username='super_admin', password='AdminPassword123!')
        response = self.client.get(self.admin_dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_dashboard/dashboard.html')

    def test_11_admin_can_view_users(self):
        """11. Admin can view users list (200 OK)."""
        self.client.login(username='super_admin', password='AdminPassword123!')
        response = self.client.get(self.admin_users_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'student_user')
        self.assertContains(response, 'active_teacher')

    def test_12_admin_can_create_teacher(self):
        """12. Admin can create a new Teacher account."""
        self.client.login(username='super_admin', password='AdminPassword123!')
        response = self.client.post(self.admin_teachers_url, {
            'username': 'created_teacher',
            'email': 'createdteacher@example.com',
            'first_name': 'Created',
            'last_name': 'Teacher',
            'password1': 'TeacherPass123!',
            'password2': 'TeacherPass123!',
        })
        self.assertEqual(response.status_code, 302)
        teacher = User.objects.get(username='created_teacher')
        self.assertEqual(teacher.role, User.Role.TEACHER)
        self.assertTrue(teacher.is_active)

    def test_13_approved_teacher_can_login(self):
        """13. Active/approved Teacher can log in and access Teacher Dashboard."""
        login_success = self.client.login(username='active_teacher', password='TeacherPassword123!')
        self.assertTrue(login_success)
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_14_deactivated_teacher_cannot_login(self):
        """14. Deactivated Teacher cannot log in."""
        login_success = self.client.login(username='inactive_teacher', password='TeacherPassword123!')
        self.assertFalse(login_success)

    def test_15_existing_student_dashboard_still_works(self):
        """15. Existing Student Dashboard still works."""
        self.client.login(username='student_user', password='StudentPassword123!')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_16_existing_teacher_dashboard_still_works(self):
        """16. Existing Teacher Dashboard still works."""
        self.client.login(username='active_teacher', password='TeacherPassword123!')
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_17_existing_login_logout_still_works(self):
        """17. Existing login/logout still works."""
        login_success = self.client.login(username='student_user', password='StudentPassword123!')
        self.assertTrue(login_success)
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, 302)

