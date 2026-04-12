import logging
from decimal import Decimal
from uuid import uuid4
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from core.models.courses import Course, CoursePathWay, Lesson, LessonRating, Module
from core.models.media import Media

logger = logging.getLogger(__name__)
User = get_user_model()
faker = Faker()

class TestLessonRating(TestCase):
    """Test cases for LessonRating ViewSet"""

    def setUp(self):
        self.client = APIClient()

        # Base URL for the endpoint
        self.base_url = "/lesson-rating"

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
        )
        
        
        # Create test media and lesson
        self.test_media = Media.objects.create(media_type="photo")
        
        # create test course_pathway
        self.course_pathway = CoursePathWay.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
        )
        
        # Create test course
        self.course = Course.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
            course_pathway = self.course_pathway,
            level="Beginner",
            stage="Active",
            amount=Decimal("99.99"),
        )
        
        # Create a Module instance
        self.module = Module.objects.create(
            course=self.course,
            title="Test Module",
            description="A test module for lessons.",
            learning_outcome="Understand testing modules.",
            objectives="Learn how to test Django models.",
        )

        self.lesson = Lesson.objects.create(
            module = self.module,
            title=faker.name(),
            description=faker.text(),
            transcript=faker.text(),
            note=faker.text(),
            video_embed=faker.text(),
            order=1,
        )

        # Create sample lesson rating
        self.lesson_rating = LessonRating.objects.create(
            lesson=self.lesson,
            user=self.normal_user,
            rating=4,
            feedback_text=faker.text(),
        )

        # Set up authentication
        self.client.force_authenticate(user=self.normal_user)

    def test_get_all_lesson_ratings(self):
        """Test retrieving all ratings for a lesson"""
        url = reverse("lesson-rating-get-all", kwargs={"pk": str(self.lesson.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.json())
        self.assertEqual(len(response.json()["data"]), 1)

    def test_get_all_ratings_invalid_lesson(self):
        """Test retrieving ratings for a non-existent lesson"""
        url = reverse("lesson-rating-get-all", kwargs={"pk": "123e4567-e89b-12d3-a456-426614174000"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()["success"])

    def test_get_user_lesson_ratings(self):
        """Test retrieving ratings for a specific user"""
        url = reverse("lesson-rating-get-by-id", kwargs={"pk": str(self.normal_user.id)})
        response = self.client.get(url, {"lesson_id": str(self.lesson.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertEqual(len(response.json()["data"]), 1)

    def test_get_user_lesson_ratings_invalid_user(self):
        """Test retrieving ratings for a non-existent user"""
        url = reverse("lesson-rating-get-by-id", kwargs={"pk": "123e4567-e89b-12d3-a456-426614174000"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()["success"])

    def test_create_lesson_rating(self):
        """Test creating a new lesson rating"""
        # Create new user and course for this test
        new_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
        )
        
        new_lesson = Lesson.objects.create(
            module = self.module,
            title=faker.name(),
            description=faker.text(),
            transcript=faker.text(),
            note=faker.text(),
            video_embed=faker.text(),
            order=2,
        )
        
        self.client.force_authenticate(user=new_user)
        
        data = {
            "lesson": str(new_lesson.id),
            "user": str(new_user.id),
            "rating": 5.0,
            "feedback_text": "Excellent lesson!",
        }

        url = reverse("lesson-rating-list")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["data"]["rating"], "5.0")
        
    
    def test_create_lesson_rating_invalid_data(self):
        """Test creating a new lesson rating"""
        # Create new user and course for this test
        new_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
        )
        
        new_lesson = Lesson.objects.create(
            module = self.module,
            title=faker.name(),
            description=faker.text(),
            transcript=faker.text(),
            note=faker.text(),
            video_embed=faker.text(),
            order=2,
        )
        
        self.client.force_authenticate(user=new_user)
        
        data = {
            "lesson": str(new_lesson.id),
            "user": str(new_user.id),
            "rating": 6.0,
            "feedback_text": "Excellent lesson!",
        }

        url = reverse("lesson-rating-list")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_lesson_rating(self):
        """Test updating an existing lesson rating"""
        update_data = {
            "rating": 3,
            "feedback_text": "Updated feedback",
        }
        url = reverse("lesson-rating-detail", kwargs={"pk": str(self.lesson_rating.id)})
        response = self.client.put(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["data"]["rating"], "3.0")
        
    
    def test_update_non_existing_lesson_rating(self):
        """Test updating an non existing lesson rating"""
        update_data = {
            "rating": 3,
            "feedback_text": "Updated feedback",
        }
        url = reverse("lesson-rating-detail", kwargs={"pk": str(uuid4())})
        response = self.client.put(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    
    
    def test_update_lesson_rating_invalid_data(self):
        """Test updating lesson rating invlaid data"""
        update_data = {
            "rating": 6,
            "feedback_text": "Updated feedback",
        }
        url = reverse("lesson-rating-detail", kwargs={"pk": str(self.lesson_rating.id)})
        response = self.client.put(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_lesson_rating(self):
        """Test deleting a lesson rating"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("lesson-rating-detail", kwargs={"pk": str(self.lesson_rating.id)})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertFalse(LessonRating.objects.filter(id=self.lesson_rating.id).exists())


    def test_delete_lesson_rating_unauthorized(self):
        """Test deleting a rating without proper permissions"""
        url = reverse('lesson-rating-detail', kwargs={'pk': str(self.lesson_rating.id)})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_nonexistent_lesson_rating(self):
        """Test deleting a non-existent rating"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('lesson-rating-detail', kwargs={'pk': '123e4567-e89b-12d3-a456-426614174000'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()["success"])