import logging
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import timedelta

from core.models.courses import (
    CourseStreak, 
    CourseEnrollment, 
    Course, 
    CoursePathWay
)

User = get_user_model()
faker = Faker()
logger = logging.getLogger(__name__)

class TestUserCourseStreak(TestCase):
    """Test cases for User Course Streak Endpoint"""

    def setUp(self):
        """Set up test data for user course streak endpoint"""
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
            role="user",
        )

        # Create test pathway
        self.pathway = CoursePathWay.objects.create(
            title=faker.name(), 
            description=faker.text()
        )

        # Create sample courses
        self.course1 = Course.objects.create(
            title=faker.name(),
            description=faker.text(),
            course_pathway=self.pathway,
            amount=Decimal("99.99"),
        )

        self.course2 = Course.objects.create(
            title=faker.name(),
            description=faker.text(),
            course_pathway=self.pathway,
            amount=Decimal("149.99"),
        )

        # Enroll user in courses
        CourseEnrollment.objects.create(user=self.user, course=self.course1)
        CourseEnrollment.objects.create(user=self.user, course=self.course2)

        # Set up authentication
        self.client.force_authenticate(user=self.user)

    def _create_course_streaks(self, course, num_days=7):
        """Helper method to create course streaks"""
        today = timezone.now()
        for i in range(num_days):
            streak_date = today - timedelta(days=i)
            CourseStreak.objects.create(
                user=self.user,
                course=course,
                streak_score=0.5,
                created_at=streak_date
            )

    def test_get_course_streak_this_week(self):
        """Test retrieving course streak for this week"""
        # Create streaks for courses
        self._create_course_streaks(self.course1)
        self._create_course_streaks(self.course2)

        # Make request
        url = reverse('user_course_streak', kwargs={'pathway_id': self.pathway.id})
        url += '?period=this_week'
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('labels', response.data)
        self.assertIn('datasets', response.data)
        self.assertEqual(len(response.data['labels']), 7)  # Weekdays
        self.assertEqual(len(response.data['datasets']), 2)  # Two courses

    def test_get_course_streak_last_7_days(self):
        """Test retrieving course streak for last 7 days"""
        # Create streaks for courses
        self._create_course_streaks(self.course1)
        self._create_course_streaks(self.course2)

        # Make request
        url = reverse('user_course_streak', kwargs={'pathway_id': self.pathway.id})
        url += '?period=last_7days'
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('labels', response.data)
        self.assertIn('datasets', response.data)
        self.assertEqual(len(response.data['labels']), 7)  # Weekdays
        self.assertEqual(len(response.data['datasets']), 2)  # Two courses
        
    
    def test_get_course_streak_last_last_6months(self):
        """Test retrieving course streak for last 7 days"""
        # Create streaks for courses
        self._create_course_streaks(self.course1)
        self._create_course_streaks(self.course2)

        # Make request
        url = reverse('user_course_streak', kwargs={'pathway_id': self.pathway.id})
        url += '?period=last_6months'
        response = self.client.get(url)
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('labels', response.data)
        self.assertIn('datasets', response.data)
        self.assertEqual(len(response.data['datasets']), 2)  # Two courses
        
    
    def test_get_course_streak_last_year(self):
        """Test retrieving course streak for last 7 days"""
        # Create streaks for courses
        self._create_course_streaks(self.course1)
        self._create_course_streaks(self.course2)

        # Make request
        url = reverse('user_course_streak', kwargs={'pathway_id': self.pathway.id})
        url += '?period=year'
        response = self.client.get(url)
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('labels', response.data)
        self.assertIn('datasets', response.data)
        self.assertEqual(len(response.data['datasets']), 2)  # Two courses

    def test_get_course_streak_no_data(self):
        """Test retrieving course streak with no streak data"""
        # Make request without creating any streaks
        url = reverse('user_course_streak', kwargs={'pathway_id': self.pathway.id})
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('labels', response.data)
        self.assertIn('datasets', response.data)
        self.assertEqual(len(response.data['datasets']), 2)  # Two enrolled courses
        self.assertTrue(all(dataset['data'] == [0]*7 for dataset in response.data['datasets']))

    def test_get_course_streak_unauthorized(self):
        """Test unauthorized access to course streak endpoint"""
        self.client.force_authenticate(user=None)
        
        url = reverse('user_course_streak', kwargs={'pathway_id': self.pathway.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)