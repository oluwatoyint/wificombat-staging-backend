import logging
from uuid import uuid4
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from core.models.courses import CoursePathWay, Course
from core.models.media import Media

logger = logging.getLogger(__name__)
User = get_user_model()
faker = Faker()


class TestCoursePathWay(TestCase):
    """Test cases for CoursePathWay ViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse("course-pathway-list")

        # Create test users
        self.admin_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
            is_staff=True,
            role="main_admin",
        )

        self.normal_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
            role="user",
        )

        # Create test media for cover image
        self.test_media = Media.objects.create(media_type="photo")

        # Create sample pathway with all fields from BaseContent
        self.pathway = CoursePathWay.objects.create(
            title=faker.name(), description=faker.text(), cover_image=self.test_media
        )

        self.valid_pathway_data = {
            "title": faker.name(),
            "description": faker.text(),
            "cover_image": self.test_media.id,
        }

        # Set up authentication
        self.client.force_authenticate(user=self.admin_user)

    def test_list_pathways(self):
        """Test getting list of course pathways"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.json())
        self.assertEqual(len(response.json()["data"]), 1)

        # Verify the returned data structure
        pathway_data = response.json()["data"][0]
        self.assertIn("title", pathway_data)
        self.assertIn("description", pathway_data)
        self.assertIn("cover_image", pathway_data)

    def test_retrieve_pathway(self):
        """Test retrieving a specific course pathway"""
        url = reverse("course-pathway-detail", kwargs={"pk": self.pathway.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["title"], self.pathway.title)
        self.assertEqual(
            response.json()["data"]["description"], self.pathway.description
        )
        self.assertIsNotNone(response.json()["data"]["cover_image"])

    def test_create_pathway_with_all_fields(self):
        """Test creating a new course pathway with all available fields"""
        response = self.client.post(self.list_url, self.valid_pathway_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify all fields were saved correctly
        pathway = CoursePathWay.objects.get(title=self.valid_pathway_data["title"])
        self.assertEqual(pathway.description, self.valid_pathway_data["description"])
        self.assertEqual(pathway.cover_image.id, self.valid_pathway_data["cover_image"])

    def test_create_pathway_without_optional_fields(self):
        """Test creating a pathway without optional fields"""
        data = {
            "title": faker.name(),
            "description": faker.text(),
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_pathway_full(self):
        """Test updating all fields of an existing course pathway"""
        url = reverse("course-pathway-detail", kwargs={"pk": self.pathway.id})
        updated_data = {
            "title": "Updated Pathway",
            "description": "Updated description",
            "cover_image": self.test_media.id,
        }
        response = self.client.put(url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.pathway.refresh_from_db()
        self.assertEqual(self.pathway.title, "Updated Pathway")
        self.assertEqual(self.pathway.description, "Updated description")
        self.assertEqual(self.pathway.cover_image.id, self.test_media.id)

    def test_partial_update_pathway(self):
        """Test partially updating a course pathway"""
        url = reverse("course-pathway-detail", kwargs={"pk": self.pathway.id})
        original_description = self.pathway.description

        patch_data = {"title": "Partially Updated Pathway"}
        response = self.client.put(url, patch_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.pathway.refresh_from_db()
        self.assertEqual(self.pathway.title, "Partially Updated Pathway")
        self.assertEqual(
            self.pathway.description, original_description
        )
        
    
    def test_partial_update_pathway_that_does_not_exist(self):
        """Test partially updating a course pathway"""
        url = reverse("course-pathway-detail", kwargs={"pk": "123e4567-e89b-12d3-a456-426614174000"})

        patch_data = {"title": "Partially Updated Pathway"}
        response = self.client.put(url, patch_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_pathway(self):
        """Test deleting a course pathway"""
        url = reverse("course-pathway-detail", kwargs={"pk": self.pathway.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CoursePathWay.objects.filter(id=self.pathway.id).exists())
        
    
    def test_delete_pathway_that_does_not_exist(self):
        """Test deleting a course pathway that does not exist"""
        url = reverse("course-pathway-detail", kwargs={"pk": "123e4567-e89b-12d3-a456-426614174000"})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_pathway_with_invalid_media(self):
        """Test creating a pathway with invalid media ID"""
        invalid_data = self.valid_pathway_data.copy()
        invalid_data["cover_image"] = 99999  # Non-existent media ID
        response = self.client.post(self.list_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_access(self):
        """Test unauthorized access to admin-only actions"""
        self.client.force_authenticate(user=self.normal_user)

        # Try to create
        response = self.client.post(self.list_url, self.valid_pathway_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try to update
        url = reverse("course-pathway-detail", kwargs={"pk": self.pathway.id})
        response = self.client.put(url, {"title": "Updated"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try to delete
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verify read access is still allowed
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_nonexistent_pathway(self):
        """Test retrieving a non-existent pathway"""
        url = reverse("course-pathway-detail", kwargs={"pk": str(uuid4())})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
