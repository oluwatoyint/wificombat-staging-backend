# core/utils.py
from datetime import timezone, datetime
from decimal import Decimal
from django.utils.timezone import now
from django.db.models import Sum, Count
from django.db import transaction
from core.models.users import TransactionHistory, Wallet
from core.models.courses import (
    CourseEnrollment,
    UserLessonProgress,
    UserModuleProgress,
    Module,
    Lesson,
    LessonQuiz,
    UserEarnedPoint,
)
from core.managers import utils


def create_transaction(
    user, wallet_id, amount, transaction_type, status, reference=None, description=None
):
    """Utility function to create a transaction for a user."""

    try:
        # Start a database transaction
        with transaction.atomic():
            # Get the wallet
            wallet = Wallet.objects.get(id=wallet_id)

            # Only update wallet balance for successful transactions
            if status == "successful":
                if transaction_type == "deposit":
                    wallet.balance += Decimal(amount)
                elif transaction_type == "withdrawal":
                    if wallet.balance < Decimal(amount):
                        raise ValueError("Insufficient funds in wallet")
                    wallet.balance -= Decimal(amount)
                wallet.save()

            # Create the transaction record
            transaction_record = TransactionHistory.objects.create(
                user=user,
                wallet=wallet,
                amount=Decimal(amount),
                transaction_type=transaction_type,
                status=status,
                reference=reference,
                description=description,
            )

            return transaction_record
    except Wallet.DoesNotExist:
        raise ValueError(f"Wallet with ID {wallet_id} does not exist")
    except Exception as e:
        raise ValueError(f"Error creating transaction: {str(e)}")


# class Enrollment:
#     """ "
#     Enroll a user to a particular course

#     """

#     def __init__(self, user, courses):
#         """init"""
#         self.user = user
#         self.courses = courses

#     def enroll_user(self):
#         """enroll the user"""
#         for course in self.courses:
#             try:
#                 # Check if the user is already enrolled in the course
#                 if CourseEnrollment.objects.filter(
#                     user=self.user, course=course
#                 ).exists():
#                     continue
#                     # raise ValueError(
#                     #     f"User is already enrolled in the course with id {course.id}"
#                     # )

#                 # Create the enrollment record
#                 enrollment = CourseEnrollment.objects.create(
#                     user=self.user, course=course, amount_paid=course.amount
#                 )
#                 # Initialize progress tracking for all lessons in the course
#                 index = 1
#                 for module in course.module_set.all():
#                     module_progress = UserModuleProgress.objects.create(
#                         user=self.user, module=module
#                     )
#                     for lesson in module.lesson_set.all():
#                         lesson_progress = UserLessonProgress.objects.create(
#                             user=self.user, lesson=lesson
#                         )
#                         # check if this is the first lesson, so it should be unlocked
#                         if index == 1:
#                             lesson_progress.is_locked = False
#                             module_progress.is_locked = False
#                             module_progress.save()
#                             lesson_progress.save()
#                         index += 1

#                 # create a user activity log
#                 utils.log_user_activity(
#                     user=self.user,
#                     activity_type="course",
#                     description=f"Enrolled in course: {course.title}",
#                 )

#             except Exception as err:
#                 raise ValueError(f"Error enrolling user to course: {str(err)}") from err


class Enrollment:
    """
    Enroll a user to a particular course.
    """

    def __init__(self, user, courses):
        """Initialize enrollment with user and courses."""
        self.user = user
        self.courses = courses

    def enroll_user(self):
        """Enroll the user in the courses."""
        for course in self.courses:
            try:
                # Skip if user is already enrolled in the course
                if CourseEnrollment.objects.filter(
                    user=self.user, course=course
                ).exists():
                    continue

                # Create the enrollment record
                enrollment = CourseEnrollment.objects.create(
                    user=self.user, course=course, amount_paid=course.amount
                )

                # Initialize progress tracking
                self.initialize_progress(course)

                # Log user activity
                utils.log_user_activity(
                    user=self.user,
                    activity_type="course",
                    description=f"Enrolled in course: {course.title}",
                )

            except Exception as err:
                raise ValueError(f"Error enrolling user to course: {str(err)}") from err

    def initialize_progress(self, course):
        """Initialize progress tracking for course modules and lessons."""
        for module_index, module in enumerate(
            course.module_set.all().order_by("order"), start=1
        ):
            # Determine if this module is the first (to unlock and set started_on)
            is_first_module = module_index == 1
            module_progress = UserModuleProgress.objects.create(
                user=self.user,
                module=module,
                is_locked=not is_first_module,
                started_on=now() if is_first_module else None,
                is_current=is_first_module,
            )

            for lesson_index, lesson in enumerate(
                module.lesson_set.all().order_by("order"), start=1
            ):
                # Determine if this lesson is the first in the first module (to unlock and set started_on)
                is_first_lesson = is_first_module and lesson_index == 1
                UserLessonProgress.objects.create(
                    user=self.user,
                    lesson=lesson,
                    is_locked=not is_first_lesson,
                    started_on=now() if is_first_lesson else None,
                    is_current=is_first_lesson,
                    status="in_progress" if is_first_lesson else "not_started",
                )


def handle_lesson_completion(user, lesson, quiz_score):
    """
    Handle lesson completion when a quiz is submitted, marking the current lesson as complete
    and unlocking the next lesson if available.

    Args:
        user: User instance
        lesson: Lesson instance
        quiz_score: LessonQuizScore instance
    """
    with transaction.atomic():
        # Update current lesson progress
        user_lesson_progress = UserLessonProgress.objects.select_for_update().get(
            user=user, lesson=lesson
        )

        # Mark current lesson as completed
        user_lesson_progress.status = UserLessonProgress.Status.COMPLETED
        user_lesson_progress.completed_date = datetime.now()
        user_lesson_progress.is_current = False
        user_lesson_progress.save()

        # Find the next lesson in the same module
        next_lesson = (
            Lesson.objects.filter(module=lesson.module, order__gt=lesson.order)
            .order_by("order")
            .first()
        )
        print(f"Current lesson completed: {lesson.title}")

        if next_lesson:
            print(f"Next lesson found: {next_lesson.title}")
            # Get or create progress record for next lesson
            (
                next_lesson_progress,
                created,
            ) = UserLessonProgress.objects.select_for_update().get_or_create(
                user=user,
                lesson=next_lesson,
                defaults={
                    "status": UserLessonProgress.Status.IN_PROGRESS,
                    "is_locked": False,  # Unlock the next lesson
                    "is_current": True,  # Mark as current lesson
                    "started_on": datetime.now(),
                },
            )

            if not created:
                print(f"Next lesson progress already exists for {next_lesson.title}")
                # If the progress record already existed, update it
                next_lesson_progress.is_locked = False
                next_lesson_progress.is_current = True
                next_lesson_progress.status = UserLessonProgress.Status.IN_PROGRESS
                next_lesson_progress.save()


def handle_module_completion(user, module):
    """
    Handle module completion when a user completes all lessons in a module.

    Args:
        user: User instance
        module: Module instance
    """
    # Update module progress
    module_progress = UserModuleProgress.objects.select_for_update().get(
        user=user, module=module
    )
    module_progress.update_progress()

    # Find next module in the course
    next_module = (
        Module.objects.filter(
            course=module.course,
            order__gt=module.order,
        )
        .order_by("order")
        .first()
    )
    print(f"Current module completed: {module.title}")

    if next_module:
        print(f"Next module found: {next_module.title}")
        (
            next_module_progress,
            _,
        ) = UserModuleProgress.objects.select_for_update().get_or_create(
            user=user,
            module=next_module,
            defaults={
                "is_locked": False,
                "is_current": True,
                "started_on": datetime.now(),
            },
        )
        next_module_progress.is_locked = False
        next_module_progress.is_current = True
        next_module_progress.save()
        print(f"Next module progress created or retrieved for {next_module.title}")


from django.db.models import Sum, Count


def handle_quiz_submission_earn_point(user, lesson, quiz_score, time_spent):
    """
    Compute the points earned by the user based on quiz scores and time spent.
    """
    with transaction.atomic():
        # Get the total allocated time and the total number of quizzes for the lesson
        lesson_quiz_summary = LessonQuiz.objects.filter(lesson=lesson).aggregate(
            total_allocated_time=Sum("allocated_time"), total_quizzes=Count("id")
        )

        total_allocated_time = lesson_quiz_summary["total_allocated_time"] or 0
        total_quizzes = lesson_quiz_summary["total_quizzes"] or 0

        point_earned = 0
        # Compute the points earned
        if total_quizzes > 0:
            no_of_correct_answers = (quiz_score / 100) * total_quizzes
            point_earned += Decimal((no_of_correct_answers / total_quizzes) * 100)
        point_earned += (Decimal(time_spent) / total_allocated_time) * 100

        UserEarnedPoint.objects.create(
            user=user,
            points=point_earned,
            course=lesson.module.course,
            point_type=UserEarnedPoint.PointType.QUIZ_SUBMITTED,
        )
