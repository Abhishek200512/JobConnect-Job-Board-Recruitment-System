"""User API endpoints under /api/users/."""
from django.urls import path
from rest_framework import generics, permissions

from .models import JobSeekerProfile
from .serializers import SeekerProfileSerializer

from . import api_views


class MeAPIView(generics.RetrieveAPIView):
    """GET /api/users/me/ — current user."""
    serializer_class = None  # replaced below
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        from .serializers import UserSerializer
        return UserSerializer


class MyProfileAPIView(generics.RetrieveUpdateAPIView):
    """GET/PUT/PATCH /api/users/profile/ — seeker profile of the logged-in user."""
    serializer_class = SeekerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = JobSeekerProfile.objects.get_or_create(user=self.request.user)
        return profile


urlpatterns = [
    path("me/", MeAPIView.as_view(), name="api_me"),
    path("profile/", MyProfileAPIView.as_view(), name="api_profile"),
    path("seekers/", api_views.SeekerListAPIView.as_view(), name="api_seekers"),
]
