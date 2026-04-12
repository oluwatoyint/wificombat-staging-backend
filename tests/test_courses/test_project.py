import logging
from uuid import uuid4
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from core.models.courses import Course, Module, Assignment, CourseProject, CoursePathWay
from core.models.media import Media

logger = logging.getLogger(__name__)
User = get_user_model()
faker = Faker()


class TestCourseProject(TestCase):
    """Comprehensive test suite for CourseProject ViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse("project-list")

        # Create test users
        self.admin_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
            is_staff=True,
            role="main_admin",
        )
        self.client.force_authenticate(user=self.admin_user)
        self.instructor = User.objects.create_user(
            email=faker.email(),
            password=faker.password(length=10),
            full_name=faker.name(),
            is_active=True,
            role="tutor",
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

        self.course_project = CourseProject.objects.create(
            title="Sample Project",
            description="Detailed project description",
            grading_description="Detailed grading criteria",
            is_locked=False,
            course=self.course,
            transcript="Project transcript",
            video_embed="Embedded video link",
        )

    def test_create_course_project(self):
        """Test successful creation of a course project"""
        data = {
            "title": "New Project",
            "description": "A new course project",
            "grading_description": "Grading criteria for new project",
            "is_locked": False,
            "course": self.course.id,
            "transcript": "Transcript text",
            "video_embed": "https://embed.video",
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CourseProject.objects.count(), 2)

    def test_create_course_project_invalid_data(self):
        """Test creation with invalid data"""
        data = {
            "title": "",  # Missing title
            "description": "A project with invalid data",
            "grading_description": "",
            "course": "string",  # Missing course
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_retrieve_all_course_project(self):
        """Test retrieving all course project"""
        detail_url = reverse("get_projects", args=[self.course.id])
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]), 1)


    def test_retrieve_all_course_project_bad_id(self):
        """Test retrieving all course project"""
        detail_url = reverse("get_projects", args=[uuid4])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    def test_retrieve_course_project(self):
        """Test retrieving a single course project"""
        detail_url = reverse("project-detail", args=[self.course_project.id])
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["title"], "Sample Project")
        self.assertEqual(response.json()["data"]["grading_description"], "Detailed grading criteria")
        
        
    def test_retrieve_non_existing_course_project(self):
        """Test retrieving a single course project"""
        detail_url = reverse("project-detail", args=[uuid4()])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    
    def test_retrieve_bad_course_project_id(self):
        """Test retrieving a single course project"""
        detail_url = reverse("project-detail", args=[uuid4])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_update_course_project(self):
        """Test updating a course project"""
        detail_url = reverse("project-detail", args=[self.course_project.id])
        data = {"title": "Updated Project Title"}
        response = self.client.put(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course_project.refresh_from_db()
        self.assertEqual(self.course_project.title, "Updated Project Title")
        
    
    def test_update_course_project_invalid_data(self):
        """Test updating a course project with invalid data"""
        detail_url = reverse("project-detail", args=[self.course_project.id])
        data = {"title": "Updated Project Title", "is_locked": faker.word()}
        response = self.client.put(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    
    def test_update_non_existing_course_project(self):
        """Test updating a course project"""
        detail_url = reverse("project-detail", args=[uuid4()])
        data = {"title": "Updated Project Title"}
        response = self.client.put(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_course_project(self):
        """Test deleting a course project"""
        detail_url = reverse("project-detail", args=[self.course_project.id])
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CourseProject.objects.count(), 0)

    def test_delete_course_project_invalid(self):
        """Test deleting a non-existing course project"""
        detail_url = reverse("project-detail", args=[uuid4()])
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# class TestAssignment(TestCase):
#     """Comprehensive test suite for Assignment ViewSet"""

#     def setUp(self):
#         self.client = APIClient()
#         self.list_url = reverse("assignment-list")

#         # Create test users
#         self.admin_user = User.objects.create_user(
#             email=faker.email(),
#             password=faker.password(length=10),
#             full_name=faker.name(),
#             is_active=True,
#             is_staff=True,
#             role="main_admin",
#         )
#         self.client.force_authenticate(user=self.admin_user)

#         # Create test data
#         self.course = Course.objects.create(
#             title=faker.name(),
#             description=faker.text(),
#             level="Beginner",
#             stage="Active",
#         )

#         self.module = Module.objects.create(
#             title=faker.name(),
#             description=faker.text(),
#             course=self.course,
#         )

#         self.assignment = Assignment.objects.create(
#             title="Sample Assignment",
#             description="Detailed assignment description",
#             grading_description="Detailed grading criteria",
#             is_locked=True,
#             module=self.module,
#         )

#     def test_create_assignment(self):
#         """Test successful creation of an assignment"""
#         data = {
#             "title": "New Assignment",
#             "description": "A new assignment for the module",
#             "grading_description": "Grading criteria for new assignment",
#             "is_locked": False,
#             "module": self.module.id,
#         }
#         response = self.client.post(self.list_url, data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Assignment.objects.count(), 2)

#     def test_create_assignment_invalid_data(self):
#         """Test creation with invalid data"""
#         data = {
#             "title": "",  # Missing title
#             "description": "Assignment with invalid data",
#             "module": None,  # Missing module
#         }
#         response = self.client.post(self.list_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_retrieve_assignment(self):
#         """Test retrieving a single assignment"""
#         detail_url = reverse("assignment-detail", args=[self.assignment.id])
#         response = self.client.get(detail_url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.json()["data"]["title"], "Sample Assignment")

#     def test_update_assignment(self):
#         """Test updating an assignment"""
#         detail_url = reverse("assignment-detail", args=[self.assignment.id])
#         data = {"title": "Updated Assignment Title"}
#         response = self.client.patch(detail_url, data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assignment.refresh_from_db()
#         self.assertEqual(self.assignment.title, "Updated Assignment Title")

#     def test_delete_assignment(self):
#         """Test deleting an assignment"""
#         detail_url = reverse("assignment-detail", args=[self.assignment.id])
#         response = self.client.delete(detail_url)
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#         self.assertEqual(Assignment.objects.count(), 0)

#     def test_delete_assignment_invalid(self):
#         """Test deleting a non-existing assignment"""
#         detail_url = reverse("assignment-detail", args=[uuid4()])
#         response = self.client.delete(detail_url)
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
