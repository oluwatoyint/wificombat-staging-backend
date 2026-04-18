from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create staging superuser if not exists"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        email = "toyin.tejuoso@wificombatacademy.com"
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                password="WifiAdmin2024!",
                username="admin"
            )
            self.stdout.write("Superuser created successfully")
        else:
            self.stdout.write("Superuser already exists")