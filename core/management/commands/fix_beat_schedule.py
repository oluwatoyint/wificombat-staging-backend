from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule

class Command(BaseCommand):
    help = "Fix Celery beat schedule - remove old tasks and add correct ones"

    def handle(self, *args, **kwargs):
        # Delete all existing periodic tasks
        PeriodicTask.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Deleted all old periodic tasks"))

        # Create correct crontab schedule - midnight daily
        schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=0,
            minute=0,
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )

        # Create correct periodic task
        PeriodicTask.objects.create(
            crontab=schedule,
            name="run-daily-streak",
            task="core.tasks.run_daily_streak_recording",
        )
        self.stdout.write(self.style.SUCCESS("Created correct periodic task!"))
