from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.controllers.assessement import (
    DetermineCareerInterestViewSet,
)

# register the view set
router = DefaultRouter()
router.register(
    r"determine-career-interest",
    DetermineCareerInterestViewSet,
    basename="determine-career-interest",
)
urlpatterns = [
    # Include the router's URLs
    path("", include(router.urls)),
]
