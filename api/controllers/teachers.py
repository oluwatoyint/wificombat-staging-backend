import logging, json
from rest_framework import status, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from core.models.users import UserActivity, AssignedClass
from core.models.courses import Qoutes, QouteToken
from api.serializers.courses import ReturnAssignedClassSerializer, ReturnQuoteSerializer
from api.serializers.users import ReturnUserSerializer
from support import helpers, http
from core.managers import utils
from core.models.courses import Qoutes, QouteToken
from support.helpers import StandardResultsSetPagination, send_notification
from support.http import success_response, failed_response
from core.tasks import send_bulk_token_emails


logger = logging.getLogger(__name__)
User = get_user_model()


class TeacherDashboard(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=["get"])
    def my_class(self, request):
        """Return all classes asssigned to aaaa teacher"""
        assigned_classes = AssignedClass.objects.filter(teacher=request.user)
        serializer = ReturnAssignedClassSerializer(assigned_classes, many=True)
        return success_response(data=serializer.data)

    @action(detail=False, methods=["get"])
    def my_students(self, request):
        """Get all users in class"""

        _class = request.query_params.get("class")
        if not _class:
            return http.failed_response(
                None,
                _("Class parameter is required."),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            school_id = request.user.school.id
        except AttributeError:
            return http.failed_response(
                None,
                _("User is not associated with any school."),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        query = User.objects.filter(
            school_id=school_id, role=User.Roles.STUDENT, _class=_class
        )

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(query, request)
        serializer = ReturnUserSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=["get"])
    def get_by_id(self, request, pk=None):
        """Get a specific user by ID"""

        try:
            query = User.objects.get(id=pk)

            serializer = ReturnUserSerializer(query)
            return http.success_response(data=serializer.data)

        except User.DoesNotExist:

            return http.failed_response(
                None,
                _("User not found."),
                status_code=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def get_class_pathways(self, request):
        """Get all course pathways for a specific class"""

        _class = request.query_params.get("class")
        term = request.query_params.get("term")
        if not _class:
            return http.failed_response(
                None,
                _("Class parameter is required."),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            school_id = request.user.school.id
        except AttributeError:
            return http.failed_response(
                None,
                _("User is not associated with any school."),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        query = Qoutes.objects.filter(
            user__school_id=school_id,
            class_name__contains=_class,
            term=term,
            status="approved",
            is_active=True,
        )

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(query, request)
        serializer = ReturnQuoteSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
