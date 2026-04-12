""""This module is part of the course moudle, but have been seperated so trhe course module will not be too crowded.


"""

from decimal import Decimal
from datetime import timezone, datetime
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models.users import User
from core.models.media import Media
from support.models.mixims import TouchDatesMixim
from core.models.courses import Lesson, Module, Course, Qoutes


class TeacherCourseEnrollment(TouchDatesMixim):
    """
    Teachers courses enrollments is used to enroll a school(teachers) into a course or courses their pathway belongs to.
    The school is used inplace of `user`here because we different teachers could be in charge of this course, and any could resign. This school relationship, gives all teachers
    access to the courses.

    The unique togther is set to quote, course, etc to allow the school enroll for such course next term.
    """

    school = models.ForeignKey(
        "School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="school_teacher",
    )
    course = models.ForeignKey(
        "Course",
        on_delete=models.CASCADE,
        verbose_name=_("Course"),
        related_name="school_courses",
    )
    is_active = models.BooleanField(_("Is Active"), default=True)
    completed = models.BooleanField(_("Completed"), default=False)
    amount_paid = models.DecimalField(
        _("Amount Paid"), max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    payment_date = models.DateTimeField(_("Payment Date"), auto_now_add=True)
    # add the quote token
    quote = models.ForeignKey(
        "Qoutes", on_delete=models.CASCADE, verbose_name=_("Quote")
    )

    class Meta:
        unique_together = ("quote", "course")
        verbose_name = _("Teacher Course Enrollment")
        verbose_name_plural = _("Teacher Course Enrollments")

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"

    def get_progress_percentage(self):
        """Calculate the overall course progress"""
        completed_lessons = TeacherUserLessonProgress.objects.filter(
            school=self.school,
            lesson__module__course=self.course,
            status=TeacherUserLessonProgress.Status.COMPLETED,
        ).count()

        total_lessons = Lesson.objects.filter(module__course=self.course).count()

        return (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0


class TeacherUserLessonProgress(TouchDatesMixim):
    """
    Tracks individual lesson progress for each school teacher
    """

    class Status(models.TextChoices):
        """choices"""

        NOT_STARTED = "not_started", _("Not Started")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")

    school = models.ForeignKey(
        "School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="school_teacher_lesson",
    )
    lesson = models.ForeignKey(
        "Lesson",
        on_delete=models.CASCADE,
        verbose_name=_("Lesson"),
        related_name="school_lessons",
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
    quote = models.ForeignKey(
        "Qoutes",
        on_delete=models.CASCADE,
        verbose_name=_("Quote"),
        related_name="quote_lesson",
    )

    class Meta:
        """meta"""

        unique_together = ("quote", "lesson")
        verbose_name = _("Teacher Lesson Progress")
        verbose_name_plural = _("Teacher Lesson Progress")

    def __str__(self):
        return f"{self.user.email} - {self.lesson.title} - {self.status}"


class TeacherUserModuleProgress(TouchDatesMixim):
    """
    Tracks module completion status for each user
    """

    school = models.ForeignKey(
        "School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="school_teacher_modules",
    )
    module = models.ForeignKey(
        "Module",
        on_delete=models.CASCADE,
        verbose_name=_("Module"),
        related_name="school_modules",
    )
    is_current = models.BooleanField(default=False)
    completed = models.BooleanField(_("Completed"), default=False)
    completed_date = models.DateTimeField(_("Completion Date"), null=True, blank=True)
    started_on = models.DateTimeField(_("Started On"), null=True, blank=True)
    is_locked = models.BooleanField(_("Is Locked"), default=True)
    quote = models.ForeignKey(
        "Qoutes",
        on_delete=models.CASCADE,
        verbose_name=_("Quote"),
        related_name="quote_module",
    )

    class Meta:
        unique_together = ("quote", "module")
        verbose_name = _("Teacher Module Progress")
        verbose_name_plural = _("Teacher Module Progress")

    def __str__(self):
        return f"{self.user.email} - {self.module.title}"

    def get_progress_percentage(self):
        """Calculate the module progress percentage based on completed lessons"""
        total_lessons = Lesson.objects.filter(module=self.module).count()
        completed_lessons = TeacherUserLessonProgress.objects.filter(
            school=self.school,
            lesson__module=self.module,
            status=TeacherUserLessonProgress.Status.COMPLETED,
        ).count()

        # Calculate percentage, return 0 if no lessons exist
        return (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

    def get_progress_details(self):
        """Get detailed progress information for the module"""
        total_lessons = Lesson.objects.filter(module=self.module).count()
        lessons_progress = (
            TeacherUserLessonProgress.objects.filter(
                school=self.school,
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
            if progress["status"] == TeacherUserLessonProgress.Status.COMPLETED:
                progress_stats["completed_lessons"] = progress["count"]
            elif progress["status"] == TeacherUserLessonProgress.Status.IN_PROGRESS:
                progress_stats["in_progress_lessons"] = progress["count"]
            elif progress["status"] == TeacherUserLessonProgress.Status.NOT_STARTED:
                progress_stats["not_started_lessons"] = progress["count"]

        return progress_stats

    def update_progress(self):
        """Update module completion status based on lesson progress"""
        total_lessons = Lesson.objects.filter(module=self.module).count()
        completed_lessons = TeacherUserLessonProgress.objects.filter(
            school=self.school,
            lesson__module=self.module,
            status=TeacherUserLessonProgress.Status.COMPLETED,
        ).count()

        if total_lessons > 0 and total_lessons == completed_lessons:
            self.completed = True
            self.is_current = False
            self.completed_date = datetime.now()
            self.save()
