from rest_framework.routers import DefaultRouter
from django.urls import path
from api.controllers import users as views

router = DefaultRouter()
# router.register('user-password', views.Profile, basename='user-profile')



urlpatterns = [
    path("retrieve-schools", views.SchoolAPIView.as_view(), name="get-schools"),
    path("register", views.UserRegistration.as_view(), name="register"),
    path(
        "resend-activation-token",
        views.ResendActivationToken.as_view(),
        name="resend_activation_token",
    ),
    path("verify-token", views.VerifyToken.as_view(), name="verify-token"),
    path("login", views.LoginView.as_view(), name="login"),
    path("admin-login", views.AdminLoginView.as_view(), name="admin-login"),
    path(
        "request-password-reset",
        views.RequestPasswordReset.as_view(),
        name="request-password-reset",
    ),
    path(
        "set-new-password",
        views.SetNewPasswordAPIView.as_view(),
        name="set-new-password",
    ),
    path(
        "dashboard/change-password",
        views.Profile.as_view({"put": "change_password_in_dashboard"}),
        name="change-password",
    ),
    path(
        "dashboard/update-profile",
        views.Profile.as_view({"put": "update_profile"}),
        name="update-profile",
    ),
    path(
        "profile/user/<str:user_id>",
        views.Profile.as_view({"get": "get_single_user_profile"}),
        name="get-profile",
    ),
    path(
        "profile/user/<str:user_id>/activities",
        views.Profile.as_view({"get": "get_user_activities"}),
        name="activities",
    ),
    path(
        "recent-activities",
        views.Profile.as_view({"get": "recent_activities"}),
        name="recent-activities",
    ),

] + router.urls
