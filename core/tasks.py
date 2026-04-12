from datetime import datetime
import json
import logging
from celery import shared_task
from core.task_manager.course import record_daily_streak
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from support.helpers import sendMail

logger = logging.getLogger(__name__)


@shared_task
def run_daily_streak_recording():
    """
    Task to record daily streaks for all users.
    This task will run at midnight every day.
    """
    record_daily_streak()


@shared_task
def send_bulk_token_emails(email_data):
    logger.info(email_data)
    for data in email_data:
        sendMail(
            subject=f"Course onboarding token",
            recipient_list=data["email"],
            template="course_token.html",
            context={
                "email": data["email"],
                "pathway_title": data["pathway_title"],
                "token": data["token"],
                "expiry": data["expiry"],
                "term": data["term"],
            },
        )

    logger.info(f"Bulk token emails sent successfully: {len(email_data)}")
