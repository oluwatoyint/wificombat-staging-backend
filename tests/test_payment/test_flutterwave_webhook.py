import json
import logging
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from faker import Faker
from core.models.users import Wallet, TransactionHistory

logger = logging.getLogger(__name__)
User = get_user_model()
faker = Faker()

class TestFlutterwaveWebhook(TestCase):
    """Test the Flutterwave webhook endpoint"""

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
        self.initial_balance = Decimal('1000.00')
        self.wallet.balance = self.initial_balance
        self.wallet.save()

        # Test reference
        self.tx_ref = "TEST_TX_REF_123"
        
        # Create pending transaction
        self.transaction = TransactionHistory.objects.create(
            user=self.user,
            wallet=self.wallet,
            reference=self.tx_ref,
            amount=Decimal('5000.00'),
            transaction_type='deposit',
            status='pending'
        )

        # Test data
        self.valid_payload = {
            "event": "charge.completed",
            "data": {
                "tx_ref": self.tx_ref,
                "amount": 5000.00,
            },
            "meta_data": {
                "wallet_id": str(self.wallet.id)
            }
        }
        
        self.url = reverse("flutterwave-webhook")
        
        # Mock webhook signature
        self.valid_signature = "valid-signature-hash"
        settings.FLUTTERWAVE_SECRET_HASH = self.valid_signature

    def test_successful_webhook_processing(self):
        """Test successful processing of webhook with valid signature and data"""
        headers = {"HTTP_VERIF_HASH": self.valid_signature}
        
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            **headers
        )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh objects from database
        self.wallet.refresh_from_db()
        self.transaction.refresh_from_db()
        
        # Verify wallet balance updated
        self.assertEqual(self.wallet.balance, self.initial_balance + Decimal('5000.00'))
        
        # Verify transaction status updated
        self.assertEqual(self.transaction.status, 'successful')

    def test_invalid_signature(self):
        """Test webhook with invalid signature"""
        headers = {"verif-hash": "invalid-signature"}
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid Signature")

    def test_invalid_event_type(self):
        """Test webhook with invalid event type"""
        payload = self.valid_payload.copy()
        payload["event"] = "charge.failed"
        
        headers = {"HTTP_VERIF_HASH": self.valid_signature}
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Event type not handled")

    def test_amount_mismatch(self):
        """Test webhook with amount mismatch"""
        payload = self.valid_payload.copy()
        payload["data"]["amount"] = 6000.00
        
        headers = {"HTTP_VERIF_HASH": self.valid_signature}
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            **headers
        )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Amount mismatch")
        
        # Verify transaction marked as failed
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, 'failed')

    def test_invalid_wallet_id(self):
        """Test webhook with invalid wallet ID"""
        payload = self.valid_payload.copy()
        payload["meta_data"]["wallet_id"] = "12345678-1234-5678-1234-567812345678"
        
        headers = {"HTTP_VERIF_HASH": self.valid_signature}
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Wallet not found")

    def test_missing_pending_transaction(self):
        """Test webhook when no pending transaction exists"""
        # Delete existing transaction
        self.transaction.delete()
        
        headers = {"HTTP_VERIF_HASH": self.valid_signature}
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            **headers
        )
        
        # Verify successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify new transaction created
        new_transaction = TransactionHistory.objects.get(reference=self.tx_ref)
        self.assertEqual(new_transaction.status, 'successful')
        self.assertEqual(new_transaction.amount, Decimal('5000.00'))
        
        # Verify wallet balance updated
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, self.initial_balance + Decimal('5000.00'))

    def test_missing_metadata(self):
        """Test webhook with missing metadata"""
        payload = self.valid_payload.copy()
        del payload["meta_data"]
        
        headers = {"HTTP_VERIF_HASH": self.valid_signature}
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid metadata")