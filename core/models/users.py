import uuid, string, random
from decimal import Decimal
from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext as _
from core.managers.managers import UserManager
from support.models.mixims import TouchDatesMixim, SoftDeleteModel
from core.models.media import Media
from support.helpers import generate_random_token
from .text_choices import ClassLevel


class School(TouchDatesMixim):
    """School model"""

    name = models.CharField(max_length=255)
    school_type = models.CharField(max_length=255, null=True, blank=True)
    school_website = models.CharField(max_length=255, null=True, blank=True)
    school_phone = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"School: {self.name}"


class User(AbstractBaseUser, PermissionsMixin, TouchDatesMixim, SoftDeleteModel):
    """User model"""

    class Roles(models.TextChoices):
        USER = "user", "user"
        STUDENT = "student", "student"
        TEACHER = "teacher", "teacher"
        TUTOR = "tutor", "tutor"
        SCHOOL_ADMIN = (
            "school_admin",
            "school_admin",
        )
        MAIN_ADMIN = "main_admin", "main_admin"

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    profile_pic = models.ForeignKey(
        Media, on_delete=models.SET_NULL, null=True, blank=True
    )
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)

    bio = models.CharField(max_length=255, null=True, blank=True)
    sex = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=(
            ("male", "Male"),
            ("female", "Female"),
        ),
    )
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.USER,
        help_text="User's role in the system",
    )
    age = models.PositiveIntegerField(null=True, blank=True)
    no_student_you_teach = models.PositiveIntegerField(null=True, blank=True, default=0)
    interest = models.CharField(max_length=255, null=True, blank=True)
    _class = models.CharField(
        max_length=255, null=True, blank=True, choices=ClassLevel.choices
    )
    country = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    street = models.CharField(max_length=255, null=True, blank=True)
    zipcode = models.CharField(max_length=255, null=True, blank=True)
    teacherId = models.CharField(max_length=255, null=True, blank=True)
    current_stage = models.CharField(max_length=255, null=True, blank=True)
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    school_type = models.CharField(max_length=255, null=True, blank=True)

    USERNAME_FIELD = "email"

    objects = UserManager()

    def __str__(self):
        """str method"""
        return f"{self.email}"

    def save(self, *args, **kwargs):
        """Override save method to set staff and superuser flags based on role"""
        role_permissions = {
            "main_admin": (True, True),
            "tutor": (True, False),
        }

        if self.role:
            self.is_staff, self.is_superuser = role_permissions.get(
                self.role, (False, False)
            )
        if self.is_superuser:
            self.role = "main_admin"

        super().save(*args, **kwargs)

    @property
    def user_interests(self):
        """Return a list of interests. If no interests, return an empty list."""
        interests = self.interests.all()  # Use the correct related_name
        return [interest.name for interest in interests]


class AssignedClass(TouchDatesMixim):
    """Record the class a teacher is assigned to teach"""

    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="classes_taught"
    )
    class_name = models.CharField(max_length=50, choices=ClassLevel.choices)
    school = models.ForeignKey(School, on_delete=models.CASCADE)


class Otp(TouchDatesMixim):
    """
    Model for handling One-Time Passwords (OTP) with enhanced security and validation.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otp"
    )
    token = models.CharField(
        max_length=4, null=True, blank=True, help_text="6-digit OTP token"
    )
    expiration = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when the OTP expires"
    )

    def save(self, *args, **kwargs):
        """Override save to handle OTP generation and expiration"""
        if not self.token:
            self.expiration = timezone.now() + timedelta(minutes=10)
            self.token = generate_random_token()

        super().save(*args, **kwargs)

    def is_valid(self):
        """
        Check if OTP is still valid

        Returns:
            bool: True if OTP is valid (and matches provided token if given)

        """
        self.clean()  # Run validation checks

        now = timezone.now()
        is_expired = now >= self.expiration

        if is_expired:
            return False

        return True

    def refresh(self):
        """Generate a new OTP token and reset related fields"""
        self.token = generate_random_token()
        self.expiration = timezone.now() + timedelta(minutes=10)
        self.save()

    def __str__(self):
        return f"OTP for {self.user.email}"

    class Meta:
        """otp meta class"""

        verbose_name = "OTP"
        verbose_name_plural = "OTPs"


class UserActivity(TouchDatesMixim):
    ACTIVITY_CHOICES = [
        ("login", "Login"),
        ("profile", "Profile"),
        ("course", "Course"),
        ("assignment", "Assignment"),
        ("project", "Project"),
        ("enrollment", "Enrollment"),
        ("career_pathway", "Career Pathway"),
        ("report", "Report"),
        ("studies", "Studies"),
        ("upload", "Upload"),
        ("add", "Add"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.full_name} - {self.activity_type} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class Wallet(TouchDatesMixim):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    def __str__(self):
        return f"Wallet for {self.user.email}- Balance: {self.balance}"


class TransactionHistory(TouchDatesMixim):
    """
    Model for tracking all wallet transactions including deposits, withdrawals,
    and purchase.
    """

    TRANSACTION_TYPE_CHOICES = (
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
        ("purchase", "Purchase"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text=_("User who initiated the transaction"),
    )
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
    )
    reference = models.CharField(
        max_length=100, unique=True, help_text=_("Unique transaction reference")
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Transaction History")
        verbose_name_plural = _("Transaction Histories")

    def __str__(self):
        return f"{self.reference} - {self.user.email} - {self.amount}"


class Interest(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="interests")

    def __str__(self):
        return self.name
