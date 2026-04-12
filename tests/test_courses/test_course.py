import logging
from uuid import uuid4
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from decimal import Decimal
from django.contrib.auth import get_user_model
from core.models.courses import CoursePathWay, Course
from core.models.media import Media

logger = logging.getLogger(__name__)
User = get_user_model()
faker = Faker()


class TestCourse(TestCase):
    """Test cases for Course ViewSet"""

    def setUp(self):
        self.client = APIClient()

        # Define base URL for custom actions
        self.base_url = "/courses"  # Adjust based on your URL configuration

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

        # Create test media for cover image
        self.test_media = Media.objects.create(media_type="photo")

        # Create test pathway
        self.pathway = CoursePathWay.objects.create(
            title=faker.name(), description=faker.text(), cover_image=self.test_media
        )

        # Create sample course with all fields
        self.course = Course.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
            level="Beginner",
            stage="Active",
            course_pathway=self.pathway,
            amount=Decimal("99.99"),
            instructor=self.instructor,
        )

        self.valid_course_data = {
            "title": faker.name(),
            "description": faker.text(),
            "cover_image": self.test_media.id,
            "level": "1",
            "stage": "beginner",
            "course_pathway": self.pathway.id,
            "amount": "149.99",
            "instructor": self.instructor.id,
        }

        # Set up authentication
        self.client.force_authenticate(user=self.admin_user)

    def test_get_all_courses(self):
        """Test getting list of courses"""
        response = self.client.get(f"{self.base_url}/get_all/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertIn("data", response.json())
        self.assertEqual(len(response.json()["data"]), 1)

        # Verify the returned data structure
        course_data = response.json()["data"][0]
        self.assertIn("title", course_data)
        self.assertIn("description", course_data)
        self.assertIn("level", course_data)
        self.assertIn("stage", course_data)
        self.assertIn("amount", course_data)
        
    def test_get_courses_by_pathway(self):
        """Test getting courses filtered by pathway ID"""
        # Test filtering by original pathway
        response = self.client.get(f"{self.base_url}/get_all/?pathway_id={self.pathway.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertIn("data", response.json())
        
        # Should only return courses from the specified pathway
        course_data = response.json()["data"][0]
        self.assertIn("title", course_data)
        self.assertIn("description", course_data)
        self.assertEqual(course_data["course_pathway"]['id'], str(self.pathway.id))
        
    
    def test_get_courses_by_tutor(self):
        """Test getting courses filtered by tutor"""
        # Test filtering by original pathway
        response = self.client.get(f"{self.base_url}/get_all/?instructor_id={self.instructor.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertIn("data", response.json())
        
        # Should only return courses from the specified pathway
        course_data = response.json()["data"][0]
        self.assertIn("title", course_data)
        self.assertIn("description", course_data)
        self.assertEqual(course_data["instructor"]['id'], str(self.instructor.id))

    def test_get_course_by_id(self):
        """Test retrieving a specific course"""
        response = self.client.get(f"{self.base_url}/{self.course.id}/get_by_id/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["data"]["title"], self.course.title)
        self.assertEqual(response.json()["data"]["level"], self.course.level)
        self.assertEqual(response.json()["data"]["stage"], self.course.stage)

    def test_add_course_with_all_fields(self):
        """Test creating a new course with all available fields"""
        response = self.client.post(f"{self.base_url}/add/", self.valid_course_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["success"])

        # Verify all fields were saved correctly
        course = Course.objects.get(title=self.valid_course_data["title"])
        self.assertEqual(course.level, self.valid_course_data["level"])
        self.assertEqual(course.stage, self.valid_course_data["stage"])
        self.assertEqual(str(course.amount), self.valid_course_data["amount"])

    def test_add_course_without_optional_fields(self):
        """Test creating a course without optional fields"""
        data = {
            "title": faker.name(),
            "description": faker.text(),
            "course_pathway": self.pathway.id,
            "level": "1",
            "stage": "beginner",
            "amount": "0.00",
        }
        response = self.client.post(f"{self.base_url}/add/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["success"])

    def test_modify_course_full(self):
        """Test updating all fields of an existing course"""
        updated_data = {
            "title": "Updated Course",
            "description": "Updated description",
            "cover_image": self.test_media.id,
            "level": "1",
            "stage": "beginner",
            "course_pathway": self.pathway.id,
            "amount": "199.99",
            "instructor": self.instructor.id,
        }
        response = self.client.put(
            f"{self.base_url}/{self.course.id}/modify/", updated_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])

        self.course.refresh_from_db()
        self.assertEqual(self.course.title, "Updated Course")
        self.assertEqual(self.course.level, "1")
        self.assertEqual(self.course.stage, "beginner")
        self.assertEqual(str(self.course.amount), "199.99")
        
    
    def test_modify_course_invalid_data(self):
        """Test updating all fields of an existing course"""
        updated_data = {
            "title": "Updated Course",
            "description": "Updated description",
            "cover_image": self.test_media.id,
            "level": "beginner",
            "stage": "beginner",
            "course_pathway": self.pathway.id,
            "amount": "199.99",
            "instructor": self.instructor.id,
        }
        response = self.client.put(
            f"{self.base_url}/{self.course.id}/modify/", updated_data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_modify_course_partial(self):
        """Test partially updating a course"""
        original_description = self.course.description
        patch_data = {"title": "Partially Updated Course"}

        response = self.client.put(
            f"{self.base_url}/{self.course.id}/modify/", patch_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])

        self.course.refresh_from_db()
        self.assertEqual(self.course.title, "Partially Updated Course")
        self.assertEqual(self.course.description, original_description)
        
        
    def test_modify_course_invalid_data(self):
        """Test partially updating a course"""
        patch_data = {"amount": "Invalid Amount"} 

        response = self.client.put(
            f"{self.base_url}/{self.course.id}/modify/", patch_data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])
        self.assertIn("Invalid data provided", response.json()["message"])
    
    def test_modify_course_does_not_exist(self):
        """Test partially updating a course"""
        original_description = self.course.description
        patch_data = {"title": "Partially Updated Course"}

        response = self.client.put(
            f"{self.base_url}/123e4567-e89b-12d3-a456-426614174000/modify/", patch_data
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_course(self):
        """Test deleting a course"""
        response = self.client.delete(f"{self.base_url}/{self.course.id}/remove/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())

    def test_remove_not_existing_course(self):
        """Test deleting a non existing course"""
        response = self.client.delete(f"{self.base_url}/123e4567-e89b-12d3-a456-426614174000/remove/")
        self.assertEqual(response.status_code, 404)

    def test_add_course_with_invalid_media(self):
        """Test creating a course with invalid media ID"""
        invalid_data = self.valid_course_data.copy()
        invalid_data["cover_image"] = 99999  # Non-existent media ID
        response = self.client.post(f"{self.base_url}/add/", invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])

    def test_unauthorized_access(self):
        """Test unauthorized access to admin-only actions"""
        self.client.force_authenticate(user=self.normal_user)

        # Try to create
        response = self.client.post(f"{self.base_url}/add/", self.valid_course_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try to update
        response = self.client.put(
            f"{self.base_url}/{self.course.id}/modify/", {"title": "Updated"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try to delete
        response = self.client.delete(f"{self.base_url}/{self.course.id}/remove/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verify read access is still allowed
        response = self.client.get(f"{self.base_url}/get_all/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])

    def test_get_nonexistent_course(self):
        """Test retrieving a non-existent course"""
        response = self.client.get(f"{self.base_url}/{uuid4()}/get_by_id/")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["success"])

    def test_add_course_with_invalid_pathway(self):
        """Test creating a course with invalid pathway ID"""
        invalid_data = self.valid_course_data.copy()
        invalid_data["course_pathway"] = uuid4()
        response = self.client.post(f"{self.base_url}/add/", invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])

    def test_add_course_with_invalid_instructor(self):
        """Test creating a course with invalid instructor ID"""
        invalid_data = self.valid_course_data.copy()
        invalid_data["instructor"] = uuid4()
        response = self.client.post(f"{self.base_url}/add/", invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])
