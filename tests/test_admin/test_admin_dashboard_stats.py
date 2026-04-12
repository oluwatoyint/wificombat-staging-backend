import logging
from random import choice
from datetime import timedelta
from django.utils.timezone import now
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from faker import Faker
from tests.helper_functions import create_n_user
from core.models.users import UserActivity

logger = logging.getLogger(__name__)

User = get_user_model()
faker = Faker()

class TestAdminDashboardStats(TestCase):
    """Test the admin dashboard statistics endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            password=faker.password(),
            email=faker.email(),
            is_staff=True,
            is_superuser=True,
            is_active=True,
            role="main_admin",
            full_name=faker.name(),
        )
        self.client.force_authenticate(user=self.admin_user)

        # Create test users
        self.users = create_n_user(n=20, role="user")
        self.tutors = create_n_user(n=5, role=User.Roles.TUTOR)

        # Create user activities
        for user in self.users:
            UserActivity.objects.create(
                user=user,
                description=faker.text(),
                activity_type=choice(["login", "course"]),
                created_at=now() - timedelta(days=choice(range(1, 60))),
            )

    def test_get_admin_dashboard_stats(self):
        """Test retrieving admin dashboard statistics"""
        url = reverse("dashboard-stats")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn("total_users", response_data['data'])
        self.assertIn("active_schools", response_data['data'])
        self.assertIn("courses_enrollment", response_data['data'])
        self.assertIn("total_tutors", response_data['data'])

    def test_user_stats(self):
        """Test total user statistics calculation"""
        # Simulate a week ago
        past_week = now() - timedelta(days=7)
        # Create users joined in the past week
        User.objects.create_user(
            password=faker.password(),
            email=faker.email(),
            date_joined=past_week + timedelta(days=1),
            is_active=True,
            full_name=faker.name(),
        )
        url = reverse("dashboard-stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_stats = response.json()['data'].get("total_users")

        self.assertIsNotNone(user_stats)
        self.assertIn("count", user_stats)
        self.assertIn("percentage", user_stats)
        self.assertIn("trend", user_stats)

    def test_school_stats(self):
        """Test active schools statistics calculation"""
        url = reverse("dashboard-stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        school_stats = response.json()["data"].get("active_schools")

        self.assertIsNotNone(school_stats)
        self.assertIn("count", school_stats)
        self.assertIn("percentage", school_stats)
        self.assertIn("trend", school_stats)

    def test_course_enrollment_stats(self):
        """Test course enrollment statistics calculation"""
        
        url = reverse("dashboard-stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrollment_stats = response.json()["data"].get("courses_enrollment")

        self.assertIsNotNone(enrollment_stats)
        self.assertIn("count", enrollment_stats)
        self.assertIn("percentage", enrollment_stats)
        self.assertIn("trend", enrollment_stats)

    def test_tutor_stats(self):
        """Test total tutor statistics calculation"""
        # Simulate tutors joining in the past week
        tutor_user = User.objects.create_user(
            password=faker.password(),
            email=faker.email(),
            date_joined=now() - timedelta(days=3),
            is_active=True,
            role=User.Roles.TUTOR,
            full_name=faker.name(),
        )
        url = reverse("dashboard-stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tutor_stats = response.json()["data"].get("total_tutors")

        self.assertIsNotNone(tutor_stats)
        self.assertIn("count", tutor_stats)
        self.assertIn("percentage", tutor_stats)
        self.assertIn("trend", tutor_stats)
