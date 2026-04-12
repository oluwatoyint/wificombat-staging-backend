from rest_framework import serializers
from core.models.media import Media


class MediaSerializer(serializers.ModelSerializer):
    """Serializer for Media model"""

    class Meta:
        model = Media
        fields = "__all__"
