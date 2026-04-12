from django.contrib.auth import get_user_model
from faker import Faker


faker = Faker()
User = get_user_model()


def generate_unique_email():
    while True:
        email = faker.email()
        if not User.objects.filter(email=email).exists():
            return email


def create_n_user(n=1, role="user", school=None):
    """
    Creates n users with given role in the database.
    """
    users = []
    for _ in range(n):
        user = User.objects.create_user(
            email=generate_unique_email(),
            password=faker.password(),
            school=school,
            is_active=True,
            role=role,
        )
        user.save()
        users.append(user)
    return users
