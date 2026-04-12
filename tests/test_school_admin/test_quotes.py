import logging
import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from unittest.mock import patch
from core.models.courses import CoursePathWay, QouteToken, Qoutes

User = get_user_model()
faker = Faker()


class QuotesViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(),
            is_staff=True,
            role="main_admin"
        )
        self.normal_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(),
            role="user"
        )

        # Create test pathway
        self.pathway = CoursePathWay.objects.create(
            title=faker.name(),
            description=faker.text()
        )

        # Create a valid quote
        self.quote = Qoutes.objects.create(
            user=self.admin_user,
            quantity=100,
            quantity_left=100,
            course_pathway=self.pathway,
            class_name="primary_1",
            level="1",
            term=faker.word(),
            status=Qoutes.Status.APPROVED,
            term_start=timezone.now(),
            term_end=timezone.now() + timezone.timedelta(days=30)
        )
        
        
        # Create a pending quote
        self.pending_quote = Qoutes.objects.create(
            user=self.admin_user,
            quantity=100,
            quantity_left=100,
            course_pathway=self.pathway,
            class_name="Test Class",
            level="1",
            term=faker.word(),
            status=Qoutes.Status.PENDING,
            term_start=timezone.now(),
            term_end=timezone.now() + timezone.timedelta(days=30)
        )
        
        #  Create test users
        self.test_users = [
            User.objects.create_user(
                email=f'user{i}@example.com', 
                password='testpass123',
                role='student'
            ) for i in range(2)
        ]

        # Authenticate admin user
        self.client.force_authenticate(user=self.admin_user)

    def test_create_quote_success(self):
        """Test creating a new quote"""
        quote_data = {
            "term": faker.word(),
            "course_pathway": self.pathway.id,
            "class_name": "primary_2",
            "quantity": 50,
            "term_start": timezone.now(),
            "term_end": timezone.now() + timezone.timedelta(days=30),
            "status": Qoutes.Status.PENDING
        }
        response = self.client.post(reverse('quotes'), quote_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['quantity'], 50)
        
    
    def test_create_quote_invalid_data(self):
        """Test creating a new quote"""
        quote_data = {
            "term": faker.word(),
            "course_pathway": self.pathway.id,
            "class_name": "primary_3",
            "quantity": "sklks", #invalid data
            "term_start": timezone.now(),
            "term_end": timezone.now() + timezone.timedelta(days=30),
            "status": Qoutes.Status.PENDING
        }
        response = self.client.post(reverse('quotes'), quote_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_quote_success(self):
        """Test updating an existing quote"""
        update_data = {
            "class_name": "primary_3",
            "quantity": 75
        }
        response = self.client.put(
            reverse('quote-detail', kwargs={'pk': self.pending_quote.id}), 
            update_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['class_name'], "primary_3")


    def test_update_quote_approved(self):
        """Test updating an existing quote"""
        update_data = {
            "class_name": "Updated Test Class",
            "quantity": 75
        }
        response = self.client.put(
            reverse('quote-detail', kwargs={'pk': self.quote.id}), 
            update_data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)   
    
    
    def test_update_non_existing_quote(self):
        """Test updating an existing quote"""
        update_data = {
            "class_name": "Updated Test Class",
            "quantity": 75
        }
        response = self.client.put(
            reverse('quote-detail', kwargs={'pk': uuid.uuid4()}), 
            update_data
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_quote_success(self):
        """Test deleting a pending quote"""
        response = self.client.delete(
            reverse('quote-detail', kwargs={'pk': self.pending_quote.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertFalse(Qoutes.objects.filter(id=self.pending_quote.id).exists())
        
    
    def test_delete_approved_quote(self):
        """Test deleting a pending quote"""
        response = self.client.delete(
            reverse('quote-detail', kwargs={'pk': self.quote.id})
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_delete_non_existing_quote(self):
        """Test deleting a pending quote"""
        response = self.client.delete(
            reverse('quote-detail', kwargs={'pk': uuid.uuid4()})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_quotes(self):
        """Test listing quotes with various filters"""
        # Create additional quotes
        Qoutes.objects.create(
            user=self.admin_user,
            quantity=50,
            course_pathway=self.pathway,
            status=Qoutes.Status.APPROVED,
            term_start = timezone.now(),
            term_end = timezone.now() + timezone.timedelta(days=30),
        )

        # Test listing all quotes
        response = self.client.get(reverse('quotes'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertTrue(len(response.json()['data']) >= 2)

        # Test filtering by status
        response = self.client.get(
            reverse('quotes') + f'?status={Qoutes.Status.PENDING}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pending_quotes = [q for q in response.json()['data'] if q['status'] == Qoutes.Status.PENDING]
        self.assertTrue(len(pending_quotes) > 0)
        

    def test_retrieve_quote(self):
        """Test retrieving a single quote"""
        response = self.client.get(
            reverse('quote-detail', kwargs={'pk': self.quote.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['id'], str(self.quote.id))
        
    
    def test_retrieve_non_existing_quote(self):
        """Test retrieving a single non-existing quote"""
        response = self.client.get(
            reverse('quote-detail', kwargs={'pk': uuid.uuid4()})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('core.tasks.send_bulk_token_emails.delay')
    def test_send_tokens_invalid_data(self, mock_send_emails):
        """Test successful token creation and distribution"""
        data = {
            'user_idx': [str(user.id) for user in self.test_users],
            'quote_id': str(self.quote.id)
        }

        response = self.client.post(
            reverse('send-token'), 
            data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

        
    @patch('core.tasks.send_bulk_token_emails.delay')
    def test_send_tokens_success(self, mock_send_emails):
        """Test successful token creation and distribution"""
        data = {
            'user_ids': [str(user.id) for user in self.test_users],
            'quote_id': str(self.quote.id)
        }

        response = self.client.post(
            reverse('send-token'), 
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])

        # Verify tokens created
        tokens = QouteToken.objects.filter(qoute=self.quote)
        self.assertEqual(tokens.count(), 2)

        # Verify quote quantity updated
        updated_quote = Qoutes.objects.get(id=self.quote.id)
        self.assertEqual(updated_quote.quantity_left, 98)

        # Verify email task called
        mock_send_emails.assert_called_once()

    def test_send_tokens_quote_not_approved(self):
        """Test token creation for non-approved quote"""
        # Change quote status to pending
        self.quote.status = Qoutes.Status.PENDING
        self.quote.save()

        data = {
            'user_ids': [str(user.id) for user in self.test_users],
            'quote_id': str(self.quote.id)
        }

        response = self.client.post(
            reverse('send-token'), 
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_send_tokens_insufficient_quantity(self):
        """Test token creation with insufficient quote quantity"""
        # Reduce quote quantity
        self.quote.quantity_left = 1
        self.quote.save()

        data = {
            'user_ids': [str(user.id) for user in self.test_users],
            'quote_id': str(self.quote.id)
        }

        response = self.client.post(
            reverse('send-token'), 
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_send_tokens_non_existent_users(self):
        """Test token creation with non-existent users"""
        data = {
            'user_ids': [str(uuid.uuid4()), str(uuid.uuid4())],
            'quote_id': str(self.quote.id)
        }

        response = self.client.post(
            reverse('send-token'), 
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])