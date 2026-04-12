import logging
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from core.models.courses import Course, CoursePathWay, CourseRating
from core.models.media import Media

logger = logging.getLogger(__name__)
User = get_user_model()
faker = Faker()

class TestCourseRating(TestCase):
    """Test cases for CourseRating ViewSet"""

    def setUp(self):
        self.client = APIClient()
        
        # Define base URL
        self.base_url = "/course-rating"
        
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

        # Create test media for course
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
        
        # Create sample course rating
        self.course_rating = CourseRating.objects.create(
            course=self.course,
            user=self.normal_user,
            score=Decimal("4.5"),
            feedback_text=faker.text()
        )

        self.valid_rating_data = {
            "course": str(self.course.id),
            "user": str(self.normal_user.id),
            "score": "4.0",
            "feedback_text": faker.text()
        }

        # Set up authentication
        self.client.force_authenticate(user=self.normal_user)

    def test_get_all_course_ratings(self):
        """Test getting all ratings for a course"""
        
        url = reverse('course-rating-get-all', kwargs={'pk': str(self.course.id)})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.json())
        self.assertEqual(len(response.json()["data"]), 1)
        # Verify the returned data structure
        rating_data = response.json()["data"][0]
        self.assertIn("score", rating_data)
        self.assertIn("feedback_text", rating_data)
        self.assertIn("user", rating_data)
        self.assertIn("course", rating_data)
        
    def test_get_all_ratings_invalid_course(self):
        """Test getting ratings for non-existent course"""
        url = reverse('course-rating-get-all', kwargs={'pk': '123e4567-e89b-12d3-a456-426614174000'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()["success"])

    def test_get_user_course_ratings(self):
        """Test getting ratings by user ID"""
        url = reverse('course-rating-get-by-id', kwargs={'pk': str(self.normal_user.id)})
        response = self.client.get(url, {"course_id": str(self.course.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertEqual(len(response.json()["data"]), 1)

    def test_get_user_ratings_invalid_user(self):
        """Test getting ratings for non-existent user"""
        url = reverse('course-rating-get-by-id', kwargs={'pk': '123e4567-e89b-12d3-a456-426614174000'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()["success"])

    def test_create_course_rating(self):
        """Test creating a new course rating"""
        # Create new user and course for this test
        new_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
        )
        new_course = Course.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
            course_pathway = self.course_pathway,
            level="Beginner",
            stage="Active",
            amount=Decimal("99.99"),
        )
        
        self.client.force_authenticate(user=new_user)
        
        data = {
            "course": str(new_course.id),
            "user": str(new_user.id),
            "score": "4.5",
            "feedback_text": "Great course!"
        }
        
        url = reverse('course-rating-list')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["data"]["score"], "4.5")

    def test_create_duplicate_course_rating(self):
        """Test creating a duplicate course rating for same user and course"""
        url = reverse('course-rating-list')
        response = self.client.post(url, self.valid_rating_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])

    def test_create_course_rating_invalid_score(self):
        """Test creating course rating with invalid score"""
        invalid_data = self.valid_rating_data.copy()
        invalid_data["score"] = "6.0"  # Above max allowed value
        url = reverse('course-rating-list')
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])

    def test_update_course_rating(self):
        """Test updating an existing rating"""
        update_data = {
            "score": "3.5",
            "feedback_text": "Updated feedback"
        }
        url = reverse('course-rating-detail', kwargs={'pk': str(self.course_rating.id)})
        response = self.client.put(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["data"]["score"], "3.5")
        self.assertEqual(response.json()["data"]["feedback_text"], "Updated feedback")
        
    
    def test_update_course_rating_invalid_data(self):
        """Test updating an existing rating"""
        update_data = {
            "score": "6.0",
            "feedback_text": "Updated feedback"
        }
        url = reverse('course-rating-detail', kwargs={'pk': str(self.course_rating.id)})
        response = self.client.put(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_nonexistent_rating(self):
        """Test updating a non-existent course rating"""
        update_data = {
            "score": "3.5",
            "feedback_text": "Updated feedback"
        }
        url = reverse('course-rating-detail', kwargs={'pk': '123e4567-e89b-12d3-a456-426614174000'})
        response = self.client.put(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()["success"])

    def test_delete_course_rating(self):
        """Test deleting a rating"""
        # Switch to admin user as only admins can delete
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('course-rating-detail', kwargs={'pk': str(self.course_rating.id)})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertFalse(CourseRating.objects.filter(id=self.course_rating.id).exists())

    def test_delete_rating_unauthorized(self):
        """Test deleting a rating without proper permissions"""
        url = reverse('course-rating-detail', kwargs={'pk': str(self.course_rating.id)})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_nonexistent_rating(self):
        """Test deleting a non-existent rating"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('course-rating-detail', kwargs={'pk': '123e4567-e89b-12d3-a456-426614174000'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()["success"])