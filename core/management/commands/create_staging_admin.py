from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create staging superuser if not exists"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        email = "toyin.tejuoso@wificombatacademy.com"
        self.stdout.write(f"Checking if user {email} exists...")
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                password="WifiAdmin2024!",
                username="toyin"
            )
            self.stdout.write(self.style.SUCCESS(f"Superuser {email} created successfully!"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser {email} already exists!"))
