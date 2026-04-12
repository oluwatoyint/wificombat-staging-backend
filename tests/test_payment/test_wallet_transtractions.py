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

class TestWalletTransactionAPI(TestCase):
    """Test suite for WalletTransaction API endpoint."""

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

        # Create transaction history
        self.transaction_1 = TransactionHistory.objects.create(
            user=self.user,
            wallet=self.wallet,
            reference="TXN1",
            amount=Decimal("100.00"),
            transaction_type="deposit",
            status="successful",
        )
        self.transaction_2 = TransactionHistory.objects.create(
            user=self.user,
            wallet=self.wallet,
            reference="TXN2",
            amount=Decimal("50.00"),
            transaction_type="withdrawal",
            status="successful",
        )

        # Endpoint URL
        self.url = reverse("wallet-transactions")  # Replace with the actual name of your WalletTransaction endpoint

        # Authenticate client
        self.client.force_authenticate(user=self.user)

    def test_retrieve_all_transactions(self):
        """Test retrieving all transactions for the user."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]), 2)

    def test_filter_transactions_by_type(self):
        """Test filtering transactions by type."""
        response = self.client.get(self.url, {"transaction_type": "deposit"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]), 1)
        self.assertEqual(response.json()["data"][0]["transaction_type"], "deposit")

    def test_pagination(self):
        """Test paginated transaction response."""
        # Create additional transactions for testing pagination
        for i in range(1, 11):
            TransactionHistory.objects.create(
                user=self.user,
                wallet=self.wallet,
                reference=f"TXN_{i}",
                amount=Decimal("10.00"),
                transaction_type="deposit",
                status="successful",
            )

        # Set pagination size to 5 (adjust according to your pagination settings)
        response = self.client.get(self.url, {"page_size": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.json())
        self.assertEqual(len(response.json()["data"]), 5)
