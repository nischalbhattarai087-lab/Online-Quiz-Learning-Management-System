from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from users.models import User
from .models import Category, Course, Enrollment, Lesson


class CategoryModelTest(TestCase):
    """
    Tests for Category model.
    """

    def test_1_category_creation(self):
        """1. Category can be created."""
        category = Category.objects.create(
            name='Programming',
            description='Software engineering & code',
        )
        self.assertEqual(category.name, 'Programming')
        self.assertEqual(category.slug, 'programming')
        self.assertEqual(str(category), 'Programming')

    def test_2_category_name_uniqueness(self):
        """2. Category name is unique."""
        Category.objects.create(name='Networking')
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Networking')


class CourseModelTest(TestCase):
    """
    Tests for Course model, relationships, validation, and properties.
    """

    def setUp(self):
        # Create Teacher User
        self.teacher = User.objects.create_user(
            username='teacher_john',
            email='john@example.com',
            password='Password123!',
            first_name='John',
            last_name='Doe',
            role=User.Role.TEACHER,
        )

        # Create Student User
        self.student = User.objects.create_user(
            username='student_alice',
            email='alice@example.com',
            password='Password123!',
            first_name='Alice',
            last_name='Smith',
            role=User.Role.STUDENT,
        )

        # Create Category
        self.category = Category.objects.create(
            name='Web Development',
            description='Web tech & frameworks',
        )

    def test_3_course_can_be_created(self):
        """3. Course can be created."""
        course = Course.objects.create(
            title='Django Web Development',
            description='Learn Django from scratch',
            teacher=self.teacher,
            category=self.category,
        )
        self.assertEqual(course.title, 'Django Web Development')
        self.assertEqual(Course.objects.count(), 1)

    def test_4_course_belongs_to_teacher(self):
        """4. Course belongs to a Teacher."""
        course = Course.objects.create(
            title='Python Fundamentals',
            teacher=self.teacher,
            category=self.category,
        )
        self.assertEqual(course.teacher, self.teacher)
        self.assertIn(course, self.teacher.courses.all())

    def test_5_course_belongs_to_category(self):
        """5. Course belongs to a Category."""
        course = Course.objects.create(
            title='HTML & CSS',
            teacher=self.teacher,
            category=self.category,
        )
        self.assertEqual(course.category, self.category)
        self.assertIn(course, self.category.courses.all())

    def test_6_difficulty_choices(self):
        """6. Difficulty choices work correctly."""
        course1 = Course.objects.create(
            title='Easy Math',
            teacher=self.teacher,
            difficulty=Course.Difficulty.BEGINNER,
        )
        course2 = Course.objects.create(
            title='Advanced Quantum',
            teacher=self.teacher,
            difficulty=Course.Difficulty.ADVANCED,
        )
        self.assertEqual(course1.difficulty, 'beginner')
        self.assertEqual(course2.difficulty, 'advanced')
        self.assertEqual(str(course1), 'Easy Math (Beginner)')
        self.assertEqual(str(course2), 'Advanced Quantum (Advanced)')

    def test_7_free_course_supported(self):
        """7. Free courses are supported (price = 0.00)."""
        course = Course.objects.create(
            title='Free Intro Course',
            teacher=self.teacher,
            price=Decimal('0.00'),
        )
        self.assertEqual(course.price, Decimal('0.00'))

    def test_8_paid_course_prices(self):
        """8. Paid course prices are stored correctly."""
        course = Course.objects.create(
            title='Paid Mastery Course',
            teacher=self.teacher,
            price=Decimal('49.99'),
        )
        self.assertEqual(course.price, Decimal('49.99'))

    def test_9_course_slug_creation_and_uniqueness(self):
        """9. Course slug is created correctly and handles duplicate titles."""
        course1 = Course.objects.create(
            title='Python Programming',
            teacher=self.teacher,
        )
        course2 = Course.objects.create(
            title='Python Programming',
            teacher=self.teacher,
        )
        self.assertEqual(course1.slug, 'python-programming')
        self.assertEqual(course2.slug, 'python-programming-1')

    def test_10_course_is_unpublished_by_default(self):
        """10. Course is unpublished by default."""
        course = Course.objects.create(
            title='Draft Course',
            teacher=self.teacher,
        )
        self.assertFalse(course.is_published)

    def test_11_teacher_relationship(self):
        """11. Teacher relationship works correctly."""
        course1 = Course.objects.create(title='Course 1', teacher=self.teacher)
        course2 = Course.objects.create(title='Course 2', teacher=self.teacher)
        self.assertEqual(self.teacher.courses.count(), 2)

    def test_12_student_cannot_be_assigned_as_teacher(self):
        """12. Student cannot be assigned as a course teacher (raises ValidationError)."""
        with self.assertRaises(ValidationError):
            Course.objects.create(
                title='Invalid Course',
                teacher=self.student,  # Alice is a Student, not a Teacher
            )


class TeacherCourseCRUDTest(TestCase):
    """
    Test suite for Teacher Course CRUD views, security, and ownership constraints.
    """

    def setUp(self):
        # Teacher 1
        self.teacher1 = User.objects.create_user(
            username='teacher_one',
            email='teacher1@example.com',
            password='Password123!',
            first_name='Teacher',
            last_name='One',
            role=User.Role.TEACHER,
        )

        # Teacher 2
        self.teacher2 = User.objects.create_user(
            username='teacher_two',
            email='teacher2@example.com',
            password='Password123!',
            first_name='Teacher',
            last_name='Two',
            role=User.Role.TEACHER,
        )

        # Student
        self.student = User.objects.create_user(
            username='student_user',
            email='student@example.com',
            password='Password123!',
            first_name='Student',
            last_name='User',
            role=User.Role.STUDENT,
        )

        # Category
        self.category = Category.objects.create(
            name='Computer Science',
            description='CS subjects',
        )

        # Course owned by Teacher 1
        self.course1 = Course.objects.create(
            title='Data Structures in Python',
            description='Master DS & Algorithms',
            teacher=self.teacher1,
            category=self.category,
            difficulty=Course.Difficulty.INTERMEDIATE,
            price=Decimal('29.99'),
            is_published=False,
        )

    def test_1_teacher_can_create_course(self):
        """1. Teacher can create a course."""
        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.post(reverse('courses:teacher_course_create'), {
            'title': 'New Algorithms Course',
            'description': 'Comprehensive algorithms guide',
            'category': self.category.id,
            'difficulty': 'beginner',
            'price': '0.00',
            'is_published': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Course.objects.filter(title='New Algorithms Course').exists())

    def test_2_course_owner_is_automatically_set_to_request_user(self):
        """2. Course owner is automatically set to request.user."""
        self.client.login(username='teacher_one', password='Password123!')
        self.client.post(reverse('courses:teacher_course_create'), {
            'title': 'Auto Owner Test',
            'description': 'Testing owner assignment',
            'category': self.category.id,
            'difficulty': 'beginner',
            'price': '10.00',
        })
        course = Course.objects.get(title='Auto Owner Test')
        self.assertEqual(course.teacher, self.teacher1)

    def test_3_teacher_cannot_assign_another_teacher_as_course_owner(self):
        """3. Teacher cannot assign another teacher as course owner via POST payload."""
        self.client.login(username='teacher_one', password='Password123!')
        self.client.post(reverse('courses:teacher_course_create'), {
            'title': 'Owner Spoof Test',
            'description': 'Testing malicious owner payload',
            'category': self.category.id,
            'difficulty': 'beginner',
            'price': '15.00',
            'teacher': self.teacher2.id,  # Attempted payload injection
        })
        course = Course.objects.get(title='Owner Spoof Test')
        self.assertEqual(course.teacher, self.teacher1)  # Must be request.user!

    def test_4_teacher_can_view_their_own_courses(self):
        """4. Teacher can view their own courses list and detail page."""
        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.get(reverse('courses:teacher_course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Data Structures in Python')

        detail_response = self.client.get(reverse('courses:teacher_course_detail', kwargs={'slug': self.course1.slug}))
        self.assertEqual(detail_response.status_code, 200)

    def test_5_teacher_cannot_view_another_teacher_course_management_page(self):
        """5. Teacher cannot view another teacher's course management detail page (returns 404)."""
        self.client.login(username='teacher_two', password='Password123!')
        response = self.client.get(reverse('courses:teacher_course_detail', kwargs={'slug': self.course1.slug}))
        self.assertEqual(response.status_code, 404)

    def test_6_teacher_can_edit_their_own_course(self):
        """6. Teacher can edit their own course."""
        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.post(reverse('courses:teacher_course_edit', kwargs={'slug': self.course1.slug}), {
            'title': 'Data Structures in Python (Updated)',
            'description': 'Updated description text',
            'category': self.category.id,
            'difficulty': 'advanced',
            'price': '39.99',
            'is_published': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.course1.refresh_from_db()
        self.assertEqual(self.course1.title, 'Data Structures in Python (Updated)')
        self.assertEqual(self.course1.price, Decimal('39.99'))

    def test_7_teacher_cannot_edit_another_teacher_course(self):
        """7. Teacher cannot edit another teacher's course."""
        self.client.login(username='teacher_two', password='Password123!')
        response = self.client.post(reverse('courses:teacher_course_edit', kwargs={'slug': self.course1.slug}), {
            'title': 'Hacked Title',
            'description': 'Hacked description',
            'category': self.category.id,
            'difficulty': 'beginner',
            'price': '0.00',
        })
        self.assertEqual(response.status_code, 404)
        self.course1.refresh_from_db()
        self.assertNotEqual(self.course1.title, 'Hacked Title')

    def test_8_teacher_can_delete_their_own_course(self):
        """8. Teacher can delete their own course."""
        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.post(reverse('courses:teacher_course_delete', kwargs={'slug': self.course1.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Course.objects.filter(id=self.course1.id).exists())

    def test_9_teacher_cannot_delete_another_teacher_course(self):
        """9. Teacher cannot delete another teacher's course."""
        self.client.login(username='teacher_two', password='Password123!')
        response = self.client.post(reverse('courses:teacher_course_delete', kwargs={'slug': self.course1.slug}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Course.objects.filter(id=self.course1.id).exists())

    def test_10_teacher_can_publish_their_own_course(self):
        """10. Teacher can publish their own course."""
        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.post(reverse('courses:teacher_course_publish', kwargs={'slug': self.course1.slug}))
        self.assertEqual(response.status_code, 302)
        self.course1.refresh_from_db()
        self.assertTrue(self.course1.is_published)

    def test_11_teacher_can_unpublish_their_own_course(self):
        """11. Teacher can unpublish their own course."""
        self.course1.is_published = True
        self.course1.save()

        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.post(reverse('courses:teacher_course_unpublish', kwargs={'slug': self.course1.slug}))
        self.assertEqual(response.status_code, 302)
        self.course1.refresh_from_db()
        self.assertFalse(self.course1.is_published)

    def test_12_student_cannot_access_teacher_course_management(self):
        """12. Student cannot access Teacher course management (403 Forbidden)."""
        self.client.login(username='student_user', password='Password123!')
        response = self.client.get(reverse('courses:teacher_course_list'))
        self.assertEqual(response.status_code, 403)

    def test_13_unauthenticated_user_cannot_access_teacher_course_management(self):
        """13. Unauthenticated user cannot access Teacher course management (302 Redirect)."""
        response = self.client.get(reverse('courses:teacher_course_list'))
        self.assertEqual(response.status_code, 302)

    def test_14_negative_course_price_is_rejected(self):
        """14. Negative course price is rejected by form validation."""
        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.post(reverse('courses:teacher_course_create'), {
            'title': 'Invalid Price Course',
            'description': 'Testing negative price',
            'category': self.category.id,
            'difficulty': 'beginner',
            'price': '-15.00',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'price', 'Course price cannot be negative.')

    def test_15_invalid_image_upload_is_rejected(self):
        """15. Invalid image upload (e.g. text file disguised as image) is rejected."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_file = SimpleUploadedFile("script.txt", b"print('hello')", content_type="text/plain")

        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.post(reverse('courses:teacher_course_create'), {
            'title': 'Fake Image Course',
            'description': 'Testing fake image upload',
            'category': self.category.id,
            'difficulty': 'beginner',
            'price': '0.00',
            'thumbnail': fake_file,
        })
        self.assertEqual(response.status_code, 200)

    def test_16_course_title_validation_works(self):
        """16. Course title validation works (blank title rejected)."""
        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.post(reverse('courses:teacher_course_create'), {
            'title': '   ',
            'description': 'Valid description',
            'category': self.category.id,
            'difficulty': 'beginner',
            'price': '0.00',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'title', 'Course title is required.')

    def test_17_course_list_only_shows_courses_owned_by_logged_in_teacher(self):
        """17. Course list only shows courses owned by the logged-in Teacher."""
        # Create course for Teacher 2
        course2 = Course.objects.create(
            title="Teacher 2 Exclusive Course",
            teacher=self.teacher2,
        )

        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.get(reverse('courses:teacher_course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Data Structures in Python')
        self.assertNotContains(response, 'Teacher 2 Exclusive Course')

    def test_18_existing_student_dashboard_still_works(self):
        """18. Existing Student Dashboard still works."""
        self.client.login(username='student_user', password='Password123!')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_19_existing_teacher_dashboard_still_works(self):
        """19. Existing Teacher Dashboard still works."""
        self.client.login(username='teacher_one', password='Password123!')
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total Courses')

    def test_20_existing_authentication_still_works(self):
        """20. Existing authentication still works."""
        login_success = self.client.login(username='teacher_one', password='Password123!')
        self.assertTrue(login_success)
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, 302)


# =============================================================================
# Enrollment Model & Integration Tests (Prompt 17)
# =============================================================================

class EnrollmentModelTest(TestCase):
    """
    Unit tests for the Enrollment model.
    """

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='instructor_bob',
            email='bob@example.com',
            password='Password123!',
            role=User.Role.TEACHER,
        )
        self.student = User.objects.create_user(
            username='student_eva',
            email='eva@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
        )
        self.course = Course.objects.create(
            title='Intro to Cybersecurity',
            teacher=self.teacher,
            is_published=True,
        )

    def test_1_enrollment_creation(self):
        """1. Enrollment can be created successfully."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
        )
        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(enrollment.course, self.course)
        self.assertTrue(enrollment.is_active)
        self.assertIsNotNone(enrollment.enrolled_at)

    def test_2_duplicate_student_course_enrollment_prevented(self):
        """2. Duplicate Student + Course enrollment is prevented (unique constraint)."""
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
        )
        with self.assertRaises((IntegrityError, ValidationError)):
            Enrollment.objects.create(
                student=self.student,
                course=self.course,
            )


    def test_3_enrollment_string_representation(self):
        """3. Enrollment string representation works."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
        )
        expected = f"{self.student.username} enrolled in {self.course.title}"
        self.assertEqual(str(enrollment), expected)


class StudentCourseEnrollmentTest(TestCase):
    """
    Tests for student course enrollment workflow and security.
    """

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher_dave',
            email='dave@example.com',
            password='Password123!',
            role=User.Role.TEACHER,
        )
        self.student1 = User.objects.create_user(
            username='student_sarah',
            email='sarah@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
        )
        self.student2 = User.objects.create_user(
            username='student_mike',
            email='mike@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
        )
        self.admin = User.objects.create_user(
            username='admin_boss',
            email='admin@example.com',
            password='Password123!',
            role=User.Role.ADMIN,
        )
        self.published_course = Course.objects.create(
            title='Python Full Stack Bootcamp',
            teacher=self.teacher,
            is_published=True,
        )
        self.unpublished_course = Course.objects.create(
            title='Draft AI Course',
            teacher=self.teacher,
            is_published=False,
        )

    def test_4_student_can_enroll_in_published_course(self):
        """4. Student can enroll in a published course via POST."""
        self.client.login(username='student_sarah', password='Password123!')
        response = self.client.post(
            reverse('courses:enroll_course', kwargs={'slug': self.published_course.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('courses:student_courses'))

        # Check DB
        self.assertTrue(
            Enrollment.objects.filter(
                student=self.student1,
                course=self.published_course,
                is_active=True,
            ).exists()
        )

    def test_5_student_cannot_enroll_twice_in_same_course(self):
        """5. Student cannot enroll twice; duplicate POST is handled gracefully without crash."""
        self.client.login(username='student_sarah', password='Password123!')
        # First enrollment
        self.client.post(reverse('courses:enroll_course', kwargs={'slug': self.published_course.slug}))
        self.assertEqual(Enrollment.objects.filter(student=self.student1, course=self.published_course).count(), 1)

        # Second enrollment attempt
        response = self.client.post(
            reverse('courses:enroll_course', kwargs={'slug': self.published_course.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Enrollment.objects.filter(student=self.student1, course=self.published_course).count(), 1)

    def test_6_student_cannot_enroll_in_unpublished_course(self):
        """6. Student cannot enroll in an unpublished course (returns 404)."""
        self.client.login(username='student_sarah', password='Password123!')
        response = self.client.post(
            reverse('courses:enroll_course', kwargs={'slug': self.unpublished_course.slug})
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            Enrollment.objects.filter(student=self.student1, course=self.unpublished_course).exists()
        )

    def test_7_teacher_cannot_enroll_through_student_endpoint(self):
        """7. Teacher cannot enroll (403 Forbidden)."""
        self.client.login(username='teacher_dave', password='Password123!')
        response = self.client.post(
            reverse('courses:enroll_course', kwargs={'slug': self.published_course.slug})
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Enrollment.objects.filter(course=self.published_course).exists())

    def test_8_admin_cannot_enroll_through_student_endpoint(self):
        """8. Admin cannot enroll through the Student endpoint (403 Forbidden)."""
        self.client.login(username='admin_boss', password='Password123!')
        response = self.client.post(
            reverse('courses:enroll_course', kwargs={'slug': self.published_course.slug})
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Enrollment.objects.filter(course=self.published_course).exists())

    def test_9_unauthenticated_user_redirected_to_login(self):
        """9. Unauthenticated user is redirected to login (302)."""
        response = self.client.post(
            reverse('courses:enroll_course', kwargs={'slug': self.published_course.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_10_post_required_for_enrollment_action(self):
        """10. GET request does not enroll and redirects back to course detail."""
        self.client.login(username='student_sarah', password='Password123!')
        response = self.client.get(
            reverse('courses:enroll_course', kwargs={'slug': self.published_course.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('courses:course_detail', kwargs={'slug': self.published_course.slug})
        )
        self.assertFalse(
            Enrollment.objects.filter(student=self.student1, course=self.published_course).exists()
        )

    def test_11_csrf_protection_enabled_on_enrollment(self):
        """11. CSRF protection is active for enrollment endpoint."""
        csrf_client = self.client_class(enforce_csrf_checks=True)
        csrf_client.login(username='student_sarah', password='Password123!')
        # Post without CSRF token
        response = csrf_client.post(
            reverse('courses:enroll_course', kwargs={'slug': self.published_course.slug})
        )
        self.assertEqual(response.status_code, 403)


class MyCoursesViewTest(TestCase):
    """
    Tests for the Student My Courses page (/student/courses/).
    """

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='instructor_tom',
            email='tom@example.com',
            password='Password123!',
            role=User.Role.TEACHER,
        )
        self.student_a = User.objects.create_user(
            username='student_alice_mc',
            email='alice_mc@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
        )
        self.student_b = User.objects.create_user(
            username='student_bob_mc',
            email='bob_mc@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
        )
        self.course_python = Course.objects.create(
            title='Python 101',
            teacher=self.teacher,
            is_published=True,
        )
        self.course_django = Course.objects.create(
            title='Django 101',
            teacher=self.teacher,
            is_published=True,
        )

    def test_12_student_can_view_their_enrolled_courses(self):
        """12. Student can view their enrolled courses."""
        Enrollment.objects.create(student=self.student_a, course=self.course_python)
        self.client.login(username='student_alice_mc', password='Password123!')
        response = self.client.get(reverse('courses:student_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python 101')
        self.assertContains(response, 'My Courses')

    def test_13_student_cannot_see_another_students_courses(self):
        """13. Student cannot see another Student's courses."""
        Enrollment.objects.create(student=self.student_b, course=self.course_django)

        # Student A logs in (enrolled only in Python)
        Enrollment.objects.create(student=self.student_a, course=self.course_python)
        self.client.login(username='student_alice_mc', password='Password123!')
        response = self.client.get(reverse('courses:student_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python 101')
        self.assertNotContains(response, 'Django 101')

    def test_14_only_active_enrollments_shown(self):
        """14. Inactive enrollments are excluded from My Courses."""
        Enrollment.objects.create(student=self.student_a, course=self.course_python, is_active=False)
        self.client.login(username='student_alice_mc', password='Password123!')
        response = self.client.get(reverse('courses:student_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Python 101')

    def test_15_empty_enrollment_state_works(self):
        """15. Empty enrollment state shows helpful message and Browse Courses button."""
        self.client.login(username='student_alice_mc', password='Password123!')
        response = self.client.get(reverse('courses:student_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You haven't enrolled in any courses yet.")
        self.assertContains(response, reverse('courses:course_list'))


class CourseDetailEnrollmentStatusTest(TestCase):
    """
    Tests for course detail page enrollment button status.
    """

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='instructor_rachel',
            email='rachel@example.com',
            password='Password123!',
            role=User.Role.TEACHER,
        )
        self.student = User.objects.create_user(
            username='student_emma',
            email='emma@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
        )
        self.course = Course.objects.create(
            title='Data Science Essentials',
            teacher=self.teacher,
            is_published=True,
        )

    def test_16_unenrolled_student_sees_enroll_now_button(self):
        """16. Unenrolled Student sees 'Enroll Now' button."""
        self.client.login(username='student_emma', password='Password123!')
        response = self.client.get(reverse('courses:course_detail', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enroll Now')
        self.assertNotContains(response, 'Enrolled')

    def test_17_enrolled_student_sees_enrolled_badge(self):
        """17. Enrolled Student sees 'Enrolled' badge and 'Go to My Courses' link."""
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(username='student_emma', password='Password123!')
        response = self.client.get(reverse('courses:course_detail', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enrolled')
        self.assertContains(response, 'Go to My Courses')

    def test_18_enrollment_status_correct_for_each_student(self):
        """18. Enrollment status is isolated and correct per student."""
        other_student = User.objects.create_user(
            username='student_lucas',
            email='lucas@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
        )
        Enrollment.objects.create(student=other_student, course=self.course)

        # Emma is not enrolled
        self.client.login(username='student_emma', password='Password123!')
        response = self.client.get(reverse('courses:course_detail', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enroll Now')


class StudentDashboardEnrollmentIntegrationTest(TestCase):
    """
    Tests for Student Dashboard integration with real enrollment metrics.
    """

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher_dash',
            email='dash_teacher@example.com',
            password='Password123!',
            role=User.Role.TEACHER,
        )
        self.student = User.objects.create_user(
            username='student_dash',
            email='dash_student@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
        )
        self.course1 = Course.objects.create(
            title='Course Alpha',
            teacher=self.teacher,
            is_published=True,
        )
        self.course2 = Course.objects.create(
            title='Course Beta',
            teacher=self.teacher,
            is_published=True,
        )

    def test_19_student_dashboard_displays_real_enrolled_courses_count(self):
        """19. Student Dashboard displays accurate count of enrolled courses."""
        self.client.login(username='student_dash', password='Password123!')

        # 0 courses
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['enrolled_courses_count'], 0)

        # Enroll in 2 courses
        Enrollment.objects.create(student=self.student, course=self.course1)
        Enrollment.objects.create(student=self.student, course=self.course2)

        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['enrolled_courses_count'], 2)
        self.assertContains(response, 'Course Alpha')
        self.assertContains(response, 'Course Beta')


class LessonModelTest(TestCase):
    """
    Tests for the Lesson model: creation, relationships, ordering,
    slug uniqueness, file validation, cascade deletion, and timestamps.
    """

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='lesson_teacher',
            email='lessonteacher@example.com',
            password='Password123!',
            first_name='Lesson',
            last_name='Teacher',
            role=User.Role.TEACHER,
        )
        self.category = Category.objects.create(
            name='Lesson Testing Category',
            description='For lesson tests',
        )
        self.course_a = Course.objects.create(
            title='Course A for Lessons',
            teacher=self.teacher,
            category=self.category,
        )
        self.course_b = Course.objects.create(
            title='Course B for Lessons',
            teacher=self.teacher,
            category=self.category,
        )

    def test_1_lesson_can_be_created(self):
        """1. Lesson can be created."""
        lesson = Lesson.objects.create(
            course=self.course_a,
            title='Introduction to Python',
            description='First lesson overview',
            order=1,
        )
        self.assertEqual(lesson.title, 'Introduction to Python')
        self.assertEqual(Lesson.objects.count(), 1)

    def test_2_lesson_belongs_to_correct_course(self):
        """2. Lesson belongs to the correct Course."""
        lesson = Lesson.objects.create(
            course=self.course_a,
            title='Lesson in Course A',
            order=1,
        )
        self.assertEqual(lesson.course, self.course_a)
        self.assertIn(lesson, self.course_a.lessons.all())
        self.assertNotIn(lesson, self.course_b.lessons.all())

    def test_3_multiple_lessons_belong_to_one_course(self):
        """3. Multiple lessons can belong to one Course."""
        Lesson.objects.create(course=self.course_a, title='Lesson 1', order=1)
        Lesson.objects.create(course=self.course_a, title='Lesson 2', order=2)
        Lesson.objects.create(course=self.course_a, title='Lesson 3', order=3)
        self.assertEqual(self.course_a.lessons.count(), 3)

    def test_4_lesson_ordering_works(self):
        """4. Lesson ordering works (ordered by course, then order)."""
        l3 = Lesson.objects.create(course=self.course_a, title='Third', order=3)
        l1 = Lesson.objects.create(course=self.course_a, title='First', order=1)
        l2 = Lesson.objects.create(course=self.course_a, title='Second', order=2)
        lessons = list(Lesson.objects.filter(course=self.course_a))
        self.assertEqual(lessons, [l1, l2, l3])

    def test_5_same_order_in_different_courses(self):
        """5. Same order number can be used in different Courses."""
        lesson_a = Lesson.objects.create(
            course=self.course_a, title='Intro A', order=1,
        )
        lesson_b = Lesson.objects.create(
            course=self.course_b, title='Intro B', order=1,
        )
        self.assertEqual(lesson_a.order, 1)
        self.assertEqual(lesson_b.order, 1)

    def test_6_duplicate_order_within_same_course_rejected(self):
        """6. Duplicate order within the same Course is rejected."""
        Lesson.objects.create(
            course=self.course_a, title='Lesson One', order=1,
        )
        with self.assertRaises((IntegrityError, ValidationError)):
            Lesson.objects.create(
                course=self.course_a, title='Another Lesson One', order=1,
            )

    def test_7_lesson_slug_works(self):
        """7. Lesson slug is auto-generated from title."""
        lesson = Lesson.objects.create(
            course=self.course_a,
            title='Getting Started with Django',
            order=1,
        )
        self.assertEqual(lesson.slug, 'getting-started-with-django')

    def test_8_same_slug_in_different_courses(self):
        """8. Same slug can exist in different Courses."""
        Lesson.objects.create(
            course=self.course_a, title='Introduction', order=1,
        )
        lesson_b = Lesson.objects.create(
            course=self.course_b, title='Introduction', order=1,
        )
        self.assertEqual(lesson_b.slug, 'introduction')

    def test_9_duplicate_course_slug_rejected(self):
        """9. Duplicate Course + slug combination is rejected."""
        Lesson.objects.create(
            course=self.course_a, title='Introduction', slug='introduction', order=1,
        )
        with self.assertRaises((IntegrityError, ValidationError)):
            Lesson.objects.create(
                course=self.course_a, title='Another Intro', slug='introduction', order=2,
            )

    def test_10_new_lessons_are_unpublished_by_default(self):
        """10. New lessons are unpublished by default."""
        lesson = Lesson.objects.create(
            course=self.course_a, title='Draft Lesson', order=1,
        )
        self.assertFalse(lesson.is_published)

    def test_11_pdf_file_validation_works(self):
        """11. PDF file validation works (valid PDF extension accepted)."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        pdf_file = SimpleUploadedFile('lesson.pdf', b'%PDF-1.4 test content', content_type='application/pdf')
        lesson = Lesson.objects.create(
            course=self.course_a,
            title='PDF Lesson',
            order=1,
            pdf_file=pdf_file,
        )
        self.assertIsNotNone(lesson.pdf_file)
        self.assertTrue(lesson.pdf_file.name.endswith('.pdf'))

    def test_12_invalid_file_types_rejected(self):
        """12. Invalid file types are rejected."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        exe_file = SimpleUploadedFile('malware.exe', b'MZ\x00\x00', content_type='application/octet-stream')
        with self.assertRaises(ValidationError):
            Lesson.objects.create(
                course=self.course_a,
                title='Bad File Lesson',
                order=1,
                pdf_file=exe_file,
            )

    def test_13_lesson_deleted_when_course_deleted(self):
        """13. Lesson is deleted when its Course is deleted (CASCADE)."""
        Lesson.objects.create(course=self.course_a, title='Will be deleted', order=1)
        self.assertEqual(Lesson.objects.count(), 1)
        self.course_a.delete()
        self.assertEqual(Lesson.objects.count(), 0)

    def test_14_created_at_and_updated_at_work(self):
        """14. created_at and updated_at are set automatically."""
        lesson = Lesson.objects.create(
            course=self.course_a, title='Timestamp Lesson', order=1,
        )
        self.assertIsNotNone(lesson.created_at)
        self.assertIsNotNone(lesson.updated_at)

    def test_15_model_string_representation(self):
        """15. Model string representation is useful."""
        lesson = Lesson.objects.create(
            course=self.course_a, title='Variables and Data Types', order=3,
        )
        self.assertEqual(str(lesson), 'Lesson 3: Variables and Data Types')
