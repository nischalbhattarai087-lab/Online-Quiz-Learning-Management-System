from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from users.models import User
from .models import Category, Course


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
