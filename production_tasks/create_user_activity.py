from django.contrib.auth import get_user_model
from faker import Faker
from production_tasks.base_task import BaseTask
from core.managers.utils import log_user_activity

faker = Faker()
User = get_user_model()


class CreateDummyUserActivities(BaseTask):
    """
    A Prod task to create dummy users' activities in the database.
    """

    def handle(self):
        """
        Create dummy activities for users based on their roles.

        Returns:
            str: Success message.
        """
        users = User.objects.all()
        general_activities = [
            "login",
            "profile",
            "course",
            "assignment",
            "project",
        ]
        school_admin_activities = ["career_pathway", "enrollment"]
        tutor_activities = ["upload", "add"]
        teacher_activities = ["studies", "report"]

        for user in users:
            # General activities for all users
            for activity in general_activities:
                for _ in range(3):  # Create 3 activities for each type
                    log_user_activity(user, activity)

            # Special activities for school_admins
            if user.role == "school_admin":
                for activity in school_admin_activities:
                    for _ in range(3):  # Create 3 activities for each type
                        log_user_activity(user, activity)

            # Special activities for tutors
            if user.role == "tutor":
                for activity in tutor_activities:
                    for _ in range(3):  # Create 3 activities for each type
                        log_user_activity(user, activity)
            # Special activities for tutors
            if user.role == "teacher":
                for activity in teacher_activities:
                    for _ in range(3):  # Create 3 activities for each type
                        log_user_activity(user, activity)

        return "Dummy data created successfully."
