from decimal import Decimal
import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from core.models.courses import (
    Assignment,
    Course,
    CoursePathWay,
    Module,
    Lesson,
    LessonQuizScore,
    ModuleAssignmentResponse,
    CourseProject,
    CourseProjectResponse,
    UserEarnedPoint,
)
from core.models.media import Media

User = get_user_model()
faker = Faker()

class TestReportCardView(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a test user
        self.user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(),
            full_name=faker.name(),
            is_active=True,
            role="student",
        )
        
        self.instructor = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
            role="tutor",
        )

        # Authenticate the client
        self.client.force_authenticate(user=self.user)

        
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

        # Create a module
        self.module = Module.objects.create(
            course=self.course,
            title="Test Module",
            description="A test module.",
            order=1,
        )

        # Create lessons
        self.lesson = Lesson.objects.create(
            module=self.module,
            title="Test Lesson",
            description="This is a test lesson.",
            order=1,
        )
        
        
        # Create lessons
        self.assignment = Assignment.objects.create(
            module=self.module,
            title="Test Lesson",
            description="This is a test lesson.",
            grading_description= faker.sentence()
        )

        # Create quiz score
        self.quiz_score = LessonQuizScore.objects.create(
            user=self.user,
            lesson=self.lesson,
            score=Decimal("50.00"),
        )

        # Create assignment response
        self.assignment_response = ModuleAssignmentResponse.objects.create(
            user=self.user,
            assignment= self.assignment,
            score=Decimal("30.00"),
        )

        # Create a course project
        self.project = CourseProject.objects.create(
            course=self.course,
            title="Test Project",
            description="A test project.",
        )

        # Create project response
        self.project_response = CourseProjectResponse.objects.create(
            user=self.user,
            project=self.project,
            score=Decimal("20.00"),
        )

        # Create earned points
        self.earned_points = UserEarnedPoint.objects.create(
            user=self.user,
            course=self.course,
            points=10,
            point_type="quiz",
        )

        # URL for the ReportCardView
        self.url = reverse("report_card", kwargs={"course_id": self.course.id, "user_id": self.user.id})

    def test_report_card_view_success(self):
        """Test successful retrieval of report card data."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("total_score" in response.json())
        self.assertTrue("scores_breakdown" in response.json())
        self.assertTrue("modules" in response.json())
        self.assertTrue("total_points" in response.json())
        self.assertTrue("points_breakdown" in response.json())
        self.assertTrue("extra_info" in response.json())

    def test_report_card_view_user_not_found(self):
        """Test report card retrieval when the user does not exist."""
        invalid_url = reverse(
            "report_card", kwargs={"course_id": self.course.id, "user_id": uuid.uuid4()}
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["message"], "User not found")

    def test_report_card_view_course_not_found(self):
        """Test report card retrieval when the course does not exist."""
        invalid_url = reverse(
            "report_card", kwargs={"course_id": uuid.uuid4(), "user_id": self.user.id}
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error"], "Course not found")

    def test_report_card_view_calculations(self):
        """Test the correctness of score calculations in the response."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["scores_breakdown"]["quiz_scores"], 50.00)
        self.assertEqual(data["scores_breakdown"]["assignment_scores"], 30.00)
        self.assertEqual(data["scores_breakdown"]["project_scores"], 20.00)
        self.assertEqual(data["total_score"], 100.00)
        self.assertEqual(data["total_points"], 10)

    # def test_report_card_view_no_scores(self):
    #     """Test report card view when no scores are present."""
    #     self.quiz_score.delete()
    #     self.assignment_response.delete()
    #     self.project_response.delete()
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     data = response.json()
    #     self.assertEqual(data["scores_breakdown"]["quiz_scores"], 0.00)
    #     self.assertEqual(data["scores_breakdown"]["assignment_scores"], 0.00)
    #     self.assertEqual(data["scores_breakdown"]["project_scores"], 0.00)
    #     self.assertEqual(data["total_score"], 0.00)
    #     self.assertEqual(data["total_points"], 0)

