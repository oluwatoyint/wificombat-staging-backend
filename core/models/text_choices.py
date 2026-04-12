from django.db import models
from django.utils.translation import gettext_lazy as _


class ClassLevel(models.TextChoices):
    """Choices for class levels"""

    PRIMARY_1 = "primary_1", "Primary 1"
    PRIMARY_2 = "primary_2", "Primary 2"
    PRIMARY_3 = "primary_3", "Primary 3"
    PRIMARY_4 = "primary_4", "Primary 4"
    PRIMARY_5 = "primary_5", "Primary 5"
    PRIMARY_6 = "primary_6", "Primary 6"
    JSS_1_YEAR_7 = "jss_1_year_7", "JSS 1/Year 7"
    JSS_2_YEAR_8 = "jss_2_year_8", "JSS 2/Year 8"
    JSS_3_YEAR_9 = "jss_3_year_9", "JSS 3/Year 9"
    SSS_1_YEAR_10 = "sss_1_year_10", "SSS 1/Year 10"
    SSS_2_YEAR_11 = "sss_2_year_11", "SSS 2/Year 11"
    SSS_3_YEAR_12 = "sss_3_year_12", "SSS 3/Year 12 (Level 1)"
    LEVEL_A = "level_a", "Level A"


class Level(models.TextChoices):
    # Beginner Levels
    LEVEL_1 = "1", _("Level 1 (Beginner: pri 1 - 3)")
    LEVEL_2 = "2", _("Level 2 (Beginner: pri 4)")
    LEVEL_3 = "3", _("Level 3 (Beginner: pri 5 - 6)")

    # Intermediate Levels
    LEVEL_4 = "4", _("Level 4 (Intermediate: Jss 1 - 2)")
    LEVEL_5 = "5", _("Level 5 (Intermediate: Jss 3)")

    # Advanced Levels
    LEVEL_6 = "6", _("Level 6 (Advanced: SS1)")
    LEVEL_7 = "7", _("Level 7 (Advanced: SS2)")


class PortfolioContentType(models.TextChoices):
    """Choices for portfolio content types"""

    # valid lists are project, competition, techpreneurship, other
    PROJECT = "project", _("Project")
    COMPETITION = "competition", _("Competition")
    TECHPRENEURSHIP = "techpreneurship", _("Tech Preneurship")
    OTHER = "other", _("Other")


class LibraryContentType(models.TextChoices):
    """Choices for library content types"""

    # valid lists are book, video, audio, other
    BOOK = "book", _("Book")
    VIDEO = "video", _("Video")
    AUDIO = "audio", _("Audio")
    SLIDE = "slide", _("Slide")
    OTHER = "other", _("Other")
