import logging
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from core.models.courses import Course, CourseEnrollment, CoursePathWay, UserLessonProgress, UserModuleProgress
from core.models.media import Media
from core.models.users import Wallet

User = get_user_model()
faker = Faker()
logger = logging.getLogger(__name__)


class TestPurchaseCourse(TestCase):
    """Test cases for Course Purchase Endpoint"""

    def setUp(self):
        """Set up test data for purchase course endpoint"""
        self.client = APIClient()

        # Create test users
        self.normal_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
            role="user",
        )
        
        # Get user wallet
        self.wallet = Wallet.objects.get(user=self.normal_user)
        self.wallet.balance = Decimal("300.00")
        self.wallet.save()


        # Create test media for cover image
        self.test_media = Media.objects.create(media_type="photo")

        # Create test pathway
        self.pathway = CoursePathWay.objects.create(
            title=faker.name(), description=faker.text(), cover_image=self.test_media
        )

        # Create sample courses
        self.course1 = Course.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
            level="Beginner",
            stage="Active",
            course_pathway=self.pathway,
            amount=Decimal("99.99"),
        )

        self.course2 = Course.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
            level="Intermediate",
            stage="Active",
            course_pathway=self.pathway,
            amount=Decimal("149.99"),
        )

        # Set up authentication
        self.client.force_authenticate(user=self.normal_user)

    def test_successful_course_purchase(self):
        """Test successful purchase of multiple courses"""

        # Prepare purchase data
        purchase_data = {
            "courses": [str(self.course1.id), str(self.course2.id)]
        }

        # Make purchase request
        response = self.client.post(
            reverse("purchase_course"), 
            data=purchase_data, 
            format="json"
        )

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        
        # Verify wallet balance
        self.wallet.refresh_from_db()
        expected_balance = Decimal("300.00") - (self.course1.amount + self.course2.amount)
        self.assertEqual(self.wallet.balance, expected_balance)

        # Verify course enrollments
        enrollments = CourseEnrollment.objects.filter(user=self.normal_user)
        self.assertEqual(enrollments.count(), 2)
        self.assertTrue(enrollments.filter(course=self.course1).exists())
        self.assertTrue(enrollments.filter(course=self.course2).exists())

    def test_insufficient_wallet_balance(self):
        """Test purchase with insufficient wallet balance"""
        # Create wallet with insufficient balance
        self.wallet.balance = Decimal("50.00")
        self.wallet.save()
        
        # Prepare purchase data
        purchase_data = {
            "courses": [str(self.course1.id), str(self.course2.id)]
        }

        # Make purchase request
        response = self.client.post(
            reverse("purchase_course"), 
            data=purchase_data, 
            format="json"
        )

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])
        self.assertIn("Insufficient balance", response.json()["message"])

        # Verify no enrollments created
        enrollments = CourseEnrollment.objects.filter(user=self.normal_user)
        self.assertEqual(enrollments.count(), 0)

    def test_purchase_non_existent_course(self):
        """Test purchase with a non-existent course ID"""

        # Prepare purchase data with invalid course ID
        non_existent_course_id = "123e4567-e89b-12d3-a456-426614174000"
        purchase_data = {
            "courses": [str(self.course1.id), non_existent_course_id]
        }

        # Make purchase request
        response = self.client.post(
            reverse("purchase_course"), 
            data=purchase_data, 
            format="json"
        )

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])
        self.assertIn("does not exist", response.json()["message"])

        # Verify no enrollments created
        enrollments = CourseEnrollment.objects.filter(user=self.normal_user)
        self.assertEqual(enrollments.count(), 0)

    # def test_already_enrolled_course(self):
    #     """Test attempting to purchase a course user is already enrolled in"""

    #     # Pre-enroll user in course1
    #     CourseEnrollment.objects.create(
    #         user=self.normal_user, 
    #         course=self.course1, 
    #         amount_paid=self.course1.amount
    #     )

    #     # Prepare purchase data including already enrolled course
    #     purchase_data = {
    #         "courses": [str(self.course1.id), str(self.course2.id)]
    #     }

    #     # Make purchase request
    #     response = self.client.post(
    #         reverse("purchase_course"), 
    #         data=purchase_data, 
    #         format="json"
    #     )
    #     print('--------------', response.json())

    #     # Assertions
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertFalse(response.json()["success"])
    #     self.assertIn("already enrolled", response.json()["message"])

    #     # Verify only original enrollment exists
    #     enrollments = CourseEnrollment.objects.filter(user=self.normal_user)
    #     self.assertEqual(enrollments.count(), 1)