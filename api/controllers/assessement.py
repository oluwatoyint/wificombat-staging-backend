import logging
from decimal import Decimal
from rest_framework import status, permissions, viewsets
from rest_framework.views import APIView
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, AllowAny
from support import helpers, http
from core.models.assessment import DetermineCareerInterest
from rest_framework.response import Response
from rest_framework.decorators import action
from core.models.assessment import DetermineCareerInterest
from rest_framework.serializers import ModelSerializer
from support.helpers import StandardResultsSetPagination, rank_strings
from api.serializers.assessement import (
    DetermineCareerInterestSerializer,
    RankedCareerInterestSerializer,
)
from core.models.courses import CoursePathWay
from api.serializers.courses import ReturnCoursePathWaySerializer


class DetermineCareerInterestViewSet(viewsets.ViewSet):
    """
    ViewSet for managing DetermineCareerInterest.
    Provides CRUD operations.
    """

    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Custom permission handling."""
        if self.action in ["list", "retrieve", "rank_career_interests"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def list(self, request):
        """Get all career interest questions."""
        queryset = DetermineCareerInterest.objects.all()
        age_grp = request.query_params.get("age_grp")
        pathway_name = request.query_params.get("pathway_name")
        question_type = request.query_params.get("question_type")
        if request.query_params.get("pathway_id"):
            queryset = queryset.filter(
                pathway__id=request.query_params.get("pathway_id")
            )
        if pathway_name:
            queryset = queryset.filter(pathway__title__icontains=pathway_name)
        if question_type:
            queryset = queryset.filter(question_type=question_type)
        if age_grp:
            queryset = queryset.filter(age_grp=age_grp)
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = DetermineCareerInterestSerializer(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get a specific career interest question by ID."""
        try:
            question = DetermineCareerInterest.objects.get(pk=pk)
            serializer = DetermineCareerInterestSerializer(question)
            return http.success_response(data=serializer.data)
        except DetermineCareerInterest.DoesNotExist:
            return http.failed_response(
                message="Career interest question not found.",
            )

    def create(self, request):
        """Create a new career interest question."""
        serializer = DetermineCareerInterestSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return http.success_response(data=serializer.data, status_code=201)
        return http.failed_response(
            message=serializer.errors,
        )

    def update(self, request, pk=None):
        """Update an existing career interest question."""
        try:
            question = DetermineCareerInterest.objects.get(pk=pk)
            serializer = DetermineCareerInterestSerializer(
                question, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return http.success_response(data=serializer.data, status_code=200)
            return http.failed_response(
                message=serializer.errors,
            )
        except DetermineCareerInterest.DoesNotExist:
            return http.failed_response(
                message="Career interest question not found.",
            )

    def destroy(self, request, pk=None):
        """Delete a career interest question."""
        try:
            question = DetermineCareerInterest.objects.get(pk=pk)
            question.delete()
            return http.success_response(
                message="Career interest question deleted successfully."
            )
        except DetermineCareerInterest.DoesNotExist:
            return http.failed_response(
                message="Career interest question not found.",
            )

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """Bulk create career interest questions."""
        serializer = DetermineCareerInterestSerializer(data=request.data, many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return http.success_response(data=serializer.data, status_code=201)
        return http.failed_response(
            message=serializer.errors,
        )

    @action(detail=False, methods=["post"], url_path="rank-career-interests")
    def rank_career_interests(self, request):
        """
        After the assessment has been completed,  there is a list of string containing the pathways the user has showned interests.
        This pathways are ranked, sorted and returned back to the user as recommendations.

        Payload: [list of pathway title]
        return {
                "pathways": [
                    {
                        "title": "Pathway Title",
                        "rank": 1
                    }
                ]
            }

        """
        serializer = RankedCareerInterestSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            interests = serializer.validated_data.get("interests")
            interests = rank_strings(interests)

            ranked_interest = []
            for pathway_title, rank in interests:
                pathway = CoursePathWay.objects.filter(
                    title__icontains=pathway_title
                ).first()
                if pathway:  # Only include if pathway exists
                    ranked_interest.append(
                        {
                            "pathway": ReturnCoursePathWaySerializer(pathway).data,
                            "rank": rank,
                        }
                    )

            return http.success_response(data=ranked_interest)
        return http.failed_response(
            message=serializer.errors,
        )
