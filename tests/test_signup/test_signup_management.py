import logging
import random
from django.test import TestCase
from datetime import timedelta
from django.utils.timezone import now
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from core.models.users import Otp, School, Wallet


logger = logging.getLogger(__name__)

User = get_user_model()
faker = Faker()


class TestUserRegistration(TestCase):
    """Test cases for UserRegistration and VerifyToken API views"""

    def setUp(self):
        self.client = APIClient()
        self.registration_url = reverse("register")
        self.verify_token_url = reverse("verify-token")
        self.resend_activation_url = reverse("resend_activation_token")
        self.valid_registration_data = {
            "email": faker.email(),
            "password": faker.password(length=10),
            "role": random.choice(["user", "tutor", "main_admin"]),
        }
        self.inactive_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=False,
        )

        self.active_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
        )
        self.valid_token = Otp.objects.create(user=self.inactive_user).token
        self.invalid_token = "000."

        # create dummy school 5 schools
        for i in range(5):
            School.objects.create(name=f"School {i+1}")

    # test get schools
    def test_get_schools(self):
        """Test successful get schools"""
        response = self.client.get(reverse("get-schools"))
        print(response.json(), "sbsdvsdv")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_successful_registration(self):
        """Test successful user registration"""
        response = self.client.post(self.registration_url, self.valid_registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify user creation
        user = User.objects.filter(email=self.valid_registration_data["email"]).first()
        self.assertIsNotNone(user)
        self.assertFalse(user.is_active)

        # Verify OTP generation
        otp = Otp.objects.filter(user=user).first()
        self.assertIsNotNone(otp)

    def test_successful_registration_admin(self):
        """Test successful user registration school admin"""

        data = {
            "email": self.valid_registration_data["email"],
            "password": self.valid_registration_data["password"],
            "school_type": "private",
            "school_website": "http://google.com",
            "school_phone": "1234567890",
            "role": "school_admin",
            "country": "USA",
            "current_class": "9th",
            "name": faker.name(),
        }
        response = self.client.post(self.registration_url, data=data)
        print(response.json(), "vbsdvdsmvbjdsvbds")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify user creation
        user = User.objects.filter(email=self.valid_registration_data["email"]).first()
        self.assertIsNotNone(user)
        self.assertFalse(user.is_active)

        # Verify OTP generation
        otp = Otp.objects.filter(user=user).first()
        self.assertIsNotNone(otp)

    def test_registration_with_invalid_email(self):
        """Test registration with an invalid email format"""
        invalid_data = self.valid_registration_data.copy()
        invalid_data["email"] = "invalid-email"
        response = self.client.post(self.registration_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_with_existing_email(self):
        """Test registration with an email that already exists"""
        User.objects.create_user(
            email=self.valid_registration_data["email"],
            password=self.valid_registration_data["password"],
        )
        response = self.client.post(self.registration_url, self.valid_registration_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_token_with_valid_token(self):
        """Test token verification with a valid token"""
        user_email = self.inactive_user.email
        data = {"email": user_email, "token": self.valid_token}
        response = self.client.post(self.verify_token_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check user activation
        self.inactive_user.refresh_from_db()
        self.assertTrue(self.inactive_user.is_active)
        self.assertEqual(
            response.data["message"], "Your account has been successfully activated."
        )

    def test_verify_token_with_invalid_token(self):
        """Test token verification with an invalid token"""
        data = {"email": self.inactive_user.email, "token": self.invalid_token}
        response = self.client.post(self.verify_token_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid token.")

    def test_verify_token_with_expired_token(self):
        """Test token verification with an expired token"""

        otp = Otp.objects.get(user=self.inactive_user)
        otp.expiration = now() - timedelta(days=1)  # Expired token
        otp.save()

        data = {"email": self.inactive_user.email, "token": otp.token}
        response = self.client.post(self.verify_token_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["message"], "The token has expired. Please request a new one."
        )

    def test_resend_activation_success(self):
        """Test successful resend of activation token for an inactive user"""
        data = {"email": self.inactive_user.email}
        response = self.client.post(self.resend_activation_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            "A new activation token has been sent to your email.",
        )

        # Verify that an OTP was created or refreshed
        otp = Otp.objects.filter(user=self.inactive_user).first()
        self.assertIsNotNone(otp)

    def test_resend_activation_user_not_found(self):
        """Test resend activation when the email does not belong to any user"""
        data = {"email": faker.email()}  # Use a random email not in the database
        response = self.client.post(self.resend_activation_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["message"],
            "No user found with this email.",
        )

    def test_resend_activation_user_already_active(self):
        """Test resend activation when the user is already active"""
        data = {"email": self.active_user.email}
        response = self.client.post(self.resend_activation_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["message"],
            "User is already active.",
        )

    def test_successful_registration_resgistraion_and_wallet(self):
        """Test successful user registration school admin"""
        email = self.valid_registration_data["email"]
        data = {
            "email": email,
            "password": self.valid_registration_data["password"],
            "role": "user",
            "country": "USA",
            "current_class": "9th",
            "name": faker.name(),
        }
        response = self.client.post(self.registration_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # test wallet was create for tis user wotj a defult 0.0 balance
        wallet_created = Wallet.objects.filter(user__email=email).exists()
        self.assertTrue(wallet_created)
