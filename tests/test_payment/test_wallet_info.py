from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models.users import Wallet, TransactionHistory
from faker import Faker
from decimal import Decimal

faker = Faker()
User = get_user_model()


class TestWalletInfoAPI(TestCase):
    """Test suite for WalletInfo API endpoint."""

    def setUp(self):
        self.client = APIClient()

        # Create test user and wallet
        self.user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(),
            full_name=faker.name(),
            is_active=True,
        )
        self.wallet = Wallet.objects.get(user=self.user)

        # Endpoint URL
        self.url = reverse("wallet-info")

        # Authenticate client
        self.client.force_authenticate(user=self.user)

    def test_retrieve_wallet_info_success(self):
        """Test retrieving wallet information for authenticated user."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["id"], str(self.wallet.id))
        self.assertEqual(
            Decimal(response.json()["data"]["balance"]),
            self.wallet.balance
        )

    def test_wallet_not_found(self):
        """Test response when wallet is not found for the user."""
        # Delete the wallet
        self.wallet.delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["success"], False)
        self.assertEqual(response.json()["message"], "Wallet not found for the user.")
