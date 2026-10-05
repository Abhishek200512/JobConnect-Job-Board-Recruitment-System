"""Auth API endpoints under /api/auth/."""
from django.urls import path

from . import api_views

app_name = "auth_api"

urlpatterns = [
    path("register/", api_views.RegisterAPIView.as_view(), name="register"),
    path("otp/request/", api_views.OTPRequestAPIView.as_view(), name="otp_request"),
    path("otp/verify/", api_views.OTPVerifyAPIView.as_view(), name="otp_verify"),
    path("login-status/", api_views.LoginStatusAPIView.as_view(), name="login_status"),
]
