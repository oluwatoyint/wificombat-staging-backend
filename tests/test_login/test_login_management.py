from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models.users import Otp
from faker import Faker
from datetime import timedelta
from django.utils.timezone import now

User = get_user_model()
faker = Faker()


class TestUserLogin(TestCase):
    """Test cases for Login, Password Reset Request, and Set New Password"""

    def setUp(self):
        self.client = APIClient()
        self.user_email = faker.email()
        self.user_password = "TestPass123"
        self.user = User.objects.create_user(
            email=self.user_email,
            password=self.user_password,
            is_active=True,
        )
        self.login_url = reverse("login")
        self.admin_login_url = reverse("admin-login")
        self.request_password_reset_url = reverse("request-password-reset")
        self.set_new_password_url = reverse("set-new-password")
        self.otp = Otp.objects.create(user=self.user)

    def test_successful_login(self):
        """Test successful user login"""
        data = {"email": self.user_email, "password": self.user_password}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {"email": self.user_email, "password": "wrongpassword"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid email or password.")

    def test_successful_password_reset_request(self):
        """Test requesting a password reset for a valid email"""
        data = {"email": self.user_email}
        response = self.client.post(self.request_password_reset_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Password reset token has been sent to your email"
        )

    def test_password_reset_request_for_nonexistent_email(self):
        """Test password reset request for an email not in the system"""
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(self.request_password_reset_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "The email address does not exist.")

    def test_successful_set_new_password(self):
        """Test setting a new password with valid token and email"""
        token = self.otp.token
        data = {
            "email": self.user_email,
            "token": token,
            "password": "new_secure_password",
        }
        response = self.client.post(self.set_new_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password reset successful.")

        # Verify the password is updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new_secure_password"))

    def test_set_new_password_with_invalid_token(self):
        """Test setting a new password with an invalid token"""
        data = {
            "email": self.user_email,
            "token": "000.",
            "password": "new_secure_password",
        }
        response = self.client.post(self.set_new_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid token.")

    def test_set_new_password_with_expired_token(self):
        """Test setting a new password with an expired token"""
        self.otp.expiration = now() - timedelta(days=1)
        self.otp.save()

        data = {
            "email": self.user_email,
            "token": self.otp.token,
            "password": "new_secure_password",
        }
        response = self.client.post(self.set_new_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Token has expired.")

    def test_set_new_password_with_nonexistent_email(self):
        """Test setting a new password for an email not in the system"""
        data = {
            "email": "nonexistent@example.com",
            "token": self.otp.token,
            "password": "new_secure_password",
        }
        response = self.client.post(self.set_new_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "No user found with this email.")


    # test admin user
    def test_admin_login_with_valid_staff_credentials(self):
        """Test login with valid staff credentials."""
        
        self.staff_user = User.objects.create_user(
            email=faker.email(),
            password=self.user_password,
            role = "main_admin",
            is_active=True,
        )
        self.staff_user.is_staff = True
        self.staff_user.save()
        
        self.staff_user.refresh_from_db()
        print(f"is_staff: {self.staff_user.is_staff}")  # Should be True
        print(f"is_active: {self.staff_user.is_active}")
        
        data = {"email": self.staff_user.email, "password": self.user_password}
        response = self.client.post(self.admin_login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Login successful.")

    
    def test_admin_login_with_non_staff_user(self):
        """Test login attempt with non-staff user credentials."""
        
        self.user = User.objects.create_user(
            email="user@gmail.com",
            password=self.user_password,
            is_active=True,
        )
        
        data = {"email": self.user.email, "password": self.user_password}
        response = self.client.post(self.admin_login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data.get("message"),
            "Access denied. Only staff members can log in."
        )