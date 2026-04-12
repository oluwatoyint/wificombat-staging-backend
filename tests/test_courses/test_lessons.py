import logging
from uuid import uuid4
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from core.models.courses import Lesson, Module, Course, CoursePathWay
from core.models.media import Media

logger = logging.getLogger(__name__)
User = get_user_model()
faker = Faker()


class TestLesson(TestCase):
    """Test cases for Lesson ViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse("lesson-list")

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
        self.test_media = Media.objects.create(media_type="video")

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

        # Create test module
        self.module = Module.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
            learning_outcome=faker.text(),
            objectives=faker.text(),
            course=self.course,
        )

        # Create sample lesson
        self.lesson = Lesson.objects.create(
            title=faker.name(),
            description=faker.text(),
            video_embed=faker.text(10),
            module=self.module,
            note=faker.text(20),
            order=1,
        )

        self.valid_lesson_data = {
            "title": faker.name(),
            "description": faker.text(),
            "video_embed": faker.text(10),
            "module": self.module.id,
            "note": faker.text(20),
            "transcript": faker.text(30),
            "order": 2,
        }

        # Set up authentication
        self.client.force_authenticate(user=self.admin_user)

    def test_list_lessons(self):
        """Test getting list of lessons"""
        # url = reverse("get_lessons", kwargs={"module_id": self.module.id})
        url = f"{reverse('lesson-get-all')}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertIn("data", response.json())
        self.assertEqual(len(response.json()["data"]), 1)

    def test_get_module_lessons(self):
        """Test getting list of module lessons"""
        # url = reverse("get_lessons", kwargs={"module_id": self.module.id})
        url = f"{reverse('lesson-get-all')}?module_id={self.module.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertIn("data", response.json())

    def test_retrieve_lesson(self):
        """Test retrieving a specific lesson"""
        url = reverse("lesson-detail", kwargs={"pk": self.lesson.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["data"]["title"], self.lesson.title)

    def test_create_lesson_with_all_fields(self):
        """Test creating a new lesson with all available fields"""
        # Authenticate the test client
        self.client.force_authenticate(user=self.instructor)
        
        response = self.client.post(self.list_url, self.valid_lesson_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["success"])

        # Verify all fields were saved correctly
        lesson = Lesson.objects.get(title=self.valid_lesson_data["title"])
        self.assertEqual(lesson.description, self.valid_lesson_data["description"])

    def test_update_lesson_full(self):
        """Test updating all fields of an existing lesson"""
        url = reverse("lesson-detail", kwargs={"pk": self.lesson.id})
        updated_data = {
            "title": "Updated Lesson",
            "description": "Updated description",
            "video": faker.text(10),
            "module": self.module.id,
        }
        response = self.client.put(url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])

        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, "Updated Lesson")
        
    
    def test_update_lesson_invalid_data(self):
        """Test updating lesson with invalid data"""
        url = reverse("lesson-detail", kwargs={"pk": self.lesson.id})
        updated_data = {
            "title": faker.word(),
            "description": "Updated description",
            "vide_o": faker.text(10),
            "module": 999,
            "order": 1,
        }
        response = self.client.put(url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_update_non_existing_lesson_full(self):
        """Test updating all fields of a non existing lesson"""
        url = reverse("lesson-detail", kwargs={"pk": "123e4567-e89b-12d3-a456-426614174000"})
        updated_data = {
            "title": "Updated Lesson",
            "description": "Updated description",
            "video": faker.text(10),
            "module": self.module.id,
        }
        response = self.client.put(url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_lesson(self):
        """Test deleting a lesson"""
        url = reverse("lesson-detail", kwargs={"pk": self.lesson.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Lesson.objects.filter(id=self.lesson.id).exists())
        
        
    def test_delete_non_existing_lesson(self):
        """Test deleting a non existing lesson"""
        url = reverse("lesson-detail", kwargs={"pk": "123e4567-e89b-12d3-a456-426614174000"})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_create_lesson_with_invalid_module(self):
        """Test creating a lesson with invalid module ID"""
        invalid_data = self.valid_lesson_data.copy()
        invalid_data["module"] = uuid4()
        response = self.client.post(self.list_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])

    def test_unauthorized_access(self):
        """Test unauthorized access to admin-only actions"""
        self.client.force_authenticate(user=self.normal_user)

        # Try to create
        response = self.client.post(self.list_url, self.valid_lesson_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try to update
        url = reverse("lesson-detail", kwargs={"pk": self.lesson.id})
        response = self.client.put(url, {"title": "Updated"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try to delete
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_nonexistent_lesson(self):
        """Test retrieving a non-existent lesson"""
        url = reverse("lesson-detail", kwargs={"pk": uuid4()})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()["success"])

    def test_create_lesson_missing_required_fields(self):
        """Test creating a lesson with missing required fields"""
        invalid_data = {
            "title": faker.name(),  # Missing other required fields
        }
        response = self.client.post(self.list_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])
