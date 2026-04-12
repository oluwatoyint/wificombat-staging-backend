from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.controllers.teachers import TeacherDashboard

# Create a router and register the CoursePathWayViewSet
router = DefaultRouter()
router.register(r"teacher-dashboard", TeacherDashboard, basename="teacher-dashboard")


urlpatterns = [
    # Include the router's URLs
    path("", include(router.urls)),
]
