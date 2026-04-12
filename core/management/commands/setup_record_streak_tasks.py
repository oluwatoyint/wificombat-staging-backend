# courses/management/commands/setup_periodic_tasks.py
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.utils import timezone


class Command(BaseCommand):
    help = "Setup periodic tasks for the application"

    def handle(self, *args, **kwargs):
        # Create the schedule (midnight/12 AM)
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
            timezone=timezone.get_current_timezone_name(),
        )

        # Create the periodic task
        PeriodicTask.objects.get_or_create(
            name="Daily Streak Recording",
            task="core.tasks.run_daily_streak_recording",
            crontab=schedule,
            enabled=True,
        )

        self.stdout.write(self.style.SUCCESS("Successfully created periodic task"))
