import logging
import uuid
from random import choice
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from faker import Faker
from tests.helper_functions import create_n_user
from core.models.users import UserActivity


logger = logging.getLogger(__name__)

user = get_user_model()
faker = Faker()


class TestAdminDashboardSection(TestCase):
    """Test the admin management of users"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = user.objects.create_superuser(
            password=faker.password(),
            email=faker.email(),
            is_staff=True,
            is_superuser=True,
            is_active=True,
            role="main_admin",
            full_name=faker.name(),
        )
        self.client.force_authenticate(user=self.admin_user)
        # create test 20 users
        self.users = create_n_user(n=20, role="user")
        # create 20 random user activities  manually
        for i in range(20):
            UserActivity.objects.create(
                user=self.users[i],
                description=faker.text(),
                activity_type=choice(["login", "profile"]),
            )

    #  test get the admin dashboard stats
    def test_get_admin_dashboard_stats(self):
        """get the admin dashboard stats"""
        url = reverse("dashboard-stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # test get recent activities
    def test_get_recent_activities(self):
        """get recent activities"""
        url = reverse("recent-activities")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
