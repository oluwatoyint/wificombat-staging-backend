import logging
import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from faker import Faker
from tests.helper_functions import create_n_user


logger = logging.getLogger(__name__)

user = get_user_model()
faker = Faker()


class TestAdminMabageUserAPI(TestCase):
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

    def test_get_all_users(self):
        url = reverse("get_users")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_single_user(self):
        """get single user"""
        user_id = self.users[0].id
        response = self.client.get(reverse("get_user", kwargs={"user_id": user_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["id"], str(user_id))

    def test_delete_single_user(self):
        """delete single user"""
        user_id = self.users[0].id
        response = self.client.delete(reverse("get_user", kwargs={"user_id": user_id}))
        self.assertEqual(response.status_code, 200)

        # check user still exists
        response = self.client.get(reverse("get_user", kwargs={"user_id": user_id}))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["message"], "User not found.")

    # update user
    def test_update_single_user(self):
        """update single user"""
        user_id = self.users[0].id
        updated_data = {"role": "user"}
        response = self.client.put(
            reverse("get_user", kwargs={"user_id": user_id}), updated_data
        )
        self.assertEqual(response.status_code, 200)

        # test 404
        response = self.client.put(
            reverse("get_user", kwargs={"user_id": str(uuid.uuid4())}), updated_data
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["message"], "User not found.")
