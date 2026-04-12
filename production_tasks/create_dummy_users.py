from django.contrib.auth import get_user_model
from faker import Faker
from production_tasks.base_task import BaseTask
from core.models.users import School

faker = Faker()
user_model = get_user_model()


class CreateDummyUser(BaseTask):
    """
    A Prod task to create dummy users in the db
    """

    def handle(self):
        """
        Returns:
            None
        """

        def generate_unique_email():
            while True:
                email = faker.email()
                if not user_model.objects.filter(email=email).exists():
                    return email

        # Create 200 normal users
        for i in range(50):
            user = user_model.objects.create_user(
                email=generate_unique_email(),
                password=faker.password(),
                is_active=True,
                role="user",
            )
            user.save()

        for i in range(50):
            school = School.objects.create(name=faker.company())
            school.save()

            # Attach school to a school owner
            school_admin = user_model.objects.create_user(
                role="school_admin",
                school=school,
                email=generate_unique_email(),
                password=faker.password(),
                is_active=True,
            )
            school_admin.save()

            # Attach school to 20 students and 10 teachers
            for j in range(20):
                student = user_model.objects.create_user(
                    role="student",
                    school=school,
                    email=generate_unique_email(),
                    password=faker.password(),
                    is_active=True,
                )
                student.save()

            for j in range(10):
                teacher = user_model.objects.create_user(
                    role="teacher",
                    school=school,
                    email=generate_unique_email(),
                    password=faker.password(),
                    is_active=True,
                )
                teacher.save()

        return "Dummy data created successfully."


class CompleteUserProfile(BaseTask):
    """Add bio, phone and other to dummy user profile"""

    def handle(self):
        """
        Returns:
            None
        """

        # get all users
        users = user_model.objects.all()

        for user in users:
            if not user.bio and not user.phone and not user.full_name:
                user.bio = faker.text(max_nb_chars=100)
                user.phone = faker.phone_number()
                user.country = faker.country()
                user.state = faker.city()
                # add full name
                user.full_name = faker.name()
                user.interest = faker.catch_phrase()
                if user.role in ["user", "student"]:
                    user.age = faker.random_int(min=9, max=20)
                user.current_stage = "completed"
                # include teacher id if a teacher

                user.save()

        return "Dummy user profiles updated successfully."
