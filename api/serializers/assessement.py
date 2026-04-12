from rest_framework import serializers
from core.models.assessment import DetermineCareerInterest


class DetermineCareerInterestSerializer(serializers.ModelSerializer):
    """Serializer for DetermineCareerInterest model"""

    class Meta:
        model = DetermineCareerInterest
        fields = [
            "id",
            "age_grp",
            "qus",
            "options",
            "created_at",
            "updated_at",
            "pathway",
            "question_type",
            "correct_answer",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RankedCareerInterestSerializer(serializers.Serializer):
    """Serializer for DetermineCareerInterest model"""

    interests = serializers.ListField(child=serializers.CharField(max_length=100))
