import logging
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.response import Response
from django.db.models import Q, Sum
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from api.controllers.permissions import IsSchoolAdmin
from django.contrib.auth import authenticate
from django.db.models import Q
from core.models.users import User, School, Otp, UserActivity
from core.models.courses import UserEarnedPoint, UserBadge
from django.conf import settings
from support import helpers, http
from api.serializers import users as user_serializer_module
from core.managers import utils
from support.helpers import StandardResultsSetPagination, send_notification

logger = logging.getLogger(__name__)


User = get_user_model()


class SchoolAPIView(APIView):
    serializer_class = user_serializer_module.SchoolSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Retrieve all schools"""
        schools = School.objects.all().order_by("name")
        # include filters
        q = request.query_params.get("name")
        if q:
            schools = schools.filter(name__icontains=q)
        serializer = self.serializer_class(schools, many=True)
        # include pagniation
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(schools, request)
        serializer = self.serializer_class(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class UserRegistration(APIView):
    """User registeration view"""

    serializer_class = user_serializer_module.UserSerializer
    school_serializer = user_serializer_module.SchoolSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Handles POST requests to register a new user.

        Validates the provided registration data, creates a new user, sets the user's password, and sends an activation
        email with a token. Returns a success response with the newly created user's data and authentication tokens.

        Args:
            request (Request): The HTTP request object containing the user registration data.

        Returns:
            Response: A success response with user data and authentication tokens, or a failure response if validation
                      errors occur.
        """

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            role = serializer.validated_data["role"]
            if role == "school_admin":
                # valid the school serializer
                school_serializer = self.school_serializer(data=request.data)
                if school_serializer.is_valid(raise_exception=True):
                    school = school_serializer.save()
                    serializer.validated_data["school"] = school
                else:
                    return http.failed_response(None, school_serializer.errors)
            new_user = serializer.save()
            new_user.set_password(serializer.validated_data["password"])
            new_user.save()
            token = Otp.objects.create(user=new_user)
            # send token to mail
            helpers.sendMail(
                subject="Activation code",
                template="activtation_token.html",
                recipient_list=new_user.email,
                context={"token": token.token},
            )
            # Create response and set cookies
            response = http.success_response(
                None,
                _(
                    "Registration successful. Activation token has been sent to your email."
                ),
                status.HTTP_201_CREATED,
            )
            return response

        return http.failed_response(None, serializer.errors)


class ResendActivationToken(APIView):
    """API view to resend activation token"""

    serializer_class = user_serializer_module.ResendActivationTokenSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Handles POST requests to resend the activation token.

        Validates the provided email, generates a new activation token, and sends it to the user's email.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data["email"]
            try:
                # Check if the user exists
                user = User.objects.get(email=email)

                # Check if the user is already active
                if user.is_active:
                    return http.failed_response(
                        None,
                        _("User is already active."),
                        status.HTTP_400_BAD_REQUEST,
                    )

                # Refresh the OTP
                token, created = Otp.objects.get_or_create(user=user)
                if not created:
                    token.refresh()

                # Send the new token via email
                helpers.sendMail(
                    subject="Activation code (Resent)",
                    template="activtation_token.html",
                    recipient_list=user.email,
                    context={"token": token.token},
                )

                return http.success_response(
                    None,
                    _("A new activation token has been sent to your email."),
                    status.HTTP_200_OK,
                )
            except User.DoesNotExist:
                # User not found
                return http.failed_response(
                    None,
                    _("No user found with this email."),
                    status.HTTP_400_BAD_REQUEST,
                )
        return http.failed_response(None, serializer.errors)


class VerifyToken(APIView):
    """API view to verify activation tokens"""

    serializer_class = user_serializer_module.VerifyTokenSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Handles POST requests to verify the activation token.

        Marks the user as active if the token is valid.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get("email")
            token = serializer.validated_data.get("token")

            try:
                # Fetch the user and their OTP
                user = User.objects.get(email=email)
                otp = Otp.objects.get(user=user, token=token)

                # Check if the token is valid
                if not otp.is_valid():
                    return http.failed_response(
                        None,
                        _("The token has expired. Please request a new one."),
                        status.HTTP_400_BAD_REQUEST,
                    )

                if user.is_active:
                    # reset password success message
                    message = "Your password has been successfully reset."
                else:
                    # Activate the user
                    user.is_active = True
                    user.current_stage = "unboarding"
                    user.save()
                    message = "Your account has been successfully activated."
                    # record the activity log
                    utils.log_user_activity(
                        user=user,
                        activity_type="profile",
                        description="User activated their account",
                    )
                    # get access token for the user

                # Delete the OTP as it's no longer needed
                otp.delete()
                # Create access token
                access_token = utils.get_tokens_for_user(user)
                serializer = user_serializer_module.UserListSerializer(
                    user, many=False, context={"request": request}
                )

                # Create response and set cookies
                response = http.success_response(
                    {
                        "user": serializer.data,
                        "token": access_token["access"],
                        "refresh": access_token["refresh"],
                    },
                    _(message),
                    status.HTTP_200_OK,
                )
                return response
            except User.DoesNotExist:
                return http.failed_response(
                    None,
                    _("No user found with this email."),
                    status.HTTP_404_NOT_FOUND,
                )
            except Otp.DoesNotExist:
                return http.failed_response(
                    None,
                    _("Invalid token."),
                    status.HTTP_400_BAD_REQUEST,
                )

        return http.failed_response(None, serializer.errors)


class AdminLoginView(APIView):
    """API view for user login"""

    serializer_class = user_serializer_module.LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Handle POST request to authenticate user and generate JWT tokens.

        Validates the user's email and credentials, generates JWT tokens if valid, and returns them
        in the response. Sets the tokens as cookies with HttpOnly flag.

        Args:
            request (Request): The request object containing the user's login credentials.

        Returns:
            Response: A response object with JWT tokens if login is successful, or an error message if not.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):

            # Authenticate user
            user = authenticate(
                email=request.data["email"], password=request.data["password"]
            )
            if not user:
                return http.failed_response(
                    None,
                    _("Invalid email or password."),
                    status.HTTP_400_BAD_REQUEST,
                )

            # Check if the user is a staff member
            if not user.is_staff:
                # Log unauthorized access attempt
                utils.log_user_activity(
                    user=user,
                    activity_type="login",
                    description=f"unauthorized_access.",
                )

                return http.failed_response(
                    None,
                    _("Access denied. Only staff members can log in."),
                    status.HTTP_403_FORBIDDEN,
                )

            # Generate JWT tokens
            token = utils.get_tokens_for_user(user)
            # check if fcm token was submitted
            if request.data.get("fcm_token"):
                # save fcm_token
                user.fcm_token = request.data["fcm_token"]
            # update user's last login
            user.last_login = timezone.now()
            user.save()

            serializer = user_serializer_module.UserListSerializer(
                user, many=False, context={"request": request}
            )
            # Create response and set cookies
            response = http.success_response(
                {
                    "user": serializer.data,
                    "token": token["access"],
                    "refresh": token["refresh"],
                },
                _("Login successful."),
                status.HTTP_200_OK,
            )
            response.set_cookie(
                key="refresh",
                value=token["refresh"],
                httponly=True,  # Set HttpOnly flag
            )
            response.set_cookie(
                key="access", value=token["access"], httponly=True  # Set HttpOnly flag
            )
            # record the activity log
            utils.log_user_activity(
                user=user,
                activity_type="login",
                description=f"User logged in.",
            )
            return response

        return http.failed_response(None, serializer.errors)


class LoginView(APIView):
    """API view for user login"""

    serializer_class = user_serializer_module.LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Handle POST request to authenticate user and generate JWT tokens.

        Validates the user's email and credentials, generates JWT tokens if valid, and returns them
        in the response. Sets the tokens as cookies with HttpOnly flag.

        Args:
            request (Request): The request object containing the user's login credentials.

        Returns:
            Response: A response object with JWT tokens if login is successful, or an error message if not.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):

            email = request.data.get("email")
            password = request.data.get("password")

            try:
                # Fetch the user by email
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return http.failed_response(None, _("Invalid email."))

            # Check if the user is active
            if not user.is_active:
                user_data = {
                    "id": user.id,
                    "email": user.email,
                    "username": user.full_name,
                    "is_active": user.is_active,
                }
                return http.failed_response(
                    user_data,
                    _(
                        "Your account is inactive. Please activate your account to log in."
                    ),
                    status.HTTP_403_FORBIDDEN,
                )

            # Validate the password
            if not user.check_password(password):
                return http.failed_response(None, _("Invalid email or password."))

            # Generate JWT tokens
            token = utils.get_tokens_for_user(user)
            # check if fcm token was submitted
            if request.data.get("fcm_token"):
                # save fcm_token
                user.fcm_token = request.data["fcm_token"]
            # update user's last login
            user.last_login = timezone.now()
            user.save()
            serializer = user_serializer_module.UserListSerializer(
                user, many=False, context={"request": request}
            )
            # Create response and set cookies
            response = http.success_response(
                {
                    "user": serializer.data,
                    "token": token["access"],
                    "refresh": token["refresh"],
                },
                _("Login successful"),
                status.HTTP_200_OK,
            )
            response.set_cookie(
                key="refresh",
                value=token["refresh"],
                httponly=True,  # Set HttpOnly flag
            )
            response.set_cookie(
                key="access", value=token["access"], httponly=True  # Set HttpOnly flag
            )
            # record the activity log
            utils.log_user_activity(
                user=user,
                activity_type="login",
                description=f"User logged in.",
            )
            return response

        return http.failed_response(None, serializer.errors)


class RequestPasswordReset(APIView):
    """API view to request a password reset email"""

    serializer_class = user_serializer_module.RequestPasswordResetSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Handles POST requests to request a password reset.

        Checks if the email exists in the database, generates a reset token, and sends a password reset email.

        Args:
            request (Request): The HTTP request object containing the email for password reset.

        Returns:
            Response: A success response indicating that the reset email has been sent.
        """
        email = request.data["email"]

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            token, created = Otp.objects.get_or_create(user=user)
            if not created:
                token.refresh()  # Refresh the OTP if it was not newly created.
            logger.info(token.token)
            # send token to mail
            helpers.sendMail(
                subject="Activation code",
                template="reset_token.html",
                recipient_list=user.email,
                context={"token": token.token},
            )

            return http.success_response(
                None,
                _("Password reset token has been sent to your email"),
                status.HTTP_200_OK,
            )
        return http.failed_response(
            None, _("The email address does not exist."), status.HTTP_404_NOT_FOUND
        )


class SetNewPasswordAPIView(APIView):
    """
    API view to handle setting a new password for the user.
    It validates the provided reset token, UID, and sets a new password.
    """

    serializer_class = user_serializer_module.SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Handle POST request to reset the user's password using a valid token and user ID.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data.get("password")
        token = serializer.validated_data.get("token")
        email = serializer.validated_data.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return http.failed_response(
                None, _("No user found with this email."), status.HTTP_404_NOT_FOUND
            )

        try:
            otp = Otp.objects.get(user=user, token=token)
            if not otp.is_valid():
                return http.failed_response(
                    None, _("Token has expired."), status.HTTP_400_BAD_REQUEST
                )
        except Otp.DoesNotExist:
            return http.failed_response(
                None, _("Invalid token."), status.HTTP_400_BAD_REQUEST
            )

        user.set_password(password)
        user.save()

        # Optionally, invalidate the OTP after successful password reset
        otp.delete()  # or mark as used depending on your requirements

        # reacord activity
        utils.log_user_activity(
            user=user,
            activity_type="profile",
            description=f"User reset their password",
        )

        return Response(
            {"success": True, "message": "Password reset successful."},
            status=status.HTTP_200_OK,
        )


class Profile(viewsets.ViewSet):
    """API for authenticated users to change their password from dashboard"""

    serializer_class = user_serializer_module.ChangePasswordInDashboardSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=["put"])
    def change_password_in_dashboard(self, request):
        """Post method"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_password = serializer.validated_data.get("current_password")
        new_password = serializer.validated_data.get("new_password")

        user = request.user

        if not user.check_password(current_password):
            return http.failed_response(
                None, _("Current password is incorrect."), status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        # reacord activity
        utils.log_user_activity(
            user=user,
            activity_type="profile",
            description=f"User changed their password",
        )

        return http.success_response(message=_("Password changed successfully."))

    @action(detail=False, methods=["put"])
    def update_profile(self, request):
        """Update user profile"""
        serializer = user_serializer_module.UpdateProfileSerializer(
            request.user, data=request.data, partial=True
        )
        interests = request.data.get("interests")
        print(interests, type(interests))
        if serializer.is_valid(raise_exception=True):
            # validate the
            if interests:
                interest_data = {"interests": interests}
                interest_serializer = user_serializer_module.UserInterestSerializer(
                    data=interest_data, context={"request": request}
                )
                if not interest_serializer.is_valid(raise_exception=True):
                    return http.failed_response(None, interest_serializer.errors)
                interest_serializer.save()
            user = serializer.save()
            if user.current_stage != "completed":
                user.current_stage = "completed"
                user.save()
            serializer = user_serializer_module.UserListSerializer(
                user, context={"request": request}
            )
            # record activity
            utils.log_user_activity(
                user=user,
                activity_type="profile",
                description=f"User updated their profile",
            )

            # Set the FCM token or default to an empty string
            fcm_token = user.fcm_token or ""

            send_notification(
                user_id=request.user.id,
                title="Profile Update",
                message="Your profile has been updated",
                fcm_token=fcm_token,
                _type="profile",
            )
            return http.success_response(data=serializer.data)
        return http.failed_response(None, serializer.errors)

    @action(detail=False, methods=["get"])
    def get_single_user_profile(self, request, user_id):
        """Get single user profile"""

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return http.failed_response(
                None, "User not found", status.HTTP_404_NOT_FOUND
            )
        serializer = user_serializer_module.ProfileSerializer(
            user, context={"request": request}
        )
        points = (
            UserEarnedPoint.objects.filter(user=user).aggregate(
                total_points=Sum("points")
            )["total_points"]
            or 0
        )
        data = serializer.data
        data["points"] = points
        return http.success_response(data=data)

    @action(detail=False, methods=["get"])
    def get_user_activities(self, request, user_id):
        """Get user activities"""
        activity_type = request.query_params.get("q")
        activities = UserActivity.objects.filter(user__id=user_id)
        if activity_type:
            activities = activities.filter(activity_type__icontains=activity_type)

        paginator = self.pagination_class()

        result_page = paginator.paginate_queryset(activities, request)
        serializer = user_serializer_module.UserActivitySerializer(
            result_page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    def recent_activities(self, request):
        """Get users recent activities"""
        search_query = request.query_params.get("q", "")
        activities = self.get_recent_activities(search_query)

        paginator = self.pagination_class()

        result_page = paginator.paginate_queryset(activities, request)
        serializer = user_serializer_module.RecentUserActivitySerializer(
            result_page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def get_recent_activities(self, search_query=None):
        activities = UserActivity.objects.select_related("user").order_by("-created_at")

        if search_query:
            activities = activities.filter(
                Q(description__icontains=search_query)
                | Q(activity_type__icontains=search_query)
                | Q(user__full_name__icontains=search_query)
            )

        activities = activities[:10]  # Limit to 10 most recent activities

        return activities
