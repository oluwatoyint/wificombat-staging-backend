import logging
import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from faker import Faker
from core.models.users import School, UserActivity
from tests.helper_functions import create_n_user
from unittest.mock import patch

logger = logging.getLogger(__name__)

User = get_user_model()
faker = Faker()


class TestSchoolAdminAPI(TestCase):
    """Test the school admin API endpoints"""

    def setUp(self):
        self.client = APIClient()
        
        # Create a school
        self.school = School.objects.create(
            name=faker.company(),
        )
        
        # Create school admin
        self.admin_user = User.objects.create_user(
            password=faker.password(),
            email=faker.email(),
            is_active=True,
            role="school_admin",
            full_name=faker.name(),
            school=self.school
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Create test students and teachers
        self.students = create_n_user(n=10, role=User.Roles.STUDENT, school=self.school)
        self.teachers = create_n_user(n=5, role=User.Roles.TEACHER, school=self.school)

    def test_get_user_by_id_success(self):
        """Test successfully getting a user by ID"""
        user = self.students[0]
        url = reverse("school-admin-get-by-id", kwargs={"pk": str(user.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["id"], str(user.id))
        self.assertEqual(response.data["data"]["email"], user.email)

    def test_get_user_by_id_not_found(self):
        """Test getting a non-existent user by ID"""
        url = reverse("school-admin-get-by-id", kwargs={"pk": str(uuid.uuid4())})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        self.assertIn("User not found", response.data["message"])

    def test_modify_user_success(self):
        """Test successfully modifying a user"""
        user = self.teachers[0]
        updated_data = {
            "full_name": faker.name(),
            "email": faker.email()
        }
        
        url = reverse("school-admin-modify", kwargs={"pk": str(user.id)})
        response = self.client.put(url, updated_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["email"], updated_data["email"])
        self.assertEqual(response.data["message"], "user updated successfully")

    def test_modify_user_invalid_data(self):
        """Test modifying a user with invalid data"""
        user = self.teachers[0]
        invalid_data = {
            "email": "invalid-email"  # Invalid email format
        }
        
        url = reverse("school-admin-modify", kwargs={"pk": str(user.id)})
        response = self.client.put(url, invalid_data)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "Invalid data provided")

    def test_modify_user_not_found(self):
        """Test modifying a non-existent user"""
        url = reverse("school-admin-modify", kwargs={"pk": str(uuid.uuid4())})
        response = self.client.put(url, {"full_name": faker.name()})
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["message"], "user not found")

    def test_remove_user_success(self):
        """Test successfully removing a user"""
        user = self.students[0]
        url = reverse("school-admin-remove", kwargs={"pk": str(user.id)})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "User deleted successfully")
        
        # Verify user is actually deleted
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user.id)

    def test_remove_user_not_found(self):
        """Test removing a non-existent user"""
        url = reverse("school-admin-remove", kwargs={"pk": str(uuid.uuid4())})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["message"], "User not found")

    def test_user_recent_activities_success(self):
        """Test successfully getting user's recent activities"""
        user = self.students[0]
        
        # Create some test activities
        activities = []
        for _ in range(15):  # Create 15 activities (more than the 10 limit)
            activity = UserActivity.objects.create(
                user=user,
                activity_type="test",
                description=faker.sentence()
            )
            activities.append(activity)
        
        url = reverse("school-admin-user-recent-activities", kwargs={"pk": str(user.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["message"], "Success")
        self.assertEqual(len(response.data["data"]), 10) 

    def test_user_recent_activities_with_search(self):
        """Test getting user's recent activities with search query"""
        user = self.students[0]
        
        # Create activities with specific search term
        search_term = "specific_term"
        UserActivity.objects.create(
            user=user,
            activity_type="test",
            description=f"Activity with {search_term}"
        )
        
        # Create other activities without search term
        for _ in range(5):
            UserActivity.objects.create(
                user=user,
                activity_type="test",
                description=faker.sentence()
            )
        
        url = reverse("school-admin-user-recent-activities", kwargs={"pk": str(user.id)})
        response = self.client.get(url, {"q": search_term})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertIn(search_term, response.data["data"][0]["description"])

    def test_user_recent_activities_user_not_found(self):
        """Test getting recent activities for non-existent user"""
        url = reverse("school-admin-user-recent-activities", kwargs={"pk": str(uuid.uuid4())})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["message"], "User not found")

    def test_get_all_users_in_school(self):
        """Test getting all users (students and teachers) when no role specified"""
        url = reverse("school-admin-get-all-users-in-school")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should return both students (10) and teachers (5)
        self.assertEqual(len(response.data["data"]), 15)
        
        # Count each role type
        students_count = sum(1 for user in response.data["data"] if user["role"] == User.Roles.STUDENT)
        teachers_count = sum(1 for user in response.data["data"] if user["role"] == User.Roles.TEACHER)
        
        self.assertEqual(students_count, 10)
        self.assertEqual(teachers_count, 5)