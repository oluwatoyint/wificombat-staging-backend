from django.urls import path, include

urlpatterns = [
    path("", include("api.routers.users")),
    path("", include("api.routers.payment")),
    path("", include("api.routers.course")),
    path("", include("api.routers.school_admin")),
    path("", include("api.routers.teacher")),
    path("", include("api.routers.ai_agents")),
    path("assessement/", include("api.routers.assessement")),
    path("administration/", include("api.routers.admin")),
    path("media/", include("api.routers.media")),
]
