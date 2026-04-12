from decimal import Decimal
import json
from rest_framework.views import APIView
from rest_framework import permissions
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.conf import settings
from django.db import transaction
from api.payment_providers.payment_provider_factory import PaymentProviderFactory
from api.serializers.payment import FundWalletSerialiazer, TransactionHistorySerializer
from core.models.users import TransactionHistory, UserActivity, Wallet
from support import helpers, http



User = get_user_model()


class WalletFunding(APIView):
    """
    API view for funding a user's wallet. 
    It uses a payment provider to initialize the payment process.
    """
    serializer_class = FundWalletSerialiazer
    permission_classes = [permissions.IsAuthenticated]
    MAX_WALLET_BALANCE = 200000
    MIN_WALLET_BALANCE = 1000

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user and amount from the request
        user = request.user
        amount = serializer.validated_data.get("amount")
        success_url = serializer.validated_data.get("success_url")
        
        try:
            # Get the user's wallet
            wallet = Wallet.objects.get(user=user)
        except Wallet.DoesNotExist:
            return http.failed_response(
                None,
                _("Wallet not found for the user"),
            )

        # Check if amount is at least 1000
        if amount < self.MIN_WALLET_BALANCE:
            return http.failed_response(
                None,
                _("Amount must be at least 1000")
            )
            
        # Check if the new balance would exceed the maximum limit
        if wallet.balance + amount > self.MAX_WALLET_BALANCE:
            return http.failed_response(
                None,
                _(f"This deposit would exceed the maximum wallet balance of {self.MAX_WALLET_BALANCE:,}. Current balance: {wallet.balance:,}")
            )

        # Initialize payment using the payment provider
        try:
            provider = PaymentProviderFactory.create_provider("flutterwave")
            # Generate reference before initializing payment
            reference = provider.generate_transaction_reference(user)
            
            payment_response = provider.initialize_payment(
                amount=float(amount),
                user=user,
                redirect_url="/wallet-fund",
                customer_name=f"{user.full_name}",
                success_url=success_url,
                metadata={"wallet_id": str(wallet.id), "purpose": "wallet_funding"},
            )
            
            # Create pending transaction record
            TransactionHistory.objects.create(
                user=user,
                wallet=wallet,
                reference=reference,
                amount=amount,
                transaction_type='deposit',
                status='pending',
                description='Wallet funding via Flutterwave'
            )

            return http.success_response(
                payment_response,
                _("Payment initialized successfully"),
                200
            )
        except Exception as e:
            return http.failed_response(
                None,
                _(f"Failed to initialize payment: {e}"),
                500,
            )


class FlutterwaveWebhook(APIView):
    
    permission_classes = []
    
    def verify_webhook_signature(self, request):
        """Verify that the webhook is from Flutterwave"""
        if "verif-hash" in request.headers:
            verify_hash = request.headers.get('verif-hash')
            secret_hash = settings.FLUTTERWAVE_SECRET_HASH
            return verify_hash == secret_hash
        
        return False
    
    
    def post(self, request):
        # verify webhook signature
        if not self.verify_webhook_signature(request):
            return http.failed_response(None, "Invalid Signature")

        # Get the webhook data
        payload = json.loads(request.body)
        
        # Verify the event type
        if payload.get('event') != 'charge.completed':
            return http.failed_response(
                None,
                _("Event type not handled")
            )
            
        # Get the transaction data
        tx_data = payload.get('data', {})
        tx_ref = tx_data.get('tx_ref')
        amount = tx_data.get('amount')
            
        # Get metadata
        metadata = payload.get('meta_data', {})
        wallet_id = metadata.get('wallet_id')
        
        if not wallet_id:
            return http.failed_response(
                None,
                _("Invalid metadata"),
            )
            
        # Process the payment in a transaction
        with transaction.atomic():
            try:
                wallet = Wallet.objects.get(id=wallet_id)
                transaction_record = TransactionHistory.objects.get(
                    reference=tx_ref,
                    wallet=wallet,
                    status='pending'
                )
                
                # Verify amount matches
                if transaction_record.amount != amount:
                    transaction_record.status = 'failed'
                    transaction_record.description = 'Amount mismatch in webhook'
                    transaction_record.save()
                    return http.failed_response(
                        None,
                        _("Amount mismatch"),
                    )
                
                # Update wallet balance
                wallet.balance += Decimal(amount)
                wallet.save()
                
                # Update transaction status
                transaction_record.status = 'successful'
                transaction_record.description = 'Payment confirmed via Flutterwave webhook'
                transaction_record.save()
        
                return http.success_response()
                
            except Wallet.DoesNotExist:
                return http.failed_response(
                    None,
                    _("Wallet not found"),
                )
            except TransactionHistory.DoesNotExist:
                # If no pending transaction found, create a new one
                TransactionHistory.objects.create(
                    user=wallet.user,
                    wallet=wallet,
                    reference=tx_ref,
                    amount=amount,
                    transaction_type='deposit',
                    status='successful',
                    description='Direct payment confirmation via Flutterwave webhook'
                )
                
                # Still update the wallet balance
                wallet.balance += Decimal(amount)
                wallet.save()
                
                return http.success_response(
                    None,
                    _("Payment processed successfully"),
                )
                
                
class WalletInfo(APIView):
    """
    API view to retrieve wallet information for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve wallet information for the authenticated user."""
        user = request.user

        try:
            # Fetch the user's wallet
            wallet = Wallet.objects.get(user=user)
            wallet_info = {
                "id": wallet.id,
                "balance": wallet.balance,
                "created_at": wallet.created_at,
                "updated_at": wallet.updated_at,
            }
            return http.success_response(
                wallet_info,
                _("Wallet information retrieved successfully."),
            )
        except Wallet.DoesNotExist:
            return http.failed_response(
                None,
                _("Wallet not found for the user."),
                404
            )
             
                
class WalletTransactions(APIView):
    
    serializer_class = TransactionHistorySerializer
    pagination_class = helpers.StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Retrieve all user transactions and filter by transaction_type if provided."""
        
        user = request.user
        
        # Fetch all transactions related to the user
        transactions = TransactionHistory.objects.filter(user=user).order_by('-created_at')
        
        # Filter by transaction_type if specified in the query parameters
        transaction_type = request.query_params.get('transaction_type', None)
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        # Paginate the results
        paginator = self.pagination_class()
        paginated_transactions = paginator.paginate_queryset(transactions, request)

        # Serialize the transactions
        serializer = self.serializer_class(paginated_transactions, many=True)

        # Return paginated response
        return paginator.get_paginated_response(serializer.data)

