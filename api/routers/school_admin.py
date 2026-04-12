from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.controllers.schoola_admin import QuotesViewSet, SchoolAdminAPIView


router = DefaultRouter()
router.register(r"school-admin", SchoolAdminAPIView, basename="school-admin")


urlpatterns = [
    path(
        "quotes",
        QuotesViewSet.as_view({"get": "list_quotes", "post": "create_quote"}),
        name="quotes",
    ),
    path(
        "quotes/<str:pk>",
        QuotesViewSet.as_view(
            {"get": "retrieve_quote", "put": "update_quote", "delete": "delete_quote"}
        ),
        name="quote-detail",
    ),
    path(
        "quotes/token/send",
        QuotesViewSet.as_view({"post": "send_tokens"}),
        name="send-token",
    ),
    path(
        "quotes/bulk/create/",
        QuotesViewSet.as_view({"post": "bulk_create_quotes"}),
        name="bulk_create_quotes",
    ),
] + router.urls
