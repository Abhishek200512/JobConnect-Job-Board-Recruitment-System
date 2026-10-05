from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password/", views.reset_password, name="reset_password"),

    path("profile/", views.profile_view, name="profile"),
    path("profile/sections/", views.skills_education_view, name="profile_sections"),
    path("settings/", views.seeker_settings, name="seeker_settings"),
    path("seekers/<int:pk>/", views.public_profile, name="public_profile"),
]
