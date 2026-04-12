from rest_framework.routers import DefaultRouter
from django.urls import path
from api.controllers import payment as views


router = DefaultRouter()

urlpatterns = [
    path("wallet/fund", views.WalletFunding.as_view(), name="wallet-funding"),
    path("webhook/flutterwave", views.FlutterwaveWebhook.as_view(), name="flutterwave-webhook"),
    path("wallet/info", views.WalletInfo.as_view(), name="wallet-info"),
    path("wallet/transactions", views.WalletTransactions.as_view(), name="wallet-transactions"),
] + router.urls
