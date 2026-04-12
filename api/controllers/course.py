import logging
from decimal import Decimal
from rest_framework import status, permissions, viewsets
from rest_framework.views import APIView
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.db.models import Q
from datetime import datetime, timedelta
from django.db.models.functions import ExtractWeekDay, ExtractWeek
from django.db.models import Avg
from django.utils import timezone
from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from django.db.models import Q, Sum, F, Prefetch, Count
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from api.controllers.permissions import IsSchoolAdmin
from core.models.users import User, UserActivity
from support import helpers, http
from core.managers import utils
from core.models.courses import (
    CoursePathWay,
    Course,
    CourseRating,
    LessonRating,
    Module,
    Lesson,
    Assignment,
    CourseProject,
    LessonQuiz,
    LessonQuizScore,
    ModuleAssignmentResponse,
    CourseStreak,
    CourseEnrollment,
    QouteToken,
    CourseProjectResponse,
    UserModuleProgress,
    UserEarnedPoint,
    UserBadge,
    Certificate,
    PortfolioContent,
    Flashcard,
    Library,
    DiscountCode,
    UsedDiscountCode,
    UserLessonProgress,
)
from core.models.users import Wallet
from api.serializers.courses import (
    CoursePathWaySerializer,
    CourseRatingSerializer,
    LessonRatingSerializer,
    ReturnCoursePathWaySerializer,
    CourseSerializer,
    ReturnCourseRatingSerializer,
    ReturnCourseSerializer,
    ModuleSerializer,
    ReturnLessonRatingSerializer,
    ReturnModuleSerializer,
    LessonSerializer,
    ReturnLessonSerializer,
    CourseProjectSerializer,
    ReturnCourseProjectSerializer,
    AssignmentSerializer,
    ReturnAssignmentSerializer,
    LessonQuizSerializer,
    PurchaseCourseSerializer,
    EnrolledModuleSerializer,
    EnrolledCourseSerializer,
    LessonQuizScoreSerializer,
    ReturnLessonQuizScoreSerializer,
    ModuleAssignmentResponseSerializer,
    CourseProjectResponseSerializer,
    ReturnCourseProjectResponseSerializer,
    UnlockCourseWithCodeSerializer,
    UpdateCourseRatingSerializer,
    ReportCardSerilaizer,
    UpdateLessonRatingSerializer,
    UserBadgeSerializer,
    VideoEmbedSerializer,
    CertificateSerializer,
    PortfolioContentSerializer,
    LessonQuizListSerializer,
    UpdateModuleSerializer,
    UpdateLessonSerializer,
    FlashcardSerializer,
    ReturnFlashcardSerializer,
    LibrarySerializer,
    ReturnLibrarySerializer,
    DetailedReturnModuleSerializerJames,
    CheckDiscountCodeSerializer,
    ReturnModuleAssignmentResponseSerializer,
    ReturnCourseSerializerFrankOnly,
)
from support.helpers import StandardResultsSetPagination, send_notification
from support.http import success_response, failed_response
from api.controllers.utils import (
    Enrollment,
    handle_quiz_submission_earn_point,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class CoursePathWayViewSet(viewsets.ViewSet):
    """
    ViewSet for managing course pathways.
    Provides CRUD operations and custom actions for course pathway management.
    """

    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Custom permission handling."""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def list(self, request):
        """Get all course pathways."""
        queryset = CoursePathWay.objects.all().order_by("-created_at")
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = ReturnCoursePathWaySerializer(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get a specific course pathway by ID."""
        try:
            pathway = CoursePathWay.objects.get(pk=pk)
            serializer = ReturnCoursePathWaySerializer(pathway)
            return http.success_response(
                data=serializer.data, message=_("Course pathway retrieved successfully")
            )
        except CoursePathWay.DoesNotExist:
            return http.failed_response(
                message=_("Course pathway not found"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

    def create(self, request):
        """Create a new course pathway."""
        serializer = CoursePathWaySerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            pathway = serializer.save()

            # Log course pathway creation activity
            utils.log_user_activity(
                user=request.user,
                activity_type="career_pathway",
                description=f"Created new CareerPathWay: {pathway.title}",
            )

            return_serializer = ReturnCoursePathWaySerializer(pathway)
            return http.success_response(
                data=return_serializer.data,
                message=_("Course pathway created successfully"),
                status_code=201,
            )
        return http.failed_response(
            serializer.errors, message=_("Invalid data provided")
        )

    def update(self, request, pk=None):
        """Update an existing course pathway."""
        try:
            pathway = CoursePathWay.objects.get(pk=pk)
            serializer = CoursePathWaySerializer(
                instance=pathway, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                updated_pathway = serializer.save()

                # Log CoursePathWay update activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="career_pathway",
                    description=f"Updated CareerPathWay: {updated_pathway.title}",
                )

                return_serializer = ReturnCoursePathWaySerializer(updated_pathway)
                return http.success_response(
                    data=return_serializer.data,
                    message=_("Course pathway updated successfully"),
                )
            return http.failed_response(
                errors=serializer.errors, message=_("Invalid data provided")
            )
        except CoursePathWay.DoesNotExist:
            return http.failed_response(
                message=_("Course pathway not found"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

    def destroy(self, request, pk=None):
        """Delete a course pathway."""
        try:
            pathway = CoursePathWay.objects.get(pk=pk)
            pathway_title = pathway.title
            pathway.delete()

            # Log CareerPathWay deletion activity
            utils.log_user_activity(
                user=request.user,
                activity_type="career_pathway",
                description=f"Deleted course: {pathway_title}",
            )

            return http.success_response(
                message=_("Course pathway deleted successfully")
            )
        except CoursePathWay.DoesNotExist:
            return http.failed_response(
                message=_("Course pathway not found"),
                status_code=status.HTTP_404_NOT_FOUND,
            )


class CourseViewSet(viewsets.ViewSet):
    """
    ViewSet for managing courses.
    Provides custom actions for CRUD operations.
    """

    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Custom permission handling."""
        if self.action in [
            "get_by_id",
            "get_all",
            "get_courses_by_pathway_params_frank_only",
        ]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def get_all(self, request):
        """Get all courses"""

        courses = Course.objects.all()
        pathway_id = request.query_params.get("pathway_id")
        instructor_id = request.query_params.get("instructor_id")

        if instructor_id:
            courses = courses.filter(instructor__id=instructor_id)

        if pathway_id:
            courses = courses.filter(course_pathway_id=pathway_id)

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(courses, request)
        serializer = ReturnCourseSerializer(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=False, methods=["get"], url_path="get-courses-by-pathway-query-string"
    )
    def get_courses_by_pathway_params_frank_only(self, request):
        """
        So frank made a stupid request to give provide him some data top the landing page to filter
        courses by pathway query params with sme specific data. so this endpoint is specially for him.
        """

        courses = Course.objects.all()
        q = request.query_params.get("q")

        if q:
            courses = courses.filter(course_pathway__title__icontains=q)

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(courses, request)
        serializer = ReturnCourseSerializerFrankOnly(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=["get"])
    def get_by_id(self, request, pk=None):
        """Get a specific course by ID"""
        try:
            course = Course.objects.get(id=pk)
            serializer = ReturnCourseSerializer(course)
            return http.success_response(
                data=serializer.data, message="Course retrieved successfully"
            )
        except Course.DoesNotExist:
            return http.failed_response(
                message="Course not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return http.failed_response(
                message=f"Error retrieving course: {str(e)}", status_code=500
            )

    @action(detail=False, methods=["post"])
    def add(self, request):
        """Create a new course"""
        try:
            serializer = CourseSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                course = serializer.save(instructor=request.user)

                # Log course creation activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="course",
                    description=f"Created new course: {course.title}",
                )

                return_serializer = ReturnCourseSerializer(course)
                return http.success_response(
                    data=return_serializer.data,
                    message="Course created successfully",
                    status_code=status.HTTP_201_CREATED,
                )
            return http.failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except Exception as e:
            return http.failed_response(
                message=f"Error creating course: {str(e)}", status_code=500
            )

    @action(detail=True, methods=["put"])
    def modify(self, request, pk=None):
        """Update an existing course"""
        try:
            course = Course.objects.get(id=pk)
            serializer = CourseSerializer(course, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                updated_course = serializer.save()

                # Log course update activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="course",
                    description=f"Updated course: {updated_course.title}",
                )

                return_serializer = ReturnCourseSerializer(updated_course)
                return http.success_response(
                    data=return_serializer.data, message="Course updated successfully"
                )
            return http.failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except Course.DoesNotExist:
            return http.failed_response(
                message="Course not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return http.failed_response(
                message=f"Error updating course: {str(e)}", status_code=500
            )

    @action(detail=True, methods=["delete"])
    def remove(self, request, pk=None):
        """Delete a course"""
        try:
            course = Course.objects.get(id=pk)
            course_title = course.title
            course.delete()

            # Log course deletion activity
            utils.log_user_activity(
                user=request.user,
                activity_type="course",
                description=f"Deleted course: {course_title}",
            )

            return http.success_response(
                message="Course deleted successfully",
                status_code=200,
            )
        except Course.DoesNotExist:
            return http.failed_response(
                message="Course not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return http.failed_response(
                message=f"Error deleting course: {str(e)}", status_code=500
            )


class ModuleViewSet(viewsets.ViewSet):
    """
    ViewSet for managing course modules.
    Provides standard CRUD operations.
    """

    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Custom permission handling."""
        if self.action in ["get_all", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def get_all(self, request):
        """Get all modules"""
        try:
            course_id = request.query_params.get("course_id")

            # Base queryset
            modules = Module.objects.all().order_by("order")

            if course_id:
                modules = Module.objects.filter(course__id=course_id)

            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(modules, request)
            serializer = ReturnModuleSerializer(
                paginated_queryset, many=True, context={"request": request}
            )
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return failed_response(
                message=f"Error retrieving modules: {str(e)}", status_code=500
            )

    def retrieve(self, request, pk=None):
        """Get a specific module by ID"""
        try:
            try:
                module = Module.objects.get(pk=pk)
            except Module.DoesNotExist:
                return failed_response(
                    message="Module not found", status_code=status.HTTP_404_NOT_FOUND
                )

            serializer = ReturnModuleSerializer(module)
            return success_response(
                data=serializer.data, message="Module retrieved successfully"
            )
        except Exception as e:
            return failed_response(
                message=f"Error retrieving module: {str(e)}", status_code=500
            )

    def create(self, request):
        """Create a new module"""

        serializer = ModuleSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            module = serializer.save()
            utils.log_user_activity(
                user=request.user,
                activity_type="course",
                description=f"Created new module: {module.title} in course: {module.course.title}",
            )

            return_serializer = ReturnModuleSerializer(module)
            return success_response(
                data=return_serializer.data,
                message="Module created successfully",
                status_code=status.HTTP_201_CREATED,
            )
        return failed_response(data=serializer.errors, message="Invalid data provided")

    def update(self, request, pk=None):
        """Update an existing module"""
        try:
            module = Module.objects.get(pk=pk)
        except Module.DoesNotExist:
            return failed_response(
                message="Module not found", status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = UpdateModuleSerializer(module, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            updated_module = serializer.save()

            # Log module update activity
            utils.log_user_activity(
                user=request.user,
                activity_type="course",
                description=f"Updated module: {updated_module.title}",
            )

            return_serializer = ReturnModuleSerializer(updated_module)
            return success_response(
                data=return_serializer.data, message="Module updated successfully"
            )
        return failed_response(data=serializer.errors, message="Invalid data provided")

    def destroy(self, request, pk=None):
        """Delete a module"""
        try:
            try:
                module = Module.objects.get(pk=pk)
            except Module.DoesNotExist:
                return failed_response(
                    message="Module not found", status_code=status.HTTP_404_NOT_FOUND
                )

            module_title = module.title
            module.delete()

            # Log module deletion activity
            utils.log_user_activity(
                user=request.user,
                activity_type="course",
                description=f"Deleted course: {module_title}",
            )

            return success_response(
                message="Module deleted successfully",
                status_code=200,
            )
        except Exception as e:
            return failed_response(
                message=f"Error deleting module: {str(e)}", status_code=500
            )


class LessonViewSet(viewsets.ViewSet):
    """
    ViewSet for managing lessons.
    Provides standard CRUD operations.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Custom permission handling."""
        if self.action in ["get_all", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def get_all(self, request):
        """Get all lessons"""
        try:

            module_id = request.query_params.get("module_id")
            course_id = request.query_params.get("course_id")

            # base query
            lessons = Lesson.objects.all().order_by("-created_at")

            if module_id:
                lessons = lessons.filter(module__id=module_id)

            if course_id:
                lessons = lessons.filter(module__course__id=course_id)

            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(lessons, request)
            serializer = ReturnLessonSerializer(
                paginated_queryset, many=True, context={"request": request}
            )
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return failed_response(
                message=f"Error retrieving lessons: {str(e)}", status_code=500
            )

    def retrieve(self, request, pk=None):
        """Get a specific lesson by ID"""
        try:
            lesson = Lesson.objects.get(pk=pk)
            serializer = ReturnLessonSerializer(lesson, context={"request": request})
            return success_response(
                data=serializer.data, message="Lesson retrieved successfully"
            )
        except Lesson.DoesNotExist:
            return http.failed_response(
                message="Lesson not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return failed_response(
                message=f"Error retrieving lesson: {str(e)}", status_code=500
            )

    def create(self, request):
        """Create a new lesson"""
        try:
            serializer = LessonSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                lesson = serializer.save()

                # Log lesson creation activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="course",
                    description=f"Created new lesson: {lesson.title} in module: {lesson.module.title}",
                )

                return_serializer = ReturnLessonSerializer(
                    lesson, context={"request": request}
                )
                return success_response(
                    data=return_serializer.data,
                    message="Lesson created successfully",
                    status_code=status.HTTP_201_CREATED,
                )
            return failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except Exception as e:
            return failed_response(
                message=f"Error creating lesson: {str(e)}", status_code=500
            )

    def update(self, request, pk=None):
        """Update an existing lesson"""
        try:
            lesson = Lesson.objects.get(pk=pk)
            serializer = UpdateLessonSerializer(lesson, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                updated_lesson = serializer.save()

                # Log lesson update activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="course",
                    description=f"Updated lesson: {updated_lesson.title}",
                )

                return_serializer = ReturnLessonSerializer(
                    updated_lesson, context={"request": request}
                )
                return success_response(
                    data=return_serializer.data, message="Lesson updated successfully"
                )
            return failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except Lesson.DoesNotExist:
            return http.failed_response(
                message="Lesson not found", status_code=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, pk=None):
        """Delete a lesson"""
        try:
            lesson = Lesson.objects.get(pk=pk)
            lesson_title = lesson.title
            lesson.delete()

            # Log lesson deletion activity
            utils.log_user_activity(
                user=request.user,
                activity_type="course",
                description=f"Deleted lesson: {lesson_title}",
            )

            return success_response(
                message="Lesson deleted successfully",
                status_code=200,
            )
        except Lesson.DoesNotExist:
            return http.failed_response(
                message="Lesson not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return failed_response(
                message=f"Error deleting lesson: {str(e)}", status_code=500
            )


class AssignmentViewSet(viewsets.ViewSet):
    """
    ViewSet for managing Assignments.
    Provides standard CRUD operations.
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Custom permission handling."""
        if self.action in ["get_all", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def get_all(self, request):
        """Get all assignments for a specific module."""
        try:
            module_id = request.query_params.get("module_id")
            course_id = request.query_params.get("course_id")

            # base filter
            assignments = Assignment.objects.all().order_by("-created_at")

            if module_id:
                assignments = assignments.filter(module__id=module_id)

            if course_id:
                assignments = assignments.filter(module__course__id=course_id)

            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(assignments, request)
            serializer = ReturnAssignmentSerializer(
                paginated_queryset, many=True, context={"request": request}
            )
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return failed_response(
                message=f"Error retrieving assignments: {str(e)}", status_code=500
            )

    def retrieve(self, request, pk=None):
        """Get a specific assignment by ID."""
        try:
            assignment = Assignment.objects.get(pk=pk)
            serializer = ReturnAssignmentSerializer(assignment)
            return success_response(
                data=serializer.data, message="Assignment retrieved successfully"
            )
        except Assignment.DoesNotExist:
            return failed_response(message="Assignment not found", status_code=404)
        except Exception as e:
            return failed_response(
                message=f"Error retrieving assignment: {str(e)}", status_code=500
            )

    def create(self, request):
        """Create a new assignment."""
        try:
            serializer = AssignmentSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                assignment = serializer.save()

                # Log assignment creation activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="assignment",
                    description=f"Created new Assignment: {assignment.title} in module: {assignment.module.title}",
                )

                return_serializer = ReturnAssignmentSerializer(assignment)
                return success_response(
                    data=return_serializer.data,
                    message="Assignment created successfully",
                    status_code=status.HTTP_201_CREATED,
                )
            return failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except Exception as e:
            return failed_response(
                message=f"Error creating assignment: {str(e)}", status_code=500
            )

    def update(self, request, pk=None):
        """Update an existing assignment."""
        try:
            assignment = Assignment.objects.get(pk=pk)
            serializer = AssignmentSerializer(
                assignment, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                updated_assignment = serializer.save()

                # Log assignment update activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="assignment",
                    description=f"Updated assignment: {updated_assignment.title}",
                )

                return_serializer = ReturnAssignmentSerializer(updated_assignment)
                return success_response(
                    data=return_serializer.data,
                    message="Assignment updated successfully",
                )
            return failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except Assignment.DoesNotExist:
            return failed_response(message="Assignment not found", status_code=404)
        except Exception as e:
            return failed_response(
                message=f"Error updating assignment: {str(e)}", status_code=500
            )

    def destroy(self, request, pk=None):
        """Delete an assignment."""
        try:
            assignment = Assignment.objects.get(pk=pk)
            assignment_title = assignment.title
            assignment.delete()

            # Log assignment deletion activity
            utils.log_user_activity(
                user=request.user,
                activity_type="assignment",
                description=f"Deleted assignment: {assignment_title}",
            )

            return success_response(
                message="Assignment deleted successfully",
                status_code=200,
            )
        except Assignment.DoesNotExist:
            return failed_response(message="Assignment not found", status_code=404)
        except Exception as e:
            return failed_response(
                message=f"Error deleting assignment: {str(e)}", status_code=500
            )


class CourseProjectViewSet(viewsets.ViewSet):
    """
    ViewSet for managing Course Projects.
    Provides standard CRUD operations.
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Custom permission handling."""
        if self.action in ["get_all", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def get_all(self, request, course_id):
        """Get all course projects for a specific course."""
        try:
            projects = CourseProject.objects.filter(course__id=course_id).order_by(
                "-created_at"
            )
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(projects, request)
            serializer = ReturnCourseProjectSerializer(
                paginated_queryset, many=True, context={"request": request}
            )
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return failed_response(
                message=f"Error retrieving projects: {str(e)}", status_code=500
            )

    def retrieve(self, request, pk=None):
        """Get a specific course project by ID."""
        try:
            project = CourseProject.objects.get(pk=pk)
            serializer = ReturnCourseProjectSerializer(project)
            return success_response(
                data=serializer.data, message="Project retrieved successfully"
            )
        except CourseProject.DoesNotExist:
            return failed_response(message="Project not found", status_code=404)
        except Exception as e:
            return failed_response(
                message=f"Error retrieving project: {str(e)}", status_code=500
            )

    def create(self, request):
        """Create a new course project."""
        try:
            serializer = CourseProjectSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                project = serializer.save()

                # Log project creation activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="project",
                    description=f"Created new project: {project.title} in course: {project.course.title}",
                )

                return_serializer = ReturnCourseProjectSerializer(project)
                return success_response(
                    data=return_serializer.data,
                    message="Project created successfully",
                    status_code=status.HTTP_201_CREATED,
                )
            return failed_response(
                data=serializer.errors, message="Invalid data provided"
            )

        except Exception as e:
            return failed_response(
                message=f"Error creating project: {str(e)}", status_code=500
            )

    def update(self, request, pk=None):
        """Update an existing course project."""
        try:
            project = CourseProject.objects.get(pk=pk)
            serializer = CourseProjectSerializer(
                project, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                updated_project = serializer.save()

                # Log project update activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="project",
                    description=f"Updated project: {updated_project.title}",
                )

                return_serializer = ReturnCourseProjectSerializer(updated_project)
                return success_response(
                    data=return_serializer.data,
                    message="Project updated successfully",
                )
            return failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except CourseProject.DoesNotExist:
            return failed_response(message="Project not found", status_code=404)
        except Exception as e:
            return failed_response(
                message=f"Error updating project: {str(e)}", status_code=500
            )

    def destroy(self, request, pk=None):
        """Delete a course project."""
        try:
            project = CourseProject.objects.get(pk=pk)
            project_title = project.title
            project.delete()

            # Log assignment deletion activity
            utils.log_user_activity(
                user=request.user,
                activity_type="project",
                description=f"Deleted project: {project_title}",
            )

            return success_response(
                message="Project deleted successfully",
                status_code=200,
            )
        except CourseProject.DoesNotExist:
            return failed_response(message="Project not found", status_code=404)
        except Exception as e:
            return failed_response(
                message=f"Error deleting project: {str(e)}", status_code=500
            )


# class LessonQuizViewSet(viewsets.ModelViewSet):
#     queryset = LessonQuiz.objects.all()
#     serializer_class = LessonQuizSerializer
#     permission_classes = [IsAuthenticated]
#     pagination_class = StandardResultsSetPagination

#     # def get_queryset(self):
#     #     return LessonQuiz.objects.prefetch_related("lessonquizoption_set")

#     @action(detail=False, methods=["get"])
#     def get_all(self, request, lesson_id):
#         """Get all quizes on the for a quiz."""
#         try:
#             lessons = (
#                 LessonQuiz.objects.filter(lesson__id=lesson_id)
#                 .prefetch_related("lessonquizoption_set")
#                 .order_by("-created_at")
#             )
#             paginator = self.pagination_class()
#             paginated_queryset = paginator.paginate_queryset(lessons, request)
#             serializer = self.serializer_class(
#                 paginated_queryset, many=True, context={"request": request}
#             )
#             return paginator.get_paginated_response(serializer.data)
#         except Exception as e:
#             return failed_response(
#                 message=f"Error retrieving quiz: {str(e)}", status_code=500
#             )

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)
#         return Response(
#             serializer.data, status=status.HTTP_201_CREATED, headers=headers
#         )

#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop("partial", False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response(serializer.data)


class LessonQuizViewSet(viewsets.ModelViewSet):
    queryset = LessonQuiz.objects.all()
    serializer_class = LessonQuizSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=["get"])
    def get_all(self, request, lesson_id):
        """Get all quizzes for a lesson."""
        try:
            lessons = (
                LessonQuiz.objects.filter(lesson__id=lesson_id)
                .prefetch_related("lessonquizoption_set")
                .order_by("-created_at")
            )
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(lessons, request)
            serializer = self.serializer_class(
                paginated_queryset, many=True, context={"request": request}
            )
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response(
                {"message": f"Error retrieving quiz: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """Bulk create quizzes."""
        serializer = LessonQuizListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=serializer.data,
            status_code=201,
            message=_("Quizes added successfully."),
        )

    @action(detail=False, methods=["put"])
    def bulk_update(self, request):
        """Bulk update quizzes."""
        lesson_id = request.data.get(
            "lesson_id"
        )  # Assuming lesson_id is provided in the request
        if not lesson_id:
            return Response(
                {"message": "lesson_id is required for bulk update"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance = {"lesson": lesson_id}  # Pass the lesson ID to the serializer
        serializer = LessonQuizListSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=serializer.data,
            status_code=200,
            message=_("Quizes updated successfully."),
        )

    def create(self, request, *args, **kwargs):
        """Create a single quiz."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        """Update a single quiz."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(data=serializer.data)


# class CheckDiscountCodeValidaity(APIView):
#     """Endpoint to allow user purchase course using their wallet"""

#     permission_classes = [IsAuthenticated]
#     serializer_class = CheckDiscountCodeSerializer

#     def post(self, request):
#         """
#         Create a new purchase for a course using the authenticated user's wallet.
#         """
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid(raise_exception=True):
#             user = request.user
#             course_ids = serializer.validated_data["courses"]
#             discount_code = serializer.validated_data.get("discount_code")
#             make_purchase = (
#                 serializer.validated_data.get("make_purchase", "true").lower() == "true"
#             )
#             message = None

#             # Fetch Course objects from the provided course IDs
#             try:
#                 courses = Course.objects.filter(id__in=course_ids)
#                 if len(courses) != len(course_ids):
#                     missing_ids = set(course_ids) - set(
#                         str(course.id) for course in courses
#                     )
#                     return failed_response(
#                         message=_(
#                             f"Some courses were not found: {', '.join(missing_ids)}"
#                         )
#                     )
#             except Exception as e:
#                 return failed_response(message=f"Error fetching courses: {str(e)}")

#             # Validate discount code
#             try:
#                 discount_code_obj = self.validate_discount_code(discount_code, user)
#             except ValidationError as e:
#                 return failed_response(message=str(e))

#             # Calculate total discount amount
#             total_discount_amount = self.calculate_discount(courses, discount_code_obj)
#             if total_discount_amount is None:
#                 return failed_response(message=_("Invalid course data provided"))

#             # Check wallet balance
#             wallet = Wallet.objects.get_or_create(user=user)[0]
#             total_amount = (
#                 sum(course.amount for course in courses) - total_discount_amount
#             )
#             if wallet.balance < total_amount:
#                 return failed_response(
#                     message=_(
#                         f"Insufficient balance in wallet. User has {wallet.balance}, but needs {total_amount}"
#                     )
#                 )

#             # Enroll user in courses
#             with transaction.atomic():
#                 try:
#                     if make_purchase:
#                         self.enroll_user(
#                             user, courses, wallet, total_amount, discount_code_obj
#                         )
#                         message = _("Purchase successful")
#                 except ValueError as err:
#                     return failed_response(message=str(err))
#                 except Exception as err:
#                     raise err

#             return success_response(
#                 data={
#                     "total_discount_amount": total_discount_amount,
#                     "total_amount": total_amount,
#                 },
#                 message=message,
#             )
#         return failed_response(data=serializer.errors, message="Invalid data provided")

#     def validate_discount_code(self, discount_code, user):
#         """
#         Validate the discount code and return the discount code object if valid.
#         """
#         discount_code_obj = DiscountCode.objects.filter(code=discount_code).first()
#         if not discount_code_obj:
#             raise ValidationError(_("Discount code is not valid"))
#         if discount_code_obj.used_count >= discount_code_obj.max_uses:
#             raise ValidationError(_("Discount code has reached its maximum usage"))
#         if not discount_code_obj.is_active:
#             raise ValidationError(_("Discount code is not active"))
#         if discount_code_obj.has_user_used_code(user):
#             raise ValidationError(_("Discount code has already been used"))
#         return discount_code_obj

#     def calculate_discount(self, courses, discount_code_obj):
#         """
#         Calculate the total discount amount for the given courses and discount code.
#         """
#         total_discount_amount = Decimal("0.00")
#         for course in courses:
#             if discount_code_obj.is_valid_for_course(course):
#                 total_discount_amount += (
#                     discount_code_obj.percentage_off / 100
#                 ) * course.amount
#         return total_discount_amount

#     def enroll_user(self, user, courses, user_wallet, total_cost, discount_code_obj):
#         """
#         Enroll the user in the courses and deduct the amount from their wallet.
#         """
#         Enrollment(user, courses).enroll_user()
#         user_wallet.balance -= total_cost
#         user_wallet.save()

#         # save the discount code usage
#         UsedDiscountCode.objects.create(
#             user=user,
#             discount_code=discount_code_obj,
#         )
#         # update the discount code usage count
#         discount_code_obj.used_count += 1
#         discount_code_obj.save()


class CheckDiscountCodeValidaity(APIView):
    """Endpoint to allow user purchase course using their wallet"""

    permission_classes = [IsAuthenticated]
    serializer_class = CheckDiscountCodeSerializer

    def post(self, request):
        """
        Create a new purchase for a course using the authenticated user's wallet.
        """
        serializer = self.serializer_class(data=request.data)
        discount_code = request.query_params.get("discount_code")
        make_purchase = request.query_params.get("make_purchase")

        message = None
        wallet = Wallet.objects.get_or_create(user=request.user)[0]

        if serializer.is_valid(raise_exception=True):
            course_ids = serializer.validated_data["courses"]
            try:
                courses = Course.objects.filter(id__in=course_ids)
                if len(courses) != len(course_ids):
                    missing_ids = set(course_ids) - set(
                        str(course.id) for course in courses
                    )
                    return failed_response(
                        message=_(
                            f"Some courses were not found: {', '.join(missing_ids)}"
                        )
                    )
            except Exception as e:
                return failed_response(message=f"Error fetching courses: {str(e)}")

            if make_purchase:
                if not discount_code:
                    return failed_response(message="discount_code is required")
                try:
                    discount_code_obj = self.validate_discount_code(
                        discount_code, request.user
                    )
                except ValidationError as e:
                    return failed_response(message=str(e.detail[0]))

                total_discount_amount, original_total_amount = self.calculate_discount(
                    courses, discount_code_obj
                )
                make_purchase = make_purchase.lower() == "true"
                if not make_purchase:
                    # user want to check for validation of discount code
                    return http.success_response(
                        data={
                            "total_discount_amount": total_discount_amount,
                            "total_amount": original_total_amount,
                        },
                        message=message,
                    )
                else:
                    # purchase and enrole the user using the discount
                    total_amount = original_total_amount - total_discount_amount
                    if not self._has_enough_wallet_fund(wallet, total_amount):
                        return failed_response(
                            message="Insufficent balance in wallet. Please top up wallet"
                        )
                    # enroll the user
                    self.enroll_user(
                        request.user, courses, wallet, total_amount, discount_code_obj
                    )
                    message = "Purchase successful with discount code"
                    return success_response(message=message)
            else:
                # the make_purchase is none (not present in the params)
                # user want to purchase without discount
                total_amount = sum(course.amount for course in courses)
                if not self._has_enough_wallet_fund(wallet, total_amount):
                    return failed_response(
                        message="Insufficent balance in wallet. Please top up wallet"
                    )
                # enroll the user
                self.enroll_user_no_discount(
                    request.user, courses, wallet, total_amount
                )
                message = "Purchase successful"
                return success_response(message=message)
        return failed_response(data=serializer.errors, message="Invalid data provided")

    def validate_discount_code(self, discount_code, user):
        """
        Validate the discount code and return the discount code object if valid.
        """
        discount_code_obj = DiscountCode.objects.filter(code=discount_code).first()
        if not discount_code_obj:
            raise ValidationError(_("Discount code is not valid"))
        if discount_code_obj.used_count >= discount_code_obj.max_uses:
            raise ValidationError(_("Discount code has reached its maximum usage"))
        if not discount_code_obj.is_active:
            raise ValidationError(_("Discount code is not active"))
        if discount_code_obj.has_user_used_code(user):
            raise ValidationError(_("Discount code has already been used"))
        return discount_code_obj

    def calculate_discount(self, courses, discount_code_obj):
        """
        Calculate the total discount amount for the given courses and discount code.
        """
        total_discount_amount = Decimal("0.00")
        original_total_amount = Decimal("0.00")
        for course in courses:
            if discount_code_obj.is_valid_for_course(course):
                total_discount_amount += (
                    discount_code_obj.percentage_off / 100
                ) * course.amount
            original_total_amount += course.amount
        return total_discount_amount, original_total_amount

    def enroll_user(self, user, courses, user_wallet, total_cost, discount_code_obj):
        """
        Enroll the user in the courses and deduct the amount from their wallet.
        """
        with transaction.atomic():
            try:
                Enrollment(user, courses).enroll_user()
                user_wallet.balance -= total_cost
                user_wallet.save()

                # save the discount code usage
                UsedDiscountCode.objects.create(
                    user=user,
                    discount_code=discount_code_obj,
                )
                # update the discount code usage count
                discount_code_obj.used_count += 1
                discount_code_obj.save()
            except Exception as e:
                raise e

    def enroll_user_no_discount(self, user, courses, user_wallet, total_cost):
        """
        Enroll the user in the courses and deduct the amount from their wallet.
        """
        with transaction.atomic():
            try:
                Enrollment(user, courses).enroll_user()
                user_wallet.balance -= total_cost
                user_wallet.save()

            except Exception as e:
                raise e

    def _has_enough_wallet_fund(self, wallet, total_amount):
        # Check wallet balance
        if wallet.balance < total_amount:
            return False
        return True


class PurchaseCourse(APIView):
    """Check if a discount code is valid for a course."""

    permission_classes = [IsAuthenticated]
    serializer_class = PurchaseCourseSerializer

    def post(self, request):
        """
        Check if a discount code is valid for a course.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = request.user
            courses = serializer.validated_data["courses"]
            valid_courses = []
            total_amount = 0
            for course_id in courses:
                # check if the course exists
                try:
                    course = Course.objects.get(id=course_id)
                except Course.DoesNotExist:
                    return failed_response(
                        message=_(f"course with id {course_id} does not exist")
                    )
                total_amount += course.amount
                valid_courses.append(course)

            # check if the user has enough balance in their wallet
            wallet = Wallet.objects.get_or_create(user=user)[0]
            if wallet.balance < total_amount:
                return failed_response(
                    message=_(
                        f"Insufficient balance in wallet. User has {wallet.balance}, but needs {total_amount}"
                    )
                )

            # Enroll the user into the courses
            with transaction.atomic():
                try:
                    self.enroll_user(user, valid_courses, wallet, total_amount)
                except ValueError as err:
                    return failed_response(message=str(err))
                except Exception as err:
                    raise err

            # Return the purchase ID to the client

            return success_response(message=_("Purchase successful"))
        return failed_response(data=serializer.errors, message="Invalid data provided")

    def enroll_user(self, user, courses, user_wallet, total_cost):
        """
        Enroll the user in the course.
        """
        Enrollment(user, courses).enroll_user()
        # deduct the amount from the user's wallet
        user_wallet.balance -= total_cost
        user_wallet.save()


class MyLearningDashboard(viewsets.ViewSet):
    """Allow users track their learning"""

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=["get"])
    def enrolled_pathways(self, request):
        """
        Get all enrolled pathways for the authenticated user.
        """
        pathways = (
            CoursePathWay.objects.filter(
                course__courseenrollment__user=request.user
            ).distinct()
            # .values("id", "title", "description")
        )
        serializer = ReturnCoursePathWaySerializer(
            pathways, many=True, context={"request": request}
        )
        return success_response(
            data=serializer.data,
            message="Pathways retrieved successfully",
        )

    @action(detail=False, methods=["get"])
    def enrolled_courses(self, request, enrolled_pathway_id):
        """
        Get all enrolled courses for the authenticated user.
        """
        queryset = Course.objects.filter(
            courseenrollment__user=request.user,
            courseenrollment__is_active=True,
            course_pathway__id=enrolled_pathway_id,
        ).distinct()
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = EnrolledCourseSerializer(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    def enrolled_modules(self, request, enrolled_course_id):
        """
        Get all enrolled modules for the authenticated user.
        """
        queryset = (
            Module.objects.filter(
                usermoduleprogress__user=request.user,
                course__courseenrollment__is_active=True,
                course_id=enrolled_course_id,
            )
            .distinct()
            .order_by("order")
        )
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = EnrolledModuleSerializer(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=["get"])
    def detailed_module(self, request, module_id):
        """
        Get detailed information about a specific module.
        """
        try:
            module = Module.objects.get(pk=module_id)
            serializer = DetailedReturnModuleSerializerJames(
                module, context={"request": request}
            )
            return success_response(
                data=serializer.data, message="Module retrieved successfully"
            )
        except Module.DoesNotExist:
            return failed_response(message="Module not found", status_code=404)
        except Exception as e:
            return failed_response(
                message=f"Error retrieving module: {str(e)}", status_code=500
            )

    @action(detail=False, methods=["post"])
    def submit_lesson_quiz_score(self, request):
        """
        Submit the score for a lesson quiz.
        """
        user = request.user
        serializer = LessonQuizScoreSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            lesson_id = serializer.validated_data["lesson"]
            time_spent = serializer.validated_data["time_spent"]
            lesson = Lesson.objects.filter(id=lesson_id).first()
            if not lesson:
                return failed_response(message="Lesson not found", status_code=404)

            score = serializer.validated_data["score"]
            with transaction.atomic():
                has_previous_score = LessonQuizScore.objects.filter(
                    lesson=lesson, user=user
                ).exists()
                if has_previous_score:
                    return failed_response(message="You have already taken this quiz.")
                # record the score
                new_score = LessonQuizScore.objects.create(
                    lesson=lesson, user=user, score=score
                )

                # unlock the next lesson for that user if the user is a user. if the user is a student, do not not unlock till the teacher do that himself
                # if user.role != "student":
                #     # check if the user is a normal user. unlock the next lesson and module
                #     handle_lesson_completion(
                #         user=user, lesson=lesson, quiz_score=new_score
                #     )

                handle_quiz_submission_earn_point(
                    user=user,
                    lesson=lesson,
                    quiz_score=score,
                    time_spent=time_spent,
                )

                serializer = ReturnLessonQuizScoreSerializer(
                    new_score, many=False, context={"request": request}
                )
                return success_response(
                    data=serializer.data,
                    message="Lesson quiz score submitted successfully",
                )

        return failed_response(data=serializer.errors, message="Invalid data provided")

    @action(detail=True, methods=["get"])
    def unlock_next_lesson(self, request, pk):
        """
        Unlock the next lesson for the user.
        1: Get current lesson and mark it as completed
        2: If there's a next lesson in the same module, unlock it and make it current
        3: If no next lesson, complete current module and unlock first lesson of next module
        4: If no next module, complete the course
        """
        try:
            user = request.user
            lesson = Lesson.objects.get(pk=pk)
            course = lesson.module.course

            # Verify user is enrolled in the course
            if not CourseEnrollment.objects.filter(
                user=user, course=course, is_active=True
            ).exists():
                return failed_response(
                    message="You are not enrolled in this course",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            # Mark current lesson as completed
            current_lesson_progress = UserLessonProgress.objects.get(
                user=user, lesson=lesson
            )
            current_lesson_progress.status = UserLessonProgress.Status.COMPLETED
            current_lesson_progress.is_current = False
            current_lesson_progress.completed_date = timezone.now()
            current_lesson_progress.save()

            print(
                f"this is the current_leson... {current_lesson_progress.is_current} : {current_lesson_progress.status}"
            )

            # Get next lesson in the same module
            next_lesson = Lesson.objects.filter(
                module=lesson.module, order=lesson.order + 1
            ).first()

            if next_lesson:
                # Unlock and set next lesson as current
                next_lesson_progress, created = (
                    UserLessonProgress.objects.get_or_create(
                        user=user,
                        lesson=next_lesson,
                        defaults={
                            "status": UserLessonProgress.Status.NOT_STARTED,
                            "is_locked": False,
                            "is_current": True,
                            "started_on": timezone.now(),
                        },
                    )
                )
                if not created:
                    next_lesson_progress.is_locked = False
                    next_lesson_progress.is_current = True
                    next_lesson_progress.started_on = timezone.now()
                    next_lesson_progress.save()
                return success_response(message="Next lesson unlocked")

            # If no next lesson, complete current module and check for next module
            current_module = lesson.module
            current_module_progress = UserModuleProgress.objects.get(
                user=user, module=current_module
            )
            current_module_progress.update_progress()  # This marks the module as completed

            # Find next module
            next_module = Module.objects.filter(
                course=course, order=current_module.order + 1
            ).first()

            if next_module:
                # Create/Update progress for next module
                next_module_progress, created = (
                    UserModuleProgress.objects.get_or_create(
                        user=user,
                        module=next_module,
                        defaults={
                            "is_current": True,
                            "is_locked": False,
                            "started_on": timezone.now(),
                        },
                    )
                )
                if not created:
                    next_module_progress.is_current = True
                    next_module_progress.is_locked = False
                    next_module_progress.started_on = timezone.now()
                    next_module_progress.save()

                # Get and unlock first lesson of next module
                first_lesson = (
                    Lesson.objects.filter(module=next_module).order_by("order").first()
                )

                if first_lesson:
                    first_lesson_progress, created = (
                        UserLessonProgress.objects.get_or_create(
                            user=user,
                            lesson=first_lesson,
                            defaults={
                                "status": UserLessonProgress.Status.NOT_STARTED,
                                "is_locked": False,
                                "is_current": True,
                                "started_on": timezone.now(),
                            },
                        )
                    )
                    if not created:
                        first_lesson_progress.is_locked = False
                        first_lesson_progress.is_current = True
                        first_lesson_progress.started_on = timezone.now()
                        first_lesson_progress.save()

                    return success_response("Next module and lesson unlocked")

            # If no next module, complete the course
            course_enrollment = CourseEnrollment.objects.get(user=user, course=course)
            course_enrollment.completed = True
            course_enrollment.save()

            return success_response(message="Course completed!")

        except Lesson.DoesNotExist:
            return failed_response(message="Lesson not found", status_code=404)
        except (UserLessonProgress.DoesNotExist, UserModuleProgress.DoesNotExist):
            return failed_response(
                message="Progress tracking not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return failed_response(
                message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["get"])
    def unlock_next_module(self, request, pk):
        """
        Unlock the next module for the user.
        1: Get current module and mark it as completed
        2: Find and unlock the next module in sequence
        3: If next module exists, unlock its first lesson
        4: If no next module, complete the course
        """
        try:
            user = request.user
            current_module = Module.objects.get(pk=pk)
            course = current_module.course

            # Verify user is enrolled in the course
            if not CourseEnrollment.objects.filter(
                user=user, course=course, is_active=True
            ).exists():
                return failed_response(
                    message="You are not enrolled in this course",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            # Mark current module as completed
            current_module_progress = UserModuleProgress.objects.get(
                user=user, module=current_module
            )
            current_module_progress.update_progress()  # This marks the module as completed

            # Mark all lessons in current module as completed
            UserLessonProgress.objects.filter(
                user=user,
                lesson__module=current_module,
                status__in=[
                    UserLessonProgress.Status.NOT_STARTED,
                    UserLessonProgress.Status.IN_PROGRESS,
                ],
            ).update(
                status=UserLessonProgress.Status.COMPLETED,
                is_locked=False,
                is_current=False,
                completed_date=timezone.now(),
            )

            # Find next module
            next_module = Module.objects.filter(
                course=course, order=current_module.order + 1
            ).first()

            if next_module:
                # Create/Update progress for next module
                next_module_progress, created = (
                    UserModuleProgress.objects.get_or_create(
                        user=user,
                        module=next_module,
                        defaults={
                            "is_current": True,
                            "is_locked": False,
                            "started_on": timezone.now(),
                        },
                    )
                )
                if not created:
                    next_module_progress.is_current = True
                    next_module_progress.is_locked = False
                    next_module_progress.started_on = timezone.now()
                    next_module_progress.save()

                # Get and unlock first lesson of next module
                first_lesson = (
                    Lesson.objects.filter(module=next_module).order_by("order").first()
                )

                if first_lesson:
                    first_lesson_progress, created = (
                        UserLessonProgress.objects.get_or_create(
                            user=user,
                            lesson=first_lesson,
                            defaults={
                                "status": UserLessonProgress.Status.NOT_STARTED,
                                "is_locked": False,
                                "is_current": True,
                                "started_on": timezone.now(),
                            },
                        )
                    )
                    if not created:
                        first_lesson_progress.is_locked = False
                        first_lesson_progress.is_current = True
                        first_lesson_progress.started_on = timezone.now()
                        first_lesson_progress.save()

                    return success_response(
                        message="Next module and lesson unlocked",
                        data={
                            "next_module": {
                                "id": next_module.id,
                                "title": next_module.title,
                                "description": next_module.description,
                                "order": next_module.order,
                            },
                            "first_lesson": {
                                "id": first_lesson.id,
                                "title": first_lesson.title,
                                "order": first_lesson.order,
                            },
                        },
                    )

                return success_response(
                    message="Next module unlocked but no lessons found",
                    data={
                        "next_module": {
                            "id": next_module.id,
                            "title": next_module.title,
                            "description": next_module.description,
                            "order": next_module.order,
                        }
                    },
                )

            # If no next module, complete the course
            course_enrollment = CourseEnrollment.objects.get(user=user, course=course)
            course_enrollment.completed = True
            course_enrollment.save()

            return success_response(
                message="Course completed!",
                data={
                    "course": {
                        "id": course.id,
                        "title": course.title,
                    }
                },
            )

        except Module.DoesNotExist:
            return failed_response(
                message="Module not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except (UserModuleProgress.DoesNotExist, CourseEnrollment.DoesNotExist):
            return failed_response(
                message="Progress tracking not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return failed_response(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def submit_asssignment(self, request):
        """
        Submit an assignment.
        """
        user = request.user
        serializer = ModuleAssignmentResponseSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # check if a user has submitted a response for this assignment before
            assignment_id = serializer.validated_data["assignment"]
            previous_assignment_resp = ModuleAssignmentResponse.objects.filter(
                assignment=assignment_id, user=user
            ).first()
            if previous_assignment_resp:
                return failed_response(
                    message="You have already submitted a response for this assignment."
                )
            resp = serializer.save(user=user)
            module = resp.assignment.module

            # if user.role != "student":
            #     handle_module_completion(user=user, module=module)
            return success_response(
                data=serializer.data,
                message="Assignment submitted successfully",
            )
        return failed_response(data=serializer.errors, message="Invalid data provided")

    @action(detail=False, methods=["post"])
    def submit_project(self, request):
        """
        Submit a projet.
        """
        user = request.user
        serializer = CourseProjectResponseSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid(raise_exception=True):
            project_id = serializer.validated_data["project"]
            # check if the user has submitd a project response for this before
            previous_submission = CourseProjectResponse.objects.filter(
                project=project_id, user=user
            ).exists()
            if previous_submission:
                return failed_response(
                    message="You have already submitted a response for this project."
                )
            project = serializer.save(user=user)
            # create a certificate for that user
            Certificate.objects.create(user=request.user, course=project.project.course)
            return success_response(
                data=serializer.data, message="Project submitted successfully"
            )
        return failed_response(data=serializer.errors, message="Invalid data provided")

    @action(detail=False, methods=["post"])
    def unlock_course(self, request):
        """Endpoint to allow school students unlock courses based on the code sent to their mail

        -Ensure the code belongs to that user to prevent others using someones elses
        - ensure the code can only be used once
        - Enroll the user to all courses in the pathway connect to that quote
        """
        user = request.user
        serializer = UnlockCourseWithCodeSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            token = serializer.validated_data["token"]
            # get the token associated with
            quote_token = QouteToken.objects.filter(
                user=request.user, token=token, is_used=False
            ).first()
            if not quote_token:
                return failed_response(
                    message="Token is either invalid, used or was not issued to you."
                )
            # get the all courses associalted with that token's quote and enroll the user to them all
            path_way = quote_token.qoute.course_pathway
            level = quote_token.qoute.level
            courses = Course.objects.filter(course_pathway=path_way, level=level)
            # enroll the user
            with transaction.atomic():
                try:
                    Enrollment(user, courses).enroll_user()
                except ValueError as ve:
                    return failed_response(message=str(ve))
                except Exception as err:
                    raise err
                # update the token
                quote_token.is_used = True
                quote_token.save()
                return success_response()

        return failed_response(message="Invalid data provided", data=serializer.errors)

    @action(detail=False, methods=["get"])
    def my_badges(self, request):
        """return all badges a user has earned"""
        user = request.user
        my_badges = UserBadge.objects.filter(user=user).order_by("-created_at")
        serializer = UserBadgeSerializer(my_badges, many=True)
        return success_response(data=serializer.data, message="My badges")

    @action(detail=False, methods=["get"])
    def my_cerificates(self, request):
        """return all certificated a user has earned"""
        user = request.user
        level = request.query_params.get("level")
        stage = request.query_params.get("stage")
        my_certificates = Certificate.objects.filter(user=user).order_by("-created_at")
        if level:
            my_certificates = my_certificates.filter(course__level__icontains=level)
        if stage:
            my_certificates = my_certificates.filter(course__stage__icontains=stage)
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(my_certificates, request)
        serializer = CertificateSerializer(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    def my_video_library(self, request):
        user = request.user
        q = request.query_params.get("q")
        video_embeds = Lesson.objects.filter(userlessonprogress__user=user)
        if q:
            video_embeds = video_embeds.filter(
                module__course__course_pathway__title__icontains=q
            )
        # add paginations
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(video_embeds, request)

        # Serialize the paginated queryset
        serializer = VideoEmbedSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=["get"])
    def get_assignment_response(self, request, pk):
        """Get the response of a submittted assignment so display a feedback for a user"""
        user = request.user
        try:
            assignment = Assignment.objects.get(id=pk)
        except Assignment.DoesNotExist:
            return failed_response(message="Assignment not found", status_code=404)
        assignment_response = ModuleAssignmentResponse.objects.filter(
            assignment=assignment, user=user
        ).first()
        serializer = ReturnModuleAssignmentResponseSerializer(
            assignment_response, many=False, context={"request": request}
        )
        return success_response(data=serializer.data)

    @action(detail=True, methods=["get"])
    def get_project_response(self, request, pk):
        """Get the response of a submittted project so display a feedback for a user"""
        user = request.user
        try:
            project = CourseProject.objects.get(id=pk)
        except CourseProject.DoesNotExist:
            return failed_response(message="Project not found", status_code=404)
        project_response = CourseProjectResponse.objects.filter(
            project=project, user=user
        ).first()
        serializer = ReturnCourseProjectResponseSerializer(
            project_response, many=False, context={"request": request}
        )
        return success_response(data=serializer.data)


class UserCourseStreakView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def get_date_range(self, period):
        today = timezone.now()

        if period == "this_week":
            # Start from Monday of current week to Sunday
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == "last_7days":
            # Last 7 days including today
            start_date = today - timedelta(days=6)
            end_date = today
        elif period == "last_6months":
            # Last 6 months from today
            start_date = today - timedelta(days=180)
            end_date = today
        elif period == "year":
            # Last 365 days
            start_date = today - timedelta(days=365)
            end_date = today
        else:
            # Default to this week if invalid period
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

        return start_date.date(), end_date.date()

    def get(self, request, pathway_id):
        # Get period from query params
        period = request.query_params.get("period", "this_week")

        # Get date range based on period
        start_date, end_date = self.get_date_range(period)

        # Base queryset filtered by the authenticated user
        queryset = CourseStreak.objects.filter(
            user=request.user,  # Filter by authenticated user
            created_at__date__range=[start_date, end_date],
            course__course_pathway_id=pathway_id,
        )

        # For longer periods (6 months, 1 year), we might want to group by weeks instead of days
        if period in ["last_6months", "year"]:
            # Group by week number instead of weekday
            daily_stats = (
                queryset.annotate(week=ExtractWeek("created_at"))
                .values("course__title", "week")
                .annotate(average_streak=Avg("streak_score"))
                .order_by("course__title", "week")
            )

            # Generate week labels
            num_weeks = (end_date - start_date).days // 7 + 1
            labels = [f"Week {i+1}" for i in range(num_weeks)]

            # Format response data
            response_data = {}
            for stat in daily_stats:
                course_title = stat["course__title"]
                if course_title not in response_data:
                    response_data[course_title] = {
                        "course": course_title,
                        "data": [0] * num_weeks,
                    }
                week_idx = (
                    stat["week"] % num_weeks
                )  # Handle week numbers that wrap around
                response_data[course_title]["data"][week_idx] = round(
                    stat["average_streak"] * 100, 2
                )

        else:
            # For this_week and last_7days, group by day
            daily_stats = (
                queryset.annotate(weekday=ExtractWeekDay("created_at"))
                .values("course__title", "weekday")
                .annotate(average_streak=Avg("streak_score"))
                .order_by("course__title", "weekday")
            )

            # Format response data
            response_data = {}
            weekdays = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            labels = weekdays

            for stat in daily_stats:
                course_title = stat["course__title"]
                if course_title not in response_data:
                    response_data[course_title] = {
                        "course": course_title,
                        "data": [0] * 7,
                    }
                weekday_idx = (stat["weekday"] - 2) % 7  # Convert to 0=Monday
                response_data[course_title]["data"][weekday_idx] = round(
                    stat["average_streak"] * 100, 2
                )

        # Get enrolled courses with no streak data
        enrolled_courses = CourseEnrollment.objects.filter(
            user=request.user, is_active=True
        ).values_list("course__title", flat=True)

        # Add enrolled courses with no streak data
        for course_title in enrolled_courses:
            if course_title not in response_data:
                response_data[course_title] = {
                    "course": course_title,
                    "data": [0]
                    * (num_weeks if period in ["last_6months", "year"] else 7),
                }

        # Convert to list format
        formatted_data = {
            "labels": labels,
            "datasets": [
                {"label": course_title, "data": course_data["data"]}
                for course_title, course_data in response_data.items()
            ],
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        return Response(formatted_data)


class CourseRatingViewSet(viewsets.ViewSet):

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Custom permission handling."""
        if self.action == "destroy":
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["get"])
    def get_all(self, request, pk):

        try:
            course = Course.objects.get(id=pk)
        except Course.DoesNotExist:
            return http.failed_response(
                None, _("Course Not Found"), status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            ratings = CourseRating.objects.filter(course=course).order_by("-created_at")
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(ratings, request)
            serializer = CourseRatingSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return failed_response(
                message=f"Error retrieving course rating: {str(e)}", status_code=500
            )

    @action(detail=True, methods=["get"])
    def get_by_id(self, request, pk=None):
        """Get a specific course rating by ID."""

        course_id = request.query_params.get("course_id")

        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return http.failed_response(
                None,
                _("User not found."),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        user_rating = CourseRating.objects.filter(user=user)

        if course_id:
            user_rating = user_rating.filter(course_id=course_id)

        serializer = ReturnCourseRatingSerializer(user_rating, many=True)
        return http.success_response(data=serializer.data)

    def create(self, request):
        """Create a rating for a course."""
        try:

            # Create the rating
            serializer = CourseRatingSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                rating = serializer.save()

                # Log rating activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="course",
                    description=f"Rated course: {rating.course.title}",
                )

                # Serialize and return the created rating
                return_serializer = ReturnCourseRatingSerializer(rating)
                return success_response(
                    data=return_serializer.data,
                    message="Rating created successfully.",
                    status_code=status.HTTP_201_CREATED,
                )
            else:
                return failed_response(
                    data=serializer.errors,
                    message="Invalid data provided.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            # Catch and return any unexpected exceptions
            return failed_response(
                message=f"An error occurred while creating the rating: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, pk=None):
        """Update an existing rating."""
        try:
            user_rating = CourseRating.objects.get(pk=pk)
        except CourseRating.DoesNotExist:
            return failed_response(
                message="user course rating not found", status_code=404
            )

        serializer = UpdateCourseRatingSerializer(
            user_rating, data=request.data, partial=True
        )

        if serializer.is_valid(raise_exception=True):
            updated_user_rating = serializer.save()

            # Log user rating update activity
            utils.log_user_activity(
                user=request.user,
                activity_type="course",
                description=f"Updated course rating: {updated_user_rating.course.title}",
            )

            return_serializer = ReturnCourseRatingSerializer(updated_user_rating)
            return success_response(
                data=return_serializer.data,
                message="course rating updated successfully",
            )
        return failed_response(data=serializer.errors, message="Invalid data provided")

    def destroy(self, request, pk=None):
        """Delete course rating."""
        try:
            user_rating = CourseRating.objects.get(pk=pk)
            user_name = user_rating.user.full_name
            user_rating.delete()

            # Log user rating deletion activity
            utils.log_user_activity(
                user=request.user,
                activity_type="course",
                description=f"Deleted user: {user_name} rating",
            )

            return success_response(
                message="user course rating deleted successfully",
                status_code=200,
            )
        except CourseRating.DoesNotExist:
            return failed_response(
                message="user course rating not found", status_code=404
            )
        except Exception as e:
            return failed_response(
                message=f"Error deleting user rating: {str(e)}", status_code=500
            )


class LessonRatingViewSet(viewsets.ViewSet):

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Custom permission handling."""
        if self.action == "destroy":
            permission_classes = [permissions.IsAdminUser | IsSchoolAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["get"])
    def get_all(self, request, pk):

        try:
            lesson = Lesson.objects.get(id=pk)
        except Lesson.DoesNotExist:
            return http.failed_response(
                None, _("lesson not found"), status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            ratings = LessonRating.objects.filter(lesson=lesson).order_by("-created_at")
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(ratings, request)
            serializer = LessonRatingSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return failed_response(
                message=f"Error retrieving lession rating: {str(e)}", status_code=500
            )

    @action(detail=True, methods=["get"])
    def get_by_id(self, request, pk=None):
        """Get a specific course rating by ID."""

        lesson_id = request.query_params.get("lesson_id")

        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return http.failed_response(
                None,
                _("User not found."),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        user_rating = LessonRating.objects.filter(user=user)

        if lesson_id:
            user_rating = user_rating.filter(lesson_id=lesson_id)

        serializer = ReturnLessonRatingSerializer(user_rating, many=True)
        return http.success_response(data=serializer.data)

    def create(self, request):
        """Create a rating for a course."""
        try:

            # Create the rating
            serializer = LessonRatingSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                rating = serializer.save()

                # Log rating activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="course",
                    description=f"Rated lesson: {rating.lesson.title}",
                )

                # Serialize and return the created rating
                return_serializer = ReturnLessonRatingSerializer(rating)
                return success_response(
                    data=return_serializer.data,
                    message="Rating created successfully.",
                    status_code=status.HTTP_201_CREATED,
                )
            else:
                return failed_response(
                    data=serializer.errors,
                    message="Invalid data provided.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            # Catch and return any unexpected exceptions
            return failed_response(
                message=f"An error occurred while creating the rating: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, pk=None):
        """Update an existing rating."""
        try:
            user_rating = LessonRating.objects.get(pk=pk)
        except LessonRating.DoesNotExist:
            return failed_response(
                message="user lesson rating not found", status_code=404
            )

        serializer = UpdateLessonRatingSerializer(
            user_rating, data=request.data, partial=True
        )

        if serializer.is_valid(raise_exception=True):
            updated_user_rating = serializer.save()

            # Log user rating update activity
            utils.log_user_activity(
                user=request.user,
                activity_type="course",
                description=f"Updated lesson rating: {updated_user_rating.lesson.title}",
            )

            return_serializer = ReturnLessonRatingSerializer(updated_user_rating)
            return success_response(
                data=return_serializer.data,
                message="lesson rating updated successfully",
            )
        return failed_response(data=serializer.errors, message="Invalid data provided")

    def destroy(self, request, pk=None):
        """Delete lesson rating."""
        try:
            user_rating = LessonRating.objects.get(pk=pk)
            email = user_rating.user.email
            user_rating.delete()

            # Log user rating deletion activity
            utils.log_user_activity(
                user=request.user,
                activity_type="course",
                description=f"Deleted user: {email} lesson rating",
            )

            return success_response(
                message="user lesson rating deleted successfully",
                status_code=200,
            )
        except LessonRating.DoesNotExist:
            return failed_response(
                message="user lesson rating not found", status_code=404
            )
        except Exception as e:
            return failed_response(
                message=f"Error deleting user lesson rating: {str(e)}", status_code=500
            )


class ReportCardView(APIView):
    """Report card data for a particular course"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReportCardSerilaizer

    @action(detail=True, methods=["get"])
    def get(self, request, course_id, user_id):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return failed_response(message="User not found", status_code=404)

        try:
            course = Course.objects.prefetch_related(
                Prefetch("module_set", queryset=Module.objects.all()),
            ).get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Existing score calculation logic (as in previous implementation)
        modules = course.module_set.all()

        quiz_scores = (
            LessonQuizScore.objects.filter(user=user, lesson__module__course=course)
            .values("lesson__module__title")
            .annotate(module_quiz_score=Sum("score"))
        )

        assignment_scores = (
            ModuleAssignmentResponse.objects.filter(
                user=user, assignment__module__course=course
            )
            .values("assignment__module__title")
            .annotate(module_assignment_score=Sum("score"))
        )

        quiz_score_map = {
            item["lesson__module__title"]: item["module_quiz_score"]
            for item in quiz_scores
        }
        assignment_score_map = {
            item["assignment__module__title"]: item["module_assignment_score"]
            for item in assignment_scores
        }

        modules_data = {}
        for module in modules:
            module_quiz_score = quiz_score_map.get(module.title, Decimal("0.00"))
            module_assignment_score = assignment_score_map.get(
                module.title, Decimal("0.00")
            )
            module_total_score = module_quiz_score + module_assignment_score

            modules_data[module.title] = {
                "total_score": module_total_score,
                "quiz_scores": module_quiz_score,
                "assignment_scores": module_assignment_score,
            }

        project_scores = CourseProjectResponse.objects.filter(
            user=user, project__course=course
        ).aggregate(total_project_score=Sum("score"))["total_project_score"] or Decimal(
            "0.00"
        )

        total_points = (
            UserEarnedPoint.objects.filter(user=user, course=course).aggregate(
                total_points=Sum("points")
            )["total_points"]
            or 0
        )

        points_breakdown = (
            UserEarnedPoint.objects.filter(user=user, course=course)
            .values("point_type")
            .annotate(type_points=Sum("points"))
        )

        total_quiz_scores = sum(
            module["quiz_scores"] for module in modules_data.values()
        )
        total_assignment_scores = sum(
            module["assignment_scores"] for module in modules_data.values()
        )
        total_score = total_quiz_scores + total_assignment_scores + project_scores

        return Response(
            {
                "total_score": total_score,
                "scores_breakdown": {
                    "quiz_scores": total_quiz_scores,
                    "assignment_scores": total_assignment_scores,
                    "project_scores": project_scores,
                },
                "modules": modules_data,
                "total_points": total_points,
                "points_breakdown": list(points_breakdown),
                "extra_info": self.require_score_info(course, total_score, user),
                # 'course_stats': {
                #     'total_modules': total_modules,
                #     'total_lessons': total_lessons
                # }
            },
            status=status.HTTP_200_OK,
        )

    def require_score_info(self, course, total_score, user):
        """compute other caslculations"""
        # # Count total modules and lessons
        total_modules = Module.objects.filter(course=course).count()
        total_lessons = Lesson.objects.filter(module__course=course).count()

        # total_modules = course.module_set.count()
        # total_lessons = course.module_set.prefetch_related("lesson").aggregate(
        #     total_lessons=Sum(Count("lesson_set"))
        # )["total_lessons"]

        required_score = (
            total_lessons + total_modules + 1
        ) * 100  # where +1 acccount for project in the course
        total_badges_earned = (
            total_modules + 1
        )  # where +1 account for the bad for completing a course
        user_completed_course = CourseProjectResponse.objects.filter(
            user=user, project__course=course
        ).exists()
        completed_data = None
        if user_completed_course:
            module = UserModuleProgress.objects.filter(
                user=user, module__course=course
            ).last()
            completed_data = module.completed_date if module else None

        data = {
            "required_score": required_score,
            "total_badges_earned": total_badges_earned,
            "completed_date": completed_data,
        }
        return data


class PortfolioProjectsViewSet(viewsets.ModelViewSet):
    """Portfolio Content API"""

    queryset = PortfolioContent.objects.all()
    serializer_class = PortfolioContentSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]  # Only authenticated users can access

    def get_queryset(self):
        # Filter portfolio contents to only include those belonging to the current user
        query_set = self.queryset.filter(user=self.request.user)
        content_type = self.request.query_params.get("content_type")
        if content_type:
            query_set = query_set.filter(content_type=content_type)
        return query_set

    def perform_create(self, serializer):
        # Automatically set the user to the current authenticated user
        serializer.save(user=self.request.user)


class StudentProgressPorfolioSection(APIView):
    """Student Progress API"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # Get the user's enrolled courses
        enrolled_courses = CourseEnrollment.objects.filter(user=user).values_list(
            "course_id", flat=True
        )

        # Total quizzes available in enrolled courses
        total_quizzes = Lesson.objects.filter(
            module__course_id__in=enrolled_courses
        ).count()

        # Total quizzes completed by the user
        total_quizzes_completed = LessonQuizScore.objects.filter(user=user).count()

        # Total assignments available in enrolled courses
        total_assignments = Assignment.objects.filter(
            module__course_id__in=enrolled_courses
        ).count()

        # Total assignments completed by the user
        total_assignments_completed = ModuleAssignmentResponse.objects.filter(
            user=user
        ).count()

        # Total courses enrolled by the user
        total_courses = enrolled_courses.count()

        # Total certificates earned by the user
        total_certificates = Certificate.objects.filter(user=user).count()

        # Total projects available in enrolled courses
        total_projects = CourseProject.objects.filter(
            course_id__in=enrolled_courses
        ).count()

        # Total projects completed by the user
        total_projects_completed = CourseProjectResponse.objects.filter(
            user=user
        ).count()

        # Calculate percentages
        quiz_percentage = (
            (total_quizzes_completed / total_quizzes * 100) if total_quizzes > 0 else 0
        )
        assignment_percentage = (
            (total_assignments_completed / total_assignments * 100)
            if total_assignments > 0
            else 0
        )
        certificate_percentage = (
            (total_certificates / total_courses * 100) if total_courses > 0 else 0
        )
        project_percentage = (
            (total_projects_completed / total_projects * 100)
            if total_projects > 0
            else 0
        )

        data = {
            "quiz_percentage": quiz_percentage,
            "assignment_percentage": assignment_percentage,
            "certificate_percentage": certificate_percentage,
            "project_percentage": project_percentage,
        }
        return success_response(data)


class UserDashboardStat(APIView):
    """Student dhansboard stat API"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        this endpoint return
        -  completed courses
        - completed projects
        - total certifcated eanrned
        - total points earned

        Since the certifcate is only issues when a user completes a course,
        A course as well can only be complete when a project jas been submitted.
        so therefore

        total_certficate  = total course, total project.


        """
        user = request.user

        # Total certificates earned by the user
        total_certificates = Certificate.objects.filter(user=user).count()
        points = (
            UserEarnedPoint.objects.filter(user=user).aggregate(
                total_points=Sum("points")
            )["total_points"]
            or 0
        )

        data = {
            "total_certificates_earned": total_certificates,
            "total_course_completed": total_certificates,
            "total_projects_completed": total_certificates,
            "total_points_earned": points,
        }
        return success_response(data)


class FlashcardViewSet(viewsets.ViewSet):
    """
    ViewSet for managing flashcards.
    Provides CRUD operations and custom actions.
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Custom permission handling."""
        if self.action in ["list", "retrieve", "get_by_course"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def list(self, request):
        """Get all flashcards."""
        try:
            module_id = request.query_params.get("module_id")
            flashcards = Flashcard.objects.all()

            if module_id:
                flashcards = flashcards.filter(module_id=module_id)

            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(flashcards, request)
            serializer = ReturnFlashcardSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return failed_response(
                message=f"Error retrieving flashcards: {str(e)}", status_code=500
            )

    @action(detail=False, methods=["get"])
    def get_by_course(self, request, course_id):
        """Get all flashcards for a specific course."""
        try:
            flashcards = Flashcard.objects.filter(module__course_id=course_id)
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(flashcards, request)
            serializer = ReturnFlashcardSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return failed_response(
                message=f"Error retrieving flashcards: {str(e)}", status_code=500
            )

    def retrieve(self, request, pk=None):
        """Get a specific flashcard by ID."""
        try:
            flashcard = get_object_or_404(Flashcard, pk=pk)
            serializer = ReturnFlashcardSerializer(flashcard)
            return success_response(
                data=serializer.data, message="Flashcard retrieved successfully"
            )
        except Exception as e:
            return failed_response(
                message=f"Error retrieving flashcard: {str(e)}", status_code=500
            )

    def create(self, request):
        """Create a new flashcard."""
        try:
            serializer = FlashcardSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                flashcard = serializer.save()

                # Log flashcard creation activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="course",
                    description=f"Created new flashcard: {flashcard.question}",
                )

                return_serializer = ReturnFlashcardSerializer(flashcard)
                return success_response(
                    data=return_serializer.data,
                    message="Flashcard created successfully",
                    status_code=status.HTTP_201_CREATED,
                )
            return failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except Exception as e:
            return failed_response(
                message=f"Error creating flashcard: {str(e)}", status_code=500
            )

    def update(self, request, pk=None):
        """Update an existing flashcard."""
        try:
            flashcard = get_object_or_404(Flashcard, pk=pk)
            serializer = FlashcardSerializer(flashcard, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                updated_flashcard = serializer.save()

                # Log flashcard update activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="course",
                    description=f"Updated flashcard: {updated_flashcard.question}",
                )

                return_serializer = ReturnFlashcardSerializer(updated_flashcard)
                return success_response(
                    data=return_serializer.data,
                    message="Flashcard updated successfully",
                )
            return failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except Exception as e:
            return failed_response(
                message=f"Error updating flashcard: {str(e)}", status_code=500
            )

    def destroy(self, request, pk=None):
        """Delete a flashcard."""
        try:
            flashcard = get_object_or_404(Flashcard, pk=pk)
            question = flashcard.question
            flashcard.delete()

            # Log flashcard deletion activity
            utils.log_user_activity(
                user=request.user,
                activity_type="course",
                description=f"Deleted flashcard: {question}",
            )

            return success_response(
                message="Flashcard deleted successfully", status_code=200
            )
        except Exception as e:
            return failed_response(
                message=f"Error deleting flashcard: {str(e)}", status_code=500
            )

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """Create multiple flashcards at once."""
        try:
            # Expect an array of flashcard data
            flashcards_data = request.data.get("flashcards", [])
            if not flashcards_data:
                return failed_response(
                    message="No flashcards data provided",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            created_flashcards = []
            with transaction.atomic():  # Use transaction to ensure all or nothing
                for flashcard_data in flashcards_data:
                    serializer = FlashcardSerializer(data=flashcard_data)
                    if serializer.is_valid(raise_exception=True):
                        flashcard = serializer.save()
                        created_flashcards.append(flashcard)

                        # Log each flashcard creation
                        utils.log_user_activity(
                            user=request.user,
                            activity_type="course",
                            description=f"Created new flashcard: {flashcard.question}",
                        )

            # Serialize all created flashcards
            return_serializer = ReturnFlashcardSerializer(created_flashcards, many=True)
            return success_response(
                data=return_serializer.data,
                message=f"Successfully created {len(created_flashcards)} flashcards",
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
                message=f"Error creating flashcards: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LibraryViewSet(viewsets.ViewSet):
    """
    ViewSet for managing library content.
    Provides CRUD operations and custom actions.
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Custom permission handling."""
        if self.action in ["list", "retrieve", "get_by_pathway"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def list(self, request):
        """Get all library content."""
        try:
            pathway_id = request.query_params.get("pathway_id")
            library_type = request.query_params.get("library_type")

            queryset = Library.objects.all()

            if pathway_id:
                queryset = queryset.filter(pathway_id=pathway_id)

            if library_type:
                queryset = queryset.filter(library_type=library_type)

            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serializer = ReturnLibrarySerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return failed_response(
                message=f"Error retrieving library content: {str(e)}", status_code=500
            )

    @action(detail=False, methods=["get"])
    def get_by_pathway(self, request, pathway_id):
        """Get all library content for a specific pathway."""
        try:
            library_content = Library.objects.filter(pathway_id=pathway_id)
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(library_content, request)
            serializer = ReturnLibrarySerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return failed_response(
                message=f"Error retrieving library content: {str(e)}", status_code=500
            )

    def retrieve(self, request, pk=None):
        """Get a specific library content by ID."""
        try:
            library_content = get_object_or_404(Library, pk=pk)
            serializer = ReturnLibrarySerializer(library_content)
            return success_response(
                data=serializer.data, message="Library content retrieved successfully"
            )
        except Exception as e:
            return failed_response(
                message=f"Error retrieving library content: {str(e)}", status_code=500
            )

    def create(self, request):
        """Create new library content."""
        try:
            serializer = LibrarySerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                library_content = serializer.save(user=request.user)

                # Log creation activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="course",
                    description=f"Created new library content: {library_content.title}",
                )

                return_serializer = ReturnLibrarySerializer(library_content)
                return success_response(
                    data=return_serializer.data,
                    message="Library content created successfully",
                    status_code=status.HTTP_201_CREATED,
                )
            return failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except Exception as e:
            return failed_response(
                message=f"Error creating library content: {str(e)}", status_code=500
            )

    def update(self, request, pk=None):
        """Update existing library content."""
        try:
            library_content = get_object_or_404(Library, pk=pk)
            serializer = LibrarySerializer(
                library_content, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                updated_content = serializer.save()

                # Log update activity
                utils.log_user_activity(
                    user=request.user,
                    activity_type="course",
                    description=f"Updated library content: {updated_content.title}",
                )

                return_serializer = ReturnLibrarySerializer(updated_content)
                return success_response(
                    data=return_serializer.data,
                    message="Library content updated successfully",
                )
            return failed_response(
                data=serializer.errors, message="Invalid data provided"
            )
        except Exception as e:
            return failed_response(
                message=f"Error updating library content: {str(e)}", status_code=500
            )

    def destroy(self, request, pk=None):
        """Delete library content."""
        try:
            library_content = get_object_or_404(Library, pk=pk)
            title = library_content.title
            library_content.delete()

            # Log deletion activity
            utils.log_user_activity(
                user=request.user,
                activity_type="course",
                description=f"Deleted library content: {title}",
            )

            return success_response(
                message="Library content deleted successfully", status_code=200
            )
        except Exception as e:
            return failed_response(
                message=f"Error deleting library content: {str(e)}", status_code=500
            )
