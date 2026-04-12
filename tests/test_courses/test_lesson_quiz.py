import logging
from uuid import uuid4
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from django.contrib.auth import get_user_model
from core.models.courses import (
    Lesson, Module, Course, CoursePathWay, 
    LessonQuiz, LessonQuizOption
)
from core.models.media import Media

logger = logging.getLogger(__name__)
User = get_user_model()
faker = Faker()


class TestLessonQuiz(TestCase):
    """Test cases for LessonQuiz ViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse("quiz-list")

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

        # Create test media for options
        self.test_media = Media.objects.create(media_type="image")

        # Create test pathway and course structure
        self.pathway = CoursePathWay.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media
        )

        self.course = Course.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
            level="Beginner",
            stage="Active",
            course_pathway=self.pathway
        )

        self.module = Module.objects.create(
            title=faker.name(),
            description=faker.text(),
            cover_image=self.test_media,
            course=self.course,
            learning_outcome=faker.text(),
            objectives=faker.text()
        )

        self.lesson = Lesson.objects.create(
            title=faker.name(),
            description=faker.text(),
            module=self.module,
            transcript=faker.text(),
            note=faker.text(),
            video_embed=faker.text(),
            order=1,
            is_locked=False
        )

        # Create sample quiz with options
        self.quiz = LessonQuiz.objects.create(
            type=LessonQuiz.QuestionType.MULTIPLE_CHOICE,
            question="Sample multiple choice question?",
            lesson=self.lesson,
            correct_answer="Option A"
        )

        # Create quiz options with labels
        self.quiz_options = [
            LessonQuizOption.objects.create(
                lesson_quiz=self.quiz,
                text_option=f"Option {label}",
                option_label=label,
                image_option=self.test_media if label == 'a' else None  # Add image to first option
            ) for label in LessonQuizOption.OPTIONLABEL.values
        ]

        # Valid quiz data matching model fields
        self.valid_quiz_data = {
            "type": LessonQuiz.QuestionType.MULTIPLE_CHOICE,
            "question": "New test question?",
            "lesson": self.lesson.id,
            "correct_answer": "Option A",
            "options": [
                {
                    "text_option": "Option A",
                    "option_label": "a",
                    "image_option": self.test_media.id
                },
                {
                    "text_option": "Option B",
                    "option_label": "b"
                },
                {
                    "text_option": "Option C",
                    "option_label": "c"
                }
            ]
        }

        # Set up authentication
        self.client.force_authenticate(user=self.admin_user)

    def test_get_all_quizzes(self):
        """Test getting all quizzes for a lesson"""
        url = reverse("get_lessons", kwargs={"lesson_id": self.lesson.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        data = response.json()["data"]
        
        # Verify quiz data structure
        quiz_data = data[0]
        self.assertIn("type", quiz_data)
        self.assertIn("question", quiz_data)
        self.assertIn("correct_answer", quiz_data)
        self.assertIn("options", quiz_data)

    def test_create_quiz_all_types(self):
        """Test creating quizzes of different types"""
        for quiz_type in LessonQuiz.QuestionType.choices:
            
            data = self.valid_quiz_data.copy()
            data["type"] = quiz_type[0]
            
            response = self.client.post(self.list_url, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify quiz was created with correct type
            quiz = LessonQuiz.objects.filter(type=data["type"])
            self.assertEqual(quiz[0].type, quiz_type[0])

    def test_create_quiz_with_image_options(self):
        """Test creating a quiz with image options"""
        data = {
            "type": LessonQuiz.QuestionType.MULTIPLE_IMAGE,
            "question": "Image question test?",
            "lesson": self.lesson.id,
            "correct_answer": "a",
            "options": [
                {
                    "option_label": "a",
                    "image_option": self.test_media.id
                },
                {
                    "option_label": "b",
                    "image_option": self.test_media.id
                }
            ]
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify image options were created
        quiz = LessonQuiz.objects.get(question=data["question"])
        self.assertTrue(all(
            opt.image_option for opt in quiz.lessonquizoption_set.all()
        ))

    # def test_unique_option_labels(self):
    #     """Test that duplicate option labels are rejected"""
    #     data = self.valid_quiz_data.copy()
    #     data["lessonquizoption_set"] = [
    #         {
    #             "text_option": "Option A",
    #             "option_label": "a"
    #         },
    #         {
    #             "text_option": "Option B",
    #             "option_label": "a"  # Duplicate label
    #         }
    #     ]
    #     response = self.client.post(self.list_url, data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_quiz_type(self):
        """Test updating quiz type and options"""
        url = reverse("quiz-detail", kwargs={"pk": self.quiz.id})
        updated_data = {
            "type": LessonQuiz.QuestionType.TRUE_FALSE,
            "question": "Updated true/false question?",
            "correct_answer": "True",
            "lesson": self.lesson.id,
            "lessonquizoption_set": [
                {"text_option": "True", "option_label": "a"},
                {"text_option": "False", "option_label": "b"}
            ]
        }
        
        response = self.client.put(url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify quiz type and options were updated
        self.quiz.refresh_from_db()        
        self.assertEqual(self.quiz.type, LessonQuiz.QuestionType.TRUE_FALSE)
        # self.assertEqual(self.quiz.lessonquizoption_set.count(), 2)

    def test_invalid_quiz_type(self):
        """Test creating quiz with invalid type"""
        data = self.valid_quiz_data.copy()
        data["type"] = "invalid_type"
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)