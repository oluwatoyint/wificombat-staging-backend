from random import choice
from django.contrib.auth import get_user_model
from faker import Faker
from django.utils import timezone
from production_tasks.base_task import BaseTask
from core.models.media import Media

faker = Faker()
User = get_user_model()


class SeedProfilePicWithLastLogin(BaseTask):
    """Seed profile pics to all users"""

    def handle(self):
        """
        Fetch all users and seed profile pics.

        Returns:
            str: Success message.
        """
        users = User.objects.all()
        media_objects = Media.objects.filter(media_type="photo")

        if not media_objects:
            return "No media objects found to seed profile pictures."

        success_count = 0
        for user in users:
            try:
                user.profile_pic = choice(media_objects)
                # Generate timezone-aware datetime
                user.last_login = timezone.make_aware(faker.past_datetime(tzinfo=None))
                user.save()
                success_count += 1
            except Exception as e:
                print(f"Failed to update user {user.id}: {str(e)}")

        return f"Profile pics seeded successfully for {success_count} users."
