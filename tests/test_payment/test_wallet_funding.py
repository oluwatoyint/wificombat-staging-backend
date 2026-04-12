import logging
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from faker import Faker
from core.models.users import Wallet

logger = logging.getLogger(__name__)
User = get_user_model()
faker = Faker()

class TestWalletFunding(TestCase):
    """Test the wallet funding endpoint"""

    def setUp(self):
        self.client = APIClient()
        # Create test user
        self.user = User.objects.create_user(
            password=faker.password(),
            email=faker.email(),
            is_active=True,
            full_name=faker.name(),
        )
        # Create wallet for the user
        self.wallet = Wallet.objects.get(user=self.user)
        self.client.force_authenticate(user=self.user)
        
        # Test data
        self.valid_payload = {
            "amount": 5000,
            "success_url": "https://www.google.com"
        }
        self.url = reverse("wallet-funding")

    @patch('api.payment_providers.payment_provider_factory.PaymentProviderFactory.create_provider')
    def test_successful_wallet_funding(self, mock_provider):
        """Test successful wallet funding initialization"""
        # Mock the payment provider response
        mock_payment = MagicMock()
        mock_payment.initialize_payment.return_value = {
            "success": True,
            "message": "Payment initialized successfully",
            "data": {
                "status": "success",
                "message": "Hosted Link",
                "data": {
                    "link": "https://checkout-v2.dev-flutterwave.com/v3/hosted/pay/fe4635df164841f17c1c"
                }
            }
        }
        mock_payment.generate_transaction_reference.return_value = "test_reference"
        mock_provider.return_value = mock_payment

        response = self.client.post(self.url, self.valid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Payment initialized successfully")


    def test_unauthorized_access(self):
        """Test that authentication is required"""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        

    def test_amount_below_minimum(self):
        """Test validation for minimum amount requirement"""
        payload = self.valid_payload.copy()
        payload["amount"] = 500
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Amount must be at least 1000")


    def test_amount_exceeding_maximum(self):
        """Test validation for exceeding maximum wallet balance"""
        payload = self.valid_payload.copy()
        payload["amount"] = 200001
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This deposit would exceed the maximum wallet balance", response.data["message"])

    def test_wallet_not_found(self):
        """Test scenario where user wallet doesn't exist"""
        # Delete the wallet
        self.wallet.delete()
        
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_data(self):
        """Test validation for invalid data"""
        invalid_payload = {
            "amount": "invalid",
            "success_url": "not-a-url"
        }
        
        response = self.client.post(self.url, invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)