from rest_framework import status, permissions
from rest_framework.views import APIView
from django.db.models import Max
from rest_framework import status, permissions, viewsets
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from core.models.users import UserActivity
from support import helpers, http
from api.serializers import users as user_serializer_module
from api.serializers.courses import (
    ReturnQuoteSerializer,
    CreateQuoteSerializer,
    DiscountCodeSerializer,
)
from core.models.courses import Course, Qoutes, DiscountCode
from core.models.users import School

User = get_user_model()


class AllUser(APIView):
    """List all users using pagination and order by created_at"""

    serializer_class = user_serializer_module.UserListSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = helpers.StandardResultsSetPagination

    def get(self, request):
        """Get method to retrieve all user"""
        school_id = request.query_params.get("school_id")
        role = request.query_params.get("role")
        search = request.query_params.get("q")
        users = (
            User.objects.all()
            # .exclude(email=request.user.email)
            .order_by("-date_joined")
        ).order_by(
            "-created_at"
        )  # exclude the admin

        if school_id:
            users = users.filter(school__id=school_id)

        if role:
            users = users.filter(role=role)
        # filter the user by the search (email | full_name | )
        if search:
            users = users.filter(
                Q(email__icontains=search) | Q(full_name__icontains=search)
            )

        paginator = self.pagination_class()

        result_page = paginator.paginate_queryset(users, request)
        serializer = self.serializer_class(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class RetrieveUpdateSingleUser(APIView):
    """Retrieve, update, and delete a single user"""

    serializer_class = user_serializer_module.UserListSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_user(self, user_id):
        """
        Returns a single user or None if the user does not exist.
        """
        user = User.objects.filter(id=user_id).first()
        if not user:
            return None
        return user

    def get(self, request, *args, **kwargs):
        """Retrieve a single user"""

        user = self.get_user(kwargs.get("user_id"))
        if user is not None:
            serializer = self.serializer_class(
                user, many=False, context={"request": request}
            )

            return http.success_response(serializer.data)
        return http.failed_response(status_code=404, message="User not found.")

    def put(self, request, *args, **kwargs):
        """
        Update a single user
        """

        user = self.get_user(kwargs.get("user_id"))
        if user is not None:
            serializer = user_serializer_module.AdminUpdateUserSerializer(
                user, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                serializer = self.serializer_class(user, many=False)
            return http.success_response(data=serializer.data)
        return http.failed_response(status_code=404, message="User not found.")

    def delete(self, request, *args, **kwargs):
        """
        Delete a single user
        """

        user = self.get_user(kwargs.get("user_id"))
        if user is not None:
            user.delete()
            return http.success_response(status_code=200)
        return http.failed_response(status_code=404, message="User not found.")


class AdminDashboardStatsView(APIView):
    """
    API endpoint that provides admin dashboard statistics :
    - Total Users (compared to last week)
    - Active Schools (compared to last month)
    - Courses Enrollment (compared to last term)
    - Total Tutors (compared to last week)
    """

    def get_user_stats(self):
        """Method to get user stat"""
        now = timezone.now()
        current_week = now - timedelta(days=7)
        previous_week = current_week - timedelta(days=7)

        current_users = User.objects.filter(
            date_joined__gte=current_week, is_active=True, deleted_at__isnull=True
        ).count()

        previous_users = User.objects.filter(
            date_joined__range=(previous_week, current_week),
            is_active=True,
            deleted_at__isnull=True,
        ).count()

        total_users = User.objects.filter(
            is_active=True, deleted_at__isnull=True
        ).count()

        percentage = (
            ((current_users - previous_users) / previous_users * 100)
            if previous_users
            else 0
        )

        return {
            "count": total_users,
            "percentage": abs(round(percentage, 1)),
            "trend": "increase" if percentage >= 0 else "decrease",
            "period": "from last week",
        }

    def get_school_stats(self):
        """Method to get school stat"""
        now = timezone.now()
        current_month = now - timedelta(days=30)
        previous_month = current_month - timedelta(days=30)

        current_schools = (
            UserActivity.objects.filter(
                created_at__gte=current_month, user__school__isnull=False
            )
            .values("user__school")
            .distinct()
            .count()
        )

        previous_schools = (
            UserActivity.objects.filter(
                created_at__range=(previous_month, current_month),
                user__school__isnull=False,
            )
            .values("user__school")
            .distinct()
            .count()
        )

        percentage = (
            ((current_schools - previous_schools) / previous_schools * 100)
            if previous_schools
            else 0
        )

        return {
            "count": current_schools,
            "percentage": abs(round(percentage, 1)),
            "trend": "increase" if percentage >= 0 else "decrease",
            "period": "from last month",
        }

    def get_enrollment_stats(self):
        """Method to get course enrollment stat"""
        now = timezone.now()
        # Assuming a term is 4 months
        current_term = now - timedelta(days=120)
        previous_term = current_term - timedelta(days=120)

        current_enrollments = UserActivity.objects.filter(
            created_at__gte=current_term, activity_type="course"
        ).count()

        previous_enrollments = UserActivity.objects.filter(
            created_at__range=(previous_term, current_term), activity_type="course"
        ).count()

        percentage = (
            ((current_enrollments - previous_enrollments) / previous_enrollments * 100)
            if previous_enrollments
            else 0
        )

        return {
            "count": current_enrollments,
            "percentage": abs(round(percentage, 1)),
            "trend": "increase" if percentage >= 0 else "decrease",
            "period": "from last term",
        }

    def get_tutor_stats(self):
        """Tutor stat"""
        now = timezone.now()
        current_week = now - timedelta(days=7)
        previous_week = current_week - timedelta(days=7)

        current_tutors = User.objects.filter(
            date_joined__gte=current_week,
            role=User.Roles.TUTOR,
            is_active=True,
            deleted_at__isnull=True,
        ).count()

        previous_tutors = User.objects.filter(
            date_joined__range=(previous_week, current_week),
            role=User.Roles.TUTOR,
            is_active=True,
            deleted_at__isnull=True,
        ).count()

        total_tutors = User.objects.filter(
            role=User.Roles.TUTOR, is_active=True, deleted_at__isnull=True
        ).count()

        percentage = (
            ((current_tutors - previous_tutors) / previous_tutors * 100)
            if previous_tutors
            else 0
        )

        return {
            "count": total_tutors,
            "percentage": abs(round(percentage, 1)),
            "trend": "increase" if percentage >= 0 else "decrease",
            "period": "from last week",
        }

    def get(self, request):
        """
        Get admin dashboard statistics.
        """
        try:
            search_query = request.query_params.get("search", "")

            response_data = {
                "total_users": self.get_user_stats(),
                "active_schools": self.get_school_stats(),
                "courses_enrollment": self.get_enrollment_stats(),
                "total_tutors": self.get_tutor_stats(),
            }

            return http.success_response(response_data)

        except Exception as e:
            return http.failed_response(message=str(e), status_code=500)


class SchoolsWithUserQuotesView(viewsets.ViewSet):
    """
    Fetch schools where users associated with them have requested quotes
    """

    permission_classes = [permissions.IsAdminUser]
    pagination_class = helpers.StandardResultsSetPagination
    serializer_class = user_serializer_module.SchoolQuotesSerializer

    def get_requested_routes(self, request):
        """Get schools with the last quote request timestamp"""

        school_namne = request.query_params.get("q")
        schools_with_quotes = (
            School.objects.filter(
                id__in=User.objects.filter(qoutes__isnull=False).values_list(
                    "school_id", flat=True
                )
            )
            .annotate(last_request=Max("user__qoutes__created_at"))
            .order_by("-last_request")
        )  # Order by most recent

        if school_namne:
            schools_with_quotes = schools_with_quotes.filter(
                name__icontains=school_namne
            )

        # Paginate the data
        paginator = self.pagination_class()
        paginated_schools = paginator.paginate_queryset(schools_with_quotes, request)

        # Serialize the data
        serializer = self.serializer_class(
            paginated_schools, many=True, context={"request": request}
        )

        # Return paginated response
        return paginator.get_paginated_response(serializer.data)

    def get_single_school_qoutes(self, request, id):
        """get all quotes belonging to a school made by the school admin"""

        _status = request.query_params.get("_")
        term = request.query_params.get("term")
        is_paused = request.query_params.get("is_paused")
        is_active = request.query_params.get("is_active")

        quotes = Qoutes.objects.filter(
            user__school_id=id,  # where id is the school id
        ).order_by("-created_at")

        # apply filters
        if _status:
            quotes = quotes.filter(status__icontains=_status)
        if term:
            quotes = quotes.filter(term__icontains=term)
        if is_paused:
            quotes = quotes.filter(is_paused=(is_paused.lower() == "true"))
        if is_active:
            quotes = quotes.filter(is_active=(is_active.lower() == "true"))

        paginator = self.pagination_class()
        paginated_quotes = paginator.paginate_queryset(quotes, request)

        serializer = ReturnQuoteSerializer(
            paginated_quotes, many=True, context={"request": request}
        )
        # Return paginated response
        return paginator.get_paginated_response(serializer.data)

    def update_quote_request(self, request, id):
        """Approve or reject, or do anything to the quotes"""
        try:
            quote = Qoutes.objects.get(id=id)  # where id is the id of the quotes
            serializer = CreateQuoteSerializer(quote, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return http.success_response(message="Quote updated successfully")
            return http.failed_response(message=serializer.errors)
        except Qoutes.DoesNotExist:
            return http.failed_response(message="Quote not found", status_code=404)


class DiscountCodeViewSet(viewsets.ViewSet):
    """
    API endpoint that allows for creating, retrieving, updating, and deleting discount codes.
    """

    permission_classes = [permissions.IsAdminUser]
    serializer_class = DiscountCodeSerializer
    pagination_class = helpers.StandardResultsSetPagination

    def list(self, request):
        """List all discount codes"""
        discount_codes = DiscountCode.objects.all()
        paginator = self.pagination_class()
        paginated_discount_codes = paginator.paginate_queryset(discount_codes, request)
        serializer = self.serializer_class(
            paginated_discount_codes, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        """Retrieve a specific discount code by ID"""
        try:
            discount_code = DiscountCode.objects.get(pk=pk)
            serializer = self.serializer_class(discount_code)
            return http.success_response(data=serializer.data)
        except DiscountCode.DoesNotExist:
            return http.failed_response(
                message="Discount code not found.",
            )

    def create(self, request):
        """Create a new discount code"""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return http.success_response(data=serializer.data, status_code=201)
        return http.failed_response(
            message=serializer.errors,
        )

    def update(self, request, pk=None):
        """Update an existing discount code"""
        try:
            discount_code = DiscountCode.objects.get(pk=pk)
            serializer = self.serializer_class(
                discount_code, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return http.success_response(data=serializer.data, status_code=200)
            return http.failed_response(
                message=serializer.errors,
            )
        except DiscountCode.DoesNotExist:
            return http.failed_response(
                message="Discount code not found.",
            )

    def destroy(self, request, pk=None):
        """Delete a discount code"""
        try:
            discount_code = DiscountCode.objects.get(pk=pk)
            discount_code.delete()
            return http.success_response(message="Discount code deleted successfully.")
        except DiscountCode.DoesNotExist:
            return http.failed_response(
                message="Discount code not found.",
            )
