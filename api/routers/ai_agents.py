from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.controllers.ai_agents import AIAgent

# Create a router and register the CoursePathWayViewSet
router = DefaultRouter()
router.register(r"ai-agents", AIAgent, basename="ai-agent")


urlpatterns = [
    # Include the router's URLs
    path("", include(router.urls)),
]
