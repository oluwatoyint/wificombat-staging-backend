from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils.translation import gettext as _
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from core.models.users import Otp, School, User, UserActivity, Interest
from api.serializers.media import MediaSerializer


class SchoolSerializer(serializers.ModelSerializer):
    """Serializer for School model"""

    class Meta:
        """School serializer meta class"""

        model = School
        fields = [
            "id",
            "name",
            "created_at",
            "updated_at",
            "school_type",
            "school_website",
            "school_phone",
        ]
        read_only_fields = ["created_at", "updated_at"]


class SchoolQuotesSerializer(serializers.ModelSerializer):
    """Serializer for School model"""

    last_request = serializers.DateTimeField(read_only=True)  # Include annotated field

    class Meta:
        """School serializer meta class"""

        model = School
        fields = [
            "id",
            "name",
            "created_at",
            "updated_at",
            "school_type",
            "school_website",
            "school_phone",
            "last_request",
        ]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        """Meta class"""

        model = User
        fields = [
            "email",
            "password",
            "school",
            "role",
            "age",
            "interest",
            "_class",
            "country",
            "current_stage",
            "teacherId",
        ]


class ReturnUserSerializer(serializers.ModelSerializer):

    class Meta:
        """Meta class"""

        model = User
        fields = [
            "id",
            "email",
            "school",
            "role",
            "age",
            "interest",
            "_class",
            "country",
            "current_stage",
            "teacherId",
            "created_at",
            "updated_at",
        ]


class AdminUpdateUserSerializer(serializers.ModelSerializer):
    """Serializer for updating a user's role or deactivating a user"""

    class Meta:
        """Meta class"""

        model = User
        fields = ["is_active", "role"]


class UserListSerializer(serializers.ModelSerializer):
    """Simplified User serializer for list views"""

    school = SchoolSerializer()
    profile_pic = MediaSerializer()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "first_name",
            "last_name",
            "street",
            "zipcode",
            "school_type",
            "phone",
            "date_of_birth",
            "bio",
            "sex",
            "role",
            "is_active",
            "school",
            "profile_pic",
            "age",
            # "interest",
            "_class",
            "country",
            "current_stage",
            "teacherId",
            "no_student_you_teach",
            "date_joined",
            "last_login",
            "created_at",
            "updated_at",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    """Simplified User serializer for list views"""

    school = SchoolSerializer()
    profile_pic = MediaSerializer()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "first_name",
            "last_name",
            "street",
            "zipcode",
            "school_type",
            "phone",
            "date_of_birth",
            "bio",
            "sex",
            "role",
            "is_active",
            "school",
            "profile_pic",
            "age",
            # "interest",
            "_class",
            "country",
            "current_stage",
            "teacherId",
            "user_interests",
            "no_student_you_teach",
            "date_joined",
            "last_login",
            "created_at",
            "updated_at",
        ]


class BasicUserInfoSerializer(serializers.ModelSerializer):
    """Basic User serializer for profile view"""

    profile_pic = MediaSerializer()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "first_name",
            "last_name",
            "role",
            "profile_pic",
        ]


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Update a users profile"""

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "first_name",
            "last_name",
            "phone",
            "date_of_birth",
            "bio",
            "school",
            "profile_pic",
            "age",
            # "interest",
            "_class",
            "country",
            "no_student_you_teach",
            "street",
            "zipcode",
            "school_type",
        ]


class ResendActivationTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ["email"]


class VerifyTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    token = serializers.CharField(max_length=4, required=True)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    fcm_token = serializers.CharField(max_length=255, required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )


class RequestPasswordResetSerializer(serializers.Serializer):

    email = serializers.EmailField(required=True)

    class Meta:
        fields = ["email"]


class SetNewPasswordSerializer(serializers.Serializer):
    """Set new password serializer"""

    password = serializers.CharField(max_length=255, write_only=True)
    token = serializers.CharField(max_length=4, required=True)
    email = serializers.EmailField(required=True)


class ChangePasswordInDashboardSerializer(serializers.Serializer):
    """change user password in dashboard"""

    current_password = serializers.CharField(max_length=255, write_only=True)
    new_password = serializers.CharField(max_length=255, write_only=True)


class UpdateProfile(serializers.ModelSerializer):
    """Update user profile serializer"""

    class Meta:
        model = User
        fields = ["full_name", "phone", "date_of_birth", "bio", "sex"]


class InterestSerializer(serializers.ModelSerializer):
    """Interest serializer"""

    class Meta:
        model = Interest
        fields = ["name"]


class UserInterestSerializer(serializers.Serializer):
    """Serializer for user interests"""

    interests = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
    )

    def validate_interests(self, value):
        """
        Validate that the list of interests is not empty and contains unique values.
        """
        if not value:
            raise serializers.ValidationError("At least one interest is required.")
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Interests must be unique.")
        return value

    def create(self, validated_data):
        """
        Create or retrieve Interest instances and associate them with the user.
        """
        user = self.context["request"].user
        interest_names = validated_data["interests"]

        # Create or retrieve Interest instances
        interests = []
        for name in interest_names:
            interest, created = Interest.objects.get_or_create(name=name, user=user)
            interests.append(interest)

        return interests

    def to_representation(self, instance):
        """
        Return the user's interests after creation.
        """
        return {"interests": [interest.name for interest in instance.interests.all()]}


class UserActivitySerializer(serializers.ModelSerializer):
    """User activity serializer"""

    class Meta:
        model = UserActivity
        fields = "__all__"


class RecentUserActivitySerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="user.role")
    formatted_date = serializers.SerializerMethodField()

    class Meta:
        model = UserActivity
        fields = [
            "activity_type",
            "description",
            "role",
            "formatted_date",
            "created_at",
            "updated_at",
        ]

    def get_formatted_date(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M")


class UpdateUserSerializer(serializers.ModelSerializer):
    """Update a users profile"""

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "first_name",
            "last_name",
            "phone",
            "date_of_birth",
            "bio",
            "school",
            "profile_pic",
            "age",
            "interest",
            "_class",
            "country",
            "no_student_you_teach",
            "street",
            "zipcode",
            "school_type",
            "is_active",
        ]
        read_only_fields = ["id", "school"]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
