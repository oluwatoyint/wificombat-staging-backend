import json
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
from core.managers.utils import log_user_activity

logger = logging.getLogger(__name__)

user = get_user_model()
faker = Faker()


class TestProfileControllerEndpoint(TestCase):
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
        # create activity log for the user 10 activiies
        for i in range(10):
            log_user_activity(
                user=self.users[0],
                description=faker.text(),
                activity_type=choice(["login", "profile"]),
            )

    def test_get_single_user_logs(self):
        """get the user's log"""
        response = self.client.get(
            reverse("activities", kwargs={"user_id": self.users[0].id})
        )
        self.assertEqual(response.status_code, 200)

    def test_get_user_activities_with_query_param(self):
        """get the user's log"""
        response = self.client.get(
            f'{reverse("activities", kwargs={"user_id": self.users[0].id})}?q=course'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data)

    # test get single user profile info
    def test_get_single_user_profile(self):
        """get single user profile info"""
        user_id = self.users[0].id
        response = self.client.get(reverse("get-profile", kwargs={"user_id": user_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["id"], str(user_id))

    def test_get_single_nont_existing_user_profile(self):
        """get single user profile info"""
        response = self.client.get(
            reverse("get-profile", kwargs={"user_id": uuid.uuid4()})
        )
        self.assertEqual(response.status_code, 404)

    # test update single user profile info
    def test_update_single_user_profile(self):
        """update single user profile info"""

        # made the user current statge to be ionboarding
        self.admin_user.current_stage = "onboarding"
        self.admin_user.save()

        data = {
            "full_name": faker.name(),
            "state": faker.city(),
            "country": faker.country(),
            "phone": faker.phone_number(),
            "address": faker.address(),
            "interests": ["Programming", "Reading"]
        }
        response = self.client.put(reverse("update-profile"), data=json.dumps(data), content_type="application/json" )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["full_name"], data["full_name"])
        # test the users status changed to completed after the update
        self.assertEqual(response.data["data"]["current_stage"], "completed")

    # test change password in dashboard
    def test_change_password(self):
        """change password in dashboard"""
        # change the admins password
        current_password = "old_password"

        self.admin_user.set_password(current_password)
        data = {"current_password": current_password, "new_password": faker.password()}
        response = self.client.put(reverse("change-password"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            self.client.login(
                email=self.admin_user.email, password=data["new_password"]
            )
        )

    # test change password in dashboard
    def test_change_password_with_incorrect_password(self):

        # change the admins password
        current_password = "old_password"
        self.admin_user.set_password(current_password)
        data = {"current_password": "sjfjnlfll", "new_password": faker.password()}
        response = self.client.put(reverse("change-password"), data=data)
        self.assertEqual(response.status_code, 400)
