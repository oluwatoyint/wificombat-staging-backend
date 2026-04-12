from rest_framework.routers import DefaultRouter
from django.urls import path
from api.controllers import media as views

router = DefaultRouter()

urlpatterns = [
    path(
        "upload",
        views.UploadMedia.as_view({"post": "upload"}),
        name="upload",
    ),
] + router.urls
