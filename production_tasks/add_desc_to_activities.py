from django.contrib.auth import get_user_model
from faker import Faker
from production_tasks.base_task import BaseTask
from core.managers.utils import log_user_activity
from core.models.users import UserActivity

faker = Faker()
User = get_user_model()


class AddDescToDummyUserActivities(BaseTask):
    """
    A Prod task to create dummy users' activities in the database.
    """

    def handle(self):
        """
        Add description to dummy activities for users.

        Returns:
            str: Success message.
        """
        # Fetch activities with no description"

        activities = UserActivity.objects.filter(description=None)

        for activity in activities:
            activity.description = faker.text(max_nb_chars=10)
            activity.save()

        return "Dummy data created successfully."
