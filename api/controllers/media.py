from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework import viewsets
from django.contrib.auth import get_user_model

from core.models.media import Media
from support import helpers, http
from api.serializers.media import MediaSerializer


class UploadMedia(viewsets.ViewSet):
    """API view for uploading media"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MediaSerializer

    @action(detail=False, methods=["post"])
    def upload(self, request):
        """
        Handles POST requests to upload media.

        Validates the provided media data, creates a new media object, and saves it to the database.
        Returns a success response with the newly created media object.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return http.success_response(
            data=serializer.data, message="Media uploaded successfully"
        )
