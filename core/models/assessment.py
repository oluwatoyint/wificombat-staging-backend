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
from core.models.courses import CoursePathWay


class DetermineCareerInterest(TouchDatesMixim):
    """
    This model is used to determine the career path of a user based on their interests and skills.
    It includes fields for the user's ID, the type of content (portfolio or library), and the content ID.
    """

    AGE_GROUP_CHOICES = [
        ("5-7", "5-7"),
        ("8-10", "8-10"),
        ("11-14", "11-14"),
        ("15-18", "15-18"),
    ]
    question_type = models.CharField(
        _("Question Type"),
        max_length=50,
        choices=[
            ("determine_interest", "Determine Interest"),
            ("determine_interest_level", "Determine Interest Level"),
        ],
        default="determine_interest",
    )
    pathway = models.ForeignKey(
        CoursePathWay,
        on_delete=models.CASCADE,
        related_name="career_interest_pathway",
        verbose_name=_("Course Pathway"),
        null=True,
        blank=True,
    )
    age_grp = models.CharField(_("Age Group"), max_length=10, choices=AGE_GROUP_CHOICES)
    qus = models.TextField(_("Question"))
    options = models.JSONField(_("Options"), default=dict)
    correct_answer = models.CharField(
        _("Correct Answer"), max_length=10, null=True, blank=True
    )

    class Meta:
        verbose_name = _("Determine Career Interest")
        verbose_name_plural = _("Determine Career Interests")
