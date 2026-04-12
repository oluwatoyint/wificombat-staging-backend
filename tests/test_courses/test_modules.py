import logging
from uuid import uuid4
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from core.models.courses import CoursePathWay, Course, Module
from core.models.media import Media

logger = logging.getLogger(__name__)
User = get_user_model()
faker = Faker()


class TestModule(TestCase):
    """Test cases for Module ViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse("module-list")

        # Create test users
        self.admin_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
            is_staff=True,
            role="main_admin",
        )

        self.instructor = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
            role="tutor",
        )

        self.normal_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
            role="user",
        )

        # Create test media
        self.test_media = Media.objects.create(media_type="photo")

        # Create test pathway
        self.pathway = CoursePathWay.objects.create(
            title=faker.name(), description=faker.text(), cover_image=self.test_media
        )

        # Create test course
        self.course = Course.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
            level="Beginner",
            stage="Active",
            course_pathway=self.pathway,
            instructor=self.instructor,
        )

        # Create sample module
        self.module = Module.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
            course=self.course,
            learning_outcome=faker.text(),
            objectives=faker.text(),
            order=1
        )

        self.valid_module_data = {
            "title": faker.name(),
            "description": faker.text(),
            "cover_image": self.test_media.id,
            "course": self.course.id,
            "learning_outcome": faker.text(),
            "objectives": faker.text(),
            "order": 3,
        }

        # Set up authentication
        self.client.force_authenticate(user=self.admin_user)

    def test_list_modules(self):
        """Test getting list of modules"""
        # url = reverse("get_modules", kwargs={"course_id": self.course.id})
        url = reverse('module-get-all')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertIn("data", response.json())
        self.assertEqual(len(response.json()["data"]), 1)

        # Verify the returned data structure
        module_data = response.json()["data"][0]
        self.assertIn("title", module_data)
        self.assertIn("description", module_data)
        self.assertIn("learning_outcome", module_data)
        self.assertIn("objectives", module_data)
        self.assertIn("course", module_data)
        

    def test_list_modules_with_params(self):
        """Test getting list of modules"""
        # url = reverse("get_modules", kwargs={"course_id": self.course.id})
        url = f"{reverse('module-get-all')}?course_id={self.course.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertIn("data", response.json())
        self.assertEqual(len(response.json()["data"]), 1)

        # Verify the returned data structure
        module_data = response.json()["data"][0]
        self.assertIn("title", module_data)
        self.assertIn("description", module_data)
        self.assertIn("learning_outcome", module_data)
        self.assertIn("objectives", module_data)
        self.assertIn("course", module_data)

    def test_retrieve_module(self):
        """Test retrieving a specific module"""
        url = reverse("module-detail", kwargs={"pk": self.module.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["data"]["title"], self.module.title)
        self.assertEqual(
            response.json()["data"]["learning_outcome"], self.module.learning_outcome
        )
        self.assertEqual(response.json()["data"]["objectives"], self.module.objectives)

    def test_create_module_with_all_fields(self):
        """Test creating a new module with all available fields"""
        response = self.client.post(self.list_url, self.valid_module_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["success"])

        # Verify all fields were saved correctly
        module = Module.objects.get(title=self.valid_module_data["title"])
        self.assertEqual(module.description, self.valid_module_data["description"])
        self.assertEqual(
            module.learning_outcome, self.valid_module_data["learning_outcome"]
        )
        self.assertEqual(module.objectives, self.valid_module_data["objectives"])

    def test_create_module_without_optional_fields(self):
        """Test creating a module without optional fields"""
        data = {
            "title": faker.name(),
            "description": faker.text(),
            "course": self.course.id,
            "learning_outcome": faker.text(),
            "objectives": faker.text(),
            "order": 4
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["success"])

    def test_update_module_full(self):
        """Test updating all fields of an existing module"""
        url = reverse("module-detail", kwargs={"pk": self.module.id})
        updated_data = {
            "title": "Updated Module",
            "description": "Updated description",
            "cover_image": self.test_media.id,
            "course": self.course.id,
            "learning_outcome": "Updated learning outcome",
            "objectives": "Updated objectives",
        }
        response = self.client.put(url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])

        self.module.refresh_from_db()
        self.assertEqual(self.module.title, "Updated Module")
        self.assertEqual(self.module.learning_outcome, "Updated learning outcome")
        self.assertEqual(self.module.objectives, "Updated objectives")
        
    
    def test_update_non_existing_module(self):
        """Test updating not existing module"""
        url = reverse("module-detail", kwargs={"pk": "123e4567-e89b-12d3-a456-426614174000"})
        updated_data = {
            "title": "Updated Module",
            "description": "Updated description",
            "cover_image": self.test_media.id,
            "course": self.course.id,
            "learning_outcome": "Updated learning outcome",
            "objectives": "Updated objectives",
        }
        response = self.client.put(url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_module(self):
        """Test deleting a module"""
        url = reverse("module-detail", kwargs={"pk": self.module.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Module.objects.filter(id=self.module.id).exists())
        
    
    def test_delete_non_existing_module(self):
        """Test deleting non existing module"""
        url = reverse("module-detail", kwargs={"pk": "123e4567-e89b-12d3-a456-426614174000"})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_create_module_with_invalid_course(self):
        """Test creating a module with invalid course ID"""
        invalid_data = self.valid_module_data.copy()
        invalid_data["course"] = uuid4()
        response = self.client.post(self.list_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])

    def test_create_module_with_invalid_media(self):
        """Test creating a module with invalid media ID"""
        invalid_data = self.valid_module_data.copy()
        invalid_data["cover_image"] = 99999
        response = self.client.post(self.list_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])

    def test_unauthorized_access(self):
        """Test unauthorized access to admin-only actions"""
        self.client.force_authenticate(user=self.normal_user)

        # Try to create
        response = self.client.post(self.list_url, self.valid_module_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try to update
        url = reverse("module-detail", kwargs={"pk": self.module.id})
        response = self.client.put(url, {"title": "Updated"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try to delete
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_nonexistent_module(self):
        """Test retrieving a non-existent module"""
        url = reverse("module-detail", kwargs={"pk": uuid4()})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()["success"])

    def test_create_module_missing_required_fields(self):
        """Test creating a module with missing required fields"""
        invalid_data = {
            "title": faker.name(),  # Missing other required fields
        }
        response = self.client.post(self.list_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])
