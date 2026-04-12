from decimal import Decimal
import logging
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from core.models.courses import (
    Assignment,
    Certificate,
    Course,
    CourseEnrollment,
    CoursePathWay,
    CourseProject,
    CourseProjectResponse,
    Lesson,
    LessonQuiz,
    LessonQuizScore,
    Module,
    ModuleAssignmentResponse,
)
from core.models.media import Media

logger = logging.getLogger(__name__)
User = get_user_model()
faker = Faker()


class TestStudentProgressPortfolioSection(TestCase):
    """Test cases for Student Progress API"""

    def setUp(self):
        self.client = APIClient()
        self.base_url = reverse("portfolio_content")

        # Create a test user
        self.user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
            role="user",
        )
        self.client.force_authenticate(user=self.user)

        # Create test data
        self.media = Media.objects.create(media_type="photo")
        self.course_pathway = CoursePathWay.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.media,
        )
        self.course = Course.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.media,
            course_pathway=self.course_pathway,
            level="1",
            stage="beginner",
            amount=Decimal("99.99"),
        )
        self.module = Module.objects.create(
            course=self.course,
            title="Test Module",
            description="Test module description",
            learning_outcome="Learning outcome example",
            objectives="Objective example",
            order=1,
        )
        self.lesson = Lesson.objects.create(
            module=self.module,
            title="Test Lesson",
            description="Lesson description",
            transcript="Lesson transcript",
            note="Lesson note",
            video_embed="Lesson video embed",
            order=1,
        )
        self.assignment = Assignment.objects.create(
            module=self.module,
            title="Test Assignment",
            description="Assignment description",
            grading_description="Grading description",
        )
        self.project = CourseProject.objects.create(
            course=self.course,
            title="Test Project",
            description="Project description",
            grading_description="Grading description",
            transcript="Project transcript",
            video_embed="Project video embed",
        )
        self.lesson_quiz = LessonQuiz.objects.create(
            type=LessonQuiz.QuestionType.MULTIPLE_CHOICE,
            question="Sample question?",
            lesson=self.lesson,
            allocated_time=Decimal("0.30"),
            correct_answer="a",
        )

    def test_fetch_progress_with_partial_completion(self):
        """Test fetching progress with partial completion data"""
        CourseEnrollment.objects.create(user=self.user, course=self.course)

        # Simulate completed quiz
        LessonQuizScore.objects.create(user=self.user, lesson=self.lesson, score=80)

        # Simulate completed assignment
        ModuleAssignmentResponse.objects.create(
            user=self.user, assignment=self.assignment
        )

        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["data"]
        self.assertEqual(data["quiz_percentage"], 100)  # 1 out of 1 quiz completed
        self.assertEqual(data["assignment_percentage"], 100)  # 1 out of 1 assignment
        self.assertEqual(data["certificate_percentage"], 0)  # No certificates earned
        self.assertEqual(data["project_percentage"], 0)  # No projects completed

    def test_fetch_progress_with_no_enrollments(self):
        """Test fetching progress when the user is not enrolled in any course"""
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["data"]
        self.assertEqual(data["quiz_percentage"], 0)
        self.assertEqual(data["assignment_percentage"], 0)
        self.assertEqual(data["certificate_percentage"], 0)
        self.assertEqual(data["project_percentage"], 0)

    def test_fetch_progress_with_no_data(self):
        """Test fetching progress with no quizzes or assignments available"""
        CourseEnrollment.objects.create(user=self.user, course=self.course)
        LessonQuiz.objects.filter(lesson=self.lesson).delete()
        Assignment.objects.filter(module=self.module).delete()

        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["data"]
        self.assertEqual(data["quiz_percentage"], 0)
        self.assertEqual(data["assignment_percentage"], 0)
        self.assertEqual(data["certificate_percentage"], 0)
        self.assertEqual(data["project_percentage"], 0)

    def test_unauthorized_access(self):
        """Test access to the endpoint without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
