import logging, json
from rest_framework import status, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from rest_framework.serializers import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from api.controllers.permissions import IsSchoolAdmin
from core.models.users import UserActivity
from core.models.courses import Qoutes, QouteToken
from api.serializers.courses import (
    CreateQuoteSerializer,
    ReturnQuoteSerializer,
    BulkCreateQuoteTokenSerializer,
)
from api.serializers import users as user_serializer_module
from support import helpers, http
from core.managers import utils
from core.models.courses import Qoutes, QouteToken
from support.helpers import StandardResultsSetPagination, send_notification
from support.http import success_response, failed_response
from core.tasks import send_bulk_token_emails


logger = logging.getLogger(__name__)
User = get_user_model()


class QuotesViewSet(viewsets.ViewSet):
    """
    Handles CRUD operations and token management for Quotes.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=["post"])
    def create_quote(self, request):
        """
        Create a new quote.
        """
        serializer = CreateQuoteSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid(raise_exception=True):
            quantity = serializer.validated_data["quantity"]
            serializer.save(user=request.user, quantity_left=quantity)
            return success_response(
                data=serializer.data, message="Quote created successfully."
            )
        return failed_response(data=serializer.errors, message="Invalid data provided.")

    @action(detail=True, methods=["put"])
    def update_quote(self, request, pk=None):
        """
        Update a quote if status is pending.
        """
        quote = Qoutes.objects.filter(id=pk).first()
        if not quote:
            return failed_response(message="Quote not found.", status_code=404)
        if not quote.status == Qoutes.Status.PENDING:
            return failed_response(
                message="Cannot update. Quote is not in a pending state.",
                status_code=400,
            )
        serializer = CreateQuoteSerializer(quote, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save(quantity_left=quote.quantity)
            return success_response(
                data=serializer.data, message="Quote updated successfully."
            )
        return failed_response(data=serializer.errors, message="Invalid data provided.")

    @action(detail=True, methods=["delete"])
    def delete_quote(self, request, pk=None):
        """
        Delete a quote if status is pending.
        """
        quote = Qoutes.objects.filter(id=pk).first()
        if not quote:
            return failed_response(message="Quote not found.", status_code=404)
        if not quote.status == Qoutes.Status.PENDING:
            return failed_response(
                message="Cannot delete. Quote is not in a pending state.",
                status_code=400,
            )
        quote.delete()
        return success_response(message="Quote deleted successfully.")

    @action(detail=False, methods=["get"])
    def list_quotes(self, request):
        """
        Get all quotes with optional filters.
        """
        status = request.query_params.get("status")
        user = request.query_params.get("user")

        filters = Q()
        if status:
            filters &= Q(status=status)
        if user:
            filters &= Q(user_id=user)

        quotes = Qoutes.objects.filter(filters).order_by("-created_at")
        # add pagination
        paginator = self.pagination_class()
        quotes = paginator.paginate_queryset(quotes, request)

        serializer = ReturnQuoteSerializer(
            quotes, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=["get"])
    def retrieve_quote(self, request, pk=None):
        """
        Get a single quote.
        """
        quote = Qoutes.objects.filter(id=pk).first()
        if not quote:
            return failed_response(message="Quote not found.", status_code=404)

        serializer = ReturnQuoteSerializer(quote, context={"request": request})
        return success_response(
            data=serializer.data, message="Quote retrieved successfully."
        )

    @action(detail=False, methods=["post"])
    def send_tokens(self, request):
        serializer = BulkCreateQuoteTokenSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=True):
            return failed_response(data=serializer.errors)

        quote = serializer.validated_data["quote"]
        user_ids = serializer.validated_data["user_ids"]

        try:
            with transaction.atomic():
                # Bulk create tokens
                tokens_to_create = [
                    QouteToken(
                        user_id=user_id,
                        qoute=quote,
                        token=QouteToken.generate_unique_code(),
                    )
                    for user_id in user_ids
                ]
                created_tokens = QouteToken.objects.bulk_create(tokens_to_create)

                # Update quote quantity
                quote.quantity_left -= len(user_ids)
                quote.save()

                # Prepare email data
                email_data = [
                    {
                        "email": token.user.email,
                        "token": token.token,
                        "term": quote.term,
                        "expiry": str(quote.term_end),
                        "pathway_title": quote.course_pathway.title,
                    }
                    for token in created_tokens
                ]

                print("Hello 123")

                # Send emails in background
                send_bulk_token_emails.delay(email_data)

            return success_response(message=f"Successfully created tokens")

        except Exception as e:
            return failed_response(message=str(e))

    @action(detail=False, methods=["post"])
    def bulk_create_quotes(self, request):
        """
        Create multiple quotes at once.
        """
        try:
            # Expect an array of quote data
            quotes_data = request.data.get("quotes", [])
            if not quotes_data:
                return failed_response(
                    message="No quotes data provided",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            created_quotes = []
            with transaction.atomic():  # Use transaction to ensure all or nothing
                for quote_data in quotes_data:
                    serializer = CreateQuoteSerializer(
                        data=quote_data, context={"request": request}
                    )
                    if serializer.is_valid(raise_exception=True):
                        quantity = serializer.validated_data["quantity"]
                        quote = serializer.save(
                            user=request.user, quantity_left=quantity
                        )
                        created_quotes.append(quote)

            # Serialize all created quotes
            return_serializer = ReturnQuoteSerializer(
                created_quotes, many=True, context={"request": request}
            )
            return success_response(
                data=return_serializer.data,
                message=f"Successfully created {len(created_quotes)} quotes",
                status_code=status.HTTP_201_CREATED,
            )

        except ValidationError as e:
            return failed_response(
                message="Invalid data provided",
                data=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return failed_response(
                message=f"Error creating quotes: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SchoolAdminAPIView(viewsets.ViewSet):

    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=["get"])
    def get_all_users_in_school(self, request):
        """Get all users in school"""

        role = request.query_params.get("role")

        try:
            school_id = request.user.school.id
        except AttributeError:
            return http.failed_response(
                None,
                _("User is not associated with any school."),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            query = User.objects.filter(school_id=school_id)

            if role:
                query = query.filter(role=role)
            else:
                query = query.filter(
                    Q(role=User.Roles.STUDENT) | Q(role=User.Roles.TEACHER)
                )

            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(query, request)
            serializer = user_serializer_module.UserListSerializer(
                paginated_queryset, many=True
            )
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            logger.error(f"Error fetching school users: {str(e)}")
            return http.failed_response(
                None,
                _("An error occurred while fetching users."),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def get_by_id(self, request, pk=None):
        """Get a specific user by ID"""

        try:
            query = User.objects.get(id=pk)

            serializer = user_serializer_module.UserListSerializer(query)
            return http.success_response(data=serializer.data)

        except User.DoesNotExist:

            return http.failed_response(
                None,
                _("User not found."),
                status_code=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["put"])
    def modify(self, request, pk=None):
        """Update an existing user"""

        try:
            user = User.objects.get(id=pk)
            serializer = user_serializer_module.UserSerializer(
                user, data=request.data, partial=True
            )
            if serializer.is_valid():
                updated_user = serializer.save()

                # Log user update activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="profile",
                    description=f"SchoolAdmin Updated user Info: {updated_user.email}",
                )

                return_serializer = user_serializer_module.ReturnUserSerializer(
                    updated_user
                )
                return http.success_response(
                    data=return_serializer.data, message="user updated successfully"
                )
            return http.failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except User.DoesNotExist:
            return http.failed_response(
                message="user not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return http.failed_response(
                message=f"Error updating user: {str(e)}", status_code=500
            )

    @action(detail=True, methods=["delete"])
    def remove(self, request, pk=None):
        """Delete a user"""
        try:
            user = User.objects.get(id=pk)
            user_email = user.email
            user_full_name = user.full_name
            user.delete()

            # Log profile deletion activity
            utils.log_user_activity(
                user=request.user,
                activity_type="profile",
                description=f"Deleted profile: {user_email} - {user_full_name}",
            )

            return http.success_response(
                message="User deleted successfully",
                status_code=200,
            )
        except User.DoesNotExist:
            return http.failed_response(
                message="User not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return http.failed_response(
                message=f"Error deleting user: {str(e)}", status_code=500
            )

    @action(detail=True, methods=["get"])
    def user_recent_activities(self, request, pk=None):
        """Get users recent activities"""
        search_query = request.query_params.get("q", "")

        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return http.failed_response(
                message="User not found", status_code=status.HTTP_404_NOT_FOUND
            )

        activities = self.get_recent_activities(user, search_query)

        paginator = self.pagination_class()

        result_page = paginator.paginate_queryset(activities, request)
        serializer = user_serializer_module.RecentUserActivitySerializer(
            result_page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def get_recent_activities(self, user, search_query=None):
        activities = (
            UserActivity.objects.select_related("user")
            .filter(user=user)
            .order_by("-created_at")
        )

        if search_query:
            activities = activities.filter(
                Q(description__icontains=search_query)
                | Q(activity_type__icontains=search_query)
                | Q(user__full_name__icontains=search_query)
            )

        activities = activities[:10]  # Limit to 10 most recent activities

        return activities
