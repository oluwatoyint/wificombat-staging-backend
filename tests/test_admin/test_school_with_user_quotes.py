import logging
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from core.models import School, User
from core.models.courses import CoursePathWay, Qoutes
from core.models.media import Media


logger = logging.getLogger(__name__)
faker = Faker()

class TestSchoolsWithUserQuotesView(TestCase):
    """Test the SchoolsWithUserQuotesView functionality"""

    def setUp(self):
        self.client = APIClient()

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            password=faker.password(),
            email=faker.email(),
            is_staff=True,
            is_superuser=True,
            is_active=True,
            role="main_admin",
            full_name=faker.name(),
        )
        self.client.force_authenticate(user=self.admin_user)

        # Create schools
        self.schools = [
            School.objects.create(name=faker.company()) for _ in range(5)
        ]
        
        
        # Create test media for cover image
        self.test_media = Media.objects.create(media_type="photo")

        # Create test pathway
        self.pathway = CoursePathWay.objects.create(
            title=faker.name(), description=faker.text(), cover_image=self.test_media
        )

        # Create users associated with schools
        self.users = [
            User.objects.create_user(
                email=faker.email(),
                password=faker.password(),
                full_name=faker.name(),
                school=school,
                role="student"
            )
            for school in self.schools
        ]

        # Create quotes for some users
        self.quotes = [
            Qoutes.objects.create(
                user=user,
                status="pending",
                term="term1",
                is_active=True,
                is_paused=False,
                course_pathway=self.pathway,
                term_start=timezone.now(),
                term_end=timezone.now() + timezone.timedelta(days=30)
            )
            for user in self.users
        ]

    def test_get_requested_routes(self):
        """Test fetching schools with requested quotes"""
        url = reverse("get_requested_routes")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertIn("data", response_data)
        self.assertTrue(len(response_data["data"]) > 0) 

    def test_get_requested_routes_with_query(self):
        """Test fetching schools with a specific query filter"""
        school_name = self.schools[0].name
        url = reverse("get_requested_routes") + f"?q={school_name}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(
            any(school["name"].lower() == school_name.lower() for school in response_data["data"])
        )

    def test_get_single_school_quotes(self):
        """Test retrieving quotes for a specific school"""
        school_id = self.schools[0].id
        url = reverse("get_single_school_qoutes", kwargs={"id": school_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertIn("data", response_data)
        self.assertTrue(len(response_data["data"]) > 0)
        self.assertTrue(
            (quote["id"] == school_id for quote in response_data["data"])
        )

    def test_get_single_school_quotes_with_filters(self):
        """Test retrieving quotes for a specific school with filters"""
        school_id = self.schools[0].id
        url = (
            reverse("get_single_school_qoutes", kwargs={"id": school_id})
            + "?term=term1&status=pending&is_active=true"
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertIn("data", response_data)
        self.assertTrue(len(response_data["data"]) > 0)
        self.assertTrue(
            all(
                quote["term"] == "term1" and quote["status"] == "pending"
                for quote in response_data["data"]
            )
        )

    def test_update_quote_request(self):
        """Test updating a quote request"""
        quote_id = self.quotes[0].id
        url = reverse("get_single_school_qoutes", kwargs={"id": quote_id})
        data = {"status": "approved", "is_active": False}

        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Quote updated successfully")


    def test_update_quote_request_not_found(self):
        """Test updating a non-existing quote request"""
        invalid_id = "123e4567-e89b-12d3-a456-426614174000"
        url = reverse("get_single_school_qoutes", kwargs={"id": invalid_id})
        data = {"status": "approved"}

        response = self.client.put(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["message"], "Quote not found")
