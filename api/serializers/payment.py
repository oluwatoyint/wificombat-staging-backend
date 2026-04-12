from rest_framework import serializers
from core.models.users import TransactionHistory

class FundWalletSerialiazer(serializers.Serializer):
    """Serializer for viewing or updating a user's wallet information."""
    amount = serializers.IntegerField()
    success_url = serializers.URLField()
    

class TransactionHistorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TransactionHistory
        fields = [
            "id",
            "user",
            "wallet",
            "reference",
            "amount",
            "transaction_type",
            "status",
            "description",
            "created_at",
            "updated_at",
        ]