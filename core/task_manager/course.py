import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from core.models.courses import (
    UserLessonProgress,
    UserModuleProgress,
    CourseEnrollment,
    CourseStreak,
    LessonQuizScore,
    UserEarnedPoint,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def calculate_daily_activity_score(user, enrollment, date):
    """
    Calculate a user's daily activity score for a specific course enrollment.
    Returns a score between 0 and 100.

    Args:
        user: User object
        enrollment: CourseEnrollment object
        date: Date to calculate activity for
    """
    day_start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
    day_end = timezone.make_aware(datetime.combine(date, datetime.max.time()))

    # Get completed lessons for the specified day
    completed_lessons = UserLessonProgress.objects.filter(
        user=user,
        lesson__module__course=enrollment.course,
        status=UserLessonProgress.Status.COMPLETED,
        completed_date__range=(day_start, day_end),
    ).count()

    # Get completed modules for the specified day
    completed_modules = UserModuleProgress.objects.filter(
        user=user,
        module__course=enrollment.course,
        completed=True,
        completed_date__range=(day_start, day_end),
    ).count()

    # Get quiz attempts for the specified day
    quiz_attempts = LessonQuizScore.objects.filter(
        user=user,
        lesson__module__course=enrollment.course,
        created_at__range=(day_start, day_end),
    ).count()

    # Calculate score based on activity
    score = 0

    # Complete module completion (highest score)
    if completed_modules > 0:
        score += 100
        return score

    # Partial progress scoring
    if completed_lessons > 0:
        score += min(completed_lessons * 30, 60)  # Up to 60 points for lessons

    if quiz_attempts > 0:
        score += min(quiz_attempts * 20, 40)  # Up to 40 points for quizzes

    return min(score, 100)  # Cap at 100


def update_streak(user, course, activity_score):
    """
    Update the streak record with the new activity score.
    Never resets the streak, only increments the streak_score by the activity.

    Args:
        user: User object
        course: Course object
        activity_score: Integer score for the day's activity
    """
    streak = CourseStreak.objects.create(
        user=user, course=course, streak_score=activity_score
    )

    # record point for the user
    UserEarnedPoint.objects.create(
        user=user,
        course=course,
        point_type=UserEarnedPoint.PointType.STREAK,
        point=activity_score,
    )

    return streak


def record_daily_streak():
    """
    Main task to record daily streaks for all active enrollments.
    Runs at midnight and processes the previous day's activity.
    """
    # Calculate yesterday's date
    yesterday = timezone.now().date() - timedelta(days=2)

    logger.info(f"Starting daily streak recording task for date: {yesterday}")

    try:
        # Get all enrollments (including inactive ones to record zeros)
        enrollments = CourseEnrollment.objects.filter(
            completed=False  # Only exclude completed courses
        ).select_related("user", "course")

        for enrollment in enrollments:
            try:
                # Check if a streak already exists for yesterday
                # Convert created_at to date for comparison
                streak_exists = CourseStreak.objects.filter(
                    user=enrollment.user,
                    course=enrollment.course,
                    created_at__date=yesterday,
                ).exists()

                if streak_exists:
                    logger.info(
                        f"Skipping streak record for user {enrollment.user.id} in course "
                        f"{enrollment.course.id} for {yesterday} - streak already exists"
                    )
                    continue

                # Calculate activity score for yesterday
                activity_score = calculate_daily_activity_score(
                    enrollment.user, enrollment, yesterday
                )

                # Update streak with the score (even if it's 0)
                streak = update_streak(
                    enrollment.user, enrollment.course, activity_score
                )

                logger.info(
                    f"Updated streak for user {enrollment.user.id} in course "
                    f"{enrollment.course.id} for {yesterday}: Score={activity_score}, "
                    f"Total Streak={streak.streak_score}"
                )

            except Exception as e:
                logger.error(
                    f"Error processing streak for enrollment {enrollment.id}: {str(e)}"
                )
                continue

    except Exception as e:
        logger.error(f"Error in daily streak recording task: {str(e)}")
        raise

    logger.info(f"Completed daily streak recording task for {yesterday}")
