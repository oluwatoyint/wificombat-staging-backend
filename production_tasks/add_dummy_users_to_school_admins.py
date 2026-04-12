from django.contrib.auth import get_user_model
from faker import Faker
from production_tasks.base_task import BaseTask
from core.models.users import School

faker = Faker()
user_model = get_user_model()


class AttachDummyUserToAdminDummyUser(BaseTask):
    """
    A Prod task to create dummy users in the db
    """

    def handle(self):
        """
        Returns:
            None
        """

        # user this user a main_admin
        user = user.objects.filter(email="WifiCombatAcademy@gmail.com").first()
        if user:
            user.role = "main_admin"
            user.save()
        else:
            print("No admin user found to attach dummy users to.")

        # def generate_unique_email():
        #     while True:
        #         email = faker.email()
        #         if not user_model.objects.filter(email=email).exists():
        #             return email

        # # Attach dummy users to admin
        # school_admin = user_model.objects.filter(role="school_admin")
        # for admin in school_admin:

        #     # Attach school to 20 students and 10 teachers
        #     for j in range(5):
        #         student = user_model.objects.create_user(
        #             role="student",
        #             school=admin.school,
        #             email=generate_unique_email(),
        #             password=faker.password(),
        #             is_active=True,
        #         )
        #         student.save()
        #     for j in range(5):
        #         teacher = user_model.objects.create_user(
        #             role="teacher",
        #             school=admin.school,
        #             email=generate_unique_email(),
        #             password=faker.password(),
        #             is_active=True,
        #         )
        #         teacher.save()
