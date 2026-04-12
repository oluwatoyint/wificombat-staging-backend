from django.urls import path
from api.controllers import admin as views
from rest_framework.routers import DefaultRouter

# register DiscountCodeViewSet router
router = DefaultRouter()
router.register(r"discount-codes", views.DiscountCodeViewSet, basename="discount-code")

urlpatterns = [
    path("get-users", views.AllUser.as_view(), name="get_users"),
    path(
        "get-users/<str:user_id>",
        views.RetrieveUpdateSingleUser.as_view(),
        name="get_user",
    ),
    path(
        "dashboard/stats",
        views.AdminDashboardStatsView.as_view(),
        name="dashboard-stats",
    ),
    path(
        "dashboard/requested-quotes",
        views.SchoolsWithUserQuotesView.as_view({"get": "get_requested_routes"}),
        name="get_requested_routes",
    ),
    path(
        "dashboard/requested-quotes/<str:id>",
        views.SchoolsWithUserQuotesView.as_view(
            {"get": "get_single_school_qoutes", "put": "update_quote_request"}
        ),
        name="get_single_school_qoutes",
    ),
] + router.urls
