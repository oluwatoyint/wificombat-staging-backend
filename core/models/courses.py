from decimal import Decimal
import uuid
from datetime import timezone, datetime
import random
import string
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.models.users import User
from core.models.media import Media
from support.models.mixims import TouchDatesMixim
from .text_choices import ClassLevel, Level, PortfolioContentType, LibraryContentType


class Stage(models.TextChoices):
    Beginner = "beginner", _("Beginner")
    Intermediate = "intermediate", _("Intermediate")
    Advance = "advance", _("Advanced")


class BaseContent(TouchDatesMixim):
    """
    Base abstract model for content-related models containing common fields.

    Fields:
        title: The name/header of the content
        description: Detailed explanation of the content
        cover_image: Optional visual representation
    """

    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"))
    cover_image = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Cover Image"),
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class BaseAssessment(TouchDatesMixim):
    """
    Base abstract model for assessment-related models (assignments, projects, etc.).

    Fields:
        title: Name of the assessment
        description: Detailed instructions
        grading_description: Explanation of grading criteria
        is_locked: Access control flag indicating if the assessment is available
    """

    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"))
    grading_description = models.TextField(_("Grading Description"))
    is_locked = models.BooleanField(_("Is Locked"), default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class BaseResponse(TouchDatesMixim):
    """
    Base abstract model for user responses to assessments.

    Fields:
        user: The student submitting the response
        response: Text content of the submission
        attachment: Optional file attachment
        score: Numerical grade for the submission
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    response = models.TextField(_("Response"))
    attachment = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Attachment"),
    )
    score = models.DecimalField(
        _("Score"), max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    feedback = models.TextField(_("Feedback"), null=True, blank=True)

    class Meta:
        abstract = True


class CoursePathWay(BaseContent):
    """
    Represents a collection of related courses forming a learning path.
    """

    pass


class Course(BaseContent):
    """
    Represents an individual course within a pathway.

    Fields:
        level: Difficulty level of the course
        stage: Current phase/stage of the course
        course_pathway: Parent pathway this course belongs to
        amount: Cost of the course
    """

    level = models.CharField(_("Level"), max_length=100, choices=Level.choices)
    stage = models.CharField(_("Stage"), max_length=100, choices=Stage.choices)
    course_pathway = models.ForeignKey(
        CoursePathWay, on_delete=models.CASCADE, verbose_name=_("Course Pathway")
    )
    amount = models.DecimalField(
        _("Amount"), max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Instrusctor"),
        null=True,
        blank=True,
    )
    badge_icon = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="course_badge",
    )
    term = models.CharField(max_length=100, null=True, blank=True)
    intro_video = models.TextField(_("Intro Video"), null=True, blank=True)

    def user_course_progress(self, user):
        course_enrollment = CourseEnrollment.objects.filter(
            course=self, user=user
        ).first()
        if course_enrollment:
            return course_enrollment.get_progress_percentage()
        return 0.00

    def course_module_count(self):
        return Module.objects.filter(course=self).count()

    def course_lesson_count(self):
        return Lesson.objects.filter(module__course=self).count()

    def user_current_course_module_and_lesson(self, user):
        current_module = UserModuleProgress.objects.filter(
            user=user, module__course=self, is_current=True
        ).first()
        if current_module:
            current_lesson = UserLessonProgress.objects.filter(
                lesson__module=current_module.module, is_current=True, user=user
            ).first()
            if current_lesson:
                return {
                    "current_module": current_module.module.title,
                    "current_lesson": current_lesson.lesson.title,
                }
        return {
            "current_module": None,
            "current_lesson": None,
        }


class CourseProject(BaseAssessment):
    """
    Represents a project assignment for an entire course.

    Fields:
        course: Associated course
        transcript: Detailed project instructions/transcript
        video_embed: Embedded video instructions if any
    """

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, verbose_name=_("Course")
    )
    transcript = models.TextField(_("Transcript"))
    video_embed = models.TextField(_("Video Embed"))


class Module(BaseContent):
    """
    Represents a section/unit within a course.

    Fields:
        course: Parent course
        learning_outcome: Expected learning results
        objectives: Specific goals of the module
    """

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, verbose_name=_("Course")
    )
    learning_outcome = models.TextField(_("Learning Outcome"))
    objectives = models.TextField(_("Objectives"))
    order = models.PositiveIntegerField(_("Order"), default=1)
    badge_icon = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="module_badge",
    )

    def __str__(self):
        return f"Cource: {self.course.title} - Module: {self.title}"

    class Meta:
        # add unique togther
        ordering = ["order"]

    @property
    def total_lessons(self):
        return self.lesson_set.count()

    @property
    def total_quizzes(self):
        # Access quizzes through the lessons of this module.
        return LessonQuiz.objects.filter(lesson__module=self).count()

    @property
    def total_assignments(self):
        return self.assignment_set.count()

    def module_progress_percentage(self, user):
        progress = UserModuleProgress.objects.filter(module=self, user=user).first()
        if progress:
            return progress.get_progress_percentage()

    def is_unlocked_for_user(self, user):
        user_module = UserModuleProgress.objects.filter(module=self, user=user).first()
        if user_module:
            return user_module.is_locked is False
        return False

    def has_submitted_assignment(self, user):
        user_assignment = ModuleAssignmentResponse.objects.filter(
            assignment__module=self, user=user
        ).exists()
        return user_assignment

    # def save(self, *args, **kwargs):
    #     # If the module is newly created, set its order based on the number of existing modules in the same course
    #     if not self.pk:  # Check if the object is being created (not updated)
    #         last_module = (
    #             Module.objects.filter(course=self.course).order_by("-order").first()
    #         )
    #         self.order = (last_module.order + 1) if last_module else 1
    #     super().save(*args, **kwargs)


class Assignment(BaseAssessment):
    """
    Represents a module-level assignment.

    Fields:
        module: Parent module
    """

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, verbose_name=_("Module")
    )


class Lesson(BaseContent):
    """
    Represents an individual lesson within a module.

    Fields:
        module: Parent module
        transcript: Text content of the lesson
        note: Additional notes/resources
        video_embed: Embedded video content
        order: Sequence number of the lesson
        is_locked: Access control flag
    """

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, verbose_name=_("Module")
    )
    transcript = models.TextField(_("Transcript"))
    note = models.TextField(_("Note"))
    video_embed = models.TextField(_("Video Embed"))
    order = models.PositiveIntegerField(_("Order"))
    is_locked = models.BooleanField(_("Is Locked"), default=True)

    def is_unlocked_for_user(self, user):
        user_lesson = UserLessonProgress.objects.filter(lesson=self, user=user).first()
        if user_lesson:
            return user_lesson.is_locked is False
        return False

    def has_completed_lesson(self, user):
        user_lesson = UserLessonProgress.objects.filter(lesson=self, user=user).first()
        if user_lesson:
            return user_lesson.completed_date is not None
        return False

    def has_taken_quiz(self, user):
        user_quiz = LessonQuizScore.objects.filter(lesson=self, user=user).exists()
        return user_quiz

    def __str__(self):
        return f"Course: {self.module.course.title} - Module: {self.module.title} - Lesson: {self.title} - Order: {self.order}"

    # class Meta:
    #     # add unique togther
    #     unique_together = (("module", "order"),)


class LessonQuiz(TouchDatesMixim):
    """
    Represents a quiz question within a lesson.
    """

    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", _("Multiple Choice")
        MULTIPLE_IMAGE = "multiple_image", _("Multiple Image")
        TRUE_FALSE = "true_false", _("True or False")
        FILL_IN_BLANK = "fill_in_blank", _("Fill in the Blank")
        CHECK_BOX = "check_box", _("Check Box")
        SHORT_ANSWER = "short_answer", _("Short Answer")

    type = models.CharField(
        _("Question Type"), max_length=20, choices=QuestionType.choices
    )
    question = models.CharField(_("Question"), max_length=255)
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, verbose_name=_("Lesson")
    )
    allocated_time = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.30")
    )
    correct_answer = models.CharField(_("Correct Answer"), max_length=255)

    def __str__(self):
        return self.question


class LessonQuizOption(TouchDatesMixim):
    """
    Represents an answer option for a quiz question.
    """

    class OPTIONLABEL(models.TextChoices):
        A = "a", _("A")
        B = "b", _("B")
        C = "c", _("C")
        D = "d", _("D")
        E = "e", _("E")

    lesson_quiz = models.ForeignKey(
        LessonQuiz, on_delete=models.CASCADE, verbose_name=_("Lesson Quiz")
    )
    text_option = models.CharField(
        _("Text Option"), max_length=255, null=True, blank=True
    )
    option_label = models.CharField(
        _("Option label"),
        max_length=2,
        null=True,
        blank=True,
        choices=OPTIONLABEL.choices,
    )
    image_option = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Image Option"),
    )

    def __str__(self):
        return self.text_option

    class Meta:
        # add unique togther
        unique_together = (("lesson_quiz", "option_label"),)
        ordering = ["lesson_quiz", "option_label"]
        verbose_name = _("Lesson Quiz Option")
        verbose_name_plural = _("Lesson Quiz Options")


class LessonQuizScore(TouchDatesMixim):
    """
    Records a user's score for a lesson quiz.
    """

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, verbose_name=_("Lesson")
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    score = models.DecimalField(
        _("Score"), max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    def __str__(self):
        return f"User: {self.user.email}, Lesson: {self.lesson.title}"


class ModuleAssignmentResponse(BaseResponse):
    """
    Records a user's response to a module assignment.
    """

    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, verbose_name=_("Assignment")
    )

    def __str__(self):
        return f"User: {self.user.email}, Assignment: {self.assignment.title}"


class CourseProjectResponse(BaseResponse):
    """
    Records a user's response to a course project.
    """

    project = models.ForeignKey(
        CourseProject, on_delete=models.CASCADE, verbose_name=_("Project")
    )

    def __str__(self):
        return f"User: {self.user.email}, Project: {self.project.title}"


class Qoutes(TouchDatesMixim):
    """
    Records quotes for users with the following fields
    - quantity
    - qauntity_left
    - course_pathway
    - level
    - term
    - status

    """

    class Status(models.TextChoices):
        """choices"""

        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")
        PENDING = "pending", _("pending")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    quantity = models.PositiveIntegerField(default=0)
    quantity_left = models.PositiveIntegerField(default=0)
    course_pathway = models.ForeignKey(
        CoursePathWay, on_delete=models.CASCADE, verbose_name=_("Course Pathway")
    )
    class_name = models.CharField(max_length=100, choices=ClassLevel.choices)
    level = models.CharField(max_length=100, choices=Level.choices, default="1")
    term = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    is_paused = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    term_start = models.DateTimeField()
    term_end = models.DateTimeField()

    class Meta:
        verbose_name = _("Qoute")
        verbose_name_plural = _("Quotes")

    def check_and_deactivate(self):
        """
        Check if term_end is greater than today.
        If yes, deactivate the quote.
        """
        if self.term_end and self.term_end < datetime.now():
            self.is_active = False
            self.save()


class QouteToken(TouchDatesMixim):
    """
    Records tokens for users with the following fields
    - user (sch std the token was issued to)
    - qoute (related quote)
    - token (token to be used to unclock the course)
    - is_used (used status)

    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    qoute = models.ForeignKey(Qoutes, on_delete=models.CASCADE, verbose_name=_("Qoute"))
    token = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "qoute")
        verbose_name = _("Qoute Token")
        verbose_name_plural = _("Qoute Tokens")

    @staticmethod
    def generate_unique_code():
        """Generate a unique 5-character alphanumeric token."""
        length = 5
        characters = string.ascii_uppercase + string.digits
        while True:
            code = "".join(random.choices(characters, k=length))
            if not QouteToken.objects.filter(token=code).exists():
                return code

    def save(self, *args, **kwargs):
        """Override save method to generate token if not set."""
        if not self.token:
            self.token = QouteToken.generate_unique_code()
        super().save(*args, **kwargs)


class CourseEnrollment(TouchDatesMixim):
    """
    Tracks when a user purchases/enrolls in a course
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, verbose_name=_("Course")
    )
    is_active = models.BooleanField(_("Is Active"), default=True)
    completed = models.BooleanField(_("Completed"), default=False)
    amount_paid = models.DecimalField(
        _("Amount Paid"), max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    payment_date = models.DateTimeField(_("Payment Date"), auto_now_add=True)
    # add the quote token
    quote_token = models.ForeignKey(
        QouteToken,
        on_delete=models.CASCADE,
        verbose_name=_("Quote Token"),
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ("user", "course")
        verbose_name = _("Course Enrollment")
        verbose_name_plural = _("Course Enrollments")

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"

    def get_progress_percentage(self):
        """Calculate the overall course progress"""
        completed_lessons = UserLessonProgress.objects.filter(
            user=self.user,
            lesson__module__course=self.course,
            status=UserLessonProgress.Status.COMPLETED,
        ).count()

        total_lessons = Lesson.objects.filter(module__course=self.course).count()

        return (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0


class UserLessonProgress(TouchDatesMixim):
    """
    Tracks individual lesson progress for each user
    """

    class Status(models.TextChoices):
        """choices"""

        NOT_STARTED = "not_started", _("Not Started")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, verbose_name=_("Lesson")
    )
    status = models.CharField(
        _("Status"), max_length=20, choices=Status.choices, default=Status.NOT_STARTED
    )
    last_position = models.PositiveIntegerField(
        _("Last Video Position"), default=0
    )  # Track video progress in seconds
    completed_date = models.DateTimeField(_("Completion Date"), null=True, blank=True)
    started_on = models.DateTimeField(_("Started On"), null=True, blank=True)
    is_locked = models.BooleanField(_("Is Locked"), default=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        """meta"""

        unique_together = ("user", "lesson")
        verbose_name = _("User Lesson Progress")
        verbose_name_plural = _("User Lesson Progress")

    def __str__(self):
        return f"{self.user.email} -Module: {self.lesson.module.title} Lessom: {self.lesson.title} - {self.status} order: {self.lesson.order}"


class UserModuleProgress(TouchDatesMixim):
    """
    Tracks module completion status for each user
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, verbose_name=_("Module")
    )
    is_current = models.BooleanField(default=False)
    completed = models.BooleanField(_("Completed"), default=False)
    completed_date = models.DateTimeField(_("Completion Date"), null=True, blank=True)
    started_on = models.DateTimeField(_("Started On"), null=True, blank=True)
    is_locked = models.BooleanField(_("Is Locked"), default=True)

    class Meta:
        unique_together = ("user", "module")
        verbose_name = _("User Module Progress")
        verbose_name_plural = _("User Module Progress")

    def __str__(self):
        return f"{self.user.email} - {self.module.title} current: {self.is_current} completed: {self.completed}"

    def get_progress_percentage(self):
        """Calculate the module progress percentage based on completed lessons"""
        total_lessons = Lesson.objects.filter(module=self.module).count()
        completed_lessons = UserLessonProgress.objects.filter(
            user=self.user,
            lesson__module=self.module,
            status=UserLessonProgress.Status.COMPLETED,
        ).count()

        # Calculate percentage, return 0 if no lessons exist
        return (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

    def get_progress_details(self):
        """Get detailed progress information for the module"""
        total_lessons = Lesson.objects.filter(module=self.module).count()
        lessons_progress = (
            UserLessonProgress.objects.filter(
                user=self.user,
                lesson__module=self.module,
            )
            .values("status")
            .annotate(count=models.Count("status"))
        )

        # Convert the progress data into a dictionary
        progress_stats = {
            "total_lessons": total_lessons,
            "completed_lessons": 0,
            "in_progress_lessons": 0,
            "not_started_lessons": 0,
        }

        for progress in lessons_progress:
            if progress["status"] == UserLessonProgress.Status.COMPLETED:
                progress_stats["completed_lessons"] = progress["count"]
            elif progress["status"] == UserLessonProgress.Status.IN_PROGRESS:
                progress_stats["in_progress_lessons"] = progress["count"]
            elif progress["status"] == UserLessonProgress.Status.NOT_STARTED:
                progress_stats["not_started_lessons"] = progress["count"]

        return progress_stats

    def update_progress(self):
        """Update module completion status based on lesson progress"""
        self.completed = True
        self.is_current = False
        self.completed_date = datetime.now()
        self.save()
        # total_lessons = Lesson.objects.filter(module=self.module).count()
        # completed_lessons = UserLessonProgress.objects.filter(
        #     user=self.user,
        #     lesson__module=self.module,
        #     status=UserLessonProgress.Status.COMPLETED,
        # ).count()

        # if total_lessons > 0 and total_lessons == completed_lessons:
        #     self.completed = True
        #     self.is_current = False
        #     self.completed_date = datetime.now()
        #     self.save()


class CourseStreak(TouchDatesMixim):
    """
    Records the length of a streak for each user
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, verbose_name=_("Course")
    )
    streak_score = models.PositiveIntegerField(default=0)


class CourseRating(TouchDatesMixim):
    """
    Represents a rating given to a course by a user.
    Using OneToOne relationship to ensure one rating per course.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name=_("Course"),
        related_name="rating",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        related_name="course_rating",
    )

    score = models.DecimalField(
        _("Rating Score"),
        max_digits=2,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal("1.0")),
            MaxValueValidator(Decimal("5.0")),
        ],
    )

    feedback_text = models.TextField(_("Feedback"), blank=True, null=True)

    class Meta:
        verbose_name = _("Course Rating")
        verbose_name_plural = _("Course Ratings")
        unique_together = ["course", "user"]

    def __str__(self):
        return f"Rating for {self.course.title}: {self.score}"


class LessonRating(TouchDatesMixim):
    """
    Represents a rating for a specific lesson's audio and video quality.
    Uses a 5-star rating system.
    """

    class RatingStatus(models.TextChoices):
        BAD = "bad", _("Bad")
        VERY_BAD = "very_bad", _("Very Bad")
        GOOD = "good", _("Good")
        VERY_GOOD = "very_good", _("Very Good")

    class Section(models.TextChoices):
        VIDEO = "video", _("Video")
        AUDIO = "audio", _("Audio")
        # BOTH = "both", _("Both")

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, verbose_name=_("Lesson")
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    rating = models.DecimalField(
        _("Rating Score"),
        max_digits=2,
        decimal_places=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("Rating for lesson (1-5 stars)"),
    )

    rating_status = models.CharField(
        max_length=20, choices=RatingStatus.choices, null=True, blank=True
    )

    section = models.CharField(
        max_length=10, choices=Section.choices, null=True, blank=True
    )

    feedback_text = models.TextField(_("Feedback"), blank=True, null=True)

    class Meta:
        verbose_name = _("Lesson Rating")
        verbose_name_plural = _("Lesson Ratings")
        unique_together = ["lesson", "user"]

    def __str__(self):
        return f"Rating for {self.lesson} by {self.user.full_name}: {self.rating} stars"


class UserEarnedPoint(TouchDatesMixim):
    """
    Represents a user's daily activity points.
    """

    class PointType(models.TextChoices):
        """
        choices for lesson completed, assignment submitted, quiz submitted, daily activity, streak

        """

        LESSON_COMPLETED = "lesson_completed", _("Lesson Completed")
        MODULE_COMPLETED = "module_completed", _("Module Completed")
        COURSE_COMPLETED = "course_completed", _("Course Completed")
        ASSIGNMENT_SUBMITTED = "assignment_submitted", _("Assignment Submitted")
        QUIZ_SUBMITTED = "quiz_submitted", _("Quiz Submitted")
        DAILY_ACTIVITY = "daily_activity", _("Daily Activity")
        STREAK = "streak", _("Streak")
        # OTHER_ACTIVITY = "other_activity", _("Other Activity")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, verbose_name=_("Course")
    )
    points = models.PositiveIntegerField(default=0)
    point_type = models.CharField(
        max_length=20, choices=PointType.choices, verbose_name=_("Point Type")
    )


class Badge(TouchDatesMixim):
    """
    Represents a badge that can be earned by users.
    """

    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True, null=True)
    icon = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Icon"),
    )

    # Generic Foreign Key to link to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return self.name


class UserBadge(TouchDatesMixim):
    """
    Represents a badge earned by a user.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, verbose_name=_("Badge"))
    earned_date = models.DateTimeField(_("Earned Date"), auto_now_add=True)

    class Meta:
        unique_together = ("user", "badge")

    def __str__(self):
        return f"{self.user.email} - {self.badge.name}"


class Certificate(TouchDatesMixim):
    """
    Represents a certificate awarded to a user.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        verbose_name=_("Course"),
        null=True,
        blank=True,
    )
    certificate_file = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # add unique togther as user and course
    class Meta:
        verbose_name = _("Certificate")
        verbose_name_plural = _("Certificates")


class PortfolioContent(TouchDatesMixim):
    """
    Represents a portfolio content a user can upload.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"))
    content_type = models.CharField(
        _("Content Type"), max_length=255, choices=PortfolioContentType.choices
    )
    date = models.DateTimeField()
    link = models.URLField()
    team_members = models.CharField(max_length=500, null=True, blank=True)


class Flashcard(TouchDatesMixim):
    """
    Represents a flashcard within a module.

    Fields:
        module: Parent module
        question: The question on the flashcard
        answer: The answer to the question
    """

    module = models.ForeignKey(
        "Module", on_delete=models.CASCADE, verbose_name=_("Module")
    )
    question = models.CharField(_("Question"), max_length=255)
    answer = models.TextField(_("Answer"))

    class Meta:
        verbose_name = _("Flashcard")
        verbose_name_plural = _("Flashcards")

    def __str__(self):
        return self.question


class Library(TouchDatesMixim):
    """MOdels o store library contents"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    pathway = models.ForeignKey(
        CoursePathWay, on_delete=models.CASCADE, verbose_name=_("Pathway")
    )
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"))
    video_embed = models.TextField(_("Video Embed"), null=True, blank=True)
    media = models.ForeignKey(
        Media, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Media")
    )
    library_type = models.CharField(
        _("Library Type"), max_length=100, choices=LibraryContentType.choices
    )

    class Meta:
        verbose_name = _("Library")
        verbose_name_plural = _("Libraries")


class DiscountCode(TouchDatesMixim):
    """
    Represents a discount code for courses.
    """

    courses = models.ManyToManyField(
        Course, verbose_name=_("Courses"), related_name="discount_codes", blank=True
    )
    code = models.CharField(_("Code"), max_length=50, unique=True)
    percentage_off = models.DecimalField(
        _("Discount Value"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    start_date = models.DateTimeField(_("Expiration Date"), null=True, blank=True)
    end_date = models.DateTimeField(_("Expiration Date"), null=True, blank=True)
    max_uses = models.PositiveIntegerField(_("Max Uses"), default=1)
    used_count = models.PositiveIntegerField(_("Used Count"), default=0)
    is_active = models.BooleanField(_("Is Active"), default=True)

    # added method to check if user has used this code
    def has_user_used_code(self, user):
        return UsedDiscountCode.objects.filter(user=user, discount_code=self).exists()

    # method to check if a course is in the discount code
    def is_valid_for_course(self, course):
        return self.courses.filter(id=course.id).exists()


class UsedDiscountCode(TouchDatesMixim):
    """
    Represents a record of a discount code used by a user.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    discount_code = models.ForeignKey(
        DiscountCode, on_delete=models.CASCADE, verbose_name=_("Discount Code")
    )

    class Meta:
        unique_together = ("user", "discount_code")
        verbose_name = _("Used Discount Code")
        verbose_name_plural = _("Used Discount Codes")

    def __str__(self):
        return f"{self.user.email} - {self.discount_code.code}"
