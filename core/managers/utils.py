from rest_framework_simplejwt.tokens import RefreshToken
from core.models.users import UserActivity


def get_tokens_for_user(user):
    """
    Generate and return the tokens for a user.

    Args:
        user (object): The user whose tokens are to be generated.

    Returns:
        dict: The tokens in the format {'refresh': 'token', 'access': 'token'}.
    """
    refresh = RefreshToken.for_user(user)

    # Add custom claims to both refresh and access tokens
    # Access token claims
    refresh.access_token["email"] = user.email
    refresh.access_token["full_name"] = user.full_name
    refresh.access_token["id"] = str(user.id)
    refresh.access_token["role"] = user.role

    # If you want the same claims in refresh token
    refresh["email"] = user.email
    refresh["full_name"] = user.full_name
    refresh["id"] = str(user.id)
    refresh["role"] = user.role

    # Return the same structure as before
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def log_user_activity(user, activity_type, description=None):
    """
    Logs a user's activity.

    :param user: User instance performing the activity.
    :param activity_type: Type of activity (must match one of the choices in ACTIVITY_CHOICES).
    :param description: Optional additional description about the activity.
    :return: The created UserActivity instance.
    """
    if not user:
        raise ValueError("User is required to log an activity.")

    if activity_type not in dict(UserActivity.ACTIVITY_CHOICES):
        raise ValueError(
            f"Invalid activity_type: {activity_type}. Must be one of {dict(UserActivity.ACTIVITY_CHOICES).keys()}."
        )

    return UserActivity.objects.create(
        user=user, activity_type=activity_type, description=description
    )
