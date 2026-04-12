from decimal import Decimal
import logging
from uuid import uuid4
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from api.controllers.utils import Enrollment
from core.models.courses import Assignment, Badge, Certificate, CoursePathWay, Course, CourseProject, CourseProjectResponse, LessonQuiz, LessonQuizScore, Module, Lesson, QouteToken, Qoutes, UserBadge, UserLessonProgress
from core.models.courses import CourseEnrollment, UserModuleProgress, ModuleAssignmentResponse
from core.models.media import Media
from django.contrib.contenttypes.models import ContentType
from django.db import models


User = get_user_model()
faker = Faker()
logger = logging.getLogger(__name__)

class TestMyLearningDashboard(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        
        # Create test student
        self.student = User.objects.create_user(
            email=faker.email(),
            password=faker.password(),
            full_name=faker.name(),
            is_active=True,
            role="student"
        )

        # Create test user
        self.user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(),
            full_name=faker.name(),
            is_active=True,
            role="user"
        )
        self.client.force_authenticate(user=self.user)

        
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
            level="1",
            stage="beginner",
            amount=Decimal("99.99"),
        )
        
        self.course2 = Course.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
            course_pathway = self.course_pathway,
            level="2",
            stage="beginner",
            amount=Decimal("99.99"),
        )
        
        # Create a Module instance
        self.module = Module.objects.create(
            course=self.course,
            title="Test Module",
            description="A test module for lessons.",
            learning_outcome="Understand testing modules.",
            objectives="Learn how to test Django models.",
            order=1
        )
        
        self.module2 = Module.objects.create(
            course=self.course2,
            title="Test Module",
            description="A test module for lessons.",
            learning_outcome="Understand testing modules.",
            objectives="Learn how to test Django models.",
            order=1
        )

        # Create a lesson instance
        self.lesson = Lesson.objects.create(
            module = self.module,
            title=faker.name(),
            description=faker.text(),
            transcript=faker.text(),
            note=faker.text(),
            video_embed=faker.text(),
            order=1,
        )
        
        self.lesson2 = Lesson.objects.create(
            module = self.module2,
            title=faker.name(),
            description=faker.text(),
            transcript=faker.text(),
            note=faker.text(),
            video_embed=faker.text(),
            order=1,
        )
        
        # create Assignment
        self.assignment = Assignment.objects.create(
            module = self.module,
            title=faker.name(),
            description=faker.text(),
            grading_description=faker.text(),
        )
        
        # create course project
        self.project = CourseProject.objects.create(
            course = self.course,
            title=faker.name(),
            description=faker.text(),
            grading_description=faker.text(),
            transcript=faker.text(),
            video_embed=faker.text(),
        )
        
        # create quote
        self.quotes = (
            Qoutes.objects.create(
                user=self.user,
                status="approved",
                term="term1",
                is_active=True,
                is_paused=False,
                course_pathway=self.course_pathway,
                term_start=timezone.now(),
                term_end=timezone.now() + timezone.timedelta(days=30)
            )
        )
        
        self.lesson_quiz = LessonQuiz.objects.create(
            type=LessonQuiz.QuestionType.MULTIPLE_CHOICE,
            question=faker.sentence(),
            lesson=self.lesson,
            allocated_time=Decimal("0.30"),
            correct_answer="a",
        )
        
        # Create a sample related object
        self.related_object = self.course

        # Get the ContentType for the related object
        self.content_type = ContentType.objects.get_for_model(Course)
        
        # Create a test instance of Badge
        self.badge = Badge.objects.create(
            name=faker.word(),
            description=faker.text(),
            icon=self.test_media,
            content_type = self.content_type,
            object_id = self.related_object.id 
        )
        
        # Create test badges
        self.badge1 = UserBadge.objects.create(user=self.user, badge=self.badge)
        
        # Create test certificates
        self.certificate1 = Certificate.objects.create(
            user=self.user, course=self.course, certificate_file=self.test_media
        )
        self.certificate2 = Certificate.objects.create(
            user=self.user, course=self.course2, certificate_file=self.test_media
        )
        
        UserLessonProgress.objects.create(user=self.user, lesson=self.lesson2, status="approved")
        
        # Enroll user in course
        Enrollment(self.user, [self.course]).enroll_user()
        
          # Create a valid quote token
        self.token = "123456"
        self.quote_token = QouteToken.objects.create(
            user=self.user,
            token=self.token,
            qoute=self.quotes,
            is_used=False,
        )
        
        # 
        self.url = reverse("unlock_course")


    def test_enrolled_pathways(self):
        """Test retrieving enrolled pathways"""
        response = self.client.get(reverse('enrolled_pathways'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertEqual(len(response.json()['data']), 1)
        self.assertEqual(response.json()['data'][0]['id'], str(self.course_pathway.id))

    def test_enrolled_courses(self):
        """Test retrieving enrolled courses for a specific pathway"""
        response = self.client.get(reverse('enrolled_courses', kwargs={'enrolled_pathway_id': self.course_pathway.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 1)
        self.assertEqual(response.json()['data'][0]['id'], str(self.course.id))

    def test_enrolled_modules(self):
        """Test retrieving enrolled modules for a specific course"""
        response = self.client.get(reverse('enrolled_modules', kwargs={'enrolled_course_id': self.course.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 1)
        self.assertEqual(response.json()['data'][0]['id'], str(self.module.id))

    def test_student_submit_lesson_quiz_score_success(self):
        """Test successful student lesson quiz score submission"""
        
        self.client.force_authenticate(user=self.student)
        
        quiz_data = {
            'lesson': str(self.lesson.id),
            'score': 85,
            'time_spent': 1.20
        }
        
        response = self.client.post(
            reverse('submit_lesson_quiz_score'), 
            data=quiz_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        
        # Verify quiz score was saved
        quiz_score = LessonQuizScore.objects.get(
            lesson=self.lesson, 
            user=self.student
        )
        self.assertEqual(quiz_score.score, 85)


    def test_user_submit_lesson_quiz_score_success(self):
        """Test successful user lesson quiz score submission"""

        # Create a new user and authenticate
        new_user = User.objects.create_user(
            email=faker.email(),
            password=faker.password(),
            full_name=faker.name(),
            is_active=True,
            role="user"  # Ensure role matches expected logic
        )
        self.client.force_authenticate(user=new_user)

        # Enroll user in course
        Enrollment(new_user, [self.course]).enroll_user()

        # Unlock the lesson manually if necessary
        UserLessonProgress.objects.filter(user=new_user, lesson=self.lesson).update(
            is_locked=False
        )

        # Submit quiz data
        quiz_data = {
            'lesson': str(self.lesson.id),
            'score': 85,
            'time_spent': 0.20
        }
        response = self.client.post(
            reverse('submit_lesson_quiz_score'), 
            data=quiz_data
        )

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])

        # Verify quiz score was saved
        quiz_score = LessonQuizScore.objects.get(
            lesson=self.lesson, 
            user=new_user
        )
        self.assertEqual(quiz_score.score, 85)


    def test_submit_lesson_quiz_score_wrong_lesson_id(self):
        """Test successful student lesson quiz score submission"""
        
        self.client.force_authenticate(user=self.student)
        
        quiz_data = {
            'lesson': str(uuid4()),
            'score': 85,
            'time_spent': 1.20
        }
        response = self.client.post(
            reverse('submit_lesson_quiz_score'), 
            data=quiz_data
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_submit_lesson_quiz_score_low_score(self):
        """Test submitting a quiz score below passing threshold"""
        quiz_data = {
            'lesson': str(self.lesson.id),
            'score': 60,
            'time_spent': 1.20
        }
        response = self.client.post(
            reverse('submit_lesson_quiz_score'), 
            data=quiz_data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])
        self.assertIn("Score should be greater than or equal to 70", response.json()['message'])
        
    
    def test_submit_lesson_quiz_score_low_than_previous_score(self):
        """Test submitting a quiz score below passing threshold"""
        
        self.client.force_authenticate(user=self.student)
        
        lesson_score = LessonQuizScore.objects.create(
                lesson=self.lesson, user=self.student, score=86
        )
        
        quiz_data = {
            'lesson': str(lesson_score.lesson.id),
            'score': 80,
            'time_spent': 1.20
        }
        response = self.client.post(
            reverse('submit_lesson_quiz_score'), 
            data=quiz_data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])
        self.assertIn("Score not updated.", response.json()['message'])
        

    def test_student_submit_assignment(self):
        """Test submitting a module assignment"""
        
        self.client.force_authenticate(user=self.student)

        assignment_data = {
            'assignment': str(self.assignment.id),
            "response":"string",
            'attachment': str(self.test_media.id)
        }
        response = self.client.post(
            reverse('submit_asssignment'), 
            data=assignment_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])

        # Verify assignment response was saved
        assignment_response = ModuleAssignmentResponse.objects.get(
            assignment=self.assignment, 
            user=self.student
        )
        self.assertIsNotNone(assignment_response)
        
        
    def test_user_submit_assignment(self):
        """Test submitting a module assignment"""
        
        self.client.force_authenticate(user=self.user)

        assignment_data = {
            'assignment': str(self.assignment.id),
            "response":"string",
            'attachment': str(self.test_media.id)
        }
        response = self.client.post(
            reverse('submit_asssignment'), 
            data=assignment_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])

        # Verify assignment response was saved
        assignment_response = ModuleAssignmentResponse.objects.get(
            assignment=self.assignment, 
            user=self.user
        )
        self.assertIsNotNone(assignment_response)


    def test_submit_project(self):
        """Test submitting a course project"""

        project_data = {
            'project': str(self.project.id),
            "response":"string",
            'attachment': str(self.test_media.id)
        }
        response = self.client.post(
            reverse('submit_project'), 
            data=project_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])

        # Verify project response was saved
        project_response = CourseProjectResponse.objects.get(
            project=self.project, 
            user=self.user
        )
        self.assertIsNotNone(project_response)
        
        
    def test_unlock_course_with_valid_token(self):
        """Test unlocking courses with a valid token"""
        response = self.client.post(self.url, {"token": self.token})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])

        # Check if courses were enrolled
        Enrollment(user=self.user, courses=[self.course]).enroll_user()
        # Check if the token was marked as used
        self.quote_token.refresh_from_db()
        self.assertTrue(self.quote_token.is_used)

    def test_unlock_course_with_invalid_token(self):
        """Test unlocking courses with an invalid token"""
        response = self.client.post(self.url, {"token": "123455"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])
        self.assertEqual(
            response.json()["message"], "Token is either invalid, used or was not issued to you."
        )

    def test_unlock_course_with_already_used_token(self):
        """Test unlocking courses with an already used token"""
        self.quote_token.is_used = True
        self.quote_token.save()

        response = self.client.post(self.url, {"token": self.token})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])
        self.assertEqual(
            response.json()["message"], "Token is either invalid, used or was not issued to you."
        )

    def test_unlock_course_with_invalid_data(self):
        """Test unlocking courses with invalid data"""
        response = self.client.post(self.url, {"tokens": "kjdnlnskfnknssf"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    
    def test_my_badges(self):
        """Test retrieving all badges earned by the user"""
        response = self.client.get(reverse("my_badges"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertEqual(len(response.json()["data"]), 1)

    def test_my_certificates(self):
        """Test retrieving certificates with and without filters"""
        response = self.client.get(reverse("my_cerificates"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertEqual(len(response.json()["data"]), 2)

        # Test with level filter
        response = self.client.get(reverse("my_cerificates"), {"level": "1"})
        self.assertEqual(len(response.json()["data"]), 1)
        self.assertEqual(response.json()["data"][0]["course"], str(self.course.id))

        # Test with stage filter
        response = self.client.get(reverse("my_cerificates"), {"stage": "beginner"})
        self.assertEqual(len(response.json()["data"]), 2)

    def test_my_video_library(self):
        """Test retrieving user's video library with and without search query"""
        response = self.client.get(reverse("my_video_library"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertEqual(len(response.json()["data"]), 2)

        # Test with search query
        response = self.client.get(reverse("my_video_library"), {"q": self.course_pathway.title})
        self.assertEqual(len(response.json()["data"]), 2)